'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Plus,
  Play,
  Pause,
  Edit,
  Trash2,
  Calendar,
  Target,
  DollarSign,
  Eye,
  Upload,
  Image,
  Video,
  FileText,
  Clock,
  Users,
  BarChart3,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Copy,
  Filter,
  Search,
  Settings,
  Download
} from 'lucide-react';

interface Campaign {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'paused' | 'completed' | 'scheduled';
  objective: string;
  budget: {
    total: number;
    daily: number;
    spent: number;
    remaining: number;
  };
  dates: {
    start: Date;
    end: Date;
    created: Date;
  };
  targeting: {
    locations: string[];
    demographics: {
      ageGroups: string[];
      incomeLevel: string[];
      interests: string[];
    };
    venues: string[];
    timeSlots: string[];
  };
  content: {
    id: string;
    name: string;
    type: string;
    url: string;
    duration: number;
    status: string;
  }[];
  performance: {
    impressions: number;
    clicks: number;
    ctr: number;
    conversions: number;
    cpm: number;
    reach: number;
  };
  bookings: {
    total: number;
    confirmed: number;
    pending: number;
  };
}

interface ContentItem {
  id: string;
  name: string;
  type: 'image' | 'video' | 'html5';
  file: File | null;
  url: string;
  duration: number;
  size: number;
  status: 'uploading' | 'processing' | 'approved' | 'rejected';
  callToAction?: string;
  landingUrl?: string;
}

