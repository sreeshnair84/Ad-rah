export interface Company {
  id: string;
  name: string;
  type: 'HOST' | 'ADVERTISER';
  address: string;
  city: string;
  country: string;
  phone?: string;
  email?: string;
  website?: string;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

export interface UserRole {
  id: string;
  user_id: string;
  company_id: string;
  role: 'ADMIN' | 'HOST' | 'ADVERTISER';
  is_default: boolean;
  status: 'active' | 'inactive';
  created_at: string;
}

export interface User {
  id: string;
  name?: string;
  email: string;
  phone?: string;
  status: 'active' | 'inactive';
  roles: UserRole[];
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: string;
  name: 'ADMIN' | 'HOST' | 'ADVERTISER';
  permissions: string[];
  access_level: 'global' | 'organization' | 'campaign';
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
}

export interface Review {
  id: string;
  ad_id: string;
  ai_score: number;
  reviewer_id?: string;
  status: 'approved' | 'rejected' | 'needs_review';
  explanation?: string;
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