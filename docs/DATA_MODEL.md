Purpose: Logical + physical schema.

Contents:

Entities:

Company (id, name, type: HOST|ADVERTISER, address, city, country, phone, email, website, status).

User (id, name, email, phone, status, hashed_password, roles).

UserRole (id, user_id, company_id, role: ADMIN|HOST|ADVERTISER, is_default, status).

ContentMeta (id, owner_id, filename, content_type, size, uploaded_at, status).

ContentMetadata (id, title, description, owner_id, categories, start_time, end_time, tags).

Review (id, content_id, ai_confidence, action, reviewer_id, notes).

Additional models implemented in the codebase:

- Screen / Kiosk: modelled in `backend/content_service/app/models.py` as `ScreenCreate`, `ScreenUpdate`, `ScreenStatus`, `ScreenOrientation` with fields such as resolution, orientation, company_id, name, and status. Used by `backend/content_service/app/api/screens.py`.

- Overlay (ContentOverlay): overlays are stored per screen and expose CRUD via `/api/screens/{screen_id}/overlays` (frontend uses `frontend/src/app/dashboard/content-overlay/page.tsx`). Overlay schema includes content_id, position, size, and layer order.

- DigitalTwin: virtual device representation and control data structures exist in frontend `frontend/src/app/dashboard/digital-twin/page.tsx` and backend endpoints; the twin holds references to current content overlays, test mode flags, and telemetry mapping.

- Event / ProofOfPlay: `backend/content_service/app/content_delivery/proof_of_play.py` manages proof-of-play events; an events API exists in `backend/content_service/app/api/events.py` for ingestion and retrieval of play/analytics events.

Relationships:

1:N Company → UserRole.

1:N User → UserRole.

1:N User → ContentMeta.

1:N ContentMeta → Review.

N:M ContentMetadata → Categories (via categories array).

Data storage:

MongoDB for all metadata (companies, users, roles, content, reviews).

Azure Blob Storage for media files.

Event storage: Azure Service Bus for event queuing, MongoDB for event logs.