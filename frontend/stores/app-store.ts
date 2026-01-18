import { create } from 'zustand';

export type AgentState = 'idle' | 'working' | 'done' | 'error';

export interface ActiveAgent {
  id: string;
  role: string;
  state: AgentState;
  task?: string;
  startedAt?: number;
}

export interface TaskExecution {
  id: string;
  task: string;
  vertical: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  agents: ActiveAgent[];
  output?: string;
  complianceStatus?: Record<string, { passed: boolean; issues: string[] }>;
  startedAt: number;
  completedAt?: number;
}

interface AppState {
  // Theme
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;

  // Current task execution
  currentTask: TaskExecution | null;
  setCurrentTask: (task: TaskExecution | null) => void;
  updateAgent: (agentId: string, updates: Partial<ActiveAgent>) => void;

  // Task history (local cache)
  taskHistory: TaskExecution[];
  addToHistory: (task: TaskExecution) => void;

  // Selected vertical
  selectedVertical: string;
  setSelectedVertical: (vertical: string) => void;

  // Compliance standards selection
  selectedStandards: string[];
  toggleStandard: (standard: string) => void;
  setStandards: (standards: string[]) => void;

  // RAG toggle
  useRAG: boolean;
  setUseRAG: (use: boolean) => void;

  // UI state
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Theme
  theme: 'light',
  setTheme: (theme) => set({ theme }),
  toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),

  // Current task
  currentTask: null,
  setCurrentTask: (task) => set({ currentTask: task }),
  updateAgent: (agentId, updates) =>
    set((state) => {
      if (!state.currentTask) return state;
      return {
        currentTask: {
          ...state.currentTask,
          agents: state.currentTask.agents.map((agent) =>
            agent.id === agentId ? { ...agent, ...updates } : agent
          ),
        },
      };
    }),

  // Task history
  taskHistory: [],
  addToHistory: (task) =>
    set((state) => ({
      taskHistory: [task, ...state.taskHistory].slice(0, 50),
    })),

  // Selected vertical
  selectedVertical: 'fintech',
  setSelectedVertical: (vertical) => set({ selectedVertical: vertical }),

  // Compliance standards
  selectedStandards: ['PCI-DSS'],
  toggleStandard: (standard) =>
    set((state) => ({
      selectedStandards: state.selectedStandards.includes(standard)
        ? state.selectedStandards.filter((s) => s !== standard)
        : [...state.selectedStandards, standard],
    })),
  setStandards: (standards) => set({ selectedStandards: standards }),

  // RAG
  useRAG: true,
  setUseRAG: (use) => set({ useRAG: use }),

  // UI
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
