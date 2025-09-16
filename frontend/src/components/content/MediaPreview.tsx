'use client';

import React, { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Download,
  Eye,
  FileText,
  Image as ImageIcon,
  Video,
  Music,
  File,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  RotateCw
} from 'lucide-react';

interface MediaPreviewProps {
  content: {
    id: string;
    title: string;
    filename?: string;
    content_type?: string;
    size?: number;
    file_info?: {
      is_image: boolean;
      is_video: boolean;
      is_text: boolean;
      is_audio: boolean;
      formatted_size: string;
    };
    preview_url?: string;
    description?: string;
    created_at?: string;
    duration_seconds?: number;
  };
  showFullScreen?: boolean;
  showDownload?: boolean;
  showMetadata?: boolean;
  className?: string;
}

export function MediaPreview({
  content,
  showFullScreen = true,
  showDownload = true,
  showMetadata = true,
  className = ''
}: MediaPreviewProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [showFullDialog, setShowFullDialog] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  const getFileIcon = () => {
    if (!content.content_type) return <File className="h-6 w-6" />;
    
    if (content.file_info?.is_image) return <ImageIcon className="h-6 w-6 text-blue-500" />;
    if (content.file_info?.is_video) return <Video className="h-6 w-6 text-purple-500" />;
    if (content.file_info?.is_audio) return <Music className="h-6 w-6 text-green-500" />;
    if (content.file_info?.is_text) return <FileText className="h-6 w-6 text-orange-500" />;
    
    return <File className="h-6 w-6 text-gray-500" />;
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleVideoPlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleAudioPlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleDownload = () => {
    if (content.preview_url) {
      const link = document.createElement('a');
      link.href = content.preview_url;
      link.download = content.filename || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const resetImageTransform = () => {
    setZoom(1);
    setRotation(0);
  };

  const renderImagePreview = () => (
    <div className="relative bg-gray-50 rounded-lg overflow-hidden min-h-[200px] flex items-center justify-center">
      {!imageLoaded && !imageError && (
        <div className="flex items-center gap-2 text-gray-500">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Loading image...
        </div>
      )}
      
      {imageError && (
        <div className="text-center text-gray-500">
          <ImageIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>Unable to load image</p>
          <p className="text-sm">{content.filename}</p>
        </div>
      )}

      {content.preview_url && (
        <img
          src={content.preview_url}
          alt={content.title}
          className="max-w-full max-h-80 object-contain transition-transform duration-200"
          style={{
            transform: `scale(${zoom}) rotate(${rotation}deg)`,
            display: imageError ? 'none' : 'block'
          }}
          onLoad={() => setImageLoaded(true)}
          onError={() => setImageError(true)}
        />
      )}

      {imageLoaded && !imageError && (
        <div className="absolute top-2 right-2 flex gap-1">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setZoom(Math.min(zoom + 0.2, 3))}
            className="bg-white/80 hover:bg-white"
          >
            <ZoomIn className="h-3 w-3" />
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setZoom(Math.max(zoom - 0.2, 0.5))}
            className="bg-white/80 hover:bg-white"
          >
            <ZoomOut className="h-3 w-3" />
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setRotation((rotation + 90) % 360)}
            className="bg-white/80 hover:bg-white"
          >
            <RotateCw className="h-3 w-3" />
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={resetImageTransform}
            className="bg-white/80 hover:bg-white"
          >
            <RefreshCw className="h-3 w-3" />
          </Button>
        </div>
      )}
    </div>
  );

  const renderVideoPreview = () => (
    <div className="relative bg-black rounded-lg overflow-hidden">
      <video
        ref={videoRef}
        src={content.preview_url}
        className="w-full max-h-80 object-contain"
        onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
        onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        controls={false}
      />
      
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/50 to-transparent p-3">
        <div className="flex items-center gap-2 text-white">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleVideoPlay}
            className="text-white hover:bg-white/20"
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          
          <div className="flex-1 bg-white/20 rounded-full h-1">
            <div
              className="bg-white h-1 rounded-full transition-all"
              style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
            />
          </div>
          
          <span className="text-xs">
            {formatDuration(currentTime)} / {formatDuration(duration)}
          </span>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={handleMute}
            className="text-white hover:bg-white/20"
          >
            {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );

  const renderAudioPreview = () => (
    <div className="bg-gray-50 rounded-lg p-6">
      <div className="text-center mb-4">
        <Music className="h-12 w-12 mx-auto text-green-500 mb-2" />
        <h4 className="font-medium">{content.title}</h4>
        <p className="text-sm text-gray-500">{content.filename}</p>
      </div>
      
      <audio
        ref={audioRef}
        src={content.preview_url}
        onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
        onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        className="hidden"
      />
      
      <div className="space-y-3">
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleAudioPlay}
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleMute}
          >
            {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          </Button>
        </div>
        
        <div className="space-y-1">
          <div className="bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all"
              style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>{formatDuration(currentTime)}</span>
            <span>{formatDuration(duration)}</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderTextPreview = () => (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="text-center text-gray-500">
        <FileText className="h-12 w-12 mx-auto mb-2" />
        <p className="font-medium">{content.filename}</p>
        <p className="text-sm">Text file preview not available</p>
        <p className="text-xs mt-1">Click download to view content</p>
      </div>
    </div>
  );

  const renderFilePreview = () => (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="text-center text-gray-500">
        <File className="h-12 w-12 mx-auto mb-2" />
        <p className="font-medium">{content.filename}</p>
        <p className="text-sm">Preview not available for this file type</p>
        <p className="text-xs mt-1">{content.content_type}</p>
      </div>
    </div>
  );

  const renderPreview = () => {
    if (!content.preview_url) {
      return renderFilePreview();
    }

    if (content.file_info?.is_image) {
      return renderImagePreview();
    }
    
    if (content.file_info?.is_video) {
      return renderVideoPreview();
    }
    
    if (content.file_info?.is_audio) {
      return renderAudioPreview();
    }
    
    if (content.file_info?.is_text) {
      return renderTextPreview();
    }
    
    return renderFilePreview();
  };

  const renderMetadata = () => {
    if (!showMetadata) return null;

    return (
      <div className="mt-4 space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span className="font-medium">File Type</span>
          <div className="flex items-center gap-1">
            {getFileIcon()}
            <span>{content.content_type || 'Unknown'}</span>
          </div>
        </div>
        
        {content.file_info?.formatted_size && (
          <div className="flex items-center justify-between">
            <span className="font-medium">Size</span>
            <span>{content.file_info.formatted_size}</span>
          </div>
        )}
        
        {content.duration_seconds && (
          <div className="flex items-center justify-between">
            <span className="font-medium">Duration</span>
            <span>{formatDuration(content.duration_seconds)}</span>
          </div>
        )}
        
        {content.created_at && (
          <div className="flex items-center justify-between">
            <span className="font-medium">Uploaded</span>
            <span>{new Date(content.created_at).toLocaleDateString()}</span>
          </div>
        )}
      </div>
    );
  };

  const renderActions = () => (
    <div className="flex gap-2 mt-4">
      {showFullScreen && content.preview_url && (
        <Dialog open={showFullDialog} onOpenChange={setShowFullDialog}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              <Eye className="h-4 w-4 mr-1" />
              Full View
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh]">
            <DialogHeader>
              <DialogTitle>{content.title}</DialogTitle>
            </DialogHeader>
            <div className="overflow-auto">
              {renderPreview()}
            </div>
          </DialogContent>
        </Dialog>
      )}
      
      {showDownload && content.preview_url && (
        <Button variant="outline" size="sm" onClick={handleDownload}>
          <Download className="h-4 w-4 mr-1" />
          Download
        </Button>
      )}
    </div>
  );

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          {getFileIcon()}
          {content.title}
        </CardTitle>
        {content.description && (
          <p className="text-sm text-gray-600 mt-1">{content.description}</p>
        )}
      </CardHeader>
      
      <CardContent>
        {renderPreview()}
        {renderMetadata()}
        {renderActions()}
      </CardContent>
    </Card>
  );
}