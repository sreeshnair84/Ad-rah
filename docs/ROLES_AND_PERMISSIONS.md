interface UserRole {
  ADMIN: {
    permissions: ['content_moderation', 'user_management', 'platform_settings', 'analytics_full'];
    access_level: 'global';
  };
  HOST: {
    permissions: ['screen_management', 'ad_placement', 'revenue_analytics', 'content_approval'];
    access_level: 'organization';
  };
  ADVERTISER: {
    permissions: ['campaign_creation', 'content_upload', 'performance_analytics', 'billing'];
    access_level: 'campaign';
  };
}

Additional permissions discovered in code and UI (add to permission matrix):

- `screen_management` - create/update/delete screens (used by `/api/screens` and frontend kiosks pages)
- `overlay_management` - manage content overlays per screen (`/api/screens/{id}/overlays`)
- `digital_twin_view` - view virtual twin and live preview (`/dashboard/digital-twin`)
- `digital_twin_control` - send test/control commands to digital twin/device via WebSocket
- `analytics_view` - view analytics and performance dashboards (`/dashboard/performance`)
- `proof_of_play_audit` - access proof-of-play and event ingestion records

Map these permissions into role templates as needed (e.g., HOST gets `screen_management`, `overlay_management`, `analytics_view`, `proof_of_play_audit`; ADVERTISER keeps `campaign_creation` and limited `analytics_view`).