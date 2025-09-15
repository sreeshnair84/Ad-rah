'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/components/ui/use-toast';
import {
  Monitor,
  Plus,
  Move,
  RotateCw,
  Eye,
  EyeOff,
  Trash2,
  Save,
  Play,
  Layers,
  Image,
  Video,
  Type,
  MousePointer,
  Grid,
  Maximize,
  Copy,
  Download,
  Upload
} from 'lucide-react';

interface ContentItem {
  id: string;
  title: string;
  content_type: string;
  file_url?: string;
  thumbnail_url?: string;
  categories: string[];
  tags: string[];
  status: string;
}

interface OverlayElement {
  id: string;
  content_id: string;
  name: string;
  type: 'host_content' | 'ad_content' | 'text' | 'image' | 'video';
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  style: {
    opacity: number;
    rotation: number;
    z_index: number;
  };
  content_data?: {
    text?: string;
    font_size?: number;
    color?: string;
    background_color?: string;
  };
  visibility_schedule?: {
    start_time?: string;
    end_time?: string;
    repeat_pattern?: string;
  };
  targeting?: {
    categories?: string[];
    tags?: string[];
    age_range?: { min: number; max: number };
  };
}

interface OverlayTemplate {
  id: string;
  name: string;
  description: string;
  template_data: {
    elements: OverlayElement[];
    canvas_size: { width: number; height: number };
  };
  thumbnail?: string;
}

interface OverlayDesignerProps {
  screenId?: string;
  templateId?: string;
  onSave?: (overlayData: any) => void;
  onPreview?: (overlayData: any) => void;
}

