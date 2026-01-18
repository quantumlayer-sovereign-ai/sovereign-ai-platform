'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AgentTable, PoolGauge, AuditModal, type AgentEntry } from '@/components/agents';
import { useRoles, useAudit } from '@/lib/hooks';
import { Trash2, RefreshCw } from 'lucide-react';

const demoAgents: AgentEntry[] = [
  { id: 'd4b927f1', role: 'fintech_coder', state: 'working', task: 'Building payment API...', duration: 12.3 },
  { id: 'a8c234e2', role: 'security', state: 'working', task: 'Security review...', duration: 8.7 },
  { id: 'f2e891c3', role: 'fintech_architect', state: 'done', task: 'System design...', duration: 5.2 },
  { id: 'c7a442d4', role: 'reviewer', state: 'idle' },
  { id: 'b9d123e5', role: 'compliance', state: 'working', task: 'Compliance check...', duration: 3.1 },
  { id: 'e5f678a6', role: 'tester', state: 'idle' },
  { id: '1a2b3c7', role: 'documentation', state: 'idle' },
  { id: '4d5e6f8', role: 'pm', state: 'idle' },
  { id: '7g8h9i9', role: 'cto', state: 'done', task: 'Architecture review...', duration: 2.1 },
  { id: 'j0k1l10', role: 'payment_specialist', state: 'idle' },
];

const demoAuditEntries = [
  { id: '1', timestamp: new Date().toISOString(), agent: 'fintech_coder', action: 'Started task execution', status: 'success' as const, duration: 0.05 },
  { id: '2', timestamp: new Date(Date.now() - 5000).toISOString(), agent: 'security', action: 'Code security scan', status: 'success' as const, duration: 2.3 },
  { id: '3', timestamp: new Date(Date.now() - 10000).toISOString(), agent: 'fintech_architect', action: 'System design complete', status: 'success' as const, duration: 5.2 },
  { id: '4', timestamp: new Date(Date.now() - 15000).toISOString(), agent: 'compliance', action: 'PCI-DSS validation', status: 'success' as const, duration: 1.8 },
  { id: '5', timestamp: new Date(Date.now() - 20000).toISOString(), agent: 'tester', action: 'Unit tests passed', status: 'success' as const, duration: 3.4 },
  { id: '6', timestamp: new Date(Date.now() - 25000).toISOString(), agent: 'reviewer', action: 'Code review started', status: 'pending' as const },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentEntry[]>(demoAgents);
  const { data: roles } = useRoles();
  const { data: audit } = useAudit();

  const activeCount = agents.filter((a) => a.state === 'working').length;
  const totalCount = agents.length;
  const completedCount = agents.filter((a) => a.state === 'done').length;

  // Simulate agent state changes
  useEffect(() => {
    const interval = setInterval(() => {
      setAgents((prev) => {
        const updatedAgents = [...prev];
        // Randomly update durations for working agents
        updatedAgents.forEach((agent) => {
          if (agent.state === 'working' && agent.duration) {
            agent.duration += 0.1;
          }
        });
        return updatedAgents;
      });
    }, 100);

    return () => clearInterval(interval);
  }, []);

  const handleClearCompleted = () => {
    setAgents((prev) => prev.map((a) => (a.state === 'done' ? { ...a, state: 'idle' as const, task: undefined, duration: undefined } : a)));
  };

  const handleRefresh = () => {
    // Reset to demo state
    setAgents(demoAgents);
  };

  return (
    <div className="mx-auto max-w-container px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-h2 text-foreground mb-2">Agent Monitor</h1>
          <p className="text-muted-foreground">
            Real-time status of all AI agents in the system
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={activeCount > 0 ? 'default' : 'secondary'} className={activeCount > 0 ? 'bg-primary' : ''}>
            <span className={`h-2 w-2 rounded-full mr-2 ${activeCount > 0 ? 'bg-white animate-pulse' : 'bg-muted-foreground'}`} />
            {activeCount > 0 ? `${activeCount} active` : 'All idle'}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Pool Gauge - spans 2 columns */}
        <div className="lg:col-span-2">
          <PoolGauge active={activeCount} total={totalCount} />
        </div>

        {/* Quick Stats */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Quick Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 rounded-lg bg-primary/10">
                <div className="text-2xl font-bold text-primary">{activeCount}</div>
                <div className="text-xs text-muted-foreground">Working</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-success/10">
                <div className="text-2xl font-bold text-success">{completedCount}</div>
                <div className="text-xs text-muted-foreground">Completed</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted">
                <div className="text-2xl font-bold">{agents.filter((a) => a.state === 'idle').length}</div>
                <div className="text-xs text-muted-foreground">Idle</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted">
                <div className="text-2xl font-bold">{roles?.count || 13}</div>
                <div className="text-xs text-muted-foreground">Total Roles</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agent Table */}
      <AgentTable agents={agents} />

      {/* Actions */}
      <div className="flex items-center justify-between mt-6">
        <AuditModal entries={audit || demoAuditEntries} />
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleClearCompleted} disabled={completedCount === 0}>
            <Trash2 className="h-4 w-4 mr-2" />
            Clear Completed
          </Button>
        </div>
      </div>
    </div>
  );
}
