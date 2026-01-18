'use client';

import { useState } from 'react';
import { TaskInput, AgentCards, OutputViewer, SystemStatus } from '@/components/dashboard';
import { useAppStore, type ActiveAgent } from '@/stores/app-store';
import { useExecuteTask } from '@/lib/hooks';
import { useToast } from '@/hooks/use-toast';

interface TaskResult {
  task: string;
  agents_used: string[];
  outputs: Record<string, string>;
  compliance_status: Record<string, { passed: boolean; issues: string[] }>;
  execution_time: number;
}

// Helper function to parse agent outputs from the combined output string
function parseAgentOutputs(output: string): Record<string, string> {
  const outputs: Record<string, string> = {};

  // Split by agent headers (## agent_name ✓)
  const sections = output.split(/^## /gm).filter(Boolean);

  for (const section of sections) {
    // Extract agent name from first line (e.g., "coder ✓" or "fintech_coder ✓")
    const firstLineEnd = section.indexOf('\n');
    if (firstLineEnd === -1) continue;

    const header = section.substring(0, firstLineEnd).trim();
    const agentName = header.replace(/\s*✓\s*$/, '').trim();
    const content = section.substring(firstLineEnd + 1).trim();

    // Skip knowledge base sources section
    if (agentName.toLowerCase() === 'knowledge base sources') continue;

    if (agentName && content) {
      outputs[agentName] = content;
    }
  }

  // If no sections were parsed, return the full output as a single entry
  if (Object.keys(outputs).length === 0 && output.trim()) {
    outputs['output'] = output;
  }

  return outputs;
}

// Helper function to transform compliance status from backend format
function transformComplianceStatus(
  status?: Record<string, boolean | { passed: boolean; issues: string[] }>
): Record<string, { passed: boolean; issues: string[] }> {
  if (!status) {
    return { 'PCI-DSS': { passed: true, issues: [] } };
  }

  const transformed: Record<string, { passed: boolean; issues: string[] }> = {};

  for (const [key, value] of Object.entries(status)) {
    if (typeof value === 'boolean') {
      // Backend returns simple boolean flags
      transformed[key] = { passed: value, issues: [] };
    } else if (typeof value === 'object' && value !== null) {
      // Already in expected format
      transformed[key] = value;
    }
  }

  // If empty, add default
  if (Object.keys(transformed).length === 0) {
    transformed['PCI-DSS'] = { passed: true, issues: [] };
  }

  return transformed;
}

const defaultAgents: ActiveAgent[] = [
  { id: '1', role: 'fintech_architect', state: 'idle' },
  { id: '2', role: 'fintech_coder', state: 'idle' },
  { id: '3', role: 'security', state: 'idle' },
  { id: '4', role: 'compliance', state: 'idle' },
  { id: '5', role: 'tester', state: 'idle' },
  { id: '6', role: 'reviewer', state: 'idle' },
  { id: '7', role: 'pm', state: 'idle' },
];

export default function DashboardPage() {
  const { selectedVertical, selectedStandards, useRAG } = useAppStore();
  const [agents, setAgents] = useState<ActiveAgent[]>(defaultAgents);
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null);
  const { toast } = useToast();

  const executeTask = useExecuteTask();

  const simulateAgentExecution = () => {
    // Simulate agents working
    const activeAgents = ['fintech_architect', 'fintech_coder', 'security', 'compliance', 'tester'];

    // Start all agents
    setAgents((prev) =>
      prev.map((agent) =>
        activeAgents.includes(agent.role)
          ? { ...agent, state: 'working' as const, task: 'Processing...' }
          : agent
      )
    );

    // Complete agents one by one
    activeAgents.forEach((role, index) => {
      setTimeout(() => {
        setAgents((prev) =>
          prev.map((agent) =>
            agent.role === role ? { ...agent, state: 'done' as const } : agent
          )
        );
      }, (index + 1) * 800);
    });
  };

  const handleExecute = async (task: string) => {
    try {
      simulateAgentExecution();

      const result = await executeTask.mutateAsync({
        task,
        vertical: selectedVertical,
        use_rag: useRAG,
        compliance_standards: selectedStandards,
      });

      if (result.success && result.output) {
        // Transform flat API response to dashboard format
        const transformedResult: TaskResult = {
          task,
          agents_used: result.agents_used || [],
          outputs: {
            // Parse the output into sections by agent headers (## agent_name ✓)
            ...parseAgentOutputs(result.output),
          },
          compliance_status: transformComplianceStatus(result.compliance_status),
          execution_time: result.execution_time_seconds || 0,
        };
        setTaskResult(transformedResult);
        toast({
          title: 'Task Completed',
          description: `Executed in ${(result.execution_time_seconds || 0).toFixed(1)}s with ${(result.agents_used || []).length} agents`,
        });

        // Update agent states based on agents_used
        if (result.agents_used) {
          setAgents((prev) =>
            prev.map((agent) =>
              result.agents_used?.includes(agent.role)
                ? { ...agent, state: 'done' as const }
                : agent
            )
          );
        }
      }
    } catch {
      // If API fails, show demo data
      const demoResult = {
        task,
        agents_used: ['fintech_architect', 'fintech_coder', 'security', 'compliance', 'tester'],
        outputs: {
          fintech_architect: `## Payment System Architecture

Designed a secure payment processing system with the following components:

- **Event-driven processing** using message queues
- **PCI-DSS compliant** data handling with encryption at rest
- **TLS 1.3** encryption for all network communications
- **Tokenization** for card data protection`,
          fintech_coder: `## Implementation

\`\`\`python
async def process_payment(payment_request: PaymentRequest) -> PaymentResponse:
    """
    Process a payment with PCI-DSS compliance.
    """
    # Validate and tokenize card data
    token = await tokenize_card(payment_request.card)

    # Process through secure gateway
    result = await payment_gateway.charge(
        token=token,
        amount=payment_request.amount,
        currency=payment_request.currency
    )

    # Log audit trail (no sensitive data)
    await audit_log.record(
        action="payment_processed",
        amount=payment_request.amount,
        status=result.status
    )

    return PaymentResponse(
        transaction_id=result.id,
        status=result.status
    )
\`\`\``,
          security: `## Security Review

All security requirements validated:
- No hardcoded credentials
- Proper input validation
- SQL injection prevention
- XSS protection implemented`,
        },
        compliance_status: {
          'PCI-DSS': { passed: true, issues: [] },
          'RBI': { passed: true, issues: [] },
        },
        execution_time: 23.4,
      };
      setTaskResult(demoResult);
      toast({
        title: 'Demo Mode',
        description: 'Showing demo results (API not connected)',
        variant: 'default',
      });

      // Reset agents after simulation
      setTimeout(() => {
        setAgents(defaultAgents);
      }, 4000);
    }
  };

  return (
    <div className="mx-auto max-w-container px-6 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          <TaskInput onExecute={handleExecute} isLoading={executeTask.isPending} />
          <AgentCards agents={agents} />
          <OutputViewer result={taskResult ?? undefined} isLoading={executeTask.isPending} />
        </div>

        {/* Sidebar - 1 column */}
        <div className="space-y-6">
          <SystemStatus />
        </div>
      </div>
    </div>
  );
}
