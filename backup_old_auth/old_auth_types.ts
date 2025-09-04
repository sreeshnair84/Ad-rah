// Clean TypeScript Types for RBAC Authentication System
// Aligned with backend rbac_models_new.py

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

export enum Permission {
  // User Management
  USER_CREATE = "user_create",
  USER_READ = "user_read",
  USER_UPDATE = "user_update",
  USER_DELETE = "user_delete",
  
  // Company Management
  COMPANY_CREATE = "company_create",
  COMPANY_READ = "company_read",
  COMPANY_UPDATE = "company_update",
  COMPANY_DELETE = "company_delete",
  
  // Content Management
  CONTENT_CREATE = "content_create",
  CONTENT_READ = "content_read",
  CONTENT_UPDATE = "content_update",
  CONTENT_DELETE = "content_delete",
  CONTENT_UPLOAD = "content_upload",
  CONTENT_APPROVE = "content_approve",
  CONTENT_REJECT = "content_reject",
  CONTENT_SHARE = "content_share",
  CONTENT_MODERATE = "content_moderate",
  
  // Device Management
  DEVICE_CREATE = "device_create",
  DEVICE_READ = "device_read",
  DEVICE_UPDATE = "device_update",
  DEVICE_DELETE = "device_delete",
  DEVICE_REGISTER = "device_register",
  DEVICE_CONTROL = "device_control",
  DEVICE_MONITOR = "device_monitor",
  
  // Analytics & Reporting
  ANALYTICS_READ = "analytics_read",
  ANALYTICS_EXPORT = "analytics_export",
  ANALYTICS_REPORTS = "analytics_reports",
  
  // Settings & Configuration
  SETTINGS_READ = "settings_read",
  SETTINGS_UPDATE = "settings_update",
  SETTINGS_MANAGE = "settings_manage",
  
  // Dashboard Access
  DASHBOARD_VIEW = "dashboard_view"
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

export interface User {
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

export interface CreateUserRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  user_type?: UserType;
  company_id?: string;
  company_role?: CompanyRole;
}

export interface UpdateUserRequest {
  first_name?: string;
  last_name?: string;
  phone?: string;
  company_role?: CompanyRole;
  is_active?: boolean;
}

export interface CreateCompanyRequest {
  name: string;
  company_type: CompanyType;
  organization_code?: string;
  address: string;
  city: string;
  country: string;
  phone?: string;
  email?: string;
  website?: string;
}

export interface UpdateCompanyRequest {
  name?: string;
  address?: string;
  city?: string;
  country?: string;
  phone?: string;
  email?: string;
  website?: string;
  status?: 'active' | 'inactive';
}

export interface DeviceCredentials {
  id: string;
  device_id: string;
  company_id: string;
  api_key: string;
  device_name: string;
  device_type: string;
  location?: string;
  status: 'active' | 'inactive' | 'maintenance';
  last_seen?: string;
  created_at: string;
  updated_at: string;
}

export interface PermissionInfo {
  name: string;
  description: string;
}

export interface RoleInfo {
  name: string;
  description: string;
}

export interface CompanyTypeInfo {
  name: string;
  description: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Navigation and Permission Checking Types
export interface NavigationItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  permission?: {
    resource: string;
    action: string;
  };
  user_types?: UserType[];
  company_types?: CompanyType[];
  required_roles?: CompanyRole[];
  description: string;
}

export interface NavigationGroup {
  label: string;
  items: NavigationItem[];
}

// Hook return types
export interface UseAuthReturn {
  user: UserProfile | null;
  loading: boolean;
  error: string | null;
  isInitialized: boolean;
  
  // Authentication methods
  login: (credentials: LoginCredentials) => Promise<UserProfile | null>;
  logout: () => Promise<void>;
  getCurrentUser: () => Promise<UserProfile | null>;
  
  // Permission checking
  hasPermission: (resource: string, action: string) => boolean;
  hasAnyPermission: (permissions: Array<{resource: string, action: string}>) => boolean;
  hasRole: (role: CompanyRole) => boolean;
  hasAnyRole: (roles: CompanyRole[]) => boolean;
  
  // User type checking
  isSuperUser: () => boolean;
  isCompanyUser: () => boolean;
  isHostCompany: () => boolean;
  isAdvertiserCompany: () => boolean;
  
  // Access control
  canAccess: (component: string) => boolean;
  canAccessNavigation: (navigationKey: string) => boolean;
  
  // Display helpers
  getDisplayName: () => string;
  getRoleDisplay: () => string;
  getDefaultRole: () => {
    role_name: string;
    role: string;
    company_name: string;
  } | null;
}

// API Client types
export interface AuthApiClient {
  login: (credentials: LoginCredentials) => Promise<LoginResponse>;
  getCurrentUser: () => Promise<UserProfile>;
  logout: () => Promise<void>;
  
  // User management
  getUsers: (companyId?: string) => Promise<UserProfile[]>;
  getUser: (userId: string) => Promise<UserProfile>;
  createUser: (userData: CreateUserRequest) => Promise<UserProfile>;
  updateUser: (userId: string, updates: UpdateUserRequest) => Promise<{message: string}>;
  
