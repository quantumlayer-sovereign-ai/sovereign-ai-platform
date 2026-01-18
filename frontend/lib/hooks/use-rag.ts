'use client';

import { useMutation } from '@tanstack/react-query';
import { api, RAGSearchRequest, RAGSearchResponse } from '@/lib/api';

export function useRAGSearch() {
  return useMutation<RAGSearchResponse, Error, RAGSearchRequest>({
    mutationFn: api.searchKnowledge,
  });
}

export function useIndexDocuments() {
  return useMutation<{ indexed: number }, Error, { collection: string; documents: string[] }>({
    mutationFn: ({ collection, documents }) => api.indexDocuments(collection, documents),
  });
}
