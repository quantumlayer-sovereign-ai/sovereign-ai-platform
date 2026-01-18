'use client';

import { useQuery } from '@tanstack/react-query';
import { api, HealthResponse } from '@/lib/api';

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 10000, // Refetch every 10 seconds
    retry: 1,
  });
}