  // Company management
  getCompanies: () => Promise<Company[]>;
  getCompany: (companyId: string) => Promise<Company>;
  createCompany: (companyData: CreateCompanyRequest) => Promise<Company>;
  updateCompany: (companyId: string, updates: UpdateCompanyRequest) => Promise<{message: string}>;
  
  // Metadata
  getPermissions: () => Promise<PermissionInfo[]>;
  getRoles: () => Promise<RoleInfo[]>;
  getCompanyTypes: () => Promise<CompanyTypeInfo[]>;
  getAccessibleNavigation: () => Promise<string[]>;
}

// Error types
export interface AuthError extends Error {
  status?: number;
  code?: string;
  details?: any;
}

export class UnauthorizedError extends Error implements AuthError {
  status = 401;
  code = 'UNAUTHORIZED';
  
  constructor(message = 'Unauthorized access') {
    super(message);
    this.name = 'UnauthorizedError';
  }
}

export class ForbiddenError extends Error implements AuthError {
  status = 403;
  code = 'FORBIDDEN';
  
  constructor(message = 'Insufficient permissions') {
    super(message);
    this.name = 'ForbiddenError';
  }
}

export class ValidationError extends Error implements AuthError {
  status = 400;
  code = 'VALIDATION_ERROR';
  details?: any;
  
  constructor(message = 'Validation failed', details?: any) {
    super(message);
    this.name = 'ValidationError';
    this.details = details;
  }
}

// Utility types
export type PermissionString = `${string}_${string}`;
export type NavigationKey = string;
export type CompanyId = string;
export type UserId = string;

// Constants
export const DEFAULT_PERMISSIONS = {
  SUPER_USER: Object.values(Permission),
  HOST: {
    [CompanyRole.ADMIN]: [
      Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
      Permission.CONTENT_CREATE, Permission.CONTENT_READ, Permission.CONTENT_UPDATE, Permission.CONTENT_DELETE,
      Permission.CONTENT_UPLOAD, Permission.CONTENT_APPROVE, Permission.CONTENT_REJECT, Permission.CONTENT_SHARE,
      Permission.CONTENT_MODERATE, Permission.DEVICE_CREATE, Permission.DEVICE_READ, Permission.DEVICE_UPDATE,
      Permission.DEVICE_DELETE, Permission.DEVICE_REGISTER, Permission.DEVICE_CONTROL, Permission.DEVICE_MONITOR,
      Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT, Permission.ANALYTICS_REPORTS,
      Permission.SETTINGS_READ, Permission.SETTINGS_UPDATE, Permission.SETTINGS_MANAGE,
      Permission.DASHBOARD_VIEW
    ],
    [CompanyRole.REVIEWER]: [
      Permission.USER_READ, Permission.CONTENT_READ, Permission.CONTENT_APPROVE, Permission.CONTENT_REJECT,
      Permission.CONTENT_MODERATE, Permission.DEVICE_READ, Permission.DEVICE_CONTROL, Permission.DEVICE_MONITOR,
      Permission.ANALYTICS_READ, Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
    ],
    [CompanyRole.EDITOR]: [
      Permission.CONTENT_CREATE, Permission.CONTENT_READ, Permission.CONTENT_UPDATE, Permission.CONTENT_UPLOAD,
      Permission.ANALYTICS_READ, Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
    ],
    [CompanyRole.VIEWER]: [
      Permission.CONTENT_READ, Permission.CONTENT_UPLOAD, Permission.ANALYTICS_READ,
      Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
    ]
  },
  ADVERTISER: {
    [CompanyRole.ADMIN]: [
      Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
      Permission.CONTENT_CREATE, Permission.CONTENT_READ, Permission.CONTENT_UPDATE, Permission.CONTENT_DELETE,
      Permission.CONTENT_UPLOAD, Permission.CONTENT_APPROVE, Permission.CONTENT_REJECT, Permission.CONTENT_MODERATE,
      Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT, Permission.ANALYTICS_REPORTS,
      Permission.SETTINGS_READ, Permission.SETTINGS_UPDATE, Permission.SETTINGS_MANAGE,
      Permission.DASHBOARD_VIEW
    ],
    [CompanyRole.REVIEWER]: [
      Permission.USER_READ, Permission.CONTENT_READ, Permission.CONTENT_APPROVE, Permission.CONTENT_REJECT,
      Permission.CONTENT_MODERATE, Permission.ANALYTICS_READ, Permission.ANALYTICS_REPORTS,
      Permission.DASHBOARD_VIEW
    ],
    [CompanyRole.EDITOR]: [
      Permission.CONTENT_CREATE, Permission.CONTENT_READ, Permission.CONTENT_UPDATE, Permission.CONTENT_UPLOAD,
      Permission.ANALYTICS_READ, Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
    ],
    [CompanyRole.VIEWER]: [
      Permission.CONTENT_READ, Permission.CONTENT_UPLOAD, Permission.ANALYTICS_READ,
      Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
    ]
  }
} as const;