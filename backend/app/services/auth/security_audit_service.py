"""
Security Audit Service for Phase 17.
Records and queries security audit events with strict redaction of sensitive credentials.
"""

from typing import Any, Dict, List, Optional

from backend.app.core.logging import logger
from backend.app.engines.auth.models import SecurityAuditEvent, SecurityEventType
from backend.app.engines.auth.repository import auth_repo


class SecurityAuditService:
    """
    Coordinates recording and retrieval of security audit events.
    Enforces that passwords, raw tokens, and secret parameters are never captured.
    """

    FORBIDDEN_METADATA_KEYS = {
        "password",
        "new_password",
        "current_password",
        "token",
        "token_hash",
        "password_hash",
        "secret",
        "api_key",
    }

    def record_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        result: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None,
        request_ip: Optional[str] = None,
    ) -> SecurityAuditEvent:
        # Sanitize metadata to strip any accidental sensitive keys
        clean_meta = {}
        if metadata:
            for k, v in metadata.items():
                if k.lower() in self.FORBIDDEN_METADATA_KEYS:
                    clean_meta[k] = "[REDACTED]"
                else:
                    clean_meta[k] = v

        event = SecurityAuditEvent(
            user_id=user_id,
            workspace_id=workspace_id,
            project_id=project_id,
            event_type=event_type,
            result=result,
            metadata=clean_meta,
            request_ip=request_ip,
        )
        auth_repo.record_audit_event(event)
        logger.info(
            f"SecurityAudit: event={event_type.value} result={result} "
            f"user={user_id or 'anon'} ws={workspace_id or 'none'}"
        )
        return event

    def query_events(
        self,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[SecurityAuditEvent]:
        return auth_repo.query_audit_events(
            user_id=user_id,
            workspace_id=workspace_id,
            limit=limit,
        )


# Global instance
security_audit_service = SecurityAuditService()
