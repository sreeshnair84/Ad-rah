'use client';

import { Bell, Search, User, Building2, Shield, ChevronDown, Menu } from 'lucide-react';
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
import { useCompanies } from '@/hooks/useCompanies';

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
  const { user, logout, switchRole } = useAuth();
  const { companies } = useCompanies();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleRoleSwitch = async (companyId: string, roleId: string) => {
    try {
      await switchRole(companyId, roleId);
    } catch (error) {
      console.error('Failed to switch role:', error);
    }
  };

  const getCurrentRole = () => {
    if (!user?.roles || user.roles.length === 0) return null;
    
    // First try to find using active_role and active_company
    if (user.active_role && user.active_company) {
      const activeRole = user.roles.find(r => 
        r.company_id === user.active_company && r.role_id === user.active_role
      );
      if (activeRole) return activeRole;
    }
    
    // Fallback to default role or first role
    return user.roles.find(r => r.is_default) || user.roles[0];
  };

  const getCurrentCompany = () => {
    const currentRole = getCurrentRole();
    if (!currentRole) return null;
    
    // First try to find in companies array from useCompanies
    let company = companies.find(c => c.id === currentRole.company_id);
    if (company) return company;
    
    // Fallback: try to find in user.companies array if available
    if (user?.companies) {
      company = user.companies.find(c => c.id === currentRole.company_id);
      if (company) return company;
    }
    
    // Enhanced fallback mapping for known company IDs
    const getCompanyNameById = (companyId: string) => {
      switch (companyId) {
        case '1-c':
          return 'OpenKiosk Admin';
        case 'global':
        case 'system':
          return 'System';
        case 'company_001':
          return 'TechCorp Solutions';
        case 'company_002':
          return 'Creative Ads Inc';
        case 'company_003':
          return 'Digital Displays LLC';
        case 'company_004':
          return 'AdVantage Media';
        default:
          return companyId ? `Company ${companyId.slice(-3)}` : 'Unknown Company';
      }
    };
    
    // If still not found, create a placeholder company object with meaningful names
    return {
      id: currentRole.company_id,
      name: getCompanyNameById(currentRole.company_id),
      type: currentRole.role === 'ADMIN' ? 'HOST' as const : 'HOST' as const,
      address: '',
      city: '',
      country: '',
      status: 'active' as const,
      created_at: '',
      updated_at: ''
    };
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
    <header className="h-16 border-b bg-background px-6 flex items-center justify-between">
      {/* Left side - Logo */}
      <div className="flex items-center space-x-4">
        {showSidebarToggle && onToggleSidebar && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0"
            onClick={onToggleSidebar}
            title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <Menu className="h-4 w-4" />
          </Button>
        )}
        <div className="flex items-center">
          <img 
            src="/images/logo.png" 
            alt="Adārah from Hebron™" 
            className="h-8 w-auto"
          />
        </div>
      </div>

      {/* Center - Global Search */}
      <div className="flex-1 max-w-md mx-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            name="search"
            type="search"
            autoComplete="off"
            placeholder="Search..."
            className="pl-10 bg-muted/50"
          />
        </div>
      </div>

      {/* Right side - Role/Company Info, Notifications and User Menu */}
      <div className="flex items-center space-x-4">
        {/* Current Role and Company */}
        {currentRole && (
          <div className="hidden md:flex items-center space-x-2 text-sm">
            <Building2 className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">{currentCompany?.name || 'System'}</span>
            <span className="text-muted-foreground">•</span>
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span>{currentRole.role_name || getRoleDisplayName(currentRole.role)}</span>
          </div>
        )}

        {/* Role Switcher */}
        {user && user.roles.length > 1 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                Switch Role
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
              <DropdownMenuLabel>Switch Role</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {user.roles.map((role, index) => {
                // Helper function to get company name by ID
                const getCompanyNameById = (companyId: string) => {
                  switch (companyId) {
                    case '1-c':
                      return 'OpenKiosk Admin';
                    case 'global':
                    case 'system':
                      return 'System';
                    case 'company_001':
                      return 'TechCorp Solutions';
                    case 'company_002':
                      return 'Creative Ads Inc';
                    case 'company_003':
                      return 'Digital Displays LLC';
                    case 'company_004':
                      return 'AdVantage Media';
                    default:
                      return companyId ? `Company ${companyId.slice(-3)}` : 'Unknown Company';
                  }
                };
                
                // Try to find company in companies array first, then user.companies, then use fallback
                let company = companies.find(c => c.id === role.company_id);
                if (!company && user.companies) {
                  company = user.companies.find(c => c.id === role.company_id);
                }
                
                const companyName = company?.name || getCompanyNameById(role.company_id);
                   
                const isActive = (role.company_id === user.active_company && role.role_id === user.active_role) ||
                                 (role.is_default && !user.active_company);
                
                return (
                  <DropdownMenuItem
                    key={index}
                    onClick={() => handleRoleSwitch(role.company_id, role.role_id)}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-2">
                      <Building2 className="h-4 w-4" />
                      <div>
                        <div className="font-medium">{companyName}</div>
                        <div className="text-xs text-muted-foreground">
                          {role.role_name || getRoleDisplayName(role.role)}
                        </div>
                      </div>
                    </div>
                    {isActive && (
                      <span className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded">
                        Active
                      </span>
                    )}
                  </DropdownMenuItem>
                );
              })}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute -top-1 -right-1 h-4 w-4 bg-destructive text-destructive-foreground text-xs rounded-full flex items-center justify-center">
            3
          </span>
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center space-x-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback>
                  {user?.name?.[0] || user?.email[0] || 'U'}
                </AvatarFallback>
              </Avatar>
              <span className="hidden md:block text-sm font-medium">
                {user?.name || user?.email || 'User'}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
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
