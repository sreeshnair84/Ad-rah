'use client';

import React, { useMemo, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { PermissionGate } from '@/components/PermissionGate';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Plus, Target, Search, Calendar, DollarSign, Eye } from 'lucide-react';
import { format } from 'date-fns';

interface Campaign {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'paused' | 'completed' | 'cancelled';
  budget: number;
  spent: number;
  startDate: Date;
  endDate: Date;
}

const SAMPLE_CAMPAIGNS: Campaign[] = [
  {
    id: '1',
    name: 'Summer Product Launch',
    description: 'Promoting our new summer product line',
    status: 'active',
    budget: 15000,
    spent: 8500,
    startDate: new Date('2024-06-01'),
    endDate: new Date('2024-08-31'),
  },
  {
    id: '2',
    name: 'Back to School Campaign',
    description: 'Targeting students and parents',
    status: 'draft',
    budget: 8000,
    spent: 0,
    startDate: new Date('2024-08-15'),
    endDate: new Date('2024-09-30'),
  },
];

export default function CampaignsPage() {
  const { isAdvertiserCompany } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = useMemo(
    () =>
      SAMPLE_CAMPAIGNS.filter(
        (c) =>
          c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.description.toLowerCase().includes(searchTerm.toLowerCase())
      ),
    [searchTerm]
  );

  const getStatusColor = (status: Campaign['status']) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <PermissionGate
      permission={{ resource: 'campaign', action: 'read' }}
      fallback={
        <div className="container mx-auto py-6">
          <Card>
            <CardContent className="p-6 text-center text-muted-foreground">
              You don't have permission to view campaigns.
            </CardContent>
          </Card>
        </div>
      }
    >
      <div className="container mx-auto py-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold">Campaigns</h2>
            <p className="text-muted-foreground">
              Manage your advertising campaigns and track performance
            </p>
          </div>
          {isAdvertiserCompany && (
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              New Campaign
            </Button>
          )}
        </div>

        {/* Search */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search campaigns..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
          </CardContent>
        </Card>

        {/* Campaign list */}
        {filtered.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No campaigns found</h3>
              <p className="text-muted-foreground mb-4">
                {isAdvertiserCompany
                  ? 'Create your first campaign to start advertising'
                  : 'No campaigns available'}
              </p>
              {isAdvertiserCompany && (
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create Campaign
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filtered.map((campaign) => (
              <Card key={campaign.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg mb-1">{campaign.name}</h3>
                      <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                        {campaign.description}
                      </p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        <span>
                          {format(campaign.startDate, 'MMM dd, yyyy')} -{' '}
                          {format(campaign.endDate, 'MMM dd, yyyy')}
                        </span>
                      </div>
                    </div>
                    <Badge className={`ml-2 ${getStatusColor(campaign.status)}`}>
                      {campaign.status}
                    </Badge>
                  </div>

                  <div className="flex justify-between items-center text-sm">
                    <div>
                      <div className="text-xs text-muted-foreground">Budget</div>
                      <div className="font-medium">${campaign.budget.toLocaleString()}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-muted-foreground">Spent</div>
                      <div className="font-medium text-green-600">
                        ${campaign.spent.toLocaleString()}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1 gap-1">
                      <Eye className="h-3 w-3" />
                      View
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1 gap-1">
                      <DollarSign className="h-3 w-3" />
                      Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </PermissionGate>
  );
}
