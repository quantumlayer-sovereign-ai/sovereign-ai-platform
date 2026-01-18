'use client';

import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Circle, Loader2, AlertCircle } from 'lucide-react';

export interface AgentEntry {
  id: string;
  role: string;
  state: 'idle' | 'working' | 'done' | 'error';
  task?: string;
  duration?: number;
}

interface AgentTableProps {
  agents: AgentEntry[];
}

const stateConfig: Record<string, { icon: typeof Circle; color: string; bg: string; label: string; animate?: boolean }> = {
  idle: { icon: Circle, color: 'text-muted-foreground', bg: 'bg-muted', label: 'IDLE' },
  working: { icon: Loader2, color: 'text-primary', bg: 'bg-primary/10', label: 'WORKING', animate: true },
  done: { icon: CheckCircle, color: 'text-success', bg: 'bg-success/10', label: 'DONE' },
  error: { icon: AlertCircle, color: 'text-destructive', bg: 'bg-destructive/10', label: 'ERROR' },
};

export function AgentTable({ agents }: AgentTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Agent Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left">
                <th className="pb-3 text-sm font-medium text-muted-foreground">Agent ID</th>
                <th className="pb-3 text-sm font-medium text-muted-foreground">Role</th>
                <th className="pb-3 text-sm font-medium text-muted-foreground">State</th>
                <th className="pb-3 text-sm font-medium text-muted-foreground">Task</th>
                <th className="pb-3 text-sm font-medium text-muted-foreground text-right">Duration</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent, index) => {
                const config = stateConfig[agent.state];
                const Icon = config.icon;

                return (
                  <motion.tr
                    key={agent.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="border-b last:border-0"
                  >
                    <td className="py-3">
                      <code className="text-sm font-mono bg-muted px-2 py-1 rounded">
                        {agent.id.slice(0, 6)}
                      </code>
                    </td>
                    <td className="py-3">
                      <span className="font-medium">{agent.role}</span>
                    </td>
                    <td className="py-3">
                      <Badge variant="secondary" className={`${config.bg} ${config.color}`}>
                        <Icon className={`h-3 w-3 mr-1 ${config.animate ? 'animate-spin' : ''}`} />
                        {config.label}
                      </Badge>
                    </td>
                    <td className="py-3">
                      <span className="text-sm text-muted-foreground truncate max-w-[200px] inline-block">
                        {agent.task || '-'}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <span className="text-sm text-muted-foreground">
                        {agent.duration ? `${agent.duration.toFixed(1)}s` : '-'}
                      </span>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
