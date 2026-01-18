'use client';

import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Building2, Code2, Shield, FileCheck, TestTube, Eye, Users, Briefcase, FileText, Lock, Coins, Receipt, Search } from 'lucide-react';
import type { AgentState } from '@/stores/app-store';

interface Agent {
  id: string;
  role: string;
  state: AgentState;
  task?: string;
}

interface AgentCardsProps {
  agents: Agent[];
}

const roleIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  fintech_architect: Building2,
  fintech_coder: Code2,
  security: Shield,
  compliance: FileCheck,
  tester: TestTube,
  reviewer: Eye,
  pm: Users,
  cto: Briefcase,
  documentation: FileText,
  security_analyst: Lock,
  payment_specialist: Coins,
  audit: Receipt,
  research: Search,
};

const stateColors: Record<AgentState, { bg: string; dot: string; text: string }> = {
  idle: { bg: 'bg-muted', dot: 'bg-muted-foreground', text: 'text-muted-foreground' },
  working: { bg: 'bg-primary/10', dot: 'bg-primary', text: 'text-primary' },
  done: { bg: 'bg-success/10', dot: 'bg-success', text: 'text-success' },
  error: { bg: 'bg-destructive/10', dot: 'bg-destructive', text: 'text-destructive' },
};

const stateLabels: Record<AgentState, string> = {
  idle: 'Idle',
  working: 'Working',
  done: 'Complete',
  error: 'Error',
};

export function AgentCards({ agents }: AgentCardsProps) {
  const activeCount = agents.filter((a) => a.state === 'working').length;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Active Agents</h3>
          <span className="text-sm text-muted-foreground">
            {activeCount > 0 ? (
              <span className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-primary animate-pulse-dot" />
                {activeCount} running
              </span>
            ) : (
              'All idle'
            )}
          </span>
        </div>

        <div className="flex flex-wrap gap-3">
          <TooltipProvider>
            {agents.map((agent, index) => {
              const Icon = roleIcons[agent.role] || Users;
              const colors = stateColors[agent.state];

              return (
                <Tooltip key={agent.id}>
                  <TooltipTrigger asChild>
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <div
                        className={`relative flex flex-col items-center p-3 rounded-lg border ${colors.bg} transition-all hover:scale-105 cursor-default min-w-[70px]`}
                      >
                        <Icon className={`h-6 w-6 ${colors.text} mb-1`} />
                        <span className="text-xs font-medium truncate max-w-[60px]">
                          {agent.role.replace('fintech_', '').replace('_', ' ')}
                        </span>
                        <div
                          className={`absolute -top-1 -right-1 h-3 w-3 rounded-full ${colors.dot} ${agent.state === 'working' ? 'animate-pulse-dot' : ''}`}
                        />
                      </div>
                    </motion.div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <div className="text-sm">
                      <div className="font-medium">{agent.role}</div>
                      <div className="text-muted-foreground">
                        Status: {stateLabels[agent.state]}
                      </div>
                      {agent.task && (
                        <div className="text-muted-foreground">
                          Task: {agent.task}
                        </div>
                      )}
                    </div>
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </TooltipProvider>
        </div>

        <div className="flex items-center gap-4 mt-4 pt-4 border-t text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-primary" />
            Working
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-muted-foreground" />
            Idle
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-success" />
            Complete
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