export default function CampaignManagement() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Form states for campaign creation
  const [newCampaign, setNewCampaign] = useState({
    name: '',
    description: '',
    objective: 'awareness',
    totalBudget: 1000,
    dailyBudget: 50,
    startDate: '',
    endDate: '',
    targeting: {
      locations: [],
      demographics: {
        ageGroups: [],
        incomeLevel: [],
        interests: []
      },
      venues: [],
      timeSlots: []
    }
  });

  const [contentItems, setContentItems] = useState<ContentItem[]>([]);
  const [uploadingContent, setUploadingContent] = useState(false);

  // Mock data for development
  useEffect(() => {
    const mockCampaigns: Campaign[] = [
      {
        id: '1',
        name: 'Summer Sale 2024',
        description: 'Promote summer discounts across retail locations',
        status: 'active',
        objective: 'conversions',
        budget: {
          total: 5000,
          daily: 150,
          spent: 2340,
          remaining: 2660
        },
        dates: {
          start: new Date('2024-06-01'),
          end: new Date('2024-08-31'),
          created: new Date('2024-05-15')
        },
        targeting: {
          locations: ['Seattle', 'Bellevue', 'Tacoma'],
          demographics: {
            ageGroups: ['25-34', '35-44'],
            incomeLevel: ['middle', 'high'],
            interests: ['shopping', 'fashion']
          },
          venues: ['retail', 'mall'],
          timeSlots: ['morning', 'evening']
        },
        content: [
          {
            id: 'c1',
            name: 'Summer Sale Hero Video',
            type: 'video',
            url: '/content/summer-sale.mp4',
            duration: 30,
            status: 'approved'
          }
        ],
        performance: {
          impressions: 125000,
          clicks: 3200,
          ctr: 2.56,
          conversions: 156,
          cpm: 18.72,
          reach: 87500
        },
        bookings: {
          total: 24,
          confirmed: 20,
          pending: 4
        }
      },
      {
        id: '2',
        name: 'Brand Awareness Q3',
        description: 'Increase brand visibility in fitness centers',
        status: 'paused',
        objective: 'awareness',
        budget: {
          total: 3000,
          daily: 100,
          spent: 1200,
          remaining: 1800
        },
        dates: {
          start: new Date('2024-07-01'),
          end: new Date('2024-09-30'),
          created: new Date('2024-06-20')
        },
        targeting: {
          locations: ['Seattle', 'Portland'],
          demographics: {
            ageGroups: ['25-34', '35-44', '45-54'],
            incomeLevel: ['middle', 'high'],
            interests: ['fitness', 'health']
          },
          venues: ['fitness', 'gym'],
          timeSlots: ['morning', 'evening']
        },
        content: [
          {
            id: 'c2',
            name: 'Brand Logo Animation',
            type: 'video',
            url: '/content/brand-animation.mp4',
            duration: 15,
            status: 'approved'
          }
        ],
        performance: {
          impressions: 45000,
          clicks: 890,
          ctr: 1.98,
          conversions: 23,
          cpm: 26.67,
          reach: 32000
        },
        bookings: {
          total: 12,
          confirmed: 12,
          pending: 0
        }
      },
      {
        id: '3',
        name: 'Holiday Promotion',
        description: 'Seasonal holiday advertising campaign',
        status: 'draft',
        objective: 'traffic',
        budget: {
          total: 8000,
          daily: 200,
          spent: 0,
          remaining: 8000
        },
        dates: {
          start: new Date('2024-11-15'),
          end: new Date('2024-12-31'),
          created: new Date('2024-10-01')
        },
        targeting: {
          locations: ['Seattle', 'Bellevue', 'Redmond'],
          demographics: {
            ageGroups: ['18-24', '25-34', '35-44'],
            incomeLevel: ['middle', 'high'],
            interests: ['shopping', 'gifts', 'family']
          },
          venues: ['retail', 'mall', 'food'],
          timeSlots: ['all-day']
        },
        content: [],
        performance: {
          impressions: 0,
          clicks: 0,
          ctr: 0,
          conversions: 0,
          cpm: 0,
          reach: 0
        },
        bookings: {
          total: 0,
          confirmed: 0,
          pending: 0
        }
      }
    ];

    setCampaigns(mockCampaigns);
  }, []);

  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = campaign.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         campaign.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || campaign.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleCreateCampaign = async () => {
    // Simulate campaign creation
    const campaign: Campaign = {
      id: Date.now().toString(),
      name: newCampaign.name,
      description: newCampaign.description,
      status: 'draft',
      objective: newCampaign.objective,
      budget: {
        total: newCampaign.totalBudget,
        daily: newCampaign.dailyBudget,
        spent: 0,
        remaining: newCampaign.totalBudget
      },
      dates: {
        start: new Date(newCampaign.startDate),
        end: new Date(newCampaign.endDate),
        created: new Date()
      },
      targeting: newCampaign.targeting,
      content: [],
      performance: {
        impressions: 0,
        clicks: 0,
        ctr: 0,
        conversions: 0,
        cpm: 0,
        reach: 0
      },
      bookings: {
        total: 0,
        confirmed: 0,
        pending: 0
      }
    };

    setCampaigns(prev => [...prev, campaign]);
    setShowCreateDialog(false);
    
    // Reset form
    setNewCampaign({
      name: '',
      description: '',
      objective: 'awareness',
      totalBudget: 1000,
      dailyBudget: 50,
      startDate: '',
      endDate: '',
      targeting: {
        locations: [],
        demographics: {
          ageGroups: [],
          incomeLevel: [],
          interests: []
        },
        venues: [],
        timeSlots: []
      }
    });
  };

  const handleStatusChange = (campaignId: string, newStatus: Campaign['status']) => {
    setCampaigns(prev =>
      prev.map(campaign =>
        campaign.id === campaignId
          ? { ...campaign, status: newStatus }
          : campaign
      )
    );
  };

  const handleContentUpload = (files: FileList) => {
    setUploadingContent(true);
    
    Array.from(files).forEach((file, index) => {
      const contentItem: ContentItem = {
        id: Date.now() + index.toString(),
        name: file.name,
        type: file.type.startsWith('image') ? 'image' : 'video',
        file,
        url: URL.createObjectURL(file),
        duration: file.type.startsWith('video') ? 30 : 5,
        size: file.size,
        status: 'uploading'
      };

      setContentItems(prev => [...prev, contentItem]);

      // Simulate upload progress
      setTimeout(() => {
        setContentItems(prev =>
          prev.map(item =>
            item.id === contentItem.id
              ? { ...item, status: 'processing' }
              : item
          )
        );
      }, 2000);

      setTimeout(() => {
        setContentItems(prev =>
          prev.map(item =>
            item.id === contentItem.id
              ? { ...item, status: 'approved' }
              : item
          )
        );
        setUploadingContent(false);
      }, 4000);
    });
  };

  const getStatusColor = (status: Campaign['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'scheduled': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: Campaign['status']) => {
    switch (status) {
      case 'active': return <Play className="h-3 w-3" />;
      case 'paused': return <Pause className="h-3 w-3" />;
      case 'completed': return <CheckCircle className="h-3 w-3" />;
      case 'draft': return <Edit className="h-3 w-3" />;
      case 'scheduled': return <Clock className="h-3 w-3" />;
      default: return <AlertCircle className="h-3 w-3" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Campaign Management</h2>
          <p className="text-gray-600">Create, manage, and track your advertising campaigns</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Campaign
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Campaign</DialogTitle>
            </DialogHeader>
            
            <Tabs defaultValue="basic" className="space-y-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic">Basic Info</TabsTrigger>
                <TabsTrigger value="targeting">Targeting</TabsTrigger>
                <TabsTrigger value="budget">Budget</TabsTrigger>
                <TabsTrigger value="content">Content</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Campaign Name</Label>
                    <Input
                      id="name"
                      value={newCampaign.name}
                      onChange={(e) => setNewCampaign(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter campaign name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="objective">Campaign Objective</Label>
                    <Select
                      value={newCampaign.objective}
                      onValueChange={(value) => setNewCampaign(prev => ({ ...prev, objective: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="awareness">Brand Awareness</SelectItem>
                        <SelectItem value="traffic">Drive Traffic</SelectItem>
                        <SelectItem value="conversions">Conversions</SelectItem>
                        <SelectItem value="engagement">Engagement</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={newCampaign.description}
                    onChange={(e) => setNewCampaign(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe your campaign goals and strategy"
                    rows={3}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="startDate">Start Date</Label>
                    <Input
                      id="startDate"
                      type="date"
                      value={newCampaign.startDate}
                      onChange={(e) => setNewCampaign(prev => ({ ...prev, startDate: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="endDate">End Date</Label>
                    <Input
                      id="endDate"
                      type="date"
                      value={newCampaign.endDate}
                      onChange={(e) => setNewCampaign(prev => ({ ...prev, endDate: e.target.value }))}
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="targeting" className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Target Locations</Label>
                      <div className="space-y-2">
                        {['Seattle', 'Bellevue', 'Tacoma', 'Redmond', 'Portland'].map(location => (
                          <div key={location} className="flex items-center space-x-2">
                            <Checkbox />
                            <Label>{location}</Label>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Venue Types</Label>
                      <div className="space-y-2">
                        {['retail', 'food', 'fitness', 'office', 'transportation'].map(venue => (
                          <div key={venue} className="flex items-center space-x-2">
                            <Checkbox />
                            <Label className="capitalize">{venue}</Label>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Age Groups</Label>
                      <div className="space-y-2">
                        {['18-24', '25-34', '35-44', '45-54', '55+'].map(age => (
                          <div key={age} className="flex items-center space-x-2">
                            <Checkbox />
                            <Label>{age}</Label>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Interests</Label>
                      <div className="space-y-2">
                        {['shopping', 'fitness', 'technology', 'food', 'travel'].map(interest => (
                          <div key={interest} className="flex items-center space-x-2">
                            <Checkbox />
                            <Label className="capitalize">{interest}</Label>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="budget" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="totalBudget">Total Budget ($)</Label>
                    <Input
                      id="totalBudget"
                      type="number"
                      value={newCampaign.totalBudget}
                      onChange={(e) => setNewCampaign(prev => ({ ...prev, totalBudget: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="dailyBudget">Daily Budget ($)</Label>
                    <Input
                      id="dailyBudget"
                      type="number"
                      value={newCampaign.dailyBudget}
                      onChange={(e) => setNewCampaign(prev => ({ ...prev, dailyBudget: Number(e.target.value) }))}
                    />
                  </div>
                </div>

                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Campaign duration: {newCampaign.startDate && newCampaign.endDate 
                      ? Math.ceil((new Date(newCampaign.endDate).getTime() - new Date(newCampaign.startDate).getTime()) / (1000 * 60 * 60 * 24))
                      : 0} days
                  </AlertDescription>
                </Alert>
              </TabsContent>

              <TabsContent value="content" className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Upload className="h-12 w-12 mx-auto text-gray-400" />
                  <p className="mt-2 text-gray-600">Upload your campaign content</p>
                  <p className="text-sm text-gray-500">Support for images, videos, and HTML5 content</p>
                  <Button className="mt-4" onClick={() => document.getElementById('file-upload')?.click()}>
                    Choose Files
                  </Button>
                  <input
                    id="file-upload"
                    type="file"
                    multiple
                    accept="image/*,video/*"
                    className="hidden"
                    onChange={(e) => e.target.files && handleContentUpload(e.target.files)}
                  />
                </div>

                {contentItems.length > 0 && (
                  <div className="space-y-2">
                    <Label>Uploaded Content</Label>
                    <div className="space-y-2">
                      {contentItems.map(item => (
                        <Card key={item.id}>
                          <CardContent className="p-3">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                {item.type === 'image' ? <Image className="h-5 w-5" /> : <Video className="h-5 w-5" />}
                                <div>
                                  <p className="font-medium">{item.name}</p>
                                  <p className="text-sm text-gray-600">{(item.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                              </div>
                              <Badge className={
                                item.status === 'approved' ? 'bg-green-100 text-green-800' :
                                item.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-blue-100 text-blue-800'
                              }>
                                {item.status}
                              </Badge>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </TabsContent>
            </Tabs>

            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateCampaign} disabled={!newCampaign.name}>
                Create Campaign
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters and Search */}
      <div className="flex space-x-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search campaigns..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Campaigns</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="scheduled">Scheduled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Campaign List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredCampaigns.map((campaign) => (
          <Card key={campaign.id} className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <CardTitle className="text-lg">{campaign.name}</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">{campaign.description}</p>
                </div>
                <Badge className={getStatusColor(campaign.status)}>
                  {getStatusIcon(campaign.status)}
                  <span className="ml-1 capitalize">{campaign.status}</span>
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Performance Metrics */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-gray-600">Impressions</p>
                  <p className="font-semibold">{campaign.performance.impressions.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-600">CTR</p>
                  <p className="font-semibold">{campaign.performance.ctr.toFixed(2)}%</p>
                </div>
                <div>
                  <p className="text-gray-600">Spent</p>
                  <p className="font-semibold">${campaign.budget.spent.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-600">Remaining</p>
                  <p className="font-semibold">${campaign.budget.remaining.toLocaleString()}</p>
                </div>
              </div>

              {/* Budget Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Budget Progress</span>
                  <span>{((campaign.budget.spent / campaign.budget.total) * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${Math.min((campaign.budget.spent / campaign.budget.total) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>

              {/* Campaign Duration */}
              <div className="flex items-center text-sm text-gray-600">
                <Calendar className="h-4 w-4 mr-2" />
                <span>
                  {campaign.dates.start.toLocaleDateString()} - {campaign.dates.end.toLocaleDateString()}
                </span>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-3 gap-2 pt-2">
                {campaign.status === 'active' ? (
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleStatusChange(campaign.id, 'paused')}
                  >
                    <Pause className="h-3 w-3 mr-1" />
                    Pause
                  </Button>
                ) : campaign.status === 'paused' ? (
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleStatusChange(campaign.id, 'active')}
                  >
                    <Play className="h-3 w-3 mr-1" />
                    Resume
                  </Button>
                ) : campaign.status === 'draft' ? (
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleStatusChange(campaign.id, 'active')}
                  >
                    <Play className="h-3 w-3 mr-1" />
                    Launch
                  </Button>
                ) : (
                  <Button variant="outline" size="sm" disabled>
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Complete
                  </Button>
                )}
                
                <Button variant="outline" size="sm">
                  <Edit className="h-3 w-3 mr-1" />
                  Edit
                </Button>
                
                <Button variant="outline" size="sm">
                  <BarChart3 className="h-3 w-3 mr-1" />
                  Analytics
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredCampaigns.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Target className="h-12 w-12 mx-auto text-gray-400" />
            <h3 className="text-lg font-semibold mt-4">No campaigns found</h3>
            <p className="text-gray-600 mt-2">
              {searchTerm || statusFilter !== 'all' 
                ? 'Try adjusting your search or filters'
                : 'Create your first campaign to get started'
              }
            </p>
            {!searchTerm && statusFilter === 'all' && (
              <Button className="mt-4" onClick={() => setShowCreateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Campaign
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}