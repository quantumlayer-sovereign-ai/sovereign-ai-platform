'use client';

import { useState, useEffect } from 'react';
import { Download, Copy, Check, FolderOpen, Clock, Users, FileCode } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileTree } from './file-tree';
import { CodeViewer } from './code-viewer';
import { useProject, useProjectFile } from '@/lib/hooks/use-project';
import { getAuthToken } from '@/lib/api';

interface ProjectExplorerProps {
  taskId: string;
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Dynamically determine API base URL
const getApiBase = (): string => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://localhost:8000';
};

export function ProjectExplorer({ taskId }: ProjectExplorerProps) {
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: manifest, isLoading: manifestLoading, error: manifestError } = useProject(taskId);
  const { data: fileContent, isLoading: fileLoading } = useProjectFile(taskId, selectedPath || '');

  // Auto-select first file when manifest loads
  useEffect(() => {
    if (manifest?.files && manifest.files.length > 0 && !selectedPath) {
      // Find first non-directory file (e.g., README.md)
      const firstFile = manifest.files.find((f) => !f.path.endsWith('/'));
      if (firstFile) {
        setSelectedPath(firstFile.path);
      }
    }
  }, [manifest, selectedPath]);

  const handleDownload = () => {
    const token = getAuthToken();
    const downloadUrl = `${getApiBase()}/projects/${taskId}/download`;

    // Create a temporary link with auth header
    const link = document.createElement('a');
    link.href = downloadUrl;

    // For authenticated downloads, we need to use fetch
    fetch(downloadUrl, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const url = window.URL.createObjectURL(blob);
        link.href = url;
        link.download = `${taskId}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      });
  };

  const handleCopyAll = async () => {
    if (!manifest) return;

    // Fetch all file contents and concatenate
    const allContent = manifest.files
      .map((f) => `// File: ${f.path}\n// Language: ${f.language}\n\n`)
      .join('\n---\n\n');

    await navigator.clipboard.writeText(
      `Project: ${manifest.task}\nFiles: ${manifest.total_files}\n\n${allContent}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (manifestLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center text-muted-foreground">
            <div className="animate-pulse">Loading project...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (manifestError || !manifest) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center justify-center text-muted-foreground">
            <FolderOpen className="h-12 w-12 mb-3 opacity-40" />
            <p className="text-sm">No project data available</p>
            <p className="text-xs mt-1">Execute a task to generate a project</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Build file object for code viewer
  const selectedFile = selectedPath && fileContent && fileContent.content
    ? {
        path: selectedPath,
        content: fileContent.content,
        language: fileContent.language,
        size: fileContent.size,
      }
    : null;

  return (
    <Card className="flex flex-col h-[600px]">
      {/* Header */}
      <CardHeader className="pb-3 shrink-0">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <FolderOpen className="h-5 w-5" />
              Project Explorer
            </CardTitle>
            <p className="text-sm text-muted-foreground line-clamp-1">
              {manifest.task}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleCopyAll}>
              {copied ? (
                <>
                  <Check className="h-4 w-4 mr-1.5 text-green-500" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-1.5" />
                  Copy All
                </>
              )}
            </Button>
            <Button variant="default" size="sm" onClick={handleDownload}>
              <Download className="h-4 w-4 mr-1.5" />
              Download ZIP
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2">
          <div className="flex items-center gap-1">
            <FileCode className="h-3.5 w-3.5" />
            {manifest.total_files} files
          </div>
          <div className="flex items-center gap-1">
            <span>{formatSize(manifest.total_size)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            {formatDate(manifest.created_at)}
          </div>
          {manifest.agents_used.length > 0 && (
            <div className="flex items-center gap-1">
              <Users className="h-3.5 w-3.5" />
              {manifest.agents_used.length} agents
            </div>
          )}
        </div>
      </CardHeader>

      {/* Content */}
      <CardContent className="flex-1 min-h-0 p-0">
        <div className="flex h-full border-t">
          {/* File Tree Sidebar */}
          <div className="w-64 border-r shrink-0">
            <ScrollArea className="h-full">
              <FileTree
                files={manifest.files}
                selectedPath={selectedPath}
                onSelectFile={setSelectedPath}
              />
            </ScrollArea>
          </div>

          {/* Code Viewer */}
          <div className="flex-1 min-w-0 p-3">
            <CodeViewer file={selectedFile} isLoading={fileLoading && !!selectedPath} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
