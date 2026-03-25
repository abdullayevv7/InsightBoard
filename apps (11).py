"""
Alert Celery tasks: periodic evaluation, notification dispatch.
"""

import logging

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def check_all_active_alerts():
    """
    Evaluate all active alert rules. Runs every 5 minutes via Celery Beat.
    Checks each rule's metric query, evaluates conditions, and triggers
    notifications when thresholds are breached.
    """
    from .models import AlertRule

    active_rules = AlertRule.objects.filter(
        status__in=["active", "triggered"],
    ).select_related("data_source").prefetch_related("conditions")

    evaluated = 0
    triggered = 0

    for rule in active_rules:
        try:
            result = evaluate_single_alert(str(rule.id))
            evaluated += 1
            if result.get("triggered"):
                triggered += 1
        except Exception:
            logger.exception("Error evaluating alert rule %s (%s).", rule.id, rule.name)

    logger.info(
        "Alert check complete: %d rules evaluated, %d triggered.",
        evaluated, triggered,
    )

    return {"evaluated": evaluated, "triggered": triggered}


def evaluate_single_alert(alert_id: str, dry_run: bool = False) -> dict:
    """
    Evaluate a single alert rule against its data source.

    Args:
        alert_id: UUID of the AlertRule to evaluate.
        dry_run: If True, evaluate but do not trigger notifications or update state.

    Returns:
        Dictionary with evaluation results.
    """
    from .models import AlertRule, AlertHistory
    from apps.datasources.services import get_connector, DataFetchError

    try:
        rule = AlertRule.objects.select_related(
            "data_source"
        ).prefetch_related("conditions").get(id=alert_id)
    except AlertRule.DoesNotExist:
        logger.error("AlertRule %s not found.", alert_id)
        return {"error": "Alert rule not found."}

    result = {
        "alert_id": str(rule.id),
        "alert_name": rule.name,
        "triggered": False,
        "current_value": None,
        "conditions_met": [],
        "dry_run": dry_run,
    }

    try:
        connector = get_connector(rule.data_source)
        query_result = connector.execute_query(rule.metric_query)

        rows = query_result.get("rows", [])
        if not rows:
            result["current_value"] = None
            result["message"] = "No data returned from metric query."
            if not dry_run:
                rule.last_evaluated_at = timezone.now()
                rule.last_value = None
                rule.save(update_fields=["last_evaluated_at", "last_value"])
            return result

        first_row = rows[0]
        current_value = first_row.get(rule.metric_field)

        if current_value is not None:
            try:
                current_value = float(current_value)
            except (ValueError, TypeError):
                pass

        result["current_value"] = current_value
        previous_value = rule.last_value

        conditions = rule.conditions.all()
        conditions_met = []
        all_and_met = True
        any_or_met = False

        for condition in conditions:
            met = condition.evaluate(current_value, previous_value)
            conditions_met.append({
                "operator": condition.get_operator_display(),
                "threshold": condition.threshold_value,
                "met": met,
            })

            if condition.logic_operator == "and":
                if not met:
                    all_and_met = False
            else:
                if met:
                    any_or_met = True

        has_or_conditions = any(c.logic_operator == "or" for c in conditions)
        alert_triggered = all_and_met if not has_or_conditions else (all_and_met or any_or_met)

        result["conditions_met"] = conditions_met
        result["triggered"] = alert_triggered

        if not dry_run:
            rule.last_evaluated_at = timezone.now()
            rule.last_value = current_value if isinstance(current_value, (int, float)) else None

            if alert_triggered:
                rule.current_failure_count += 1

                if rule.current_failure_count >= rule.consecutive_failures:
                    should_notify = True

                    if rule.is_muted:
                        should_notify = False

                    if rule.last_triggered_at and rule.cooldown_minutes > 0:
                        cooldown_elapsed = (
                            timezone.now() - rule.last_triggered_at
                        ).total_seconds() / 60
                        if cooldown_elapsed < rule.cooldown_minutes:
                            should_notify = False

                    if rule.status != "triggered":
                        rule.status = "triggered"
                        rule.last_triggered_at = timezone.now()

                    history = AlertHistory.objects.create(
                        alert_rule=rule,
                        event_type="triggered",
                        metric_value=current_value if isinstance(current_value, (int, float)) else None,
                        threshold_value=conditions[0].threshold_value if conditions else None,
                        message=f"Alert triggered: {rule.name} - value {current_value}",
                        notification_sent=should_notify,
                    )

                    if should_notify:
                        _send_alert_notifications(rule, history, current_value)

            else:
                if rule.status == "triggered" and rule.current_failure_count > 0:
                    rule.status = "active"
                    rule.current_failure_count = 0

                    AlertHistory.objects.create(
                        alert_rule=rule,
                        event_type="resolved",
                        metric_value=current_value if isinstance(current_value, (int, float)) else None,
                        message=f"Alert resolved: {rule.name} - value {current_value}",
                        resolved_at=timezone.now(),
                        notification_sent=rule.notify_on_resolve,
                    )

                    if rule.notify_on_resolve and not rule.is_muted:
                        _send_resolve_notifications(rule, current_value)

                rule.current_failure_count = 0

            rule.save(update_fields=[
                "last_evaluated_at", "last_value", "status",
                "current_failure_count", "last_triggered_at",
            ])

    except DataFetchError as e:
        result["error"] = str(e)
        logger.error("Failed to fetch metric for alert %s: %s", alert_id, str(e))

    return result


def _send_alert_notifications(rule, history, current_value):
    """Send notifications via configured channels when an alert triggers."""
    channels_used = []

    for channel in rule.notification_channels:
        channel_type = channel.get("type", "")
        target = channel.get("target", "")

        if channel_type == "email" and target:
            try:
                send_mail(
                    subject=f"[InsightBoard Alert] {rule.get_severity_display()}: {rule.name}",
                    message=(
                        f"Alert: {rule.name}\n"
                        f"Severity: {rule.get_severity_display()}\n"
                        f"Current Value: {current_value}\n"
                        f"Description: {rule.description}\n\n"
                        f"This alert was triggered at {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[target],
                    fail_silently=True,
                )
                channels_used.append({"type": "email", "target": target, "success": True})
            except Exception as e:
                channels_used.append({"type": "email", "target": target, "success": False, "error": str(e)})
                logger.error("Failed to send email alert to %s: %s", target, str(e))

        elif channel_type == "webhook" and target:
            try:
                import requests
                payload = {
                    "alert_name": rule.name,
                    "severity": rule.severity,
                    "current_value": current_value,
                    "description": rule.description,
                    "triggered_at": timezone.now().isoformat(),
                }
                requests.post(target, json=payload, timeout=10)
                channels_used.append({"type": "webhook", "target": target, "success": True})
            except Exception as e:
                channels_used.append({"type": "webhook", "target": target, "success": False, "error": str(e)})
                logger.error("Failed to send webhook alert to %s: %s", target, str(e))

    history.notification_channels_used = channels_used
    history.save(update_fields=["notification_channels_used"])


def _send_resolve_notifications(rule, current_value):
    """Send notifications when an alert resolves."""
    for channel in rule.notification_channels:
        channel_type = channel.get("type", "")
        target = channel.get("target", "")

        if channel_type == "email" and target:
            try:
                send_mail(
                    subject=f"[InsightBoard Alert Resolved] {rule.name}",
                    message=(
                        f"Alert Resolved: {rule.name}\n"
                        f"Current Value: {current_value}\n\n"
                        f"This alert resolved at {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[target],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error("Failed to send resolve email to %s: %s", target, str(e))
