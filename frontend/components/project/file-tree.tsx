'use client';

import { useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, Folder, FolderOpen, FileCode, FileJson, FileText, File } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ProjectFile {
  path: string;
  language: string;
  size: number;
}

interface FileTreeProps {
  files: ProjectFile[];
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
}

interface TreeNode {
  name: string;
  path: string;
  isDirectory: boolean;
  children: TreeNode[];
  file?: ProjectFile;
}

function buildTree(files: ProjectFile[]): TreeNode[] {
  const root: TreeNode[] = [];

  for (const file of files) {
    const parts = file.path.split('/');
    let currentLevel = root;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      const currentPath = parts.slice(0, i + 1).join('/');

      let existing = currentLevel.find((n) => n.name === part);

      if (!existing) {
        existing = {
          name: part,
          path: currentPath,
          isDirectory: !isLast,
          children: [],
          file: isLast ? file : undefined,
        };
        currentLevel.push(existing);
      }

      if (!isLast) {
        currentLevel = existing.children;
      }
    }
  }

  // Sort: directories first, then files, alphabetically
  const sortNodes = (nodes: TreeNode[]): TreeNode[] => {
    return nodes.sort((a, b) => {
      if (a.isDirectory && !b.isDirectory) return -1;
      if (!a.isDirectory && b.isDirectory) return 1;
      return a.name.localeCompare(b.name);
    }).map((node) => ({
      ...node,
      children: sortNodes(node.children),
    }));
  };

  return sortNodes(root);
}

function getFileIcon(name: string, _language: string) {
  const ext = name.split('.').pop()?.toLowerCase();

  if (ext === 'json') return FileJson;
  if (ext === 'md' || ext === 'txt') return FileText;
  if (['py', 'js', 'ts', 'tsx', 'jsx', 'java', 'go', 'rs', 'c', 'cpp', 'rb'].includes(ext || '')) {
    return FileCode;
  }

  return File;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface TreeNodeItemProps {
  node: TreeNode;
  depth: number;
  selectedPath: string | null;
  expandedPaths: Set<string>;
  onToggle: (path: string) => void;
  onSelect: (path: string) => void;
}

function TreeNodeItem({ node, depth, selectedPath, expandedPaths, onToggle, onSelect }: TreeNodeItemProps) {
  const isExpanded = expandedPaths.has(node.path);
  const isSelected = selectedPath === node.path;

  const handleClick = () => {
    if (node.isDirectory) {
      onToggle(node.path);
    } else {
      onSelect(node.path);
    }
  };

  const FileIcon = node.isDirectory
    ? (isExpanded ? FolderOpen : Folder)
    : getFileIcon(node.name, node.file?.language || '');

  return (
    <div>
      <button
        onClick={handleClick}
        className={cn(
          'flex items-center gap-1.5 w-full px-2 py-1 text-left text-sm rounded-md transition-colors',
          'hover:bg-muted/50',
          isSelected && 'bg-primary/10 text-primary font-medium',
          !isSelected && 'text-foreground/80'
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {node.isDirectory ? (
          isExpanded ? (
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          )
        ) : (
          <span className="w-3.5" />
        )}
        <FileIcon className={cn(
          'h-4 w-4 shrink-0',
          node.isDirectory ? 'text-amber-500' : 'text-muted-foreground'
        )} />
        <span className="truncate flex-1">{node.name}</span>
        {node.file && (
          <span className="text-xs text-muted-foreground shrink-0">
            {formatSize(node.file.size)}
          </span>
        )}
      </button>
      {node.isDirectory && isExpanded && node.children.length > 0 && (
        <div>
          {node.children.map((child) => (
            <TreeNodeItem
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              expandedPaths={expandedPaths}
              onToggle={onToggle}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function FileTree({ files, selectedPath, onSelectFile }: FileTreeProps) {
  const tree = useMemo(() => buildTree(files), [files]);

  // Initialize expanded paths with all directories
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(() => {
    const paths = new Set<string>();
    const addDirPaths = (nodes: TreeNode[]) => {
      for (const node of nodes) {
        if (node.isDirectory) {
          paths.add(node.path);
          addDirPaths(node.children);
        }
      }
    };
    addDirPaths(tree);
    return paths;
  });

  const handleToggle = (path: string) => {
    setExpandedPaths((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  if (files.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground text-sm">
        No files in project
      </div>
    );
  }

  return (
    <div className="py-2">
      {tree.map((node) => (
        <TreeNodeItem
          key={node.path}
          node={node}
          depth={0}
          selectedPath={selectedPath}
          expandedPaths={expandedPaths}
          onToggle={handleToggle}
          onSelect={onSelectFile}
        />
      ))}
    </div>
  );
}
