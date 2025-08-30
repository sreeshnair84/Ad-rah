'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import {
  Layers,
  Plus,
  Edit2,
  Trash2,
  Move,
  RotateCw,
  Eye,
  EyeOff,
  Settings,
  Monitor,
  Smartphone,
  AlertCircle,
  Save,
  Play,
  Pause,
  Square,
  Search,
  Filter,
  ZoomIn,
  ZoomOut,
  RotateCcw
} from 'lucide-react';

interface DigitalScreen {
  id: string;
  name: string;
  resolution_width: number;
  resolution_height: number;
  orientation: 'landscape' | 'portrait';
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

export default function ContentOverlayPage() {
  const { user } = useAuth();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [screens, setScreens] = useState<DigitalScreen[]>([]);
  const [overlays, setOverlays] = useState<ContentOverlay[]>([]);
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

  const [formData, setFormData] = useState<OverlayFormData>({
    content_id: 'content_001', // Mock content ID
    screen_id: '',
    company_id: user?.companies?.[0]?.id || '',
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

  // Fetch screens
  const fetchScreens = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/screens', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch screens');
      const data = await response.json();
      setScreens(data);
      if (data.length > 0 && !selectedScreen) {
        setSelectedScreen(data[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch screens');
    }
  };

  // Fetch overlays for selected screen
  const fetchOverlays = async (screenId: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/screens/${screenId}/overlays`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch overlays');
      const data = await response.json();
      setOverlays(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch overlays');
    }
  };

  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      await fetchScreens();
      setLoading(false);
    };
    initializeData();
  }, []);

  useEffect(() => {
    if (selectedScreen) {
      fetchOverlays(selectedScreen.id);
      setFormData(prev => ({ ...prev, screen_id: selectedScreen.id }));
    }
  }, [selectedScreen]);

  // Canvas drawing
  useEffect(() => {
    if (selectedScreen && canvasRef.current) {
      drawCanvas();
    }
  }, [selectedScreen, overlays, zoomLevel]);

  const drawCanvas = () => {
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
  };

  // Handle canvas mouse events for drag and drop
  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
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
        const token = localStorage.getItem('token');
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
      const token = localStorage.getItem('token');
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

  // Delete overlay
  const handleDeleteOverlay = async (overlayId: string) => {
    if (!confirm('Are you sure you want to delete this overlay?')) return;

    try {
      const token = localStorage.getItem('token');
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
      content_id: 'content_001',
      screen_id: selectedScreen?.id || '',
      company_id: user?.companies?.[0]?.id || '',
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

  // Check if user can edit overlays
  const canEditOverlays = user?.roles?.some(role => 
    ['ADMIN', 'HOST'].includes(role.role)
  ) || false;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading content overlay...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Layers className="h-8 w-8 text-blue-600" />
            Content Layout Designer
          </h1>
          <p className="text-gray-600 mt-1">
            Design and position content overlays on your digital screens
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Label htmlFor="screen-select">Screen:</Label>
            <select
              id="screen-select"
              className="p-2 border border-gray-300 rounded-md bg-white min-w-[200px]"
              value={selectedScreen?.id || ''}
              onChange={(e) => {
                const screen = screens.find(s => s.id === e.target.value);
                setSelectedScreen(screen || null);
              }}
            >
              {screens.map(screen => (
                <option key={screen.id} value={screen.id}>
                  {screen.name} ({screen.resolution_width}×{screen.resolution_height})
                </option>
              ))}
            </select>
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
                      <select
                        id="content-id"
                        className="w-full p-2 border border-gray-300 rounded-md"
                        value={formData.content_id}
                        onChange={(e) => setFormData({ ...formData, content_id: e.target.value })}
                      >
                        <option value="content_001">Welcome Image</option>
                        <option value="content_002">Event Announcement</option>
                        <option value="content_003">Company Logo</option>
                      </select>
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

                  <div className="flex justify-end space-x-2 pt-4">
                    <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleCreateOverlay}>
                      Create Overlay
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

        {/* Overlay List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Overlays</h3>
            <span className="text-sm text-gray-500">{overlays.length} items</span>
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
            {overlays
              .filter(overlay => 
                overlay.name.toLowerCase().includes(searchTerm.toLowerCase())
              )
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
                          // Open edit dialog
                        }}
                        className="flex-1 text-xs"
                      >
                        <Edit2 className="h-3 w-3 mr-1" />
                        Edit
                      </Button>
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

          {overlays.length === 0 && (
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

      {/* Properties Panel for Selected Overlay */}
      {selectedOverlay && canEditOverlays && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Properties: {selectedOverlay.name}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label>X Position</Label>
              <Input
                type="number"
                value={selectedOverlay.position_x}
                onChange={(e) => {
                  const newValue = parseInt(e.target.value) || 0;
                  setOverlays(prev => prev.map(overlay => 
                    overlay.id === selectedOverlay.id 
                      ? { ...overlay, position_x: newValue }
                      : overlay
                  ));
                }}
              />
            </div>
            <div>
              <Label>Y Position</Label>
              <Input
                type="number"
                value={selectedOverlay.position_y}
                onChange={(e) => {
                  const newValue = parseInt(e.target.value) || 0;
                  setOverlays(prev => prev.map(overlay => 
                    overlay.id === selectedOverlay.id 
                      ? { ...overlay, position_y: newValue }
                      : overlay
                  ));
                }}
              />
            </div>
            <div>
              <Label>Width</Label>
              <Input
                type="number"
                value={selectedOverlay.width}
                onChange={(e) => {
                  const newValue = parseInt(e.target.value) || 0;
                  setOverlays(prev => prev.map(overlay => 
                    overlay.id === selectedOverlay.id 
                      ? { ...overlay, width: newValue }
                      : overlay
                  ));
                }}
              />
            </div>
            <div>
              <Label>Height</Label>
              <Input
                type="number"
                value={selectedOverlay.height}
                onChange={(e) => {
                  const newValue = parseInt(e.target.value) || 0;
                  setOverlays(prev => prev.map(overlay => 
                    overlay.id === selectedOverlay.id 
                      ? { ...overlay, height: newValue }
                      : overlay
                  ));
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}