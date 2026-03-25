"""
Custom exception handler for the InsightBoard API.
Provides consistent error response format across all endpoints.
"""

import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all errors consistently as:
    {
        "error": {
            "code": "error_code",
            "message": "Human-readable message",
            "details": {...}  // optional
        }
    }
    """
    # Let DRF handle it first for proper status codes
    response = exception_handler(exc, context)

    if response is None:
        # Handle unhandled exceptions
        if isinstance(exc, DjangoValidationError):
            data = _format_error(
                code="validation_error",
                message="Validation failed.",
                details={"errors": exc.messages if hasattr(exc, "messages") else [str(exc)]},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(exc, Http404):
            data = _format_error(
                code="not_found",
                message="The requested resource was not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        if isinstance(exc, PermissionDenied):
            data = _format_error(
                code="permission_denied",
                message="You do not have permission to perform this action.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
            return Response(data, status=status.HTTP_403_FORBIDDEN)

        # Unexpected server error
        logger.exception("Unhandled exception in %s", context.get("view", "unknown"))
        data = _format_error(
            code="internal_error",
            message="An unexpected error occurred. Please try again later.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Reformat DRF-handled exceptions
    error_code = _get_error_code(exc)
    error_message = _get_error_message(exc, response)
    details = None

    if isinstance(exc, ValidationError):
        details = {"fields": response.data}
        error_message = "Validation failed."
    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        error_code = "authentication_error"
        error_message = str(exc.detail) if hasattr(exc, "detail") else "Authentication required."

    response.data = _format_error(
        code=error_code,
        message=error_message,
        details=details,
        status_code=response.status_code,
    )

    return response


def _format_error(code: str, message: str, details: dict = None, status_code: int = 400) -> dict:
    """Create a consistently formatted error response body."""
    error = {
        "error": {
            "code": code,
            "message": message,
            "status": status_code,
        }
    }
    if details:
        error["error"]["details"] = details
    return error


def _get_error_code(exc) -> str:
    """Map exception type to a machine-readable error code."""
    code_map = {
        ValidationError: "validation_error",
        AuthenticationFailed: "authentication_failed",
        NotAuthenticated: "not_authenticated",
        PermissionDenied: "permission_denied",
        Http404: "not_found",
    }

    for exc_class, code in code_map.items():
        if isinstance(exc, exc_class):
            return code

    if hasattr(exc, "default_code"):
        return exc.default_code

    return "api_error"


def _get_error_message(exc, response) -> str:
    """Extract a human-readable message from the exception."""
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list) and detail:
            return str(detail[0])
        if isinstance(detail, dict):
            first_key = next(iter(detail), None)
            if first_key:
                val = detail[first_key]
                if isinstance(val, list) and val:
                    return str(val[0])
                return str(val)
    return "An error occurred."
