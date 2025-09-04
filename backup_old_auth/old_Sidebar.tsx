import React from "react";
import {
  LayoutDashboard,
  Upload,
  ShieldCheck,
  MonitorSmartphone,
  BarChart3,
  Settings,
  Users,
  Shield,
  Building2,
  UserPlus,
  FileImage,
  PlayCircle,
  Eye,
  Zap,
  DollarSign,
  Key,
  Layers,
  Share2,
  Clock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

// Enhanced permission-based navigation structure
const navigationGroups = [
  {
    label: "Overview",
    items: [
      { 
        key: "dashboard", 
        label: "Dashboard", 
        icon: <LayoutDashboard className="h-5 w-5" />,
        permission: { resource: "dashboard", action: "view" },
        description: "Main dashboard overview"
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
        permission: { resource: "users", action: "view" },
        description: "Manage company users"
      },
      { 
        key: "roles", 
        label: "Roles & Permissions", 
        icon: <Shield className="h-5 w-5" />,
        permission: { resource: "roles", action: "view" },
        description: "Manage roles and permissions"
      },
      { 
        key: "registration", 
        label: "Registration Requests", 
        icon: <UserPlus className="h-5 w-5" />,
        userType: "SUPER_USER",
        description: "Review host/advertiser applications"
      },
      { 
        key: "device-keys", 
        label: "Device Keys", 
        icon: <Key className="h-5 w-5" />,
        permission: { resource: "devices", action: "register" },
        companyTypes: ["HOST"],
        description: "Manage device registration (HOST only)"
      },
    ]
  },
  {
    label: "Company Management",
    items: [
      { 
        key: "master-data", 
        label: "Companies", 
        icon: <Building2 className="h-5 w-5" />,
        userType: "SUPER_USER",
        description: "Manage all company profiles"
      },
    ]
  },
  {
    label: "Content Management",
    items: [
      { 
        key: "my-content", 
        label: "My Content", 
        icon: <FileImage className="h-5 w-5" />,
        permission: { resource: "content", action: "view" },
        description: "View and manage your content"
      },
      { 
        key: "upload", 
        label: "Upload Content", 
        icon: <Upload className="h-5 w-5" />,
        permission: { resource: "content", action: "upload" },
        description: "Upload new content"
      },
      { 
        key: "content-share", 
        label: "Shared Content", 
        icon: <Share2 className="h-5 w-5" />,
        permission: { resource: "content", action: "share" },
        companyTypes: ["HOST"],
        description: "Share content with other companies (HOST only)"
      },
      { 
        key: "moderation", 
        label: "Content Review", 
        icon: <Eye className="h-5 w-5" />,
        permission: { resource: "moderation", action: "view" },
        description: "Review and approve content"
      },
      { 
        key: "ads-approval", 
        label: "Approval Queue", 
        icon: <ShieldCheck className="h-5 w-5" />,
        permission: { resource: "moderation", action: "queue" },
        description: "Content approval dashboard"
      },
      { 
        key: "content-overlay", 
        label: "Content Layout", 
        icon: <Layers className="h-5 w-5" />,
        permission: { resource: "overlays", action: "view" },
        companyTypes: ["HOST"],
        description: "Design content positioning (HOST only)"
      },
    ]
  },
  {
    label: "Device & Screen Management",
    items: [
      { 
        key: "kiosks", 
        label: "Digital Screens", 
        icon: <MonitorSmartphone className="h-5 w-5" />,
        permission: { resource: "screens", action: "view" },
        companyTypes: ["HOST"],
        description: "Manage digital displays (HOST only)"
      },
      { 
        key: "devices", 
        label: "Device Control", 
        icon: <PlayCircle className="h-5 w-5" />,
        permission: { resource: "devices", action: "control" },
        companyTypes: ["HOST"],
        description: "Control device playback (HOST only)"
      },
      { 
        key: "digital-twin", 
        label: "Digital Twin", 
        icon: <Building2 className="h-5 w-5" />,
        permission: { resource: "digital_twin", action: "view" },
        companyTypes: ["HOST"],
        description: "Virtual device monitoring (HOST only)"
      },
      { 
        key: "schedules", 
        label: "Schedules", 
        icon: <Clock className="h-5 w-5" />,
        permission: { resource: "screens", action: "schedule" },
        companyTypes: ["HOST"],
        description: "Manage content scheduling (HOST only)"
      },
    ]
  },
  {
    label: "Analytics & Insights",
    items: [
      { 
        key: "analytics/real-time", 
        label: "Real-Time Analytics", 
        icon: <Zap className="h-5 w-5" />,
        permission: { resource: "analytics", action: "view" },
        description: "Live performance metrics"
      },
      { 
        key: "analytics", 
        label: "Reports & Analytics", 
        icon: <BarChart3 className="h-5 w-5" />,
        permission: { resource: "analytics", action: "reports" },
        description: "Historical performance reports"
      },
      { 
        key: "performance", 
        label: "Performance", 
        icon: <DollarSign className="h-5 w-5" />,
        permission: { resource: "analytics", action: "export" },
        description: "Advanced analytics and exports"
      },
    ]
  },
  {
    label: "System",
    items: [
      { 
        key: "settings", 
        label: "Settings", 
        icon: <Settings className="h-5 w-5" />,
        permission: { resource: "settings", action: "view" },
        description: "Company settings"
      },
      { 
        key: "billing", 
        label: "Billing", 
        icon: <DollarSign className="h-5 w-5" />,
        permission: { resource: "settings", action: "edit" },
        description: "Billing and subscription management"
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
  const { 
    user, 
    hasPermission, 
    hasRole, 
    isSuperUser, 
    isCompanyUser,
    isHostCompany,
    isAdvertiserCompany,
    canAccess,
    getRoleDisplay 
  } = useAuth();

  // Check if user has access to a navigation item
  const hasAccessToItem = (item: any) => {
    if (!user) return false;
    
    // Super users have access to everything
    if (isSuperUser()) {
      console.log(`✅ ${item.key}: Super user access`);
      return true;
    }

    console.log(`🔍 Checking ${item.key} for user:`, {
      userType: user.user_type,
      companyRole: user.company_role,
      companyType: user.company?.company_type,
      permissionsCount: user.permissions?.length || 0,
      permissions: user.permissions?.slice(0, 3) // First 3 permissions
    });

    // Check user type requirement first
    if (item.userType && user.user_type !== item.userType) {
      console.log(`❌ ${item.key}: User type mismatch - Required: ${item.userType}, User: ${user.user_type}`);
      return false;
    }

    // Check company type restrictions
    if (item.companyTypes && isCompanyUser()) {
      const userCompanyType = user.company?.company_type;
      if (!userCompanyType || !item.companyTypes.includes(userCompanyType)) {
        console.log(`❌ ${item.key}: Company type restriction - Required: ${item.companyTypes}, User: ${userCompanyType}`);
        return false;
      }
    }

    // Check role requirements
    if (item.requiredRoles && isCompanyUser()) {
      const userRole = user.company_role;
      if (!userRole || !item.requiredRoles.includes(userRole)) {
        console.log(`❌ ${item.key}: Role requirement - Required: ${item.requiredRoles}, User: ${userRole}`);
        return false;
      }
    }

    // Check specific permission
    if (item.permission) {
      const hasPermissionResult = hasPermission(item.permission.resource, item.permission.action);
      if (!hasPermissionResult) {
        console.log(`❌ ${item.key}: Permission denied - ${item.permission.resource}_${item.permission.action}`, {
          userPermissions: user.permissions
        });
        return false;
      }
      console.log(`✅ ${item.key}: Permission granted - ${item.permission.resource}_${item.permission.action}`);
    }

    // Check role requirement (legacy)
    if (item.role) {
      if (!hasRole(item.role)) {
        console.log(`❌ ${item.key}: Role denied - ${item.role}`);
        return false;
      }
    }

    // Check component access
    if (item.component) {
      if (!canAccess(item.component)) {
        console.log(`❌ ${item.key}: Component access denied - ${item.component}`);
        return false;
      }
    }

    console.log(`✅ ${item.key}: Access granted`);
    return true;
  };

  // Filter navigation groups based on user permissions
  const getAccessibleNavigation = () => {
    if (!user) return [];

    return navigationGroups
      .map(group => ({
        ...group,
        items: group.items.filter(item => hasAccessToItem(item))
      }))
      .filter(group => group.items.length > 0); // Only show groups with accessible items
  };

  const accessibleNavigation = getAccessibleNavigation();

  return (
    <aside className={`hidden shrink-0 border-r bg-background transition-all duration-300 ease-in-out sm:block ${
      isCollapsed ? 'w-16' : 'w-72'
    }`}>
      <div className="flex h-full flex-col">
        {/* Sidebar Header */}
        {!isCollapsed && (
          <div className="border-b px-6 py-4">
            <div className="flex items-center space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600">
                <span className="text-sm font-bold text-white">A</span>
              </div>
              <div>
                <h2 className="text-sm font-semibold">Navigation</h2>
                <p className="text-xs text-muted-foreground">Digital Signage Platform</p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className={`flex-1 space-y-1 overflow-y-auto ${isCollapsed ? 'p-2' : 'p-4'}`}>
          {accessibleNavigation.map((group, groupIndex) => (
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
                      isCollapsed 
                        ? 'h-12 w-12 p-0' 
                        : 'h-auto min-h-[48px] px-3 py-2'
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
                      pathname === item.key 
                        ? 'text-blue-600 scale-110' 
                        : 'text-muted-foreground group-hover:text-foreground group-hover:scale-105'
                    }`}>
                      {item.icon}
                    </span>
                    {!isCollapsed && (
                      <div className="flex-1 text-left overflow-hidden">
                        <div className={`text-sm font-medium ${
                          pathname === item.key ? 'text-blue-900' : ''
                        }`}>
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
              {!isCollapsed && groupIndex < accessibleNavigation.length - 1 && (
                <div className="mx-3 border-t border-border/50 mt-2" />
              )}
            </div>
          ))}
        </nav>
        
        {/* Sidebar Footer */}
        {!isCollapsed && user && (
          <div className="border-t p-4">
            <div className="rounded-lg border bg-gradient-to-br from-blue-50/50 to-indigo-50/50 p-3">
              <div className="flex items-center gap-2 mb-2">
                <div className={`h-2 w-2 rounded-full ${user.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                <p className="text-xs font-medium text-foreground">
                  <span className="flex items-baseline gap-1">
                    <span className="font-semibold">Adara</span>
                    <span className="text-[10px] text-muted-foreground">Digital Signage™</span>
                  </span>
                </p>
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
                {user.user_type && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Type:</span>
                    <span className={`font-medium px-2 py-0.5 rounded-sm text-xs ${
                      user.user_type === 'SUPER_USER' 
                        ? 'text-purple-700 bg-purple-100' 
                        : 'text-green-700 bg-green-100'
                    }`}>
                      {user.user_type === 'SUPER_USER' ? 'Super' : 'Company'}
                    </span>
                  </div>
                )}
              </div>
              <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-blue-400"></span>
                  Enhanced RBAC
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-green-400"></span>
                  Content Sharing
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-purple-400"></span>
                  AI Moderation
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
