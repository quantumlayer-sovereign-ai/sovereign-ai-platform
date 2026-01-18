'use client';

import { useRef, useEffect, useState } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';
import { useTheme } from '@/components/providers';
import { Copy, Check, FileCode } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { editor } from 'monaco-editor';

interface ProjectFile {
  path: string;
  content: string;
  language: string;
  size: number;
}

interface CodeViewerProps {
  file: ProjectFile | null;
  isLoading?: boolean;
}

// Map file extensions to Monaco language IDs
function getMonacoLanguage(language: string, path: string): string {
  const ext = path.split('.').pop()?.toLowerCase();

  const langMap: Record<string, string> = {
    'python': 'python',
    'py': 'python',
    'javascript': 'javascript',
    'js': 'javascript',
    'typescript': 'typescript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'jsx': 'javascript',
    'json': 'json',
    'yaml': 'yaml',
    'yml': 'yaml',
    'markdown': 'markdown',
    'md': 'markdown',
    'html': 'html',
    'css': 'css',
    'sql': 'sql',
    'bash': 'shell',
    'sh': 'shell',
    'shell': 'shell',
    'java': 'java',
    'go': 'go',
    'rust': 'rust',
    'rs': 'rust',
    'c': 'c',
    'cpp': 'cpp',
    'csharp': 'csharp',
    'cs': 'csharp',
    'ruby': 'ruby',
    'rb': 'ruby',
    'php': 'php',
    'text': 'plaintext',
    'txt': 'plaintext',
  };

  return langMap[ext || ''] || langMap[language] || 'plaintext';
}

export function CodeViewer({ file, isLoading }: CodeViewerProps) {
  const { theme } = useTheme();
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const [copied, setCopied] = useState(false);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Custom theme for light mode
    monaco.editor.defineTheme('sovereign-light', {
      base: 'vs',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#ffffff',
        'editor.foreground': '#0a2540',
        'editor.lineHighlightBackground': '#f6f9fc',
        'editorLineNumber.foreground': '#697386',
        'editorCursor.foreground': '#635bff',
      },
    });

    // Custom theme for dark mode
    monaco.editor.defineTheme('sovereign-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#1a3a5c',
        'editor.foreground': '#ffffff',
        'editor.lineHighlightBackground': '#234567',
        'editorLineNumber.foreground': '#8898aa',
        'editorCursor.foreground': '#635bff',
      },
    });

    // Apply the appropriate theme
    monaco.editor.setTheme(theme === 'dark' ? 'sovereign-dark' : 'sovereign-light');
  };

  useEffect(() => {
    if (editorRef.current) {
      // @ts-expect-error - monaco is available on the window after editor mounts
      if (window.monaco) {
        // @ts-expect-error - monaco is a global added by monaco-editor
        window.monaco.editor.setTheme(theme === 'dark' ? 'sovereign-dark' : 'sovereign-light');
      }
    }
  }, [theme]);

  const handleCopy = async () => {
    if (file?.content) {
      await navigator.clipboard.writeText(file.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-card rounded-lg border">
        <div className="animate-pulse text-muted-foreground">Loading file...</div>
      </div>
    );
  }

  if (!file) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-card rounded-lg border text-muted-foreground">
        <FileCode className="h-12 w-12 mb-3 opacity-40" />
        <p className="text-sm">Select a file to view its contents</p>
      </div>
    );
  }

  const language = getMonacoLanguage(file.language, file.path);

  return (
    <div className="flex flex-col h-full rounded-lg border overflow-hidden bg-card">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30">
        <div className="flex items-center gap-2 text-sm">
          <FileCode className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{file.path}</span>
          <span className="text-muted-foreground">({language})</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-7 px-2"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 mr-1.5 text-green-500" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5 mr-1.5" />
              Copy
            </>
          )}
        </Button>
      </div>

      {/* Editor */}
      <div className="flex-1 min-h-0">
        <Editor
          key={file.path}
          height="100%"
          language={language}
          value={file.content}
          onMount={handleEditorDidMount}
          theme={theme === 'dark' ? 'vs-dark' : 'vs'}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            padding: { top: 12, bottom: 12 },
            fontFamily: 'JetBrains Mono, Menlo, Monaco, monospace',
            tabSize: 4,
            automaticLayout: true,
            scrollbar: {
              verticalScrollbarSize: 8,
              horizontalScrollbarSize: 8,
            },
          }}
          loading={
            <div className="flex items-center justify-center h-full bg-card">
              <div className="text-muted-foreground">Loading editor...</div>
            </div>
          }
        />
      </div>
    </div>
  );
}
