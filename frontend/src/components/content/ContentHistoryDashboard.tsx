"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  User,
  Robot,
  Activity,
  TrendingUp,
  Download,
  Filter,
  Search,
  Calendar,
  BarChart3,
  Timeline,
  FileText,
  Eye
} from 'lucide-react';
import { format } from 'date-fns';

interface ContentHistoryEvent {
  id: string;
  content_id: string;
  event_type: string;
  timestamp: string;
  user_name?: string;
  user_type?: string;
  success: boolean;
  error_message?: string;
  device_id?: string;
  processing_time_ms?: number;
  details: Record<string, any>;
}

interface ContentTimelineEvent {
  id: string;
  type: string;
  timestamp: string;
  user?: string;
  system?: string;
  details: Record<string, any>;
  success: boolean;
  processing_time?: number;
}

interface ContentTimeline {
  content_id: string;
  content_title: string;
  timeline_events: ContentTimelineEvent[];
  milestones: Array<{
    type: string;
    timestamp: string;
    completed: boolean;
  }>;
  current_phase: string;
  performance_score?: number;
  bottlenecks: Array<{
    type: string;
    phase?: string;
    duration_hours?: number;
    severity: string;
  }>;
}

interface ContentLifecycleSummary {
  content_id: string;
  content_title: string;
  current_status: string;
  company_id: string;
  company_name: string;
  uploaded_at?: string;
  ai_moderation_completed_at?: string;
  approved_at?: string;
  first_deployed_at?: string;
  last_displayed_at?: string;
  total_deployments: number;
  total_displays: number;
  total_errors: number;
  uploaded_by?: string;
  reviewed_by?: string;
  recent_events: Array<{
    type: string;
    timestamp: string;
    user?: string;
    success: boolean;
  }>;
}

const ContentHistoryDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('events');
  const [events, setEvents] = useState<ContentHistoryEvent[]>([]);
  const [selectedContent, setSelectedContent] = useState<string>('');
  const [timeline, setTimeline] = useState<ContentTimeline | null>(null);
  const [lifecycle, setLifecycle] = useState<ContentLifecycleSummary | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    event_types: '',
    user_ids: '',
    start_date: '',
    end_date: '',
    include_system_events: true,
    include_error_events: true
  });

  // Load recent events on component mount
  useEffect(() => {
    loadRecentEvents();
    loadHistoryStats();
  }, []);

  const loadRecentEvents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/history/events/recent?limit=50');
      if (response.ok) {
        const data = await response.json();
        setEvents(data.events || []);
      }
    } catch (error) {
      console.error('Failed to load recent events:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadHistoryStats = async () => {
    try {
      const response = await fetch('/api/history/stats/summary?days=30');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load history stats:', error);
    }
  };

  const loadContentTimeline = async (contentId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/history/content/${contentId}/timeline`);
      if (response.ok) {
        const data = await response.json();
        setTimeline(data);
      }
    } catch (error) {
      console.error('Failed to load content timeline:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadContentLifecycle = async (contentId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/history/content/${contentId}/lifecycle`);
      if (response.ok) {
        const data = await response.json();
        setLifecycle(data);
      }
    } catch (error) {
      console.error('Failed to load content lifecycle:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleContentSelect = (contentId: string) => {
    setSelectedContent(contentId);
    if (contentId) {
      loadContentTimeline(contentId);
      loadContentLifecycle(contentId);
    }
  };

  const searchEvents = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();

      if (filters.event_types) params.append('event_types', filters.event_types);
      if (filters.user_ids) params.append('user_ids', filters.user_ids);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      params.append('include_system_events', filters.include_system_events.toString());
      params.append('include_error_events', filters.include_error_events.toString());
      params.append('limit', '100');

      const response = await fetch(`/api/history/content?${params}`);
      if (response.ok) {
        const data = await response.json();
        setEvents(data || []);
      }
    } catch (error) {
      console.error('Failed to search events:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateAuditReport = async () => {
    try {
      setLoading(true);
      const startDate = filters.start_date || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
      const endDate = filters.end_date || new Date().toISOString();

      const response = await fetch(`/api/history/audit/report?start_date=${startDate}&end_date=${endDate}&report_type=custom`);
      if (response.ok) {
        const data = await response.json();
        // Handle audit report download or display
        console.log('Audit report generated:', data);
      }
    } catch (error) {
      console.error('Failed to generate audit report:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEventIcon = (eventType: string, success: boolean) => {
    if (!success) return <XCircle className="h-4 w-4 text-red-500" />;

    switch (eventType) {
      case 'uploaded':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case 'ai_moderation_completed':
        return <Robot className="h-4 w-4 text-purple-500" />;
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'deployed':
        return <Activity className="h-4 w-4 text-blue-500" />;
      case 'displayed':
        return <Eye className="h-4 w-4 text-green-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getEventBadgeColor = (eventType: string, success: boolean) => {
    if (!success) return 'destructive';

    switch (eventType) {
      case 'uploaded':
        return 'default';
      case 'ai_moderation_completed':
        return 'secondary';
      case 'approved':
        return 'default';
      case 'rejected':
        return 'destructive';
      case 'deployed':
        return 'default';
      case 'displayed':
        return 'default';
      default:
        return 'outline';
    }
  };

  const formatEventType = (eventType: string) => {
    return eventType.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Content History & Audit</h2>
          <p className="text-muted-foreground">
            Track content lifecycle events, review performance, and generate compliance reports
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadRecentEvents}>
            <Activity className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={generateAuditReport}>
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Statistics Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Events</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_events}</div>
              <p className="text-xs text-muted-foreground">Last 30 days</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.error_rate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">System reliability</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Content</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.most_active_content.length}</div>
              <p className="text-xs text-muted-foreground">Content items</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.recent_activity.length}</div>
              <p className="text-xs text-muted-foreground">Events today</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="events">Event History</TabsTrigger>
          <TabsTrigger value="timeline">Content Timeline</TabsTrigger>
          <TabsTrigger value="lifecycle">Lifecycle Analysis</TabsTrigger>
          <TabsTrigger value="analytics">Performance Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="events" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Filter className="h-5 w-5" />
                Event Filters
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="event-types">Event Types</Label>
                  <Input
                    id="event-types"
                    placeholder="uploaded,approved,rejected"
                    value={filters.event_types}
                    onChange={(e) => setFilters(prev => ({ ...prev, event_types: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="start-date">Start Date</Label>
                  <Input
                    id="start-date"
                    type="datetime-local"
                    value={filters.start_date}
                    onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end-date">End Date</Label>
                  <Input
                    id="end-date"
                    type="datetime-local"
                    value={filters.end_date}
                    onChange={(e) => setFilters(prev => ({ ...prev, end_date: e.target.value }))}
                  />
                </div>
              </div>

              <div className="flex gap-4">
                <Button onClick={searchEvents} disabled={loading}>
                  <Search className="h-4 w-4 mr-2" />
                  Search Events
                </Button>
                <Button variant="outline" onClick={loadRecentEvents}>
                  Reset Filters
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Event History</CardTitle>
              <CardDescription>
                Comprehensive log of all content lifecycle events
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-2">
                  {events.map((event) => (
                    <div
                      key={event.id}
                      className="flex items-center space-x-4 p-3 border rounded-lg hover:bg-muted/50 cursor-pointer"
                      onClick={() => handleContentSelect(event.content_id)}
                    >
                      <div className="flex-shrink-0">
                        {getEventIcon(event.event_type, event.success)}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Badge variant={getEventBadgeColor(event.event_type, event.success)}>
                            {formatEventType(event.event_type)}
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            Content: {event.content_id}
                          </span>
                        </div>

                        <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {format(new Date(event.timestamp), 'MMM dd, yyyy HH:mm')}
                          </span>

                          {event.user_name && (
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {event.user_name}
                            </span>
                          )}

                          {event.processing_time_ms && (
                            <span className="flex items-center gap-1">
                              <BarChart3 className="h-3 w-3" />
                              {event.processing_time_ms}ms
                            </span>
                          )}
                        </div>

                        {event.error_message && (
                          <div className="text-sm text-red-600 mt-1">
                            Error: {event.error_message}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Content Timeline Viewer</CardTitle>
              <CardDescription>
                Select content to view its complete lifecycle timeline
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4">
                <Input
                  placeholder="Enter content ID"
                  value={selectedContent}
                  onChange={(e) => setSelectedContent(e.target.value)}
                  className="flex-1"
                />
                <Button
                  onClick={() => handleContentSelect(selectedContent)}
                  disabled={!selectedContent || loading}
                >
                  <Timeline className="h-4 w-4 mr-2" />
                  Load Timeline
                </Button>
              </div>

              {timeline && (
                <div className="space-y-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-semibold">{timeline.content_title}</h3>
                      <p className="text-sm text-muted-foreground">
                        Current Phase: <Badge>{timeline.current_phase}</Badge>
                      </p>
                    </div>
                    {timeline.performance_score && (
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">Performance Score</p>
                        <p className="text-2xl font-bold">{timeline.performance_score.toFixed(1)}%</p>
                      </div>
                    )}
                  </div>

                  {/* Milestones */}
                  <div>
                    <h4 className="font-medium mb-3">Milestones</h4>
                    <div className="flex gap-4">
                      {timeline.milestones.map((milestone, index) => (
                        <div key={index} className="flex flex-col items-center">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            milestone.completed ? 'bg-green-500 text-white' : 'bg-gray-200'
                          }`}>
                            {milestone.completed ? <CheckCircle className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
                          </div>
                          <span className="text-xs mt-1 text-center">{formatEventType(milestone.type)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Timeline Events */}
                  <div>
                    <h4 className="font-medium mb-3">Event Timeline</h4>
                    <ScrollArea className="h-[400px]">
                      <div className="space-y-3">
                        {timeline.timeline_events.map((event, index) => (
                          <div key={event.id} className="flex gap-3">
                            <div className="flex flex-col items-center">
                              <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                event.success ? 'bg-green-100' : 'bg-red-100'
                              }`}>
                                {getEventIcon(event.type, event.success)}
                              </div>
                              {index < timeline.timeline_events.length - 1 && (
                                <div className="w-px h-8 bg-gray-200 mt-1" />
                              )}
                            </div>
                            <div className="flex-1 pb-4">
                              <div className="flex items-center gap-2">
                                <Badge variant={getEventBadgeColor(event.type, event.success)}>
                                  {formatEventType(event.type)}
                                </Badge>
                                <span className="text-sm text-muted-foreground">
                                  {format(new Date(event.timestamp), 'MMM dd, HH:mm')}
                                </span>
                              </div>
                              <p className="text-sm mt-1">
                                {event.user ? `By ${event.user}` : 'System automated'}
                                {event.processing_time && ` (${event.processing_time}ms)`}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>

                  {/* Bottlenecks */}
                  {timeline.bottlenecks.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-3">Identified Bottlenecks</h4>
                      <div className="space-y-2">
                        {timeline.bottlenecks.map((bottleneck, index) => (
                          <div key={index} className="p-3 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                            <div className="flex justify-between items-start">
                              <div>
                                <p className="text-sm font-medium">
                                  {bottleneck.type === 'long_gap' ? 'Processing Delay' : 'High Error Rate'}
                                </p>
                                <p className="text-sm text-muted-foreground">
                                  {bottleneck.phase && `Phase: ${bottleneck.phase}`}
                                  {bottleneck.duration_hours && ` (${bottleneck.duration_hours}h delay)`}
                                </p>
                              </div>
                              <Badge variant={bottleneck.severity === 'high' ? 'destructive' : 'secondary'}>
                                {bottleneck.severity}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="lifecycle" className="space-y-4">
          {lifecycle && (
            <Card>
              <CardHeader>
                <CardTitle>Content Lifecycle Summary</CardTitle>
                <CardDescription>{lifecycle.content_title}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Current Status</Label>
                    <Badge className="w-fit">{lifecycle.current_status}</Badge>
                  </div>
                  <div className="space-y-2">
                    <Label>Total Deployments</Label>
                    <p className="text-2xl font-bold">{lifecycle.total_deployments}</p>
                  </div>
                  <div className="space-y-2">
                    <Label>Total Displays</Label>
                    <p className="text-2xl font-bold">{lifecycle.total_displays}</p>
                  </div>
                </div>

                <Separator />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium mb-3">Key Timestamps</h4>
                    <div className="space-y-2">
                      {lifecycle.uploaded_at && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Uploaded:</span>
                          <span className="text-sm">{format(new Date(lifecycle.uploaded_at), 'MMM dd, yyyy HH:mm')}</span>
                        </div>
                      )}
                      {lifecycle.ai_moderation_completed_at && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">AI Review:</span>
                          <span className="text-sm">{format(new Date(lifecycle.ai_moderation_completed_at), 'MMM dd, yyyy HH:mm')}</span>
                        </div>
                      )}
                      {lifecycle.approved_at && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Approved:</span>
                          <span className="text-sm">{format(new Date(lifecycle.approved_at), 'MMM dd, yyyy HH:mm')}</span>
                        </div>
                      )}
                      {lifecycle.first_deployed_at && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">First Deployed:</span>
                          <span className="text-sm">{format(new Date(lifecycle.first_deployed_at), 'MMM dd, yyyy HH:mm')}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-3">User Involvement</h4>
                    <div className="space-y-2">
                      {lifecycle.uploaded_by && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Uploaded by:</span>
                          <span className="text-sm">{lifecycle.uploaded_by}</span>
                        </div>
                      )}
                      {lifecycle.reviewed_by && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Reviewed by:</span>
                          <span className="text-sm">{lifecycle.reviewed_by}</span>
                        </div>
                      )}
                      {lifecycle.last_modified_by && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Last modified by:</span>
                          <span className="text-sm">{lifecycle.last_modified_by}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {lifecycle.recent_events.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3">Recent Activity</h4>
                      <div className="space-y-2">
                        {lifecycle.recent_events.slice(0, 5).map((event, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                            <div className="flex items-center gap-2">
                              {getEventIcon(event.type, event.success)}
                              <span className="text-sm">{formatEventType(event.type)}</span>
                            </div>
                            <div className="text-right">
                              <p className="text-sm">{event.user || 'System'}</p>
                              <p className="text-xs text-muted-foreground">
                                {format(new Date(event.timestamp), 'MMM dd, HH:mm')}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Event Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {stats?.events_by_type && (
                  <div className="space-y-2">
                    {Object.entries(stats.events_by_type).map(([eventType, count]: [string, any]) => (
                      <div key={eventType} className="flex justify-between items-center">
                        <span className="text-sm">{formatEventType(eventType)}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full"
                              style={{ width: `${(count / stats.total_events) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium w-8">{count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Most Active Content</CardTitle>
              </CardHeader>
              <CardContent>
                {stats?.most_active_content && (
                  <div className="space-y-2">
                    {stats.most_active_content.slice(0, 5).map((item: any, index: number) => (
                      <div key={index} className="flex justify-between items-center">
                        <span className="text-sm font-mono text-muted-foreground">
                          {item.content_id.slice(0, 8)}...
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${(item.event_count / (stats.most_active_content[0]?.event_count || 1)) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium w-6">{item.event_count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ContentHistoryDashboard;