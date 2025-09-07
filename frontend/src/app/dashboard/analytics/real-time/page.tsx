'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Activity, 
  Users, 
  Eye, 
  MousePointer, 
  Monitor, 
  AlertCircle, 
  TrendingUp, 
  DollarSign,
  Wifi,
  WifiOff,
  Play,
  Pause
} from 'lucide-react'

// Types for real-time analytics data
interface RealTimeMetrics {
  timestamp: string
  period: string
  total_impressions: number
  unique_viewers: number
  total_dwell_time: number
  average_dwell_time: number
  engagement_rate: number
  content_plays: number
  content_completions: number
  completion_rate: number
  interaction_count: number
  interaction_rate: number
  active_devices: number
  device_uptime: number
  average_performance_score: number
  error_count: number
  error_rate: number
  revenue_generated: number
  cost_per_impression: number
  return_on_investment: number
  conversion_count: number
  conversion_rate: number
  data_accuracy: number
  verification_rate: number
  confidence_level: number
}

interface DeviceStatus {
  device_id: string
  status: 'online' | 'offline' | 'error'
  last_seen: string
  performance_score: number
  current_content: string | null
  location?: { lat: number; lng: number }
}

interface AnalyticsEvent {
  id: string
  metric_type: string
  event_type: string
  device_id: string
  content_id?: string
  value: number
  timestamp: string
  audience_count?: number
}

