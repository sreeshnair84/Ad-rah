'use client';

import React from 'react';
import { Upload, FileImage, FileVideo, FileText, FileAudio, File } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface FileDropZoneProps {
  onDrop: (e: React.DragEvent) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onClick: () => void;
  isDragOver: boolean;
  disabled?: boolean;
  maxFiles: number;
  maxFileSize: string;
  acceptedTypes: Record<string, string[]>;
  title?: string;
  description?: string;
}

export function FileDropZone({
  onDrop,
  onDragOver,
  onDragLeave,
  onClick,
  isDragOver,
  disabled = false,
  maxFiles,
  maxFileSize,
  acceptedTypes,
  title = "Select Files",
  description = "Drag and drop your files here or click to browse"
}: FileDropZoneProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
            isDragOver
              ? 'border-blue-500 bg-blue-50'
              : disabled
              ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDrop={disabled ? undefined : onDrop}
          onDragOver={disabled ? undefined : onDragOver}
          onDragLeave={disabled ? undefined : onDragLeave}
          onClick={disabled ? undefined : onClick}
        >
          <Upload className={`h-12 w-12 mx-auto mb-4 ${disabled ? 'text-gray-300' : 'text-gray-400'}`} />
          <h3 className={`text-lg font-medium mb-2 ${disabled ? 'text-gray-400' : 'text-gray-900'}`}>
            Drop files here or click to upload
          </h3>
          <p className={`text-sm mb-4 ${disabled ? 'text-gray-400' : 'text-gray-500'}`}>
            Maximum {maxFiles} files, {maxFileSize} each
          </p>
          <Button variant="outline" disabled={disabled}>
            Select Files
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

interface FileIconProps {
  file: File;
  size?: 'sm' | 'md' | 'lg';
}

export function FileIcon({ file, size = 'md' }: FileIconProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  };

  const className = sizeClasses[size];

  if (file.type.startsWith('image/')) {
    return <FileImage className={`${className} text-blue-500`} />;
  }
  if (file.type.startsWith('video/')) {
    return <FileVideo className={`${className} text-purple-500`} />;
  }
  if (file.type.startsWith('audio/')) {
    return <FileAudio className={`${className} text-green-500`} />;
  }
  if (file.type === 'application/pdf') {
    return <FileText className={`${className} text-red-500`} />;
  }
  return <File className={`${className} text-gray-500`} />;
}

interface FileInputProps {
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  accept: string;
  multiple?: boolean;
  disabled?: boolean;
  id?: string;
  required?: boolean;
}

export const FileInput = React.forwardRef<HTMLInputElement, FileInputProps>(
  ({ onChange, accept, multiple = false, disabled = false, id, required = false }, ref) => {
    return (
      <input
        ref={ref}
        type="file"
        multiple={multiple}
        accept={accept}
        onChange={onChange}
        disabled={disabled}
        className="hidden"
        id={id}
        required={required}
      />
    );
  }
);

FileInput.displayName = 'FileInput';
