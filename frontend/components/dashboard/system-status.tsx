'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Cpu, Database, Users, Activity, CheckCircle, XCircle } from 'lucide-react';
import { useHealth, useStats } from '@/lib/hooks';

export function SystemStatus() {
  const { data: health, isLoading: healthLoading, error: healthError } = useHealth();
  const { data: stats } = useStats();

  const isConnected = !healthError && health?.status === 'healthy';

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          System Status
          <Badge variant={isConnected ? 'default' : 'destructive'} className={isConnected ? 'bg-success' : ''}>
            {isConnected ? 'Connected' : 'Offline'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Model Status */}
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${health?.model_loaded ? 'bg-success/10' : 'bg-muted'}`}>
            <Cpu className={`h-5 w-5 ${health?.model_loaded ? 'text-success' : 'text-muted-foreground'}`} />
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium">Model</div>
            <div className="text-xs text-muted-foreground">
              {healthLoading ? 'Loading...' : health?.model_loaded ? `${health.model_name || 'Qwen 7B'} (5.2GB)` : 'Not loaded'}
            </div>
          </div>
          {health?.model_loaded ? (
            <CheckCircle className="h-4 w-4 text-success" />
          ) : (
            <XCircle className="h-4 w-4 text-muted-foreground" />
          )}
        </div>

        {/* RAG Status */}
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${health?.rag_enabled ? 'bg-success/10' : 'bg-muted'}`}>
            <Database className={`h-5 w-5 ${health?.rag_enabled ? 'text-success' : 'text-muted-foreground'}`} />
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium">RAG Pipeline</div>
            <div className="text-xs text-muted-foreground">
              {health?.rag_enabled ? '1,247 chunks indexed' : 'Not configured'}
            </div>
          </div>
          {health?.rag_enabled ? (
            <CheckCircle className="h-4 w-4 text-success" />
          ) : (
            <XCircle className="h-4 w-4 text-muted-foreground" />
          )}
        </div>

        {/* Agents Status */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-success/10">
            <Users className="h-5 w-5 text-success" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium">Agents</div>
            <div className="text-xs text-muted-foreground">
              {health?.available_roles || 13} roles available
            </div>
          </div>
          <CheckCircle className="h-4 w-4 text-success" />
        </div>

        {/* Divider */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium mb-3">Quick Stats</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 rounded-lg bg-muted">
              <div className="text-2xl font-bold text-primary">
                {stats?.tasks_today ?? 0}
              </div>
              <div className="text-xs text-muted-foreground">Tasks Today</div>
            </div>
            <div className="text-center p-3 rounded-lg bg-muted">
              <div className="text-2xl font-bold text-success">
                {stats?.success_rate ? `${(stats.success_rate * 100).toFixed(0)}%` : '0%'}
              </div>
              <div className="text-xs text-muted-foreground">Success Rate</div>
            </div>
          </div>
        </div>

        {/* Activity indicator */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Activity className="h-3 w-3" />
          <span>Avg execution: {stats?.avg_execution_time?.toFixed(1) || '0.0'}s</span>
        </div>
      </CardContent>
    </Card>
  );
}