export default function RealTimeAnalyticsPage() {
  const [metrics, setMetrics] = useState<RealTimeMetrics | null>(null)
  const [devices, setDevices] = useState<DeviceStatus[]>([])
  const [recentEvents, setRecentEvents] = useState<AnalyticsEvent[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<string>('')

  // WebSocket connection for real-time updates
  const connectWebSocket = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//localhost:8000/api/analytics/stream`
    
    try {
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('Connected to analytics stream')
        setIsConnected(true)
        setIsStreaming(true)
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'metrics_update') {
            setMetrics(data.metrics)
            setLastUpdate(new Date().toLocaleTimeString())
          } else if (data.type === 'device_status') {
            setDevices(data.devices)
          } else if (data.type === 'metric_event') {
            setRecentEvents(prev => [data.event, ...prev.slice(0, 9)])
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      ws.onclose = () => {
        console.log('Disconnected from analytics stream')
        setIsConnected(false)
        setIsStreaming(false)
        
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000)
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
        setIsStreaming(false)
      }
      
      return ws
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      return null
    }
  }, [])

  // Fetch initial metrics via REST API
  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch('/api/analytics/real-time', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setMetrics(data.metrics)
          setLastUpdate(new Date().toLocaleTimeString())
        }
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    }
  }, [])

  // Fetch device status
  const fetchDeviceStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/devices/status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setDevices(data.devices)
        }
      }
    } catch (error) {
      console.error('Failed to fetch device status:', error)
    }
  }, [])

  useEffect(() => {
    // Initial data fetch
    fetchMetrics()
    fetchDeviceStatus()
    
    // Connect to WebSocket for real-time updates
    const ws = connectWebSocket()
    
    // Fallback polling if WebSocket fails
    const pollInterval = setInterval(() => {
      if (!isConnected) {
        fetchMetrics()
        fetchDeviceStatus()
      }
    }, 10000)
    
    return () => {
      clearInterval(pollInterval)
      if (ws) {
        ws.close()
      }
    }
  }, [connectWebSocket, fetchMetrics, fetchDeviceStatus, isConnected])

  const toggleStreaming = () => {
    if (isStreaming) {
      setIsStreaming(false)
    } else {
      connectWebSocket()
    }
  }

  return (
    <div className="flex-1 space-y-4 p-4 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Real-Time Analytics</h2>
          <p className="text-muted-foreground">
            Live performance metrics and device monitoring
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={isConnected ? "default" : "secondary"} className="flex items-center space-x-1">
            {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={toggleStreaming}
            className="flex items-center space-x-1"
          >
            {isStreaming ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            <span>{isStreaming ? 'Pause' : 'Resume'}</span>
          </Button>
          {lastUpdate && (
            <Badge variant="outline">
              Last Update: {lastUpdate}
            </Badge>
          )}
        </div>
      </div>

      {metrics ? (
        <>
          {/* Key Metrics Overview */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Impressions</CardTitle>
                <Eye className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.total_impressions.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  {metrics.unique_viewers} unique viewers
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Engagement Rate</CardTitle>
                <MousePointer className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.engagement_rate.toFixed(1)}%</div>
                <p className="text-xs text-muted-foreground">
                  {metrics.interaction_count} interactions
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Devices</CardTitle>
                <Monitor className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.active_devices}</div>
                <p className="text-xs text-muted-foreground">
                  {metrics.device_uptime.toFixed(1)}% uptime
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Revenue</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">${metrics.revenue_generated.toFixed(2)}</div>
                <p className="text-xs text-muted-foreground">
                  ${metrics.cost_per_impression.toFixed(4)} CPI
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Analytics Tabs */}
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="content">Content Performance</TabsTrigger>
              <TabsTrigger value="devices">Device Status</TabsTrigger>
              <TabsTrigger value="audience">Audience Insights</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Performance Metrics</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Content Completion Rate</span>
                        <span className="text-sm text-muted-foreground">{metrics.completion_rate.toFixed(1)}%</span>
                      </div>
                      <Progress value={metrics.completion_rate} className="mt-2" />
                    </div>
                    
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">System Performance</span>
                        <span className="text-sm text-muted-foreground">{metrics.average_performance_score.toFixed(1)}%</span>
                      </div>
                      <Progress value={metrics.average_performance_score} className="mt-2" />
                    </div>
                    
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Data Accuracy</span>
                        <span className="text-sm text-muted-foreground">{metrics.data_accuracy.toFixed(1)}%</span>
                      </div>
                      <Progress value={metrics.data_accuracy} className="mt-2" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>System Health</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          {metrics.error_count > 0 ? (
                            <AlertCircle className="h-4 w-4 text-destructive" />
                          ) : (
                            <Activity className="h-4 w-4 text-green-500" />
                          )}
                          <span className="text-sm font-medium">System Status</span>
                        </div>
                        <Badge variant={metrics.error_count > 0 ? "destructive" : "default"}>
                          {metrics.error_count > 0 ? `${metrics.error_count} Errors` : 'Healthy'}
                        </Badge>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="text-sm text-muted-foreground">Error Rate: {metrics.error_rate.toFixed(2)}%</div>
                        <div className="text-sm text-muted-foreground">Verification Rate: {metrics.verification_rate.toFixed(1)}%</div>
                        <div className="text-sm text-muted-foreground">Confidence Level: {metrics.confidence_level.toFixed(1)}%</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="content" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Content Performance</CardTitle>
                  <CardDescription>Real-time content engagement metrics</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="space-y-2">
                      <div className="text-2xl font-bold">{metrics.content_plays}</div>
                      <div className="text-sm text-muted-foreground">Content Plays</div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-2xl font-bold">{metrics.content_completions}</div>
                      <div className="text-sm text-muted-foreground">Completions</div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-2xl font-bold">{metrics.average_dwell_time.toFixed(1)}s</div>
                      <div className="text-sm text-muted-foreground">Avg Dwell Time</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="devices" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Device Status</CardTitle>
                  <CardDescription>Real-time device monitoring</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {devices.map((device) => (
                      <div key={device.device_id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            device.status === 'online' ? 'bg-green-500' :
                            device.status === 'offline' ? 'bg-gray-400' : 'bg-red-500'
                          }`} />
                          <div>
                            <div className="font-medium">{device.device_id}</div>
                            <div className="text-sm text-muted-foreground">
                              Last seen: {new Date(device.last_seen).toLocaleTimeString()}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium">{device.performance_score.toFixed(1)}% Performance</div>
                          {device.current_content && (
                            <div className="text-sm text-muted-foreground">Playing: {device.current_content}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="audience" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Audience Insights</CardTitle>
                  <CardDescription>Real-time audience engagement data</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <div className="text-2xl font-bold">{metrics.conversion_count}</div>
                      <div className="text-sm text-muted-foreground">Total Conversions</div>
                      <div className="text-sm text-green-600">{metrics.conversion_rate.toFixed(2)}% conversion rate</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{metrics.return_on_investment.toFixed(2)}%</div>
                      <div className="text-sm text-muted-foreground">Return on Investment</div>
                      <div className="text-sm text-green-600">Revenue generated: ${metrics.revenue_generated.toFixed(2)}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Recent Events */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Analytics Events</CardTitle>
              <CardDescription>Live stream of analytics events</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {recentEvents.length > 0 ? (
                  recentEvents.map((event) => (
                    <div key={event.id} className="flex items-center justify-between p-2 border rounded-lg text-sm">
                      <div className="flex items-center space-x-3">
                        <Badge variant="outline">{event.metric_type}</Badge>
                        <span>{event.event_type}</span>
                        <span className="text-muted-foreground">Device: {event.device_id}</span>
                      </div>
                      <div className="text-muted-foreground">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    No recent events. Events will appear here as they occur.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="flex items-center justify-center h-64">
            <div className="text-center">
              <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
              <div className="text-muted-foreground">Loading analytics data...</div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}