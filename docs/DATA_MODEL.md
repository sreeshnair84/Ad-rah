Purpose: Logical + physical schema.

Contents:

Entities:

Company (id, name, type: HOST|ADVERTISER, address, city, country, phone, email, website, status).

User (id, name, email, phone, status, hashed_password, roles).

UserRole (id, user_id, company_id, role: ADMIN|HOST|ADVERTISER, is_default, status).

ContentMeta (id, owner_id, filename, content_type, size, uploaded_at, status).

ContentMetadata (id, title, description, owner_id, categories, start_time, end_time, tags).

Review (id, content_id, ai_confidence, action, reviewer_id, notes).

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