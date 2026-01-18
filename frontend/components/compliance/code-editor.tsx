'use client';

import { useRef, useEffect } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';
import { useTheme } from '@/components/providers';
import type { editor } from 'monaco-editor';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
}

export function CodeEditor({ value, onChange, language = 'python' }: CodeEditorProps) {
  const { theme } = useTheme();
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

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

  return (
    <div className="rounded-lg border overflow-hidden">
      <Editor
        height="300px"
        language={language}
        value={value}
        onChange={(v) => onChange(v || '')}
        onMount={handleEditorDidMount}
        theme={theme === 'dark' ? 'vs-dark' : 'vs'}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          padding: { top: 16, bottom: 16 },
          fontFamily: 'JetBrains Mono, monospace',
          tabSize: 4,
          automaticLayout: true,
        }}
        loading={
          <div className="flex items-center justify-center h-[300px] bg-card">
            <div className="text-muted-foreground">Loading editor...</div>
          </div>
        }
      />
    </div>
  );
}
