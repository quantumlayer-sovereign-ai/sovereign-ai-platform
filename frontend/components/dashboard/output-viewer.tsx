'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Copy, Check, Clock, Users, CheckCircle, XCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface ComplianceStatus {
  passed: boolean;
  issues: string[];
}

interface TaskResult {
  task: string;
  agents_used: string[];
  outputs: Record<string, string>;
  compliance_status: Record<string, ComplianceStatus>;
  execution_time: number;
}

interface OutputViewerProps {
  result?: TaskResult;
  isLoading?: boolean;
}

export function OutputViewer({ result, isLoading }: OutputViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (result) {
      const text = Object.entries(result.outputs)
        .map(([agent, output]) => `## ${agent}\n\n${output}`)
        .join('\n\n---\n\n');
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg">Output</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <div className="relative">
              <div className="h-12 w-12 rounded-full border-4 border-muted animate-spin border-t-primary" />
            </div>
            <p className="mt-4 text-sm">Executing task...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!result) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg">Output</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <p className="text-sm">Execute a task to see results here</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">Output</CardTitle>
        <Button variant="ghost" size="sm" onClick={handleCopy}>
          {copied ? (
            <Check className="h-4 w-4 text-success" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-6">
            {Object.entries(result.outputs).map(([agent, output]) => (
              <div key={agent} className="space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-success" />
                  <h4 className="font-medium">{agent}</h4>
                </div>
                <div className="pl-6 prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown
                    components={{
                      pre: ({ children }) => (
                        <pre className="bg-muted rounded-md p-4 overflow-x-auto">
                          {children}
                        </pre>
                      ),
                      code: ({ children, className }) => {
                        const isInline = !className;
                        return isInline ? (
                          <code className="bg-muted px-1.5 py-0.5 rounded text-sm">
                            {children}
                          </code>
                        ) : (
                          <code className="font-mono text-sm">{children}</code>
                        );
                      },
                    }}
                  >
                    {output}
                  </ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        {/* Footer with compliance badges and stats */}
        <div className="flex flex-wrap items-center gap-3 pt-4 border-t">
          {Object.entries(result.compliance_status).map(([standard, status]) => (
            <Badge
              key={standard}
              variant={status.passed ? 'default' : 'destructive'}
              className={status.passed ? 'bg-success hover:bg-success/90' : ''}
            >
              {status.passed ? (
                <CheckCircle className="mr-1 h-3 w-3" />
              ) : (
                <XCircle className="mr-1 h-3 w-3" />
              )}
              {standard} {status.passed ? 'PASSED' : 'FAILED'}
            </Badge>
          ))}

          <div className="ml-auto flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {result.execution_time.toFixed(1)}s
            </span>
            <span className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              {result.agents_used.length} agents
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
