# HoopStats operational improvements

User authorized code changes on develop for seven recommended improvements.
Extend existing architecture, retain imported database data and provider quotas.

- Docker: share model volume with development scheduler; remove obsolete project containers on normal startup without deleting volumes; expose optional SYNC_ADMIN_TOKEN only to backend.
- Freshness and monitoring: distinguish browser checks from import timestamps; show failed sources prominently; authenticated retries enqueue allowlisted imports for the single scheduler. Preserve previous successful timestamps and report execution duration. Queue admission is atomic with status, and requests do not expire during long imports. Malformed status must not block imports. Never expose provider exceptions or persist operator token in browser storage.
- Prediction evaluation: keep each season's chronological holdout report separately; evaluate a season only against earlier seasons, never deployed-model accuracy. Season selection resets pagination.
- Mobile: make navigation accessible on small screens; tables scroll within their own panels.
- Performance: measure schedule query before adding a matching season/status/date index; expose request duration without logging request query values.
- Release checks: CI runs backend/frontend tests, lint, production build, Compose validation, clean PostgreSQL migrations, and last migration rollback/reapply. No deployment automation.

Validation covers incorrect/missing tokens, duplicate retry requests, scheduler overlap, missing/corrupt reports, pagination and mobile navigation.
