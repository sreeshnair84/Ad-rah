'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/hooks/useAuth';
import {
  Layers,
  Plus,
  Edit2,
  Trash2,
  Eye,
  Monitor,
  AlertCircle,
  Save,
  Search,
  ZoomIn,
  ZoomOut,
  Calendar,
  Clock,
  CheckCircle2,
  Play,
  Pause,
  Settings,
  Target,
  FileImage,
  FileVideo,
  FileText,
  File,
  ArrowRight,
  Send,
  Grid,
  List
} from 'lucide-react';

interface DigitalScreen {
  id: string;
  name: string;
  resolution_width: number;
  resolution_height: number;
  orientation: 'landscape' | 'portrait';
}

interface ApprovedContent {
  id: string;
  title: string;
  filename: string;
  content_type: string;
  size: number;
  status: 'approved';
  created_at: string;
  categories?: string[];
  description?: string;
  content_url?: string;
}

interface ContentOverlay {
  id: string;
  content_id: string;
  screen_id: string;
  company_id: string;
  name: string;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  z_index: number;
  opacity: number;
  rotation: number;
  start_time?: string;
  end_time?: string;
  status: 'draft' | 'active' | 'scheduled' | 'expired' | 'paused';
  created_by: string;
  created_at: string;
  updated_at: string;
  content?: ApprovedContent;
}

interface OverlayFormData {
  content_id: string;
  screen_id: string;
  company_id: string;
  name: string;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  z_index: number;
  opacity: number;
  rotation: number;
  start_time?: string;
  end_time?: string;
  status: 'draft' | 'active' | 'scheduled' | 'expired' | 'paused';
}

interface UnifiedOverlayManagerProps {
  mode?: 'simple' | 'advanced';
  defaultScreenId?: string;
  showCanvas?: boolean;
  showList?: boolean;
}

