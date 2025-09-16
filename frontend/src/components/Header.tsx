// Copyright (c) 2025 Adara Screen by Hebron
// Owner: Sujesh M S
// All Rights Reserved
//
// This software is proprietary to Adara Screen by Hebron.
// Unauthorized use, reproduction, or distribution is strictly prohibited.

'use client';

import { Bell, Search, User, Building2, Shield, Menu, CheckCircle2, AlertTriangle, Clock } from 'lucide-react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

interface HeaderProps {
  showSidebarToggle?: boolean;
  isSidebarCollapsed?: boolean;
  onToggleSidebar?: () => void;
}

export function Header({ 
  showSidebarToggle = false, 
  isSidebarCollapsed = false, 
  onToggleSidebar 
}: HeaderProps) {
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  // Clean RBAC: Simple role and company access
  const getCurrentRole = () => {
    if (!user) return null;
    
    // Return user's single role information
    return {
      role_name: user.role_display,
      role: user.company_role || user.user_type,
      company_id: user.company_id
    };
  };

  const getCurrentCompany = () => {
    if (!user || !user.company) return null;
    
    // For super users, don't show company
    if (user.user_type === 'SUPER_USER') {
      return null;
    }
    
    // Return the user's company
    return user.company;
  };

  const getRoleDisplayName = (role: string) => {
    switch (role?.toUpperCase()) {
      case 'ADMIN':
        return 'Administrator';
      case 'HOST':
        return 'Host Manager';
      case 'ADVERTISER':
        return 'Advertiser Manager';
      case 'SYSTEM ADMINISTRATOR':
        return 'System Administrator';
      case 'HOST MANAGER':
        return 'Host Manager';
      case 'ADVERTISER MANAGER':
        return 'Advertiser Manager';
      default:
        // Capitalize first letter and make it more readable
        if (role) {
          return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase().replace(/_/g, ' ');
        }
        return 'User';
    }
  };

  const currentRole = getCurrentRole();
  const currentCompany = getCurrentCompany();

  return (
    <header className="h-16 border-b bg-background px-4 flex items-center justify-between sticky top-0 z-50 backdrop-blur-sm bg-background/95">
      {/* Left side - Sidebar Toggle & Logo */}
      <div className="flex items-center space-x-3">
        {showSidebarToggle && onToggleSidebar && (
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 shrink-0 hover:bg-muted"
            onClick={onToggleSidebar}
            title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <Menu className="h-5 w-5" />
          </Button>
        )}
        <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-auto h-25 rounded-lg">
            <Image 
              src="/images/logo.png" 
              alt="Adara from Hebron™" 
              width={300} // Increased width from 150 to 200
              height={110}
              className="w-32 h-20 object-contain" // Increased Tailwind width from w-20 to w-32
              priority
              onError={(e) => {
              // Fallback to text if logo fails to load
              const target = e.currentTarget as HTMLImageElement;
              target.style.display = 'none';
              const fallback = target.nextElementSibling as HTMLElement;
              if (fallback) fallback.classList.remove('hidden');
              }}
            />
            <div className="hidden flex items-center space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600">
              <span className="text-sm font-bold text-white">A</span>
              </div>
              <div>
              <h2 className="text-sm font-semibold">Adara Screen</h2>
              <p className="text-xs text-muted-foreground">Platform</p>
              </div>
            </div>
            </div>
          
        </div>
      </div>

      {/* Center - Global Search */}
      <div className="flex-1 max-w-sm mx-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            name="search"
            type="search"
            autoComplete="off"
            placeholder="Search..."
            className="pl-10 bg-muted/50 border-muted-foreground/20 focus:border-primary/50"
          />
        </div>
      </div>

      {/* Right side - Company Info, Role Switcher, Notifications and User Menu */}
      <div className="flex items-center space-x-3">
        {/* Current Role and Company - Only show company if not super admin */}
        {currentRole && (
          <div className="hidden lg:flex items-center space-x-3 px-3 py-2 bg-muted/50 rounded-lg">
            {currentCompany && (
              <>
                <div className="flex items-center space-x-2 text-sm">
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium text-foreground">{currentCompany.name}</span>
                </div>
                <div className="w-px h-4 bg-border"></div>
              </>
            )}
            <div className="flex items-center space-x-2 text-sm">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">{currentRole.role_name || getRoleDisplayName(currentRole.role)}</span>
            </div>
          </div>
        )}

        {/* Role Switcher - Removed: Clean RBAC system uses single role per user */}

        {/* Enhanced Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative h-9 w-9">
              <Bell className="h-5 w-5" />
              <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-medium">
                3
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel className="flex items-center justify-between">
              <span>Notifications</span>
              <Badge variant="secondary" className="text-xs">3 new</Badge>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />

            {/* Notification Items */}
            <div className="max-h-80 overflow-y-auto">
              <DropdownMenuItem className="flex items-start gap-3 p-3 cursor-pointer">
                <div className="flex-shrink-0 w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center">
                  <Clock className="h-4 w-4 text-amber-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">3 pending approvals</p>
                  <p className="text-xs text-gray-500 mt-1">New content awaiting your review</p>
                  <p className="text-xs text-blue-600 mt-1 font-medium">Review now →</p>
                </div>
                <div className="flex-shrink-0">
                  <span className="text-xs text-gray-400">2m ago</span>
                </div>
              </DropdownMenuItem>

              <DropdownMenuItem className="flex items-start gap-3 p-3 cursor-pointer">
                <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">Screen offline</p>
                  <p className="text-xs text-gray-500 mt-1">Mall Entrance Display disconnected</p>
                  <p className="text-xs text-blue-600 mt-1 font-medium">Check status →</p>
                </div>
                <div className="flex-shrink-0">
                  <span className="text-xs text-gray-400">5m ago</span>
                </div>
              </DropdownMenuItem>

              <DropdownMenuItem className="flex items-start gap-3 p-3 cursor-pointer">
                <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">Content approved</p>
                  <p className="text-xs text-gray-500 mt-1">Summer Campaign Ad is now live</p>
                  <p className="text-xs text-blue-600 mt-1 font-medium">View campaign →</p>
                </div>
                <div className="flex-shrink-0">
                  <span className="text-xs text-gray-400">15m ago</span>
                </div>
              </DropdownMenuItem>
            </div>

            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-center text-blue-600 hover:text-blue-700 cursor-pointer">
              <span className="w-full">View all notifications</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Enhanced User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center space-x-3 h-11 px-3 hover:bg-muted/50">
              <Avatar className="h-8 w-8 border-2 border-blue-200">
                <AvatarFallback className="text-sm font-semibold bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                  {user?.display_name?.[0] || user?.first_name?.[0] || user?.email[0] || 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="hidden md:flex flex-col items-start min-w-0">
                <span className="text-sm font-semibold text-gray-900 max-w-32 truncate">
                  {user?.display_name || user?.first_name || 'User'}
                </span>
                <span className="text-xs text-gray-500 max-w-32 truncate">
                  {currentRole?.role_name || 'User'}
                </span>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel className="font-normal">
              <div className="flex items-center space-x-3 py-2">
                <Avatar className="h-12 w-12 border-2 border-blue-200">
                  <AvatarFallback className="text-lg font-semibold bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                    {user?.display_name?.[0] || user?.first_name?.[0] || user?.email[0] || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="flex flex-col space-y-1 min-w-0">
                  <p className="text-sm font-semibold leading-none text-gray-900">
                    {user?.display_name || user?.first_name || 'User'}
                  </p>
                  <p className="text-xs leading-none text-gray-500 truncate">
                    {user?.email}
                  </p>
                  <Badge variant="outline" className="text-xs w-fit mt-1">
                    {currentRole?.role_name || 'User'}
                  </Badge>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push('/profile')} className="cursor-pointer">
              <User className="mr-3 h-4 w-4" />
              My Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push('/settings')} className="cursor-pointer">
              <Shield className="mr-3 h-4 w-4" />
              Account Settings
            </DropdownMenuItem>
            {currentCompany && (
              <DropdownMenuItem className="cursor-pointer">
                <Building2 className="mr-3 h-4 w-4" />
                {currentCompany.name} Settings
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-600 focus:text-red-700">
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
