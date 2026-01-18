const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Token management
let authToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (typeof window !== 'undefined') {
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }
};

export const getAuthToken = (): string | null => {
  if (authToken) return authToken;
  if (typeof window !== 'undefined') {
    authToken = localStorage.getItem('auth_token');
  }
  return authToken;
};

// Get headers with auth
const getHeaders = (includeContentType = true): HeadersInit => {
  const headers: HeadersInit = {};
  if (includeContentType) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

// Login to get token (dev mode)
export const login = async (userId: string, email: string): Promise<string> => {
  const res = await fetch(`${API_BASE}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, email }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail || 'Login failed');
  }
  const data = await res.json();
  setAuthToken(data.access_token);
  return data.access_token;
};

export interface TaskRequest {
  task: string;
  vertical?: string;
  use_rag?: boolean;
  compliance_standards?: string[];
}

export interface TaskResponse {
  task_id: string;
  success: boolean;
  output?: string;
  agents_used?: string[];
  // Backend can return either boolean flags or structured compliance objects
  compliance_status?: Record<string, boolean | { passed: boolean; issues: string[] }>;
  execution_time_seconds?: number;
  error?: string;
  // For frontend display, we transform this to result format
  result?: {
    task: string;
    agents_used: string[];
    outputs: Record<string, string>;
    compliance_status: Record<string, { passed: boolean; issues: string[] }>;
    execution_time: number;
  };
}

export interface ComplianceRequest {
  code: string;
  standards?: string[];
}

export interface ComplianceIssue {
  severity: 'critical' | 'high' | 'medium' | 'low';
  rule_name: string;
  description: string;
  evidence?: string;
  remediation?: string;
  line_number?: number;
  // Aliases for frontend compatibility
  rule_id?: string;
  message?: string;
  line?: number;
  recommendation?: string;
}

export interface ComplianceResponse {
  passed: boolean;
  issues: ComplianceIssue[];
  summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

export interface SecurityScanRequest {
  code: string;
}

export interface RAGSearchRequest {
  query: string;
  collection?: string;
  top_k?: number;
}

export interface RAGResult {
  content: string;
  metadata: Record<string, string>;
  relevance_score: number;
}

export interface RAGSearchResponse {
  query: string;
  vertical: string;
  results: RAGResult[];
  count: number;
  collection?: string; // For backwards compatibility
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  model_name?: string;
  rag_enabled: boolean;
  available_roles: number;
  uptime_seconds?: number;
}

export interface AgentRole {
  name: string;
  description: string;
  vertical?: string;
}

export interface RolesResponse {
  roles: string[];
  count: number;
  vertical_filter: string | null;
}

export interface StatsResponse {
  tasks_today: number;
  success_rate: number;
  avg_execution_time: number;
  total_agents: number;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  agent: string;
  action: string;
  status: 'success' | 'failure' | 'pending';
  duration?: number;
}

export const api = {
  // Health (public endpoint - no auth required)
  getHealth: async (): Promise<HealthResponse> => {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed to fetch health');
    return res.json();
  },

  // Tasks
  executeTask: async (task: TaskRequest): Promise<TaskResponse> => {
    const res = await fetch(`${API_BASE}/task/execute`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(task),
    });
    if (!res.ok) throw new Error('Failed to execute task');
    return res.json();
  },

  getTaskHistory: async (limit = 10): Promise<TaskResponse[]> => {
    const res = await fetch(`${API_BASE}/tasks/history?limit=${limit}`, {
      headers: getHeaders(false),
    });
    if (!res.ok) throw new Error('Failed to fetch task history');
    return res.json();
  },

  // Compliance
  checkCompliance: async (req: ComplianceRequest): Promise<ComplianceResponse> => {
    const res = await fetch(`${API_BASE}/compliance/check`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error('Failed to check compliance');
    return res.json();
  },

  // Security
  scanCode: async (req: SecurityScanRequest): Promise<ComplianceResponse> => {
    const res = await fetch(`${API_BASE}/security/scan`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error('Failed to scan code');
    return res.json();
  },

  // RAG
  searchKnowledge: async (req: RAGSearchRequest): Promise<RAGSearchResponse> => {
    const res = await fetch(`${API_BASE}/rag/search`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error('Failed to search knowledge');
    return res.json();
  },

  indexDocuments: async (collection: string, documents: string[]): Promise<{ indexed: number }> => {
    const res = await fetch(`${API_BASE}/rag/index`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ collection, documents }),
    });
    if (!res.ok) throw new Error('Failed to index documents');
    return res.json();
  },

  // Roles & Agents (public endpoint - no auth required)
  getRoles: async (vertical?: string): Promise<RolesResponse> => {
    const url = vertical ? `${API_BASE}/roles?vertical=${vertical}` : `${API_BASE}/roles`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch roles');
    return res.json();
  },

  getStats: async (): Promise<StatsResponse> => {
    const res = await fetch(`${API_BASE}/stats`, {
      headers: getHeaders(false),
    });
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
  },

  getAudit: async (): Promise<AuditEntry[]> => {
    const res = await fetch(`${API_BASE}/audit`, {
      headers: getHeaders(false),
    });
    if (!res.ok) throw new Error('Failed to fetch audit');
    return res.json();
  },
};
