import React from "react";
import {
  LayoutDashboard,
  Upload,
  ShieldCheck,
  MonitorSmartphone,
  BarChart3,
  Settings,
  UserRound,
  Globe2,
  Search,
  Bell,
  Building2,
  Menu,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Breadcrumb } from "@/components/Breadcrumb";
import { User } from "@/types";

const nav = [
  { key: "dashboard", label: "Dashboard", icon: <LayoutDashboard className="h-4 w-4" /> },
  { key: "ads-approval", label: "Ads Approval", icon: <ShieldCheck className="h-4 w-4" /> },
  { key: "kiosks", label: "Screens", icon: <MonitorSmartphone className="h-4 w-4" /> },
  { key: "users", label: "Users", icon: <UserRound className="h-4 w-4" /> },
  { key: "moderation", label: "Moderation", icon: <ShieldCheck className="h-4 w-4" /> },
  { key: "my-ads", label: "Ads", icon: <Upload className="h-4 w-4" /> },
  { key: "performance", label: "Analytics", icon: <BarChart3 className="h-4 w-4" /> },
  { key: "settings", label: "Settings", icon: <Settings className="h-4 w-4" /> },
];

const roles = [
  { key: "ADMIN", label: "Admin" },
  { key: "HOST", label: "Host" },
  { key: "ADVERTISER", label: "Advertiser" },
];

interface TopBarProps {
  role: string;
  setRole: (role: string) => void;
  rtl: boolean;
  setRtl: (rtl: boolean) => void;
  pathname: string;
  setPathname: (pathname: string) => void;
  user: User;
  onLogout: () => void;
  isSidebarCollapsed?: boolean;
  setIsSidebarCollapsed?: (collapsed: boolean) => void;
}

export function TopBar({ role, setRole, rtl, setRtl, pathname, setPathname, user, onLogout, isSidebarCollapsed = false, setIsSidebarCollapsed }: TopBarProps) {
  const getBreadcrumbItems = () => {
    const currentNavItem = nav.find(item => item.key === pathname);
    if (!currentNavItem) return [];

    if (pathname === 'dashboard') {
      return [{ label: 'Dashboard', isActive: true }];
    }

    return [
      { label: 'Dashboard', href: '/dashboard' },
      { label: currentNavItem.label, isActive: true }
    ];
  };

  return (
    <div className="sticky top-0 z-40 w-full border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex w-full items-center gap-3 px-4 py-3">
        <div className="flex items-center gap-2">
          {setIsSidebarCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              className="hidden md:flex rounded-full"
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {isSidebarCollapsed ? <Menu className="h-5 w-5" /> : <X className="h-5 w-5" />}
            </Button>
          )}
          <div className="flex items-center gap-2 rounded-2xl border px-3 py-2 shadow-sm">
            <Building2 className="h-5 w-5" />
            <span className="inline-block">
              <span className="flex items-baseline gap-1">
                <span className="font-semibold tracking-tight">Adārah</span>
                <span className="text-xs text-muted-foreground">from Hebron™</span>
              </span>
            </span>
            <Badge className="ml-1" variant="secondary">{role}</Badge>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <div className="hidden sm:flex items-center gap-2 rounded-full border px-3 py-2">
            <Globe2 className="h-4 w-4" />
            <Label htmlFor="rtl" className="mr-2 text-sm">RTL</Label>
            <Switch id="rtl" checked={rtl} onCheckedChange={setRtl} />
          </div>

          <Select value={role} onValueChange={setRole}>
            <SelectTrigger className="w-[140px] rounded-full">
              <SelectValue placeholder="Role" />
            </SelectTrigger>
            <SelectContent align="end">
              {roles.map(r => (
                <SelectItem key={r.key} value={r.key}>{r.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button variant="ghost" size="icon" className="rounded-full"><Search className="h-5 w-5" /></Button>
          <Button variant="ghost" size="icon" className="rounded-full"><Bell className="h-5 w-5" /></Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center space-x-2 rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>
                    {user.name?.[0] || user.email[0]}
                  </AvatarFallback>
                </Avatar>
                <span className="hidden md:block text-sm font-medium">
                  {user.name || user.email}
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <UserRound className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem>
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onLogout}>
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <div className="px-4 pb-3">
        <Breadcrumb
          items={getBreadcrumbItems()}
          pathname={pathname}
          setPathname={setPathname}
        />
      </div>
    </div>
  );
}
