# AnalyzaX — Notification, Activity Center & Collaboration Communication Architecture

This document formalizes the architecture, domain models, and operational guarantees for **Phase 19: Enterprise-Grade Notifications, Activity Center & Collaboration Communication**.

---

## 1. Architectural Foundations & Principles

The notification system in AnalyzaX is designed around foundational enterprise guarantees:

1. **Notifications are Communication Metadata, Never an Authorization Mechanism:**
   Notifications inform users of actions, milestones, and shared resources. They do not grant, check, or modify access permissions. Every deep link navigated from a notification is strictly re-authorized on the server at route boundaries.
2. **Deterministic & Auditable Lifecycle:**
   Every notification originates from a real, discrete `ApplicationEvent` or a strictly validated service operation. No synthetic, fake, or unrecorded notifications exist.
3. **Cross-User & Workspace Isolation:**
   Notification reads, unread counts, archives, and preference modifications are strictly scoped to the authenticated session user (`current_user.user_id`). Users cannot inspect or mutate records belonging to other accounts (IDOR protection).
4. **Security Non-Suppressibility Guarantee:**
   Security-critical alerts (password modifications, credential revocations, unauthorized access attempts, and administrative security events) are strictly non-suppressible. User preferences cannot disable these alerts.
5. **Separation of Activity Feeds from Security Audit Logs:**
   User-facing collaborative activity feeds (`ActivityFeedItem`) provide transparency for project and workspace milestones. They are completely decoupled from administrative security audit logs (`SecurityAuditEvent`), ensuring sensitive security anomalies and credentials are never exposed in collaborative views.

---

## 2. Domain Models & Layering

### A. Normalized Application Event Model (`ApplicationEvent`)
Emitted by domain services across the platform:
- **Enums:** `ApplicationEventType` covers:
  - Auth: `USER_REGISTERED`, `USER_LOGIN`, `USER_LOGOUT`, `PASSWORD_CHANGED`, `PASSWORD_RESET`, `SESSION_REVOKED`, `SECURITY_ALERT`
  - Projects: `PROJECT_CREATED`, `PROJECT_ARCHIVED`, `PROJECT_RESTORED`
  - Membership & Invitations: `INVITATION_CREATED`, `INVITATION_ACCEPTED`, `INVITATION_REVOKED`, `MEMBER_ADDED`, `MEMBER_REMOVED`, `MEMBER_ROLE_CHANGED`
  - Collaboration: `RESOURCE_SHARED`, `RESOURCE_SHARE_REVOKED`, `SHARE_LINK_CREATED`, `SHARE_LINK_REVOKED`
  - Datasets & Lineage: `DATASET_CREATED`, `DATASET_VERSION_CREATED`, `DATASET_ARCHIVED`, `DATASET_RESTORED`
  - Analysis & Models: `ANALYSIS_STARTED`, `ANALYSIS_COMPLETED`, `ANALYSIS_FAILED`, `ML_EXPERIMENT_COMPLETED`, `ML_EXPERIMENT_FAILED`, `FORECAST_COMPLETED`, `FORECAST_FAILED`
  - Exports & Reports: `EXPORT_COMPLETED`, `EXPORT_FAILED`, `REPORT_CREATED`, `REPORT_UPDATED`, `REPORT_EXPORTED`
  - Dashboards: `DASHBOARD_CREATED`, `DASHBOARD_UPDATED`

### B. Notification Entity (`Notification`)
- `notification_id`: Globally unique identifier (`ntf_...`)
- `recipient_user_id`: Target recipient
- `event_id`: Originating `ApplicationEvent` reference
- `category`: `COLLABORATION`, `PROJECT`, `DATA`, `ANALYSIS`, `EXPORT`, `REPORT`, `SECURITY`, `SYSTEM`
- `priority`: `LOW`, `NORMAL`, `HIGH`, `CRITICAL`
- `status`: `UNREAD`, `READ`, `EXPIRED`, `ARCHIVED`
- `deep_link`: Safe, internal same-origin relative path (e.g. `/projects/{id}`, `/dataset?id={id}`)
- `created_at`, `read_at`, `expires_at`: ISO 8601 timestamps
- `metadata`: Sanitized contextual payload

---

## 3. Template Engine & Security Hardening

### Allowlisted Substitution (Zero Eval / Zero Code Execution)
All notification titles and bodies are rendered via the configuration-driven `TemplateRegistry`:
- Substitution variables are strictly extracted from an allowlist of safe parameters:
  `actor_name`, `resource_name`, `resource_type`, `project_name`, `workspace_name`, `permission`, `item_count`, `format`, `reason`, `ip_address`.
- Raw secrets, password hashes, and invitation tokens are strictly scrubbed before template rendering.
- Templating utilizes safe regex parameter injection (`{{var}}` and `{var}`). Python `eval()`, `exec()`, and Jinja2 code execution patterns are strictly banned.

### Open Redirect Prevention
- Notification `deep_link` values are strictly validated.
- Any link starting with `//`, containing `://`, or attempting protocol-relative redirection is sanitized to an internal relative route or set to `None`.

---

## 4. Recipient Resolution & Storm Protection

### Recipient Resolution
The `NotificationService` resolves intended recipients using the following deterministic cascade:
1. Explicit recipient metadata: `recipient_user_id`, `recipient_id`, or `target_user_id`.
2. Workspace / Project membership mapping: When a project event occurs, active members of that project (excluding the triggering actor) receive the event.
3. Administrative alerts: Security events target the affected user and workspace owners.

### Deduplication & Storm Protection
To prevent flooding user feeds during automated batch operations:
- A composite deduplication key is calculated: `f"{event_id}:{recipient_user_id}:{notification_type}"`.
- Events matching an active deduplication window are safely coalesced without creating duplicate notifications.

---

## 5. Storage, Retention & Bounded Growth

All notification and activity records are persisted via atomic JSON file persistence with in-memory indexes:
- `data/notifications/notifications.json`
- `data/notifications/events.json`
- `data/notifications/preferences.json`
- `data/notifications/activity.json`

### Retention Policy
- Read notifications older than `NOTIFICATION_RETENTION_DAYS` (default 30 days) are pruned.
- Unread notifications are retained up to 90 days.
- User notification mailboxes are capped at `NOTIFICATION_MAX_PER_USER` (default 500 notifications), automatically evicting oldest archived/read records first.

---

## 6. Verification & Test Evidence

Phase 19 verification was completed with automated suites:
- `backend/tests/test_notifications.py` (12 unit tests): Validated creation, persistence, user-scoped unread count, read/unread status transitions, pagination, template variable allowlisting, idempotent deduplication, preference suppression, security non-suppressibility, open redirect prevention, activity feed gating, security audit separation, and retention cleanup.
- `backend/tests/test_notifications_api.py` (1 integration test): End-to-end API verification covering auth, listing, badge count, IDOR security boundaries, preferences updates, and workspace activity.
- Total Phase 19 test suite: **13/13 passing in 2.24s**.
- Regression test suite (Phases 17 & 18): **13/13 passing in 8.91s**.
- Frontend TypeScript type check: **0 errors**.
