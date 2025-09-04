// Clean TypeScript Types for RBAC
export enum UserType {
  SUPER_USER = "SUPER_USER",
  COMPANY_USER = "COMPANY_USER", 
  DEVICE_USER = "DEVICE_USER"
}

export enum CompanyType {
  HOST = "HOST",
  ADVERTISER = "ADVERTISER"
}

export enum CompanyRole {
  ADMIN = "ADMIN",
  REVIEWER = "REVIEWER",
  EDITOR = "EDITOR", 
  VIEWER = "VIEWER"
}

export interface Company {
  id: string;
  name: string;
  company_type: CompanyType;
  organization_code: string;
  registration_key: string;
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

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  user_type: UserType;
  company_id?: string;
  company_role?: CompanyRole;
  permissions: string[];
  is_active: boolean;
  email_verified: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
  company?: Company;
  accessible_navigation: string[];
  display_name: string;
  role_display: string;
  is_super_admin?: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface User extends UserProfile {}
