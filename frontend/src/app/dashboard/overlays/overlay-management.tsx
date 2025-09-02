'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Monitor, Plus, Edit, Trash2, Eye, Grid, Layers } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

interface ContentOverlay {
  id: string;
  content_id: string;
  screen_id: string;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  z_index: number;
  opacity: number;
  is_active: boolean;
  start_time?: string;
  end_time?: string;
  created_at: string;
  created_by: string;
}

interface OverlayFormData {
  content_id: string;
  screen_id: string;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  z_index: number;
  opacity: number;
  is_active: boolean;
  start_time?: string;
  end_time?: string;
}

interface Screen {
  id: string;
  name: string;
  resolution: { width: number; height: number };
  location: string;
}

interface ContentItem {
  id: string;
  title: string;
  status: string;
  categories: string[];
}

export default function OverlayManagement() {
  const [overlays, setOverlays] = useState<ContentOverlay[]>([]);
  const [screens, setScreens] = useState<Screen[]>([]);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingOverlay, setEditingOverlay] = useState<ContentOverlay | null>(null);
  const [selectedScreen, setSelectedScreen] = useState<string>('');
  const [formData, setFormData] = useState<OverlayFormData>({
    content_id: '',
    screen_id: '',
    position: { x: 10, y: 10, width: 200, height: 150 },
    z_index: 1,
    opacity: 100,
    is_active: true
  });

  const { user } = useAuth();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadOverlays(),
        loadScreens(),
        loadContent()
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadOverlays = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/overlays/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setOverlays(data);
      }
    } catch (error) {
      console.error('Failed to load overlays:', error);
    }
  };

  const loadScreens = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/screens/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setScreens(data);
      } else {
        // Fallback to mock data if API not available
        setScreens([
          { 
            id: 'screen-1', 
            name: 'Main Lobby Display', 
            resolution: { width: 1920, height: 1080 },
            location: 'Lobby'
          },
          { 
            id: 'screen-2', 
            name: 'Reception Display', 
            resolution: { width: 1366, height: 768 },
            location: 'Reception'
          },
          { 
            id: 'screen-3', 
            name: 'Cafeteria Display', 
            resolution: { width: 1920, height: 1080 },
            location: 'Cafeteria'
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to load screens:', error);
      // Fallback to mock data
      setScreens([
        { 
          id: 'screen-1', 
          name: 'Main Lobby Display', 
          resolution: { width: 1920, height: 1080 },
          location: 'Lobby'
        }
      ]);
    }
  };

  const loadContent = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/content/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        // Only show approved content
        setContent(data.filter((item: ContentItem) => item.status === 'approved'));
      }
    } catch (error) {
      console.error('Failed to load content:', error);
    }
  };

  const createOverlay = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/overlays/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...formData,
          created_by: user?.id
        })
      });

      if (response.ok) {
        await loadOverlays();
        setShowCreateDialog(false);
        resetForm();
      }
    } catch (error) {
      console.error('Failed to create overlay:', error);
    }
  };

  const updateOverlay = async () => {
    if (!editingOverlay) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/overlays/${editingOverlay.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        await loadOverlays();
        setEditingOverlay(null);
        resetForm();
      }
    } catch (error) {
      console.error('Failed to update overlay:', error);
    }
  };

  const deleteOverlay = async (overlayId: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/overlays/${overlayId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await loadOverlays();
      }
    } catch (error) {
      console.error('Failed to delete overlay:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      content_id: '',
      screen_id: '',
      position: { x: 10, y: 10, width: 200, height: 150 },
      z_index: 1,
      opacity: 100,
      is_active: true
    });
  };

  const openEditDialog = (overlay: ContentOverlay) => {
    setEditingOverlay(overlay);
    setFormData({
      content_id: overlay.content_id,
      screen_id: overlay.screen_id,
      position: overlay.position,
      z_index: overlay.z_index,
      opacity: overlay.opacity * 100, // Convert to percentage
      is_active: overlay.is_active,
      start_time: overlay.start_time,
      end_time: overlay.end_time
    });
  };

  const getContentTitle = (contentId: string) => {
    const contentItem = content.find(c => c.id === contentId);
    return contentItem?.title || 'Unknown Content';
  };

  const getScreenName = (screenId: string) => {
    const screen = screens.find(s => s.id === screenId);
    return screen?.name || 'Unknown Screen';
  };

  const filteredOverlays = selectedScreen 
    ? overlays.filter(overlay => overlay.screen_id === selectedScreen)
    : overlays;

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Overlay Management</CardTitle>
          <CardDescription>Loading overlay data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="h-5 w-5" />
              Overlay Management
            </div>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Overlay
            </Button>
          </CardTitle>
          <CardDescription>
            Define where advertisements appear on digital displays
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-6">
            <div className="flex-1">
              <Label>Filter by Screen</Label>
              <Select value={selectedScreen} onValueChange={setSelectedScreen}>
                <SelectTrigger>
                  <SelectValue placeholder="All screens" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All screens</SelectItem>
                  {screens.map((screen) => (
                    <SelectItem key={screen.id} value={screen.id}>
                      {screen.name} ({screen.resolution.width}×{screen.resolution.height})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {filteredOverlays.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Grid className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No overlays configured {selectedScreen ? 'for this screen' : ''}</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredOverlays.map((overlay) => (
                <div key={overlay.id} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Monitor className="h-4 w-4" />
                        <h3 className="font-semibold">{getContentTitle(overlay.content_id)}</h3>
                        <Badge variant={overlay.is_active ? "default" : "secondary"}>
                          {overlay.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                        <div>
                          <p><strong>Screen:</strong> {getScreenName(overlay.screen_id)}</p>
                        </div>
                        <div>
                          <p><strong>Position:</strong> {overlay.position.x}, {overlay.position.y}</p>
                        </div>
                        <div>
                          <p><strong>Size:</strong> {overlay.position.width}×{overlay.position.height}</p>
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
                        onClick={() => openEditDialog(overlay)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => deleteOverlay(overlay.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Overlay Dialog */}
      <AlertDialog open={showCreateDialog || !!editingOverlay} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false);
          setEditingOverlay(null);
          resetForm();
        }
      }}>
        <AlertDialogContent className="max-w-3xl">
          <AlertDialogHeader>
            <AlertDialogTitle>
              {editingOverlay ? 'Edit Overlay' : 'Create New Overlay'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              Configure how and where content appears on the digital display
            </AlertDialogDescription>
          </AlertDialogHeader>
          
          <div className="space-y-6 py-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="content_id">Content *</Label>
                <Select 
                  value={formData.content_id} 
                  onValueChange={(value) => setFormData({ ...formData, content_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select content" />
                  </SelectTrigger>
                  <SelectContent>
                    {content.map((item) => (
                      <SelectItem key={item.id} value={item.id}>
                        {item.title} ({item.categories.join(', ')})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="screen_id">Screen *</Label>
                <Select 
                  value={formData.screen_id} 
                  onValueChange={(value) => setFormData({ ...formData, screen_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select screen" />
                  </SelectTrigger>
                  <SelectContent>
                    {screens.map((screen) => (
                      <SelectItem key={screen.id} value={screen.id}>
                        {screen.name} ({screen.resolution.width}×{screen.resolution.height})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-4">
              <Label>Position & Size</Label>
              <div className="grid gap-4 md:grid-cols-4">
                <div>
                  <Label htmlFor="x">X Position</Label>
                  <Input
                    id="x"
                    type="number"
                    value={formData.position.x}
                    onChange={(e) => setFormData({
                      ...formData,
                      position: { ...formData.position, x: parseInt(e.target.value) || 0 }
                    })}
                  />
                </div>
                <div>
                  <Label htmlFor="y">Y Position</Label>
                  <Input
                    id="y"
                    type="number"
                    value={formData.position.y}
                    onChange={(e) => setFormData({
                      ...formData,
                      position: { ...formData.position, y: parseInt(e.target.value) || 0 }
                    })}
                  />
                </div>
                <div>
                  <Label htmlFor="width">Width</Label>
                  <Input
                    id="width"
                    type="number"
                    value={formData.position.width}
                    onChange={(e) => setFormData({
                      ...formData,
                      position: { ...formData.position, width: parseInt(e.target.value) || 0 }
                    })}
                  />
                </div>
                <div>
                  <Label htmlFor="height">Height</Label>
                  <Input
                    id="height"
                    type="number"
                    value={formData.position.height}
                    onChange={(e) => setFormData({
                      ...formData,
                      position: { ...formData.position, height: parseInt(e.target.value) || 0 }
                    })}
                  />
                </div>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <Label htmlFor="z_index">Z-Index (Layer)</Label>
                <Input
                  id="z_index"
                  type="number"
                  min="1"
                  max="100"
                  value={formData.z_index}
                  onChange={(e) => setFormData({ ...formData, z_index: parseInt(e.target.value) || 1 })}
                />
              </div>
              <div>
                <Label>Opacity: {formData.opacity}%</Label>
                <Slider
                  value={[formData.opacity]}
                  onValueChange={(value: number[]) => setFormData({ ...formData, opacity: value[0] })}
                  min={0}
                  max={100}
                  step={5}
                  className="mt-2"
                />
              </div>
              <div className="flex items-center space-x-2 pt-6">
                <Switch
                  id="is_active"
                  checked={formData.is_active}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                />
                <Label htmlFor="is_active">Active</Label>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="start_time">Start Time (optional)</Label>
                <Input
                  id="start_time"
                  type="datetime-local"
                  value={formData.start_time || ''}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="end_time">End Time (optional)</Label>
                <Input
                  id="end_time"
                  type="datetime-local"
                  value={formData.end_time || ''}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                />
              </div>
            </div>
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={editingOverlay ? updateOverlay : createOverlay}
              disabled={!formData.content_id || !formData.screen_id}
            >
              {editingOverlay ? 'Update Overlay' : 'Create Overlay'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
