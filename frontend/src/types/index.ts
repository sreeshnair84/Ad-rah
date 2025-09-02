// Enhanced RBAC Types
export interface Company {
  id: string;
  name: string;
  company_type: 'HOST' | 'ADVERTISER';
  contact_email: string;
  contact_phone?: string;
  address?: string;
  city?: string;
  country?: string;
  website?: string;
  status: 'active' | 'inactive';
  sharing_settings?: {
    allow_content_sharing: boolean;
    max_shared_companies: number;
    require_approval_for_sharing: boolean;
  };
  limits?: {
    max_users: number;
    max_devices: number;
    max_content_size_mb: number;
  };
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface Permission {
  resource: string;
  action: string;
  description?: string;
}

export interface Role {
  id: string;
  name: string;
  company_role_type: 'ADMIN' | 'REVIEWER' | 'EDITOR' | 'VIEWER';
  permissions: Permission[];
  company_id?: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserRole {
  id: string;
  user_id: string;
  role_id: string;
  company_id?: string;
  assigned_by: string;
  assigned_at: string;
  role: Role;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  user_type: 'SUPER_USER' | 'COMPANY_USER' | 'DEVICE_USER';
  company_id?: string;
  company_role?: 'ADMIN' | 'REVIEWER' | 'EDITOR' | 'VIEWER';
  permissions: string[];
  is_active: boolean;
  last_login?: string;
  failed_login_attempts?: number;
  locked_until?: string;
  roles?: UserRole[];
  company?: Company;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface Device {
  id: string;
  name: string;
  company_id: string;
  api_key: string;
  device_type: string;
  location?: string;
  status: 'active' | 'inactive' | 'maintenance';
  last_seen?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface ContentShare {
  id: string;
  content_id: string;
  from_company_id: string;
  to_company_id: string;
  shared_by: string;
  permissions: {
    can_edit: boolean;
    can_reshare: boolean;
    can_download: boolean;
  };
  expires_at?: string;
  status: 'active' | 'expired' | 'revoked';
  created_at: string;
}

export interface Content {
  id: string;
  title: string;
  description?: string;
  content_type: 'image' | 'video' | 'html5' | 'text';
  file_path?: string;
  file_size?: number;
  duration?: number;
  company_id: string;
  category_id?: string;
  status: 'draft' | 'pending_review' | 'approved' | 'rejected' | 'archived';
  visibility_level: 'private' | 'shared' | 'public';
  approval_status?: {
    approved_by?: string;
    approved_at?: string;
    rejection_reason?: string;
  };
  ai_moderation?: {
    score: number;
    flags: string[];
    reviewed_at: string;
  };
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface Ad {
  id: string;
  type: 'image' | 'video' | 'html5';
  category_id: string;
  business_id: string;
  company_id: string;
  status: 'pending' | 'approved' | 'rejected';
  file_path: string;
  metadata?: Record<string, unknown>;
}

export interface Category {
  id: string;
  name: string;
  description: string;
  company_id?: string;
  is_global: boolean;
}

export interface Review {
  id: string;
  content_id: string;
  reviewer_id: string;
  ai_score?: number;
  status: 'approved' | 'rejected' | 'needs_review';
  comments?: string;
  reviewed_at: string;
}

export interface Kiosk {
  id: string;
  partner_id: string;
  company_id: string;
  location: string;
  device_info: Record<string, unknown>;
}

export interface Schedule {
  startTime?: string;
  endTime?: string;
  daysOfWeek?: string[];
  frequency?: 'daily' | 'weekly' | 'monthly';
  startDate?: string;
  endDate?: string;
}

export interface Playlist {
  id: string;
  kiosk_id: string;
  name: string;
  schedule: Schedule;
  ads: string[];
}

export interface AuditLog {
  id: string;
  user_id: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details?: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
  success: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface CreateUserRequest {
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  company_role?: 'ADMIN' | 'REVIEWER' | 'EDITOR' | 'VIEWER';
}

export interface ShareContentRequest {
  target_company_id: string;
  permissions: {
    can_edit: boolean;
    can_reshare: boolean;
    can_download: boolean;
  };
  expires_at?: string;
}