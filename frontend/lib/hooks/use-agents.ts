'use client';

import { useQuery } from '@tanstack/react-query';
import { api, RolesResponse, StatsResponse, AuditEntry } from '@/lib/api';

export function useRoles(vertical?: string) {
  return useQuery<RolesResponse>({
    queryKey: ['roles', vertical],
    queryFn: () => api.getRoles(vertical),
  });
}

export function useStats() {
  return useQuery<StatsResponse>({
    queryKey: ['stats'],
    queryFn: api.getStats,
    refetchInterval: 15000,
  });
}

export function useAudit() {
  return useQuery<AuditEntry[]>({
    queryKey: ['audit'],
    queryFn: api.getAudit,
    refetchInterval: 5000,
  });
}
