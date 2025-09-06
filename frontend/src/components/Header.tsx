'use client';

import { Bell, Search, User, Building2, Shield, Menu } from 'lucide-react';
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
          <div className="flex items-center justify-center w-auto h-10 rounded-lg">
            <Image 
              src="/images/logo.png" 
              alt="Adara from Hebron™" 
              width={80}
              height={40}
              className="w-20 h-10 object-contain"
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
                <h2 className="text-sm font-semibold">Adārah</h2>
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

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative h-9 w-9">
          <Bell className="h-5 w-5" />
          <span className="absolute -top-1 -right-1 h-4 w-4 bg-destructive text-destructive-foreground text-xs rounded-full flex items-center justify-center">
            3
          </span>
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center space-x-2 h-9">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="text-xs">
                  {user?.display_name?.[0] || user?.first_name?.[0] || user?.email[0] || 'U'}
                </AvatarFallback>
              </Avatar>
              <span className="hidden md:block text-sm font-medium max-w-24 truncate">
                {user?.display_name || user?.email || 'User'}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">{user?.display_name || 'User'}</p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user?.email}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push('/profile')}>
              <User className="mr-2 h-4 w-4" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push('/settings')}>
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
