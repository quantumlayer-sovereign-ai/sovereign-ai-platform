'use client';

import { useMutation, useQuery } from '@tanstack/react-query';
import { api, TaskRequest, TaskResponse } from '@/lib/api';

export function useExecuteTask() {
  return useMutation<TaskResponse, Error, TaskRequest>({
    mutationFn: api.executeTask,
  });
}

export function useTaskHistory(limit = 10) {
  return useQuery<TaskResponse[]>({
    queryKey: ['taskHistory', limit],
    queryFn: () => api.getTaskHistory(limit),
    refetchInterval: 30000,
  });
}
