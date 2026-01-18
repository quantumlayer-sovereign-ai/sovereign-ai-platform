'use client';

import { useMutation } from '@tanstack/react-query';
import { api, ComplianceRequest, ComplianceResponse, SecurityScanRequest } from '@/lib/api';

export function useComplianceCheck() {
  return useMutation<ComplianceResponse, Error, ComplianceRequest>({
    mutationFn: api.checkCompliance,
  });
}

export function useSecurityScan() {
  return useMutation<ComplianceResponse, Error, SecurityScanRequest>({
    mutationFn: api.scanCode,
  });
}
