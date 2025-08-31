'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Header } from '@/components/Header';
import { Sidebar } from '@/components/Sidebar';
import { useAuth } from '@/hooks/useAuth';
import { Loader2, Home } from 'lucide-react';
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [rtl, setRtl] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const { user, getCurrentUser, loading, isInitialized } = useAuth();

  useEffect(() => {
    // Authentication is handled by useAuth hook initialization
    // This component just needs to wait for initialization
    console.log('Dashboard layout mounted, waiting for auth initialization');
  }, []);

  // Handle redirect when authentication state changes
  useEffect(() => {
    if (isInitialized) {
      const token = localStorage.getItem('token');
      if (!token || !user) {
        console.log('User not authenticated, redirecting to login');
        if (token && !user) {
          localStorage.removeItem('token'); // Clear invalid token
        }
        router.replace('/login');
      } else {
        console.log('User authenticated:', user.email);
      }
    }
  }, [isInitialized, user, router]);

  const getCurrentPath = () => {
    const path = pathname.split('/').pop();
    return path === 'dashboard' ? 'dashboard' : path || 'dashboard';
  };

  const setPathname = (newPath: string) => {
    if (newPath === 'dashboard') {
      router.push('/dashboard');
    } else {
      router.push(`/dashboard/${newPath}`);
    }
  };

  // Navigation mapping for breadcrumbs
  const navigationMap = {
    'dashboard': { label: 'Dashboard', group: 'Overview' },
    'users': { label: 'Users', group: 'User Management' },
    'roles': { label: 'Roles & Permissions', group: 'User Management' },
    'registration': { label: 'Registration Requests', group: 'User Management' },
    'device-keys': { label: 'Device Keys', group: 'User Management' },
    'master-data': { label: 'Companies', group: 'Company Management' },
    'my-ads': { label: 'My Content', group: 'Content Management' },
    'my-content': { label: 'My Content', group: 'Content Management' },
    'ads-approval': { label: 'Ads Approval', group: 'Content Management' },
    'moderation': { label: 'Content Review', group: 'Content Management' },
    'host-review': { label: 'Host Review', group: 'Content Management' },
    'content-overlay': { label: 'Content Layout', group: 'Content Management' },
    'upload': { label: 'Content Upload', group: 'Content Management' },
    'kiosks': { label: 'Digital Screens', group: 'Screen Management' },
    'digital-twin': { label: 'Virtual Testing', group: 'Screen Management' },
    'performance': { label: 'Analytics', group: 'Analytics & Insights' },
    'billing': { label: 'Billing', group: 'Billing' },
    'schedules': { label: 'Schedules', group: 'Content Management' },
    'settings': { label: 'Settings', group: 'System' },
  };

  const getBreadcrumbs = () => {
    const currentPath = getCurrentPath();
    
    // If we're on dashboard, just show Dashboard
    if (currentPath === 'dashboard') {
      return [{ label: 'Dashboard', path: 'dashboard', isLast: true }];
    }
    
    // For all other pages, show just the current page name
    const pathInfo = navigationMap[currentPath as keyof typeof navigationMap];
    const pageLabel = pathInfo ? pathInfo.label : currentPath
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
    
    return [
      { label: pageLabel, path: currentPath, isLast: true }
    ];
  };

  // Show loading screen while authentication is being checked
  if (!isInitialized || loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Don't render anything if user is not authenticated (redirect will happen in useEffect)
  if (!user) {
    return (
      <div className="flex justify-center items-center h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div dir={rtl ? "rtl" : "ltr"} className="min-h-screen bg-background text-foreground flex flex-col">
      <Header 
        showSidebarToggle={true}
        isSidebarCollapsed={isSidebarCollapsed}
        onToggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          pathname={getCurrentPath()}
          setPathname={setPathname}
          isCollapsed={isSidebarCollapsed}
        />
        <main className="flex-1 overflow-auto">
          <div className="h-full">
            {/* Breadcrumb Navigation */}
            <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-gray-200/50 px-6 py-4">
              <Breadcrumb>
                <BreadcrumbList>
                  {getBreadcrumbs().map((crumb, index) => (
                    <React.Fragment key={crumb.path}>
                      {index > 0 && <BreadcrumbSeparator />}
                      <BreadcrumbItem>
                        {crumb.isLast ? (
                          <BreadcrumbPage className="font-medium text-blue-700 flex items-center gap-1.5">
                            {crumb.path === 'dashboard' && <Home className="h-3.5 w-3.5" />}
                            {crumb.label}
                          </BreadcrumbPage>
                        ) : (
                          <BreadcrumbLink 
                            onClick={() => setPathname(crumb.path)}
                            className="flex items-center gap-1.5"
                          >
                            {crumb.path === 'dashboard' && <Home className="h-3.5 w-3.5" />}
                            {crumb.label}
                          </BreadcrumbLink>
                        )}
                      </BreadcrumbItem>
                    </React.Fragment>
                  ))}
                </BreadcrumbList>
              </Breadcrumb>
            </div>            {/* Main Content */}
            <div className="p-6">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
