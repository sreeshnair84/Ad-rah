// Clean Sidebar with RBAC
import React from "react";
import Image from "next/image";
import {
  LayoutDashboard, Upload, ShieldCheck, MonitorSmartphone, BarChart3,
  Settings, Users, Shield, Building2, UserPlus, FileImage, PlayCircle,
  Eye, Zap, DollarSign, Key, Layers, Share2, Clock, Activity,
  CheckSquare, Globe, Smartphone, TrendingUp, Calendar, GitBranch,
  CreditCard, Database, Headphones
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { UserType, CompanyType } from "@/types/auth";

const navigationGroups = [
  {
    label: "Overview",
    items: [
      { 
        key: "dashboard", 
        label: "Dashboard", 
        icon: <LayoutDashboard className="h-5 w-5" />, 
        description: "Main dashboard",
        permission: { resource: "dashboard", action: "view" }
      },
      { 
        key: "unified", 
        label: "Unified View", 
        icon: <Globe className="h-5 w-5" />, 
        description: "Unified platform view",
        permission: { resource: "dashboard", action: "view" },
        userTypes: ["SUPER_USER"]
      },
    ]
  },
  {
    label: "User Management", 
    items: [
      { 
        key: "users", 
        label: "Users", 
        icon: <Users className="h-5 w-5" />, 
        description: "Manage users",
        permission: { resource: "user", action: "read" },
        requiredRoles: ["ADMIN"],
        userTypes: ["SUPER_USER", "COMPANY_USER"]
      },
      { 
        key: "companies", 
        label: "Companies", 
        icon: <Building2 className="h-5 w-5" />, 
        description: "Manage companies",
        permission: { resource: "company", action: "read" },
        userTypes: ["SUPER_USER"]
      },
      { 
        key: "roles", 
        label: "Roles", 
        icon: <Shield className="h-5 w-5" />, 
        description: "Manage roles",
        permission: { resource: "user", action: "read" },
        userTypes: ["SUPER_USER"]
      },
      { 
        key: "registration", 
        label: "Registration", 
        icon: <UserPlus className="h-5 w-5" />, 
        description: "User registration",
        permission: { resource: "user", action: "create" },
        userTypes: ["SUPER_USER"]
      },
    ]
  },
  {
    label: "Content Management",
    items: [
      { 
        key: "content", 
        label: "All Content", 
        icon: <FileImage className="h-5 w-5" />, 
        description: "View all content",
        permission: { resource: "content", action: "read" }
      },
      { 
        key: "content/upload", 
        label: "Upload Content", 
        icon: <Upload className="h-5 w-5" />, 
        description: "Upload new content",
        permission: { resource: "content", action: "upload" }
      },
      { 
        key: "content/review", 
        label: "Review Queue", 
        icon: <Eye className="h-5 w-5" />, 
        description: "Review AI-analyzed content",
        permission: { resource: "content", action: "approve" }
      },
      { 
        key: "content-overlay", 
        label: "Overlay Designer", 
        icon: <Layers className="h-5 w-5" />, 
        description: "Design content overlays",
        permission: { resource: "overlay", action: "create" }
      },
      { 
        key: "digital-twin", 
        label: "Digital Twin", 
        icon: <Smartphone className="h-5 w-5" />, 
        description: "Test in virtual environment",
        permission: { resource: "digital_twin", action: "view" }
      },
      { 
        key: "my-content", 
        label: "My Content", 
        icon: <Layers className="h-5 w-5" />, 
        description: "View my content",
        permission: { resource: "content", action: "read" }
      },
      { 
        key: "my-ads", 
        label: "My Ads", 
        icon: <PlayCircle className="h-5 w-5" />, 
        description: "Manage advertisements",
        permission: { resource: "content", action: "read" },
        companyTypes: ["ADVERTISER"]
      },
      { 
        key: "moderation", 
        label: "Moderation", 
        icon: <Eye className="h-5 w-5" />, 
        description: "Content moderation",
        permission: { resource: "content", action: "moderate" }
      },
      { 
        key: "ads-approval", 
        label: "Ads Approval", 
        icon: <CheckSquare className="h-5 w-5" />, 
        description: "Approve advertisements",
        permission: { resource: "content", action: "approve" },
        companyTypes: ["HOST"]
      },
      { 
        key: "host-review", 
        label: "Host Review", 
        icon: <Shield className="h-5 w-5" />, 
        description: "Host content review",
        permission: { resource: "content", action: "approve" },
        companyTypes: ["HOST"]
      },
    ]
  },
  {
    label: "Device Management",
    items: [
      { 
        key: "kiosks", 
        label: "Kiosks", 
        icon: <MonitorSmartphone className="h-5 w-5" />, 
        description: "Manage kiosks",
        permission: { resource: "device", action: "read" },
        companyTypes: ["HOST"]
      },
      { 
        key: "device-keys", 
        label: "Device Keys", 
        icon: <Key className="h-5 w-5" />, 
        description: "Manage device keys",
        permission: { resource: "device", action: "register" },
        companyTypes: ["HOST"]
      },
    ]
  },
  {
    label: "Analytics & Reports",
    items: [
      { 
        key: "analytics", 
        label: "Analytics", 
        icon: <BarChart3 className="h-5 w-5" />, 
        description: "View analytics",
        permission: { resource: "analytics", action: "read" }
      },
      { 
        key: "analytics/real-time", 
        label: "Real-Time", 
        icon: <Activity className="h-5 w-5" />, 
        description: "Real-time analytics",
        permission: { resource: "analytics", action: "read" }
      },
      { 
        key: "performance", 
        label: "Performance", 
        icon: <TrendingUp className="h-5 w-5" />, 
        description: "Performance metrics",
        permission: { resource: "analytics", action: "reports" }
      },
    ]
  },
  {
    label: "Scheduling & Planning",
    items: [
      { 
        key: "schedules", 
        label: "Schedules", 
        icon: <Calendar className="h-5 w-5" />, 
        description: "Content scheduling",
        permission: { resource: "content", action: "update" },
        companyTypes: ["HOST"]
      },
    ]
  },
  {
    label: "System & Admin",
    items: [
      { 
        key: "settings", 
        label: "Settings", 
        icon: <Settings className="h-5 w-5" />, 
        description: "System settings",
        permission: { resource: "settings", action: "read" }
      },
      { 
        key: "master-data", 
        label: "Master Data", 
        icon: <Database className="h-5 w-5" />, 
        description: "Manage master data",
        permission: { resource: "settings", action: "manage" },
        userTypes: ["SUPER_USER"]
      },
      { 
        key: "billing", 
        label: "Billing", 
        icon: <CreditCard className="h-5 w-5" />, 
        description: "Billing & payments",
        permission: { resource: "settings", action: "read" },
        requiredRoles: ["ADMIN"]
      },
    ]
  },
];

interface SidebarProps {
  pathname: string;
  setPathname: (pathname: string) => void;
  isCollapsed?: boolean;
}

export function Sidebar({ pathname, setPathname, isCollapsed = true }: SidebarProps) {
  const { user, canAccessNavigation, getRoleDisplay, hasPermission, isSuperUser } = useAuth();

  const getAccessibleNavigation = () => {
    if (!user) return [];
    
    const hasAccess = (item: any): boolean => {
      // Super users have access to everything
      if (isSuperUser()) return true;
      
      // Check user type restrictions
      if (item.userTypes && !item.userTypes.includes(user.user_type)) {
        return false;
      }
      
      // Check company type restrictions
      if (item.companyTypes && user?.company?.company_type) {
        if (!item.companyTypes.includes(user.company.company_type)) {
          return false;
        }
      }
      
      // Check role restrictions
      if (item.requiredRoles && user?.company_role) {
        if (!item.requiredRoles.includes(user.company_role)) {
          return false;
        }
      }
      
      // Check permission requirements
      if (item.permission) {
        if (!hasPermission(item.permission.resource, item.permission.action)) {
          return false;
        }
      }
      
      return true;
    };
    
    return navigationGroups
      .map(group => ({
        ...group,
        items: group.items.filter(hasAccess)
      }))
      .filter(group => group.items.length > 0);
  };

  const accessibleNavigation = getAccessibleNavigation();

  if (!user) {
    return (
      <aside className={`hidden shrink-0 border-r bg-background sm:block ${isCollapsed ? 'w-16' : 'w-72'}`}>
        <div className="flex h-full items-center justify-center text-muted-foreground">
          {isCollapsed ? '⚡' : 'Authentication Required'}
        </div>
      </aside>
    );
  }

  return (
    <aside className={`hidden shrink-0 border-r bg-background transition-all duration-300 ease-in-out sm:block ${isCollapsed ? 'w-16' : 'w-72'}`}>
      <div className="flex h-full flex-col">
        {!isCollapsed && (
          <div className="border-b px-6 py-4">
            <div className="flex items-center space-x-2">
              <Image
                src="/images/logo.png"
                alt="Adara Logo"
                width={32}
                height={32}
                className="w-8 h-8 object-contain"
                onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                  // Fallback to gradient icon if logo fails to load
                  const target = e.currentTarget as HTMLImageElement;
                  target.style.display = 'none';
                  const fallback = target.nextElementSibling as HTMLElement;
                  if (fallback) fallback.classList.remove('hidden');
                }}
              />
              <div className="hidden flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600">
                <span className="text-sm font-bold text-white">A</span>
              </div>
              <div>
                <h2 className="text-sm font-semibold">Adārah Platform</h2>
                <p className="text-xs text-muted-foreground">Digital Signage</p>
              </div>
            </div>
          </div>
        )}

        <nav className={`flex-1 space-y-1 overflow-y-auto ${isCollapsed ? 'p-2' : 'p-4'}`}>
          {accessibleNavigation.length === 0 ? (
            <div className={`text-center text-muted-foreground ${isCollapsed ? 'px-2 py-4' : 'px-4 py-8'}`}>
              {isCollapsed ? '🔒' : (
                <div>
                  <div className="text-2xl mb-2">🔒</div>
                  <div className="text-sm">No accessible features</div>
                </div>
              )}
            </div>
          ) : (
            accessibleNavigation.map((group, groupIndex) => (
              <div key={group.label} className={`space-y-1 ${groupIndex > 0 ? 'pt-4' : ''}`}>
                {!isCollapsed && (
                  <div className="px-3 py-2">
                    <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      {group.label}
                    </h3>
                  </div>
                )}
                <div className="space-y-1">
                  {group.items.map((item) => (
                    <Button
                      key={item.key}
                      variant={pathname === item.key ? "secondary" : "ghost"}
                      className={`w-full justify-start gap-3 transition-all duration-200 group ${
                        isCollapsed ? 'h-12 w-12 p-0' : 'h-auto min-h-[48px] px-3 py-2'
                      } ${
                        pathname === item.key 
                          ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/50 text-blue-900 shadow-sm' 
                          : 'hover:bg-muted text-muted-foreground hover:text-foreground hover:shadow-sm'
                      }`}
                      onClick={() => setPathname(item.key)}
                      title={isCollapsed ? `${item.label} - ${item.description}` : undefined}
                    >
                      <span className={`shrink-0 flex items-center justify-center transition-all duration-200 ${
                        isCollapsed ? 'h-6 w-6' : 'h-5 w-5'
                      } ${
                        pathname === item.key ? 'text-blue-600 scale-110' : 'text-muted-foreground group-hover:text-foreground group-hover:scale-105'
                      }`}>
                        {item.icon}
                      </span>
                      {!isCollapsed && (
                        <div className="flex-1 text-left overflow-hidden">
                          <div className={`text-sm font-medium ${pathname === item.key ? 'text-blue-900' : ''}`}>
                            {item.label}
                          </div>
                          <div className="text-xs text-muted-foreground truncate leading-tight">
                            {item.description}
                          </div>
                        </div>
                      )}
                    </Button>
                  ))}
                </div>
              </div>
            ))
          )}
        </nav>
        
        {!isCollapsed && user && (
          <div className="border-t p-4">
            <div className="rounded-lg border bg-gradient-to-br from-blue-50/50 to-indigo-50/50 p-3">
              <div className="flex items-center gap-2 mb-2">
                <div className={`h-2 w-2 rounded-full ${user.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                <p className="text-xs font-medium">Adārah Platform</p>
              </div>
              
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Role:</span>
                  <span className="font-medium text-blue-700 bg-blue-100 px-2 py-0.5 rounded-sm truncate max-w-20">
                    {getRoleDisplay()}
                  </span>
                </div>
                
                {user.company?.name && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Company:</span>
                    <span className="font-medium text-gray-700 truncate max-w-20" title={user.company.name}>
                      {user.company.name}
                    </span>
                  </div>
                )}
                
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Type:</span>
                  <span className={`font-medium px-2 py-0.5 rounded-sm text-xs ${
                    user.user_type === UserType.SUPER_USER 
                      ? 'text-purple-700 bg-purple-100' 
                      : user.company?.company_type === CompanyType.HOST
                        ? 'text-green-700 bg-green-100'
                        : 'text-orange-700 bg-orange-100'
                  }`}>
                    {user.user_type === UserType.SUPER_USER ? 'Super' : user.company?.company_type || 'Company'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Access:</span>
                  <span className="font-medium text-blue-600">{user.permissions.length} permissions</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
