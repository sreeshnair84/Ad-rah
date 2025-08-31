import React from "react";
import {
  LayoutDashboard,
  Upload,
  ShieldCheck,
  MonitorSmartphone,
  BarChart3,
  Settings,
  UserRound,
  Shield,
  Building2,
  ClipboardList,
  FileCheck2,
  Layers,
  Monitor,
  Key,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

// Navigation structure with role-based access control and proper grouping
const navigationGroups = [
  {
    label: "Overview",
    items: [
      { 
        key: "dashboard", 
        label: "Dashboard", 
        icon: <LayoutDashboard className="h-4 w-4" />,
        roles: ["ADMIN", "HOST", "ADVERTISER"],
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
        icon: <UserRound className="h-4 w-4" />,
        roles: ["ADMIN"],
        description: "Manage system users"
      },
      { 
        key: "roles", 
        label: "Roles & Permissions", 
        icon: <Shield className="h-4 w-4" />,
        roles: ["ADMIN"],
        description: "Role-based access control"
      },
      { 
        key: "registration", 
        label: "Registration Requests", 
        icon: <ClipboardList className="h-4 w-4" />,
        roles: ["ADMIN"],
        description: "Review host/advertiser applications"
      },
      { 
        key: "device-keys", 
        label: "Device Keys", 
        icon: <Key className="h-4 w-4" />,
        roles: ["ADMIN"],
        description: "Manage registration keys"
      },
    ]
  },
  {
    label: "Company Management",
    items: [
      { 
        key: "master-data", 
        label: "Companies", 
        icon: <Building2 className="h-4 w-4" />,
        roles: ["ADMIN"],
        description: "Manage company profiles"
      },
    ]
  },
  {
    label: "Content Management",
    items: [
      { 
        key: "my-content", 
        label: "My Content", 
        icon: <Upload className="h-4 w-4" />,
        roles: ["HOST", "ADVERTISER"],
        description: "Upload and manage content"
      },
      { 
        key: "upload", 
        label: "Upload Content", 
        icon: <Upload className="h-4 w-4" />,
        roles: ["HOST", "ADVERTISER"],
        description: "Upload new content"
      },
      { 
        key: "moderation", 
        label: "Content Review", 
        icon: <FileCheck2 className="h-4 w-4" />,
        roles: ["ADMIN", "HOST"],
        description: "Review and approve content"
      },
      { 
        key: "host-review", 
        label: "Host Review", 
        icon: <ShieldCheck className="h-4 w-4" />,
        roles: ["HOST"],
        description: "Host content approval dashboard"
      },
      { 
        key: "content-overlay", 
        label: "Content Layout", 
        icon: <Layers className="h-4 w-4" />,
        roles: ["ADMIN", "HOST"],
        description: "Design content positioning"
      },
    ]
  },
  {
    label: "Screen Management",
    items: [
      { 
        key: "kiosks", 
        label: "Digital Screens", 
        icon: <MonitorSmartphone className="h-4 w-4" />,
        roles: ["ADMIN", "HOST"],
        description: "Manage kiosk displays"
      },
      { 
        key: "digital-twin", 
        label: "Virtual Testing", 
        icon: <Monitor className="h-4 w-4" />,
        roles: ["ADMIN", "HOST", "ADVERTISER"],
        description: "Test content in virtual environment"
      },
    ]
  },
  {
    label: "Analytics & Insights",
    items: [
      { 
        key: "performance", 
        label: "Analytics", 
        icon: <BarChart3 className="h-4 w-4" />,
        roles: ["ADMIN", "HOST", "ADVERTISER"],
        description: "Performance metrics and reports"
      },
    ]
  },
  {
    label: "System",
    items: [
      { 
        key: "settings", 
        label: "Settings", 
        icon: <Settings className="h-4 w-4" />,
        roles: ["ADMIN", "HOST", "ADVERTISER"],
        description: "System configuration"
      },
    ]
  },
];

interface SidebarProps {
  pathname: string;
  setPathname: (pathname: string) => void;
  isCollapsed?: boolean;
}

export function Sidebar({ pathname, setPathname, isCollapsed = false }: SidebarProps) {
  const { user, hasAnyRole } = useAuth();

  // Filter navigation groups based on user roles
  const getAccessibleNavigation = () => {
    if (!user) return [];

    return navigationGroups
      .map(group => ({
        ...group,
        items: group.items.filter(item => hasAnyRole(item.roles))
      }))
      .filter(group => group.items.length > 0); // Only show groups with accessible items
  };

  const accessibleNavigation = getAccessibleNavigation();

  return (
    <aside className={`hidden shrink-0 border-r p-3 sm:block transition-all duration-300 ${
      isCollapsed ? 'w-[60px]' : 'w-[280px]'
    }`}>
      <nav className="space-y-6">
        {accessibleNavigation.map((group, groupIndex) => (
          <div key={group.label} className="space-y-2">
            {!isCollapsed && (
              <h3 className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                {group.label}
              </h3>
            )}
            <div className="space-y-1">
              {group.items.map((item) => (
                <Button
                  key={item.key}
                  variant={pathname === item.key ? "secondary" : "ghost"}
                  className={`w-full justify-start gap-3 rounded-xl transition-all duration-200 ${
                    isCollapsed ? 'px-2' : 'px-3'
                  } ${
                    pathname === item.key 
                      ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/50' 
                      : 'hover:bg-gradient-to-r hover:from-gray-50 hover:to-gray-100'
                  }`}
                  onClick={() => setPathname(item.key)}
                  title={isCollapsed ? `${item.label} - ${item.description}` : item.description}
                >
                  <span className={`shrink-0 ${
                    pathname === item.key ? 'text-blue-600' : 'text-gray-600'
                  }`}>
                    {item.icon}
                  </span>
                  {!isCollapsed && (
                    <div className="flex-1 text-left">
                      <span className={`block text-sm font-medium transition-colors duration-200 ${
                        pathname === item.key ? 'text-blue-900' : 'text-gray-700'
                      }`}>
                        {item.label}
                      </span>
                      <span className="block text-xs text-muted-foreground truncate">
                        {item.description}
                      </span>
                    </div>
                  )}
                </Button>
              ))}
            </div>
            {!isCollapsed && groupIndex < accessibleNavigation.length - 1 && (
              <div className="mx-3 border-b border-gray-200/50 mt-4" />
            )}
          </div>
        ))}
      </nav>
      
      {!isCollapsed && user && (
        <div className="mt-8 rounded-2xl border border-gradient-to-r from-blue-200/30 to-indigo-200/30 bg-gradient-to-br from-blue-50/50 to-indigo-50/50 p-4 transition-all duration-200">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-2 w-2 rounded-full bg-green-500"></div>
            <p className="text-xs font-medium text-gray-700">
              <span className="flex items-baseline gap-1">
                <span className="font-semibold">Adārah</span>
                <span className="text-[10px] opacity-75">from Hebron™</span>
              </span>
            </p>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Active Role:</span>
              <span className="font-medium text-blue-700 bg-blue-100 px-2 py-1 rounded">
                {user.roles.find(r => r.is_default)?.role || user.roles[0]?.role || 'No Role'}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Company:</span>
              <span className="font-medium text-gray-700 truncate max-w-[100px]">
                {user.companies?.[0]?.name || 'No Company'}
              </span>
            </div>
          </div>
          <ul className="mt-3 space-y-1 text-xs text-gray-600">
            <li className="flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-blue-400"></span>
              Multi-role support
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-green-400"></span>
              Real-time analytics
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-purple-400"></span>
              Content moderation
            </li>
          </ul>
        </div>
      )}
    </aside>
  );
}
