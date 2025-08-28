# Copilot System Instructions

## Project Context
You are generating code for a **digital advertising CMS interface**.  
The platform manages **ads, analytics, moderation, and scheduling** across multiple kiosks/screens.  

## Roles
- **Admin** → System ops, moderation, users  
- **Host** → Screen/location owner, analytics, category restrictions  
- **Advertiser** → Upload ads, track performance  

## Tech Stack
- **Frontend:** Next.js + TailwindCSS (TypeScript)  
- **Backend:** FastAPI (Python) microservices  
- **DB:** PostgreSQL (relational), MongoDB (ad metadata), Blob Storage/local (media)  
- **Cloud:** Azure UAE Central (primary), GCP Dubai (secondary option) , Local for development 
- **Messaging/Event:** Azure Event Grid or MQTT  
- **AI:** Google Gemini APIs (moderation: image/video/text), Azure Open AI  

## File & Content Flow
1. Ad upload → Blob Storage  (local for development)
2. Metadata → MongoDB/Postgres  
3. AI moderation → Approve/flag  
4. Supervisor/Host review → Approve/reject  
5. Scheduler → Push ads to screens via Yodeck/Xibo API  
6. Kiosk analytics → Send back traffic + play logs  

## Online Actions
- Upload ads  
- Moderation (AI + manual)  
- Scheduling & pushing to screens  
- Analytics updates (real-time)  
- Engagement features (touch, optional)  

## Offline Actions
- Kiosk caches ads locally if no network  
- Queues moderation + logs until sync  
- Resumes schedule when online  

## Scheduling
- Slot granularity: 5 min  
- Recurrence: once, daily, weekly  
- Analytics-driven adjustments allowed  

## Security
- TLS 1.3  
- AES-256 storage encryption  
- Hashed IDs for traffic analytics  
- RBAC per role  
- Audit logging  

## Event Features
- Real-time triggers (ad swap on traffic surge)  
- Alerts for offline kiosks (>30 min)  
- Dashboard heatmaps from kiosk WiFi device counts  
