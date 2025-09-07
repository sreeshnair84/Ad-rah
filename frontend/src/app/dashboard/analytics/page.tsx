'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/hooks/useAuth';
import { PermissionGate } from '@/components/PermissionGate';
import {
  BarChart3,
  TrendingUp,
  Users,
  Eye,
  Clock,
  Monitor,
  PlayCircle,
  Activity
} from 'lucide-react';

export default function AnalyticsPage() {
  const { user } = useAuth();

  const analyticsCards = [
    {
      title: "Real-Time Analytics",
      description: "Live device and content performance metrics",
      icon: <Activity className="h-8 w-8 text-blue-600" />,
      href: "/dashboard/analytics/real-time",
      permission: { resource: "analytics", action: "read" },
      stats: "Live monitoring"
    },
    {
      title: "Performance Reports",
      description: "Detailed analytics and performance insights",
      icon: <TrendingUp className="h-8 w-8 text-green-600" />,
      href: "/dashboard/performance",
      permission: { resource: "analytics", action: "reports" },
      stats: "Historical data"
    },
    {
      title: "Content Analytics",
      description: "Track content performance and engagement",
      icon: <BarChart3 className="h-8 w-8 text-purple-600" />,
      href: "/dashboard/content",
      permission: { resource: "content", action: "read" },
      stats: "Content metrics"
    },
    {
      title: "Device Monitoring",
      description: "Monitor device health and status",
      icon: <Monitor className="h-8 w-8 text-orange-600" />,
      href: "/dashboard/kiosks",
      permission: { resource: "device", action: "monitor" },
      stats: "Device status"
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <BarChart3 className="h-8 w-8 text-blue-600" />
            Analytics Dashboard
          </h1>
          <p className="text-gray-600 mt-1">
            Monitor performance, track metrics, and gain insights
          </p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Total Views</p>
                <p className="text-2xl font-bold text-blue-900">12,453</p>
              </div>
              <Eye className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Active Devices</p>
                <p className="text-2xl font-bold text-green-900">
                  {user?.company?.company_type === 'HOST' ? '24' : '0'}
                </p>
              </div>
              <Monitor className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">Content Items</p>
                <p className="text-2xl font-bold text-purple-900">156</p>
              </div>
              <PlayCircle className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">Avg. Session</p>
                <p className="text-2xl font-bold text-orange-900">4m 32s</p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Analytics Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {analyticsCards.map((card, index) => (
          <PermissionGate 
            key={index} 
            permission={card.permission}
            fallback={
              <Card className="opacity-50">
                <CardContent className="p-6">
                  <div className="flex items-center justify-center h-24">
                    <div className="text-center">
                      <div className="text-gray-400 mb-2">{card.icon}</div>
                      <p className="text-sm text-gray-500">Access Restricted</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            }
          >
            <Card className="hover:shadow-lg transition-all duration-200 cursor-pointer group">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-gray-100 rounded-lg group-hover:bg-blue-100 transition-colors">
                      {card.icon}
                    </div>
                    <div>
                      <CardTitle className="text-lg">{card.title}</CardTitle>
                      <CardDescription>{card.description}</CardDescription>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-blue-600 font-medium">{card.stats}</span>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => window.location.href = card.href}
                    className="group-hover:bg-blue-50 group-hover:border-blue-200"
                  >
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          </PermissionGate>
        ))}
      </div>

      {/* User Role Information */}
      <Card className="bg-gradient-to-r from-gray-50 to-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-lg text-gray-900">Your Analytics Access</CardTitle>
          <CardDescription>
            Available analytics features based on your role and permissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-3">
              <Users className="h-5 w-5 text-blue-600" />
              <div>
                <p className="font-medium">Role</p>
                <p className="text-sm text-gray-600">{user?.role_display || 'User'}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Monitor className="h-5 w-5 text-green-600" />
              <div>
                <p className="font-medium">Company Type</p>
                <p className="text-sm text-gray-600">
                  {user?.company?.company_type || 'Platform'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <BarChart3 className="h-5 w-5 text-purple-600" />
              <div>
                <p className="font-medium">Permissions</p>
                <p className="text-sm text-gray-600">
                  {user?.permissions.filter(p => p.includes('analytics')).length} analytics permissions
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}