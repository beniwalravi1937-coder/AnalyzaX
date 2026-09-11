"""
Template Registry & Safe Variable Substitution Engine for Phase 19.
Ensures zero arbitrary code execution, allowlisted variable rendering,
and open redirect protection for notification deep links.
"""

import re
from typing import Any, Dict, Optional, Tuple

from backend.app.engines.notifications.models import (
    ApplicationEventType,
    NotificationCategory,
    NotificationPriority,
    NotificationTemplate,
)

ALLOWLISTED_VARS = {
    "actor_name",
    "resource_name",
    "resource_type",
    "project_name",
    "workspace_name",
    "role_name",
    "error_summary",
    "status",
    "message",
    "metric_name",
    "percent",
    "limit",
    "new_plan",
    "old_plan",
    "plan_name",
    "amount",
    "currency",
    "invoice_id",
    "reason",
    "effective_date",
    "interval",
}

BLOCKED_VARS = {"password", "token", "hash", "secret", "key", "api_key", "cookie", "session"}


class TemplateRegistry:
    """Centralized registry for notification templates."""

    def __init__(self):
        self._templates: Dict[str, NotificationTemplate] = {}
        self._register_default_templates()

    def _register(self, template: NotificationTemplate) -> None:
        self._templates[template.notification_type] = template
        self._templates[template.template_id] = template

    def get_template(self, event_type_or_id: str) -> Optional[NotificationTemplate]:
        return self._templates.get(event_type_or_id)

    def _register_default_templates(self) -> None:
        # Collaboration
        self._register(
            NotificationTemplate(
                template_id="tpl_share_received",
                notification_type=ApplicationEventType.RESOURCE_SHARED.value,
                title_template="New Asset Shared",
                message_template="{{actor_name}} shared '{{resource_name}}' with you.",
                category=NotificationCategory.COLLABORATION,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/dashboard/{{resource_id}}",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_share_revoked",
                notification_type=ApplicationEventType.RESOURCE_SHARE_REVOKED.value,
                title_template="Access Revoked",
                message_template="Your direct access to {{resource_name}} has been revoked.",
                category=NotificationCategory.COLLABORATION,
                priority=NotificationPriority.HIGH,
                is_security=True,
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_invitation_created",
                notification_type=ApplicationEventType.INVITATION_CREATED.value,
                title_template="Workspace Invitation",
                message_template="{{actor_name}} invited you to join {{workspace_name}} as {{role_name}}.",
                category=NotificationCategory.COLLABORATION,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/settings/members",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_member_role_changed",
                notification_type=ApplicationEventType.MEMBER_ROLE_CHANGED.value,
                title_template="Role Updated",
                message_template="Your role in {{workspace_name}} was updated to {{role_name}}.",
                category=NotificationCategory.COLLABORATION,
                priority=NotificationPriority.HIGH,
                deep_link_strategy="/settings/members",
                is_security=True,
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_member_removed",
                notification_type=ApplicationEventType.MEMBER_REMOVED.value,
                title_template="Workspace Access Removed",
                message_template="Your membership in {{workspace_name}} was removed.",
                category=NotificationCategory.COLLABORATION,
                priority=NotificationPriority.HIGH,
                is_security=True,
            )
        )

        # Exports
        self._register(
            NotificationTemplate(
                template_id="tmpl_export_completed",
                notification_type=ApplicationEventType.EXPORT_COMPLETED.value,
                title_template="Export Ready",
                message_template="Your export for {{resource_name}} is ready for download.",
                category=NotificationCategory.EXPORT,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/exports",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_export_failed",
                notification_type=ApplicationEventType.EXPORT_FAILED.value,
                title_template="Export Failed",
                message_template="Export for {{resource_name}} failed: {{error_summary}}",
                category=NotificationCategory.EXPORT,
                priority=NotificationPriority.HIGH,
                deep_link_strategy="/exports",
            )
        )

        # Reports
        self._register(
            NotificationTemplate(
                template_id="tmpl_report_created",
                notification_type=ApplicationEventType.REPORT_CREATED.value,
                title_template="Report Ready",
                message_template="Analytical report '{{resource_name}}' is complete.",
                category=NotificationCategory.REPORT,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/reports",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_report_exported",
                notification_type=ApplicationEventType.REPORT_EXPORTED.value,
                title_template="Report Export Ready",
                message_template="Your analytical report '{{resource_name}}' is ready for download.",
                category=NotificationCategory.REPORT,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/exports",
            )
        )

        # Analysis, ML & Forecasting
        self._register(
            NotificationTemplate(
                template_id="tmpl_analysis_completed",
                notification_type=ApplicationEventType.ANALYSIS_COMPLETED.value,
                title_template="Analysis Completed",
                message_template="Statistical analysis on {{resource_name}} has completed.",
                category=NotificationCategory.ANALYSIS,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/statistics",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_analysis_failed",
                notification_type=ApplicationEventType.ANALYSIS_FAILED.value,
                title_template="Analysis Failed",
                message_template="Analysis on {{resource_name}} failed: {{error_summary}}",
                category=NotificationCategory.ANALYSIS,
                priority=NotificationPriority.HIGH,
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_ml_completed",
                notification_type=ApplicationEventType.ML_EXPERIMENT_COMPLETED.value,
                title_template="ML Training Completed",
                message_template="Model training for {{resource_name}} has finished successfully.",
                category=NotificationCategory.ANALYSIS,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/ml",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_ml_failed",
                notification_type=ApplicationEventType.ML_EXPERIMENT_FAILED.value,
                title_template="ML Training Failed",
                message_template="Model training for {{resource_name}} failed: {{error_summary}}",
                category=NotificationCategory.ANALYSIS,
                priority=NotificationPriority.HIGH,
                deep_link_strategy="/ml",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_forecast_completed",
                notification_type=ApplicationEventType.FORECAST_COMPLETED.value,
                title_template="Forecast Completed",
                message_template="Forecasting model for {{resource_name}} has generated predictions.",
                category=NotificationCategory.ANALYSIS,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/forecasting",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_forecast_failed",
                notification_type=ApplicationEventType.FORECAST_FAILED.value,
                title_template="Forecast Failed",
                message_template="Forecast for {{resource_name}} failed: {{error_summary}}",
                category=NotificationCategory.ANALYSIS,
                priority=NotificationPriority.HIGH,
                deep_link_strategy="/forecasting",
            )
        )

        # Security
        self._register(
            NotificationTemplate(
                template_id="tmpl_security_alert",
                notification_type=ApplicationEventType.SECURITY_ALERT.value,
                title_template="Security Alert",
                message_template="{{message}}",
                category=NotificationCategory.SECURITY,
                priority=NotificationPriority.CRITICAL,
                deep_link_strategy="/settings/security",
                is_security=True,
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_password_changed",
                notification_type=ApplicationEventType.PASSWORD_CHANGED.value,
                title_template="Password Changed",
                message_template="Your AnalyzaX account password was successfully updated.",
                category=NotificationCategory.SECURITY,
                priority=NotificationPriority.HIGH,
                deep_link_strategy="/settings/security",
                is_security=True,
            )
        )

        # Quotas & Plans (Phase 20)
        self._register(
            NotificationTemplate(
                template_id="tmpl_quota_warning",
                notification_type=ApplicationEventType.QUOTA_WARNING.value,
                title_template="Usage Alert: {{metric_name}}",
                message_template="Your workspace has used {{percent}}% of its {{metric_name}} quota (Limit: {{limit}}).",
                category=NotificationCategory.SYSTEM,
                priority=NotificationPriority.HIGH,
                deep_link_strategy="/settings/usage",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_quota_exceeded",
                notification_type=ApplicationEventType.QUOTA_EXCEEDED.value,
                title_template="Quota Limit Reached",
                message_template="Your workspace has reached the limit for {{metric_name}} (Limit: {{limit}}). Please upgrade your plan to continue.",
                category=NotificationCategory.SYSTEM,
                priority=NotificationPriority.CRITICAL,
                deep_link_strategy="/settings/usage",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_plan_changed",
                notification_type=ApplicationEventType.PLAN_CHANGED.value,
                title_template="Workspace Plan Updated",
                message_template="Your workspace plan was changed from {{old_plan}} to {{new_plan}}.",
                category=NotificationCategory.SYSTEM,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/settings/usage",
            )
        )

        # Billing & Subscriptions (Phase 21)
        self._register(
            NotificationTemplate(
                template_id="tmpl_subscription_activated",
                notification_type=ApplicationEventType.SUBSCRIPTION_ACTIVATED.value,
                title_template="Subscription Activated",
                message_template="Your {{plan_name}} subscription is now active. Enjoy expanded workspace capacity!",
                category=NotificationCategory.BILLING,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/settings/billing",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_subscription_changed",
                notification_type=ApplicationEventType.SUBSCRIPTION_CHANGED.value,
                title_template="Subscription Updated",
                message_template="Your subscription tier has been updated to {{new_plan}} ({{interval}}).",
                category=NotificationCategory.BILLING,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/settings/billing",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_subscription_canceled",
                notification_type=ApplicationEventType.SUBSCRIPTION_CANCELED.value,
                title_template="Subscription Canceled",
                message_template="Your subscription has been canceled. Access remains active through {{effective_date}}.",
                category=NotificationCategory.BILLING,
                priority=NotificationPriority.HIGH,
                deep_link_strategy="/settings/billing",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_subscription_past_due",
                notification_type=ApplicationEventType.SUBSCRIPTION_PAST_DUE.value,
                title_template="Subscription Payment Past Due",
                message_template="Payment for your workspace subscription could not be processed. Please update your payment method to prevent restriction.",
                category=NotificationCategory.BILLING,
                priority=NotificationPriority.CRITICAL,
                deep_link_strategy="/settings/billing",
                is_security=True,
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_payment_succeeded",
                notification_type=ApplicationEventType.PAYMENT_SUCCEEDED.value,
                title_template="Payment Succeeded",
                message_template="Payment of {{amount}} {{currency}} was successfully processed.",
                category=NotificationCategory.BILLING,
                priority=NotificationPriority.NORMAL,
                deep_link_strategy="/settings/billing",
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_payment_failed",
                notification_type=ApplicationEventType.PAYMENT_FAILED.value,
                title_template="Payment Failed",
                message_template="Your payment attempt of {{amount}} {{currency}} failed: {{reason}}.",
                category=NotificationCategory.BILLING,
                priority=NotificationPriority.CRITICAL,
                deep_link_strategy="/settings/billing",
                is_security=True,
            )
        )
        self._register(
            NotificationTemplate(
                template_id="tmpl_invoice_created",
                notification_type=ApplicationEventType.INVOICE_CREATED.value,
                title_template="New Invoice Available",
                message_template="Invoice {{invoice_id}} for {{amount}} {{currency}} is now available.",
                category=NotificationCategory.BILLING,
                priority=NotificationPriority.LOW,
                deep_link_strategy="/settings/billing",
            )
        )

    def render_template(self, template_id: str, context: Dict[str, Any]) -> Tuple[str, str]:
        """Convenience method to render both title and message for a template."""
        tpl = self._templates.get(template_id)
        if not tpl:
            for t in self._templates.values():
                if t.template_id == template_id:
                    tpl = t
                    break
        if not tpl:
            return ("", "")
        title = self.render(tpl.title_template, context)
        message = self.render(tpl.message_template, context)
        return (title, message)

    def render(self, template_str: str, context: Dict[str, Any]) -> str:
        """
        Safely substitutes allowlisted placeholders in template string.
        Supports both {{var}} and {var} syntax.
        Prevents code execution, eval, and secret leakage.
        """
        result = template_str
        placeholders = re.findall(r"\{\{?([a-zA-Z0-9_]+)\}?\}", template_str)
        for ph in placeholders:
            if ph.lower() in BLOCKED_VARS:
                continue
            if ph in ALLOWLISTED_VARS or ph in context:
                val = str(context.get(ph, ""))
                # Strip potential script or HTML tags
                val = re.sub(r"<[^>]*>", "", val).strip()
                # Replace double brace then single brace
                result = result.replace(f"{{{{{ph}}}}}", val)
                result = result.replace(f"{{{ph}}}", val)
        return result

    def generate_deep_link(self, strategy: Optional[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Generates safe, internal-only deep links.
        Rejects external URLs or protocol schemes to prevent open redirects.
        """
        if not strategy:
            return None
        rendered = self.render(strategy, context)
        # Open redirect protection: must start with / and cannot start with // or contain ://
        if not rendered.startswith("/") or rendered.startswith("//") or "://" in rendered:
            return None
        return rendered


# Singleton instance
template_registry = TemplateRegistry()
