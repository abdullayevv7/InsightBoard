/**
 * Alerts API module: rules, conditions, history, actions.
 */

import apiClient from "./client";

export interface AlertCondition {
  id: string;
  operator: string;
  operator_display: string;
  threshold_value: number | null;
  comparison_window_minutes: number;
  logic_operator: "and" | "or";
  order: number;
}

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  severity: "info" | "warning" | "critical" | "emergency";
  severity_display: string;
  status: "active" | "paused" | "triggered" | "resolved";
  status_display: string;
  data_source: string;
  data_source_name: string;
  metric_query: string;
  metric_field: string;
  evaluation_interval_minutes: number;
  consecutive_failures: number;
  notification_channels: NotificationChannel[];
  notify_on_resolve: boolean;
  cooldown_minutes: number;
  last_triggered_at: string | null;
  last_evaluated_at: string | null;
  last_value: number | null;
  muted_until: string | null;
  is_muted: boolean;
  tags: string[];
  conditions: AlertCondition[];
  recent_history?: AlertHistoryEntry[];
  created_by: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface NotificationChannel {
  type: "email" | "slack" | "webhook";
  target: string;
}

export interface AlertHistoryEntry {
  id: string;
  alert_rule: string;
  alert_name: string;
  event_type: "triggered" | "resolved" | "acknowledged" | "muted" | "escalated";
  event_type_display: string;
  metric_value: number | null;
  threshold_value: number | null;
  message: string;
  notification_sent: boolean;
  acknowledged_by: string | null;
  acknowledged_by_name: string | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface AlertRuleCreatePayload {
  name: string;
  description?: string;
  severity: string;
  data_source: string;
  metric_query: string;
  metric_field: string;
  evaluation_interval_minutes?: number;
  consecutive_failures?: number;
  notification_channels?: NotificationChannel[];
  notify_on_resolve?: boolean;
  cooldown_minutes?: number;
  tags?: string[];
  conditions?: Omit<AlertCondition, "id" | "operator_display">[];
}

export const alertsApi = {
  listRules: (params?: Record<string, string>) =>
    apiClient.get<{ results: AlertRule[] }>("/alerts/rules/", { params }),

  getRule: (id: string) =>
    apiClient.get<AlertRule>(`/alerts/rules/${id}/`),

  createRule: (data: AlertRuleCreatePayload) =>
    apiClient.post<AlertRule>("/alerts/rules/", data),

  updateRule: (id: string, data: Partial<AlertRuleCreatePayload>) =>
    apiClient.patch<AlertRule>(`/alerts/rules/${id}/`, data),

  deleteRule: (id: string) =>
    apiClient.delete(`/alerts/rules/${id}/`),

  pauseRule: (id: string) =>
    apiClient.post<AlertRule>(`/alerts/rules/${id}/pause/`),

  resumeRule: (id: string) =>
    apiClient.post<AlertRule>(`/alerts/rules/${id}/resume/`),

  muteRule: (id: string, mutedUntil: string, reason?: string) =>
    apiClient.post<AlertRule>(`/alerts/rules/${id}/mute/`, {
      muted_until: mutedUntil,
      reason,
    }),

  unmuteRule: (id: string) =>
    apiClient.post<AlertRule>(`/alerts/rules/${id}/unmute/`),

  testRule: (id: string) =>
    apiClient.post(`/alerts/rules/${id}/test/`),

  // History
  listHistory: (params?: Record<string, string>) =>
    apiClient.get<{ results: AlertHistoryEntry[] }>("/alerts/history/", { params }),

  acknowledgeAlert: (historyId: string) =>
    apiClient.post<AlertHistoryEntry>(`/alerts/history/${historyId}/acknowledge/`),
};