export function UnifiedOverlayManager({
  mode = 'advanced',
  defaultScreenId,
  showCanvas = true,
  showList = true
}: UnifiedOverlayManagerProps) {
  const { user, hasPermission } = useAuth();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [screens, setScreens] = useState<DigitalScreen[]>([]);
  const [overlays, setOverlays] = useState<ContentOverlay[]>([]);
  const [approvedContent, setApprovedContent] = useState<ApprovedContent[]>([]);
  const [selectedScreen, setSelectedScreen] = useState<DigitalScreen | null>(null);
  const [selectedOverlay, setSelectedOverlay] = useState<ContentOverlay | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [zoomLevel, setZoomLevel] = useState(0.5);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [activeTab, setActiveTab] = useState('canvas');

  const [formData, setFormData] = useState<OverlayFormData>({
    content_id: '',
    screen_id: '',
    company_id: user?.company_id || '',
    name: '',
    position_x: 100,
    position_y: 100,
    width: 300,
    height: 200,
    z_index: 1,
    opacity: 1.0,
    rotation: 0,
    status: 'draft'
  });

  // Check permissions
  const canEditOverlays = hasPermission('overlay', 'create') || hasPermission('overlay', 'edit');
  const canViewOverlays = hasPermission('overlay', 'view');

  // Fetch approved content
  const fetchApprovedContent = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/content/approved', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch approved content');
      const data = await response.json();
      setApprovedContent(data.approved_content || []);
    } catch (err) {
      console.error('Failed to fetch approved content:', err);
    }
  }, []);

  // Fetch screens
  const fetchScreens = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/screens', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch screens');
      const data = await response.json();
      setScreens(data);

      // Set default screen
      if (data.length > 0) {
        const defaultScreen = defaultScreenId
          ? data.find((s: DigitalScreen) => s.id === defaultScreenId)
          : data[0];
        setSelectedScreen(defaultScreen || data[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch screens');
    }
  }, [defaultScreenId]);

  // Fetch overlays for selected screen
  const fetchOverlays = useCallback(async (screenId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/screens/${screenId}/overlays`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch overlays');
      const data = await response.json();
      setOverlays(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch overlays');
    }
  }, []);

  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      await Promise.all([fetchScreens(), fetchApprovedContent()]);
      setLoading(false);
    };
    initializeData();
  }, [fetchScreens, fetchApprovedContent]);

  useEffect(() => {
    if (selectedScreen) {
      fetchOverlays(selectedScreen.id);
      setFormData(prev => ({ ...prev, screen_id: selectedScreen.id }));
    }
  }, [selectedScreen, fetchOverlays]);

  // Canvas drawing
  useEffect(() => {
    if (selectedScreen && canvasRef.current && showCanvas) {
      drawCanvas();
    }
  }, [selectedScreen, overlays, zoomLevel, showCanvas]);

  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !selectedScreen) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size based on screen resolution and zoom
    const scaledWidth = selectedScreen.resolution_width * zoomLevel;
    const scaledHeight = selectedScreen.resolution_height * zoomLevel;

    canvas.width = scaledWidth;
    canvas.height = scaledHeight;

    // Clear canvas
    ctx.clearRect(0, 0, scaledWidth, scaledHeight);

    // Draw screen background
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, scaledWidth, scaledHeight);

    // Draw grid
    ctx.strokeStyle = '#e9ecef';
    ctx.lineWidth = 1;
    const gridSize = 50 * zoomLevel;
    for (let x = 0; x <= scaledWidth; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, scaledHeight);
      ctx.stroke();
    }
    for (let y = 0; y <= scaledHeight; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(scaledWidth, y);
      ctx.stroke();
    }

    // Draw overlays
    overlays.forEach((overlay, index) => {
      const x = overlay.position_x * zoomLevel;
      const y = overlay.position_y * zoomLevel;
      const width = overlay.width * zoomLevel;
      const height = overlay.height * zoomLevel;

      ctx.save();

      // Apply rotation
      if (overlay.rotation) {
        ctx.translate(x + width/2, y + height/2);
        ctx.rotate((overlay.rotation * Math.PI) / 180);
        ctx.translate(-width/2, -height/2);
      } else {
        ctx.translate(x, y);
      }

      // Draw overlay rectangle
      ctx.globalAlpha = overlay.opacity;
      ctx.fillStyle = selectedOverlay?.id === overlay.id ? '#3b82f6' : '#6366f1';
      ctx.fillRect(0, 0, width, height);

      // Draw border
      ctx.strokeStyle = selectedOverlay?.id === overlay.id ? '#1d4ed8' : '#4f46e5';
      ctx.lineWidth = 2;
      ctx.strokeRect(0, 0, width, height);

      // Draw label
      ctx.globalAlpha = 1;
      ctx.fillStyle = '#ffffff';
      ctx.font = `${12 * zoomLevel}px Arial`;
      ctx.textAlign = 'center';
      ctx.fillText(overlay.name, width/2, height/2);

      // Draw z-index indicator
      ctx.fillStyle = '#ef4444';
      ctx.font = `${10 * zoomLevel}px Arial`;
      ctx.textAlign = 'left';
      ctx.fillText(`Z:${overlay.z_index}`, 4, 14 * zoomLevel);

      ctx.restore();
    });
  }, [selectedScreen, overlays, zoomLevel, selectedOverlay]);

  // Handle canvas mouse events for drag and drop
  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canEditOverlays) return;

    const canvas = canvasRef.current;
    if (!canvas || !selectedScreen) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoomLevel;
    const y = (e.clientY - rect.top) / zoomLevel;

    // Check if clicking on an overlay
    const clickedOverlay = overlays.find(overlay =>
      x >= overlay.position_x &&
      x <= overlay.position_x + overlay.width &&
      y >= overlay.position_y &&
      y <= overlay.position_y + overlay.height
    );

    if (clickedOverlay) {
      setSelectedOverlay(clickedOverlay);
      setIsDragging(true);
      setDragOffset({
        x: x - clickedOverlay.position_x,
        y: y - clickedOverlay.position_y
      });
    } else {
      setSelectedOverlay(null);
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging || !selectedOverlay || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoomLevel;
    const y = (e.clientY - rect.top) / zoomLevel;

    const newX = Math.max(0, x - dragOffset.x);
    const newY = Math.max(0, y - dragOffset.y);

    // Update overlay position locally
    setOverlays(prev => prev.map(overlay =>
      overlay.id === selectedOverlay.id
        ? { ...overlay, position_x: newX, position_y: newY }
        : overlay
    ));
  };

  const handleCanvasMouseUp = async () => {
    if (isDragging && selectedOverlay) {
      // Save position to backend
      try {
        const token = localStorage.getItem('access_token');
        await fetch(`/api/screens/${selectedScreen?.id}/overlays/${selectedOverlay.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            position_x: selectedOverlay.position_x,
            position_y: selectedOverlay.position_y
          }),
        });
      } catch (err) {
        setError('Failed to update overlay position');
      }
    }
    setIsDragging(false);
  };

  // Create overlay
  const handleCreateOverlay = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/screens/${selectedScreen?.id}/overlays`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error('Failed to create overlay');

      if (selectedScreen) {
        await fetchOverlays(selectedScreen.id);
      }
      setIsCreateDialogOpen(false);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create overlay');
    }
  };

  // Update overlay
  const handleUpdateOverlay = async () => {
    if (!selectedOverlay) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/screens/${selectedScreen?.id}/overlays/${selectedOverlay.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error('Failed to update overlay');

      if (selectedScreen) {
        await fetchOverlays(selectedScreen.id);
      }
      setIsEditDialogOpen(false);
      setSelectedOverlay(null);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update overlay');
    }
  };

  // Deploy overlay to digital twin
  const handleDeployToDigitalTwin = async (overlayId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/screens/${selectedScreen?.id}/overlays/${overlayId}/deploy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          environment: 'digital_twin'
        }),
      });

      if (!response.ok) throw new Error('Failed to deploy to digital twin');

      // Update overlay status to active
      setOverlays(prev => prev.map(overlay =>
        overlay.id === overlayId
          ? { ...overlay, status: 'active' as const }
          : overlay
      ));

      // Show success message
      console.log('Overlay deployed to digital twin successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deploy to digital twin');
    }
  };

  // Delete overlay
  const handleDeleteOverlay = async (overlayId: string) => {
    if (!confirm('Are you sure you want to delete this overlay?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/screens/${selectedScreen?.id}/overlays/${overlayId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to delete overlay');

      if (selectedScreen) {
        await fetchOverlays(selectedScreen.id);
      }
      setSelectedOverlay(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete overlay');
    }
  };

  const resetForm = () => {
    setFormData({
      content_id: '',
      screen_id: selectedScreen?.id || '',
      company_id: user?.company_id || '',
      name: '',
      position_x: 100,
      position_y: 100,
      width: 300,
      height: 200,
      z_index: 1,
      opacity: 1.0,
      rotation: 0,
      status: 'draft'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'draft':
        return 'text-gray-700 bg-gray-50 border-gray-200';
      case 'scheduled':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      case 'paused':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'expired':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  // Get file icon for content type
  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith('image/')) return <FileImage className="h-4 w-4 text-blue-500" />;
    if (contentType.startsWith('video/')) return <FileVideo className="h-4 w-4 text-purple-500" />;
    if (contentType === 'application/pdf') return <FileText className="h-4 w-4 text-red-500" />;
    return <File className="h-4 w-4 text-gray-500" />;
  };

  const filteredOverlays = overlays.filter(overlay =>
    overlay.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading overlay manager...</span>
      </div>
    );
  }

  if (!canViewOverlays) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          You don't have permission to view overlays. Please contact your administrator.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Layers className="h-8 w-8 text-blue-600" />
            Content Overlay Manager
          </h1>
          <p className="text-gray-600 mt-1">
            Design and manage content overlays on your digital screens
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Label htmlFor="screen-select">Screen:</Label>
            <Select
              value={selectedScreen?.id || ''}
              onValueChange={(value) => {
                const screen = screens.find(s => s.id === value);
                setSelectedScreen(screen || null);
              }}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select screen" />
              </SelectTrigger>
              <SelectContent>
                {screens.map(screen => (
                  <SelectItem key={screen.id} value={screen.id}>
                    {screen.name} ({screen.resolution_width}×{screen.resolution_height})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {canEditOverlays && (
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Overlay
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create Content Overlay</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="overlay-name">Overlay Name *</Label>
                      <Input
                        id="overlay-name"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="Welcome Banner"
                      />
                    </div>
                    <div>
                      <Label htmlFor="content-id">Content *</Label>
                      <Select
                        value={formData.content_id}
                        onValueChange={(value) => setFormData({ ...formData, content_id: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select approved content..." />
                        </SelectTrigger>
                        <SelectContent>
                          {approvedContent.map(content => (
                            <SelectItem key={content.id} value={content.id}>
                              {content.title || content.filename}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <Label htmlFor="pos-x">X Position (px)</Label>
                      <Input
                        id="pos-x"
                        type="number"
                        value={formData.position_x}
                        onChange={(e) => setFormData({ ...formData, position_x: parseInt(e.target.value) || 0 })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="pos-y">Y Position (px)</Label>
                      <Input
                        id="pos-y"
                        type="number"
                        value={formData.position_y}
                        onChange={(e) => setFormData({ ...formData, position_y: parseInt(e.target.value) || 0 })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="width">Width (px)</Label>
                      <Input
                        id="width"
                        type="number"
                        value={formData.width}
                        onChange={(e) => setFormData({ ...formData, width: parseInt(e.target.value) || 0 })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="height">Height (px)</Label>
                      <Input
                        id="height"
                        type="number"
                        value={formData.height}
                        onChange={(e) => setFormData({ ...formData, height: parseInt(e.target.value) || 0 })}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="z-index">Layer Order</Label>
                      <Input
                        id="z-index"
                        type="number"
                        value={formData.z_index}
                        onChange={(e) => setFormData({ ...formData, z_index: parseInt(e.target.value) || 1 })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="opacity">Opacity</Label>
                      <Input
                        id="opacity"
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={formData.opacity}
                        onChange={(e) => setFormData({ ...formData, opacity: parseFloat(e.target.value) || 1 })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="rotation">Rotation (degrees)</Label>
                      <Input
                        id="rotation"
                        type="number"
                        value={formData.rotation}
                        onChange={(e) => setFormData({ ...formData, rotation: parseFloat(e.target.value) || 0 })}
                      />
                    </div>
                  </div>

                  {/* Scheduling */}
                  <div className="space-y-4 border-t pt-4">
                    <h4 className="font-medium text-gray-900 flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      Schedule (Optional)
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="start-time">Start Time</Label>
                        <Input
                          id="start-time"
                          type="datetime-local"
                          value={formData.start_time || ''}
                          onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="end-time">End Time</Label>
                        <Input
                          id="end-time"
                          type="datetime-local"
                          value={formData.end_time || ''}
                          onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end space-x-2 pt-4">
                    <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleCreateOverlay} disabled={!formData.content_id || !formData.name}>
                      Create Overlay
                    </Button>
                    <Button
                      onClick={async () => {
                        await handleCreateOverlay();
                        // Auto-deploy to digital twin for testing
                        const newOverlay = overlays[overlays.length - 1];
                        if (newOverlay) {
                          setTimeout(() => handleDeployToDigitalTwin(newOverlay.id), 500);
                        }
                      }}
                      disabled={!formData.content_id || !formData.name}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Send className="h-4 w-4 mr-2" />
                      Create & Deploy
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="canvas" disabled={!showCanvas}>
            <Grid className="h-4 w-4 mr-2" />
            Canvas Designer
          </TabsTrigger>
          <TabsTrigger value="list">
            <List className="h-4 w-4 mr-2" />
            Overlay List
          </TabsTrigger>
        </TabsList>

        {/* Canvas Tab */}
        {showCanvas && (
          <TabsContent value="canvas" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Canvas Area */}
              <div className="lg:col-span-3 space-y-4">
                {/* Canvas Controls */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setZoomLevel(Math.max(0.1, zoomLevel - 0.1))}
                      >
                        <ZoomOut className="h-4 w-4" />
                      </Button>
                      <span className="text-sm font-medium w-16 text-center">
                        {Math.round(zoomLevel * 100)}%
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setZoomLevel(Math.min(2, zoomLevel + 0.1))}
                      >
                        <ZoomIn className="h-4 w-4" />
                      </Button>
                    </div>
                    {selectedScreen && (
                      <div className="text-sm text-gray-600">
                        Screen: {selectedScreen.resolution_width} × {selectedScreen.resolution_height}px
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm">
                      <Save className="h-4 w-4 mr-2" />
                      Save Layout
                    </Button>
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4 mr-2" />
                      Preview
                    </Button>
                  </div>
                </div>

                {/* Canvas */}
                <div className="border border-gray-200 rounded-lg bg-white p-4 overflow-auto max-h-[600px]">
                  {selectedScreen ? (
                    <canvas
                      ref={canvasRef}
                      onMouseDown={handleCanvasMouseDown}
                      onMouseMove={handleCanvasMouseMove}
                      onMouseUp={handleCanvasMouseUp}
                      onMouseLeave={handleCanvasMouseUp}
                      className="border border-gray-300 cursor-crosshair"
                      style={{ maxWidth: '100%', height: 'auto' }}
                    />
                  ) : (
                    <div className="text-center py-12">
                      <Monitor className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Select a screen to start designing overlays</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Overlay List Sidebar */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Overlays</h3>
                  <span className="text-sm text-gray-500">{filteredOverlays.length} items</span>
                </div>

                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search overlays..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>

                {/* Overlay Items */}
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {filteredOverlays
                    .sort((a, b) => b.z_index - a.z_index)
                    .map((overlay) => (
                      <div
                        key={overlay.id}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          selectedOverlay?.id === overlay.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedOverlay(overlay)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{overlay.name}</h4>
                          <div className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(overlay.status)}`}>
                            {overlay.status}
                          </div>
                        </div>

                        <div className="space-y-1 text-xs text-gray-600">
                          <div className="flex justify-between">
                            <span>Position:</span>
                            <span>{overlay.position_x}, {overlay.position_y}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Size:</span>
                            <span>{overlay.width} × {overlay.height}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Layer:</span>
                            <span>Z-{overlay.z_index}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Opacity:</span>
                            <span>{Math.round(overlay.opacity * 100)}%</span>
                          </div>
                        </div>

                        {canEditOverlays && (
                          <div className="flex space-x-1 mt-2 pt-2 border-t border-gray-100">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedOverlay(overlay);
                                setFormData({
                                  content_id: overlay.content_id,
                                  screen_id: overlay.screen_id,
                                  company_id: overlay.company_id,
                                  name: overlay.name,
                                  position_x: overlay.position_x,
                                  position_y: overlay.position_y,
                                  width: overlay.width,
                                  height: overlay.height,
                                  z_index: overlay.z_index,
                                  opacity: overlay.opacity,
                                  rotation: overlay.rotation,
                                  start_time: overlay.start_time,
                                  end_time: overlay.end_time,
                                  status: overlay.status
                                });
                                setIsEditDialogOpen(true);
                              }}
                              className="flex-1 text-xs"
                            >
                              <Edit2 className="h-3 w-3 mr-1" />
                              Edit
                            </Button>
                            {overlay.status === 'draft' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeployToDigitalTwin(overlay.id);
                                }}
                                className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 text-xs"
                              >
                                <Play className="h-3 w-3 mr-1" />
                                Deploy
                              </Button>
                            )}
                            {overlay.status === 'active' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  // Pause overlay
                                }}
                                className="text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50 text-xs"
                              >
                                <Pause className="h-3 w-3 mr-1" />
                                Pause
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteOverlay(overlay.id);
                              }}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50 text-xs"
                            >
                              <Trash2 className="h-3 w-3 mr-1" />
                              Delete
                            </Button>
                          </div>
                        )}
                      </div>
                    ))}
                </div>

                {filteredOverlays.length === 0 && (
                  <div className="text-center py-8">
                    <Layers className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500 mb-4">No overlays yet</p>
                    {canEditOverlays && (
                      <Button size="sm" onClick={() => setIsCreateDialogOpen(true)}>
                        <Plus className="h-4 w-4 mr-2" />
                        Add First Overlay
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
        )}

        {/* List Tab */}
        <TabsContent value="list" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="h-5 w-5" />
                  Overlay Management
                </div>
                <Badge variant="outline">
                  {filteredOverlays.length} overlays
                </Badge>
              </CardTitle>
              <CardDescription>
                Manage overlay configurations and settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-6">
                <div className="flex-1">
                  <Input
                    placeholder="Search overlays..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="scheduled">Scheduled</SelectItem>
                    <SelectItem value="paused">Paused</SelectItem>
                    <SelectItem value="expired">Expired</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {filteredOverlays.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Grid className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No overlays found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredOverlays.map((overlay) => (
                    <div key={overlay.id} className="border rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Monitor className="h-4 w-4" />
                            <h3 className="font-semibold">{overlay.name}</h3>
                            <Badge variant={overlay.status === 'active' ? "default" : "secondary"}>
                              {overlay.status}
                            </Badge>
                          </div>

                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                            <div>
                              <p><strong>Content:</strong> {overlay.content?.title || 'Unknown'}</p>
                            </div>
                            <div>
                              <p><strong>Position:</strong> {overlay.position_x}, {overlay.position_y}</p>
                            </div>
                            <div>
                              <p><strong>Size:</strong> {overlay.width}×{overlay.height}</p>
                            </div>
                            <div>
                              <p><strong>Opacity:</strong> {Math.round(overlay.opacity * 100)}%</p>
                            </div>
                          </div>

                          {(overlay.start_time || overlay.end_time) && (
                            <div className="mt-2 text-xs text-gray-500">
                              {overlay.start_time && (
                                <span>Start: {new Date(overlay.start_time).toLocaleString()}</span>
                              )}
                              {overlay.start_time && overlay.end_time && <span> • </span>}
                              {overlay.end_time && (
                                <span>End: {new Date(overlay.end_time).toLocaleString()}</span>
                              )}
                            </div>
                          )}
                        </div>

                        <div className="flex gap-2 ml-4">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setSelectedOverlay(overlay)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {canEditOverlays && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setSelectedOverlay(overlay);
                                  setFormData({
                                    content_id: overlay.content_id,
                                    screen_id: overlay.screen_id,
                                    company_id: overlay.company_id,
                                    name: overlay.name,
                                    position_x: overlay.position_x,
                                    position_y: overlay.position_y,
                                    width: overlay.width,
                                    height: overlay.height,
                                    z_index: overlay.z_index,
                                    opacity: overlay.opacity,
                                    rotation: overlay.rotation,
                                    start_time: overlay.start_time,
                                    end_time: overlay.end_time,
                                    status: overlay.status
                                  });
                                  setIsEditDialogOpen(true);
                                }}
                              >
                                <Edit2 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDeleteOverlay(overlay.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Overlay Dialog */}
      <AlertDialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Edit Overlay: {selectedOverlay?.name}</AlertDialogTitle>
          </AlertDialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Overlay Name *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div>
                <Label>Content</Label>
                <Select
                  value={formData.content_id}
                  onValueChange={(value) => setFormData({ ...formData, content_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {approvedContent.map(content => (
                      <SelectItem key={content.id} value={content.id}>
                        {content.title || content.filename}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4">
              <div>
                <Label>X Position</Label>
                <Input
                  type="number"
                  value={formData.position_x}
                  onChange={(e) => setFormData({ ...formData, position_x: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <Label>Y Position</Label>
                <Input
                  type="number"
                  value={formData.position_y}
                  onChange={(e) => setFormData({ ...formData, position_y: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <Label>Width</Label>
                <Input
                  type="number"
                  value={formData.width}
                  onChange={(e) => setFormData({ ...formData, width: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <Label>Height</Label>
                <Input
                  type="number"
                  value={formData.height}
                  onChange={(e) => setFormData({ ...formData, height: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Z-Index</Label>
                <Input
                  type="number"
                  value={formData.z_index}
                  onChange={(e) => setFormData({ ...formData, z_index: parseInt(e.target.value) || 1 })}
                />
              </div>
              <div>
                <Label>Opacity</Label>
                <Input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.opacity}
                  onChange={(e) => setFormData({ ...formData, opacity: parseFloat(e.target.value) || 1 })}
                />
              </div>
              <div>
                <Label>Rotation</Label>
                <Input
                  type="number"
                  value={formData.rotation}
                  onChange={(e) => setFormData({ ...formData, rotation: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Start Time</Label>
                <Input
                  type="datetime-local"
                  value={formData.start_time || ''}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                />
              </div>
              <div>
                <Label>End Time</Label>
                <Input
                  type="datetime-local"
                  value={formData.end_time || ''}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                />
              </div>
            </div>
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleUpdateOverlay}>
              Update Overlay
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export default UnifiedOverlayManager;