export function OverlayDesigner({
  screenId,
  templateId,
  onSave,
  onPreview
}: OverlayDesignerProps) {
  // Canvas and design state
  const canvasRef = useRef<HTMLDivElement>(null);
  const [canvasSize, setCanvasSize] = useState({ width: 1920, height: 1080 });
  const [scale, setScale] = useState(0.5);
  const [gridVisible, setGridVisible] = useState(true);

  // Overlay elements state
  const [elements, setElements] = useState<OverlayElement[]>([]);
  const [selectedElement, setSelectedElement] = useState<string | null>(null);
  const [draggedElement, setDraggedElement] = useState<string | null>(null);

  // Content and templates
  const [availableContent, setAvailableContent] = useState<ContentItem[]>([]);
  const [hostContent, setHostContent] = useState<ContentItem[]>([]);
  const [adContent, setAdContent] = useState<ContentItem[]>([]);
  const [templates, setTemplates] = useState<OverlayTemplate[]>([]);

  // UI state
  const [showContentLibrary, setShowContentLibrary] = useState(false);
  const [activeTab, setActiveTab] = useState('design');
  const [previewMode, setPreviewMode] = useState(false);

  // Load data on component mount
  useEffect(() => {
    loadAvailableContent();
    loadTemplates();
    if (templateId) {
      loadTemplate(templateId);
    }
  }, [templateId]);

  const loadAvailableContent = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/content/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        const content = data.content || data || [];

        // Separate host content and ad content
        const host = content.filter((item: ContentItem) =>
          item.categories.includes('host_content') || item.categories.includes('informational')
        );
        const ads = content.filter((item: ContentItem) =>
          item.categories.includes('advertising') || item.categories.includes('promotional')
        );

        setAvailableContent(content);
        setHostContent(host);
        setAdContent(ads);
      }
    } catch (error) {
      console.error('Failed to load content:', error);
      toast({
        title: "Error",
        description: "Failed to load available content",
        variant: "destructive"
      });
    }
  };

  const loadTemplates = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/overlays/templates/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const loadTemplate = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/overlays/templates/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const template = await response.json();
        setElements(template.template_data.elements || []);
        setCanvasSize(template.template_data.canvas_size || { width: 1920, height: 1080 });
      }
    } catch (error) {
      console.error('Failed to load template:', error);
    }
  };

  const addElement = (type: OverlayElement['type'], content?: ContentItem) => {
    const newElement: OverlayElement = {
      id: `element_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      content_id: content?.id || '',
      name: content?.title || `New ${type}`,
      type,
      position: {
        x: 100,
        y: 100,
        width: type === 'text' ? 300 : 400,
        height: type === 'text' ? 60 : 225
      },
      style: {
        opacity: 1,
        rotation: 0,
        z_index: elements.length + 1
      },
      content_data: type === 'text' ? {
        text: 'Sample Text',
        font_size: 24,
        color: '#ffffff',
        background_color: 'rgba(0,0,0,0.5)'
      } : undefined
    };

    setElements([...elements, newElement]);
    setSelectedElement(newElement.id);
  };

  const updateElement = (id: string, updates: Partial<OverlayElement>) => {
    setElements(elements.map(el =>
      el.id === id ? { ...el, ...updates } : el
    ));
  };

  const deleteElement = (id: string) => {
    setElements(elements.filter(el => el.id !== id));
    if (selectedElement === id) {
      setSelectedElement(null);
    }
  };

  const duplicateElement = (id: string) => {
    const element = elements.find(el => el.id === id);
    if (element) {
      const newElement = {
        ...element,
        id: `element_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: `${element.name} (Copy)`,
        position: {
          ...element.position,
          x: element.position.x + 20,
          y: element.position.y + 20
        },
        style: {
          ...element.style,
          z_index: elements.length + 1
        }
      };
      setElements([...elements, newElement]);
    }
  };

  const handleElementMouseDown = (e: React.MouseEvent, elementId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setSelectedElement(elementId);
    setDraggedElement(elementId);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!draggedElement || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / scale;
    const y = (e.clientY - rect.top) / scale;

    updateElement(draggedElement, {
      position: {
        ...elements.find(el => el.id === draggedElement)?.position!,
        x: Math.max(0, Math.min(canvasSize.width - 100, x)),
        y: Math.max(0, Math.min(canvasSize.height - 100, y))
      }
    });
  };

  const handleMouseUp = () => {
    setDraggedElement(null);
  };

  const saveOverlay = async () => {
    try {
      const overlayData = {
        name: `Overlay_${new Date().toISOString().split('T')[0]}`,
        screen_id: screenId,
        elements,
        canvas_size: canvasSize,
        created_at: new Date().toISOString()
      };

      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/overlays/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(overlayData)
      });

      if (response.ok) {
        toast({
          title: "Success",
          description: "Overlay saved successfully"
        });
        if (onSave) onSave(overlayData);
      } else {
        throw new Error('Failed to save overlay');
      }
    } catch (error) {
      console.error('Failed to save overlay:', error);
      toast({
        title: "Error",
        description: "Failed to save overlay",
        variant: "destructive"
      });
    }
  };

  const previewOverlay = () => {
    setPreviewMode(!previewMode);
    if (onPreview) {
      onPreview({ elements, canvas_size: canvasSize });
    }
  };

  const renderElement = (element: OverlayElement) => {
    const isSelected = selectedElement === element.id;
    const content = availableContent.find(c => c.id === element.content_id);

    const elementStyle = {
      position: 'absolute' as const,
      left: element.position.x * scale,
      top: element.position.y * scale,
      width: element.position.width * scale,
      height: element.position.height * scale,
      opacity: element.style.opacity,
      transform: `rotate(${element.style.rotation}deg)`,
      zIndex: element.style.z_index,
      border: isSelected ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.3)',
      cursor: 'move',
      overflow: 'hidden'
    };

    return (
      <div
        key={element.id}
        style={elementStyle}
        onMouseDown={(e) => handleElementMouseDown(e, element.id)}
        className="bg-black/20 rounded"
      >
        {/* Element content rendering */}
        {element.type === 'text' && element.content_data && (
          <div
            style={{
              color: element.content_data.color,
              fontSize: (element.content_data.font_size || 24) * scale,
              backgroundColor: element.content_data.background_color,
              padding: '8px',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            {element.content_data.text}
          </div>
        )}

        {(element.type === 'image' || element.type === 'ad_content') && content && (
          <div className="w-full h-full bg-gray-800 flex items-center justify-center">
            {content.thumbnail_url ? (
              <img
                src={content.thumbnail_url}
                alt={element.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <Image className="w-8 h-8 text-white/50" />
            )}
          </div>
        )}

        {element.type === 'video' && content && (
          <div className="w-full h-full bg-gray-900 flex items-center justify-center">
            <Video className="w-8 h-8 text-white/50" />
            <span className="ml-2 text-white/70 text-xs">{content.title}</span>
          </div>
        )}

        {element.type === 'host_content' && content && (
          <div className="w-full h-full bg-blue-900/50 flex items-center justify-center border-2 border-blue-400">
            <Monitor className="w-8 h-8 text-blue-300" />
            <span className="ml-2 text-blue-200 text-xs">{content.title}</span>
          </div>
        )}

        {/* Selection handles */}
        {isSelected && !previewMode && (
          <>
            <div className="absolute -top-1 -left-1 w-3 h-3 bg-blue-500 rounded-full cursor-nw-resize"></div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full cursor-ne-resize"></div>
            <div className="absolute -bottom-1 -left-1 w-3 h-3 bg-blue-500 rounded-full cursor-sw-resize"></div>
            <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-blue-500 rounded-full cursor-se-resize"></div>
          </>
        )}

        {/* Element info */}
        {isSelected && !previewMode && (
          <div className="absolute -top-8 left-0 bg-blue-600 text-white text-xs px-2 py-1 rounded">
            {element.name}
          </div>
        )}
      </div>
    );
  };

  const selectedElementData = elements.find(el => el.id === selectedElement);

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Sidebar - Tools */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Overlay Designer</h2>
          <p className="text-sm text-gray-600">Create multi-layer content overlays</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="design">Design</TabsTrigger>
            <TabsTrigger value="content">Content</TabsTrigger>
            <TabsTrigger value="properties">Props</TabsTrigger>
          </TabsList>

          <TabsContent value="design" className="p-4 space-y-4">
            <div>
              <Label className="text-sm font-medium">Add Elements</Label>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => addElement('text')}
                >
                  <Type className="w-4 h-4 mr-1" />
                  Text
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowContentLibrary(true)}
                >
                  <Image className="w-4 h-4 mr-1" />
                  Content
                </Button>
              </div>
            </div>

            <div>
              <Label className="text-sm font-medium">Templates</Label>
              <div className="mt-2 space-y-2">
                {templates.slice(0, 3).map(template => (
                  <Button
                    key={template.id}
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={() => loadTemplate(template.id)}
                  >
                    {template.name}
                  </Button>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-sm font-medium">Canvas</Label>
              <div className="mt-2 space-y-2">
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setGridVisible(!gridVisible)}
                  >
                    <Grid className="w-4 h-4" />
                  </Button>
                  <span className="text-xs text-gray-600">Grid</span>
                </div>
                <div>
                  <Label className="text-xs">Scale: {Math.round(scale * 100)}%</Label>
                  <Slider
                    value={[scale]}
                    onValueChange={([value]) => setScale(value)}
                    min={0.1}
                    max={1}
                    step={0.1}
                    className="mt-1"
                  />
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="content" className="p-4 space-y-4">
            <div>
              <Label className="text-sm font-medium">Host Content</Label>
              <div className="mt-2 space-y-1 max-h-40 overflow-y-auto">
                {hostContent.map(content => (
                  <div
                    key={content.id}
                    className="p-2 border rounded cursor-pointer hover:bg-gray-50"
                    onClick={() => addElement('host_content', content)}
                  >
                    <div className="text-sm font-medium">{content.title}</div>
                    <div className="text-xs text-gray-500">{content.content_type}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-sm font-medium">Ad Content</Label>
              <div className="mt-2 space-y-1 max-h-40 overflow-y-auto">
                {adContent.map(content => (
                  <div
                    key={content.id}
                    className="p-2 border rounded cursor-pointer hover:bg-gray-50"
                    onClick={() => addElement('ad_content', content)}
                  >
                    <div className="text-sm font-medium">{content.title}</div>
                    <div className="text-xs text-gray-500">
                      {content.categories.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="properties" className="p-4 space-y-4">
            {selectedElementData ? (
              <>
                <div>
                  <Label className="text-sm font-medium">Element: {selectedElementData.name}</Label>
                  <Input
                    value={selectedElementData.name}
                    onChange={(e) => updateElement(selectedElementData.id, { name: e.target.value })}
                    className="mt-1"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs">X Position</Label>
                    <Input
                      type="number"
                      value={selectedElementData.position.x}
                      onChange={(e) => updateElement(selectedElementData.id, {
                        position: { ...selectedElementData.position, x: parseInt(e.target.value) || 0 }
                      })}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Y Position</Label>
                    <Input
                      type="number"
                      value={selectedElementData.position.y}
                      onChange={(e) => updateElement(selectedElementData.id, {
                        position: { ...selectedElementData.position, y: parseInt(e.target.value) || 0 }
                      })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs">Width</Label>
                    <Input
                      type="number"
                      value={selectedElementData.position.width}
                      onChange={(e) => updateElement(selectedElementData.id, {
                        position: { ...selectedElementData.position, width: parseInt(e.target.value) || 100 }
                      })}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Height</Label>
                    <Input
                      type="number"
                      value={selectedElementData.position.height}
                      onChange={(e) => updateElement(selectedElementData.id, {
                        position: { ...selectedElementData.position, height: parseInt(e.target.value) || 100 }
                      })}
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-xs">Opacity: {Math.round(selectedElementData.style.opacity * 100)}%</Label>
                  <Slider
                    value={[selectedElementData.style.opacity]}
                    onValueChange={([value]) => updateElement(selectedElementData.id, {
                      style: { ...selectedElementData.style, opacity: value }
                    })}
                    min={0}
                    max={1}
                    step={0.1}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label className="text-xs">Z-Index</Label>
                  <Input
                    type="number"
                    value={selectedElementData.style.z_index}
                    onChange={(e) => updateElement(selectedElementData.id, {
                      style: { ...selectedElementData.style, z_index: parseInt(e.target.value) || 1 }
                    })}
                  />
                </div>

                {selectedElementData.type === 'text' && selectedElementData.content_data && (
                  <>
                    <div>
                      <Label className="text-xs">Text</Label>
                      <Input
                        value={selectedElementData.content_data.text || ''}
                        onChange={(e) => updateElement(selectedElementData.id, {
                          content_data: {
                            ...selectedElementData.content_data,
                            text: e.target.value
                          }
                        })}
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Font Size</Label>
                      <Input
                        type="number"
                        value={selectedElementData.content_data.font_size || 24}
                        onChange={(e) => updateElement(selectedElementData.id, {
                          content_data: {
                            ...selectedElementData.content_data,
                            font_size: parseInt(e.target.value) || 24
                          }
                        })}
                      />
                    </div>
                  </>
                )}

                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => duplicateElement(selectedElementData.id)}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => deleteElement(selectedElementData.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </>
            ) : (
              <div className="text-sm text-gray-500">Select an element to edit properties</div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Toolbar */}
        <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4">
          <div className="flex items-center space-x-4">
            <Badge variant="outline">
              {canvasSize.width} × {canvasSize.height}
            </Badge>
            <Badge variant="outline">
              {elements.length} element{elements.length !== 1 ? 's' : ''}
            </Badge>
          </div>

          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={previewOverlay}>
              {previewMode ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              {previewMode ? 'Edit' : 'Preview'}
            </Button>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-1" />
              Export
            </Button>
            <Button size="sm" onClick={saveOverlay}>
              <Save className="w-4 h-4 mr-1" />
              Save
            </Button>
          </div>
        </div>

        {/* Canvas */}
        <div className="flex-1 overflow-auto bg-gray-800 p-8">
          <div
            ref={canvasRef}
            className="relative mx-auto bg-black"
            style={{
              width: canvasSize.width * scale,
              height: canvasSize.height * scale,
              backgroundImage: gridVisible ?
                `radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px)` : 'none',
              backgroundSize: `${20 * scale}px ${20 * scale}px`
            }}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {/* Base layer indicator */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-white/20 text-4xl font-light">
                Screen Canvas
              </div>
            </div>

            {/* Render all overlay elements */}
            {elements
              .sort((a, b) => a.style.z_index - b.style.z_index)
              .map(renderElement)}
          </div>
        </div>
      </div>

      {/* Right Sidebar - Layers */}
      <div className="w-64 bg-white border-l border-gray-200">
        <div className="p-4 border-b">
          <h3 className="text-sm font-semibold flex items-center">
            <Layers className="w-4 h-4 mr-2" />
            Layers
          </h3>
        </div>
        <div className="p-2 space-y-1">
          {elements
            .sort((a, b) => b.style.z_index - a.style.z_index)
            .map(element => (
              <div
                key={element.id}
                className={`p-2 rounded cursor-pointer flex items-center justify-between ${
                  selectedElement === element.id ? 'bg-blue-100' : 'hover:bg-gray-50'
                }`}
                onClick={() => setSelectedElement(element.id)}
              >
                <div className="flex items-center">
                  {element.type === 'text' && <Type className="w-4 h-4 mr-2" />}
                  {element.type === 'image' && <Image className="w-4 h-4 mr-2" />}
                  {element.type === 'video' && <Video className="w-4 h-4 mr-2" />}
                  {element.type === 'host_content' && <Monitor className="w-4 h-4 mr-2" />}
                  {element.type === 'ad_content' && <Play className="w-4 h-4 mr-2" />}
                  <span className="text-sm truncate">{element.name}</span>
                </div>
                <span className="text-xs text-gray-400">{element.style.z_index}</span>
              </div>
            ))}
        </div>
      </div>

      {/* Content Library Dialog */}
      <Dialog open={showContentLibrary} onOpenChange={setShowContentLibrary}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Content Library</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-3 gap-4 p-4 overflow-y-auto">
            {availableContent.map(content => (
              <Card
                key={content.id}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => {
                  addElement(
                    content.categories.includes('advertising') ? 'ad_content' : 'host_content',
                    content
                  );
                  setShowContentLibrary(false);
                }}
              >
                <CardContent className="p-4">
                  <div className="aspect-video bg-gray-100 rounded mb-2 flex items-center justify-center">
                    {content.thumbnail_url ? (
                      <img
                        src={content.thumbnail_url}
                        alt={content.title}
                        className="w-full h-full object-cover rounded"
                      />
                    ) : (
                      <Image className="w-8 h-8 text-gray-400" />
                    )}
                  </div>
                  <h4 className="font-medium text-sm">{content.title}</h4>
                  <p className="text-xs text-gray-500 mt-1">
                    {content.categories.join(', ')}
                  </p>
                  <Badge
                    variant={content.status === 'approved' ? 'default' : 'secondary'}
                    className="mt-2"
                  >
                    {content.status}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}