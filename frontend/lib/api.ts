// Dynamically determine API base URL
// If NEXT_PUBLIC_API_URL is set, use it; otherwise use the same host as the frontend on port 8000
const getApiBase = (): string => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== 'undefined') {
    // Use the same hostname as the frontend, but port 8000
    return `http://${window.location.hostname}:8000`;
  }
  // Fallback for SSR
  return 'http://localhost:8000';
};

// Lazily evaluated to ensure window is available in browser
let _apiBase: string | null = null;
const getApiUrl = (): string => {
  if (_apiBase === null) {
    _apiBase = getApiBase();
  }
  return _apiBase;
};

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
  // Always read from localStorage to get fresh token
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
export const login = async (username: string, password: string): Promise<string> => {
  const res = await fetch(`${getApiUrl()}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
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
  project_id?: string; // Project ID if project was generated
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

export interface ProjectFile {
  path: string;
  language: string;
  size: number;
  content?: string;
}

export interface ProjectManifest {
  task_id: string;
  task: string;
  created_at: string;
  files: ProjectFile[];
  agents_used: string[];
  total_files: number;
  total_size: number;
}

export interface ProjectListItem {
  task_id: string;
  task: string;
  created_at: string;
  total_files: number;
  total_size: number;
}

export const api = {
  // Health (public endpoint - no auth required)
  getHealth: async (): Promise<HealthResponse> => {
    const res = await fetch(`${getApiUrl()}/health`);
    if (!res.ok) throw new Error('Failed to fetch health');
    return res.json();
  },

  // Tasks
  executeTask: async (task: TaskRequest): Promise<TaskResponse> => {
    const url = `${getApiUrl()}/task/execute`;
    console.log('Executing task:', url, 'Token:', getAuthToken()?.substring(0, 20) + '...');
    const res = await fetch(url, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(task),
    });
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Task failed:', res.status, errorText);
      throw new Error(`Failed to execute task: ${res.status}`);
    }
    return res.json();
  },

  getTaskHistory: async (limit = 10): Promise<TaskResponse[]> => {
    const res = await fetch(`${getApiUrl()}/tasks/history?limit=${limit}`, {
      headers: getHeaders(false),
    });
    if (!res.ok) throw new Error('Failed to fetch task history');
    return res.json();
  },

  // Compliance
  checkCompliance: async (req: ComplianceRequest): Promise<ComplianceResponse> => {
    const res = await fetch(`${getApiUrl()}/compliance/check`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error('Failed to check compliance');
    return res.json();
  },

  // Security
  scanCode: async (req: SecurityScanRequest): Promise<ComplianceResponse> => {
    const res = await fetch(`${getApiUrl()}/security/scan`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error('Failed to scan code');
    return res.json();
  },

  // RAG
  searchKnowledge: async (req: RAGSearchRequest): Promise<RAGSearchResponse> => {
    const res = await fetch(`${getApiUrl()}/rag/search`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error('Failed to search knowledge');
    return res.json();
  },

  indexDocuments: async (collection: string, documents: string[]): Promise<{ indexed: number }> => {
    const res = await fetch(`${getApiUrl()}/rag/index`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ collection, documents }),
    });
    if (!res.ok) throw new Error('Failed to index documents');
    return res.json();
  },

  // Roles & Agents (public endpoint - no auth required)
  getRoles: async (vertical?: string): Promise<RolesResponse> => {
    const url = vertical ? `${getApiUrl()}/roles?vertical=${vertical}` : `${getApiUrl()}/roles`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch roles');
    return res.json();
  },

  getStats: async (): Promise<StatsResponse> => {
    const res = await fetch(`${getApiUrl()}/stats`, {
      headers: getHeaders(false),
    });
    if (!res.ok) throw new Error('Failed to fetch stats');
    const data = await res.json();
    // Transform backend response to frontend expected format
    return {
      tasks_today: data.orchestrator?.total_tasks ?? 0,
      success_rate: data.orchestrator?.success_rate ?? 0,
      avg_execution_time: data.uptime_seconds ? 0 : 0, // Backend doesn't track this yet
      total_agents: data.orchestrator?.available_roles?.length ?? 0,
    };
  },

  getAudit: async (): Promise<AuditEntry[]> => {
    const res = await fetch(`${getApiUrl()}/audit`, {
      headers: getHeaders(false),
    });
    if (!res.ok) throw new Error('Failed to fetch audit');
    return res.json();
  },

  // Projects
  getProjects: async (): Promise<{ projects: ProjectListItem[] }> => {
    const res = await fetch(`${getApiUrl()}/projects`, {
      headers: getHeaders(false),
    });
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  getProject: async (taskId: string): Promise<ProjectManifest> => {
    const res = await fetch(`${getApiUrl()}/projects/${taskId}`, {
      headers: getHeaders(false),
    });
    if (!res.ok) throw new Error('Failed to fetch project');
    return res.json();
  },

  getProjectFile: async (taskId: string, path: string): Promise<ProjectFile> => {
    const res = await fetch(`${getApiUrl()}/projects/${taskId}/files/${path}`, {
      headers: getHeaders(false),
    });
    if (!res.ok) throw new Error('Failed to fetch file');
    return res.json();
  },
};
