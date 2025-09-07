'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, Monitor, Send, CheckCircle2, AlertCircle, Calendar } from 'lucide-react';
import { useContent } from '@/hooks/useContent';
import { useDevice } from '@/hooks/useDevice';

interface ContentItem {
  id: string;
  filename: string;
  status: string;
  upload_date: string;
  approved_by?: string;
  approval_date?: string;
  ai_analysis?: any;
}

interface Device {
  id: string;
  name: string;
  location: string;
  status: 'online' | 'offline' | 'error';
  company_id: string;
  device_type: string;
}

export default function ContentDistributionPage() {
  const { loading: contentLoading, error: contentError, listMetadata } = useContent();
  const { loading: deviceLoading, error: deviceError, listDevices, distributeContent } = useDevice();
  
  const [content, setContent] = useState<ContentItem[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedContent, setSelectedContent] = useState<string[]>([]);
  const [selectedDevices, setSelectedDevices] = useState<string[]>([]);
  const [distributing, setDistributing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [contentData, deviceData] = await Promise.all([
        listMetadata(),
        listDevices()
      ]);
      
      // Only show approved content for distribution
      const approvedContent = contentData.filter((item: ContentItem) => item.status === 'approved');
      setContent(approvedContent);
      setDevices(deviceData);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  };

  const handleDistribute = async () => {
    if (selectedContent.length === 0 || selectedDevices.length === 0) {
      return;
    }

    setDistributing(true);
    try {
      // Distribute each selected content to all selected devices
      for (const contentId of selectedContent) {
        await distributeContent(contentId, selectedDevices);
      }
      
      // Reset selections
      setSelectedContent([]);
      setSelectedDevices([]);
      
      alert('Content distributed successfully!');
    } catch (err) {
      console.error('Failed to distribute content:', err);
      alert('Failed to distribute content. Please try again.');
    } finally {
      setDistributing(false);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'online':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'offline':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'online':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'offline':
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Monitor className="h-4 w-4 text-gray-400" />;
    }
  };

  const loading = contentLoading || deviceLoading;
  const error = contentError || deviceError;

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Content Distribution</h1>
        <Button
          onClick={handleDistribute}
          disabled={distributing || selectedContent.length === 0 || selectedDevices.length === 0}
          className="flex items-center gap-2"
        >
          {distributing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          Distribute Content
        </Button>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Approved Content */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              Approved Content ({selectedContent.length} selected)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span className="ml-2">Loading content...</span>
              </div>
            ) : content.length === 0 ? (
              <div className="text-center p-8 text-gray-500">
                <CheckCircle2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No approved content available for distribution.</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {content.map((item) => (
                  <div
                    key={item.id}
                    className={`flex items-center space-x-3 p-3 rounded-lg border-2 transition-all ${
                      selectedContent.includes(item.id)
                        ? 'border-blue-300 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Checkbox
                      id={`content-${item.id}`}
                      checked={selectedContent.includes(item.id)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setSelectedContent([...selectedContent, item.id]);
                        } else {
                          setSelectedContent(selectedContent.filter(id => id !== item.id));
                        }
                      }}
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-sm">{item.filename}</h4>
                        <div className="flex items-center gap-1">
                          {getStatusIcon(item.status)}
                          <Badge className={getStatusBadgeColor(item.status)}>
                            {item.status}
                          </Badge>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          Uploaded: {new Date(item.upload_date).toLocaleDateString()}
                        </div>
                        {item.approved_by && (
                          <div>Approved by: {item.approved_by}</div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Available Devices */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Monitor className="h-5 w-5 text-blue-500" />
              Available Devices ({selectedDevices.length} selected)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span className="ml-2">Loading devices...</span>
              </div>
            ) : devices.length === 0 ? (
              <div className="text-center p-8 text-gray-500">
                <Monitor className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No devices available.</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {devices.map((device) => (
                  <div
                    key={device.id}
                    className={`flex items-center space-x-3 p-3 rounded-lg border-2 transition-all ${
                      selectedDevices.includes(device.id)
                        ? 'border-blue-300 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Checkbox
                      id={`device-${device.id}`}
                      checked={selectedDevices.includes(device.id)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setSelectedDevices([...selectedDevices, device.id]);
                        } else {
                          setSelectedDevices(selectedDevices.filter(id => id !== device.id));
                        }
                      }}
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-sm">{device.name}</h4>
                        <div className="flex items-center gap-1">
                          {getStatusIcon(device.status)}
                          <Badge className={getStatusBadgeColor(device.status)}>
                            {device.status}
                          </Badge>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        <div>Location: {device.location}</div>
                        <div>Type: {device.device_type}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Distribution Summary */}
      {(selectedContent.length > 0 || selectedDevices.length > 0) && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span className="font-medium">{selectedContent.length}</span>
                  <span className="text-gray-600">content items selected</span>
                </div>
                <div className="flex items-center gap-2">
                  <Monitor className="h-4 w-4 text-blue-500" />
                  <span className="font-medium">{selectedDevices.length}</span>
                  <span className="text-gray-600">devices selected</span>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                Total distributions: <span className="font-medium">{selectedContent.length * selectedDevices.length}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
