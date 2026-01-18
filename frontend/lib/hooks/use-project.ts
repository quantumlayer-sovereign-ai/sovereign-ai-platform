'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useProject(taskId: string) {
  return useQuery({
    queryKey: ['project', taskId],
    queryFn: () => api.getProject(taskId),
    enabled: !!taskId,
  });
}

export function useProjectFile(taskId: string, path: string) {
  return useQuery({
    queryKey: ['project', taskId, 'file', path],
    queryFn: () => api.getProjectFile(taskId, path),
    enabled: !!taskId && !!path,
  });
}

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: api.getProjects,
  });
}
