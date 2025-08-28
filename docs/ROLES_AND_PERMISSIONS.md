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