'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SearchBar, ResultsList, IndexModal } from '@/components/knowledge';
import { useRAGSearch } from '@/lib/hooks';
import { useToast } from '@/hooks/use-toast';
import { Database, FileText, Folder } from 'lucide-react';
import type { RAGResult } from '@/lib/api';

export default function KnowledgePage() {
  const [query, setQuery] = useState('');
  const [collection, setCollection] = useState('all');
  const [results, setResults] = useState<RAGResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const { toast } = useToast();

  const ragSearch = useRAGSearch();

  const handleSearch = async () => {
    if (!query.trim()) return;

    try {
      const result = await ragSearch.mutateAsync({
        query,
        collection: collection === 'all' ? undefined : collection,
        top_k: 10,
      });
      setResults(result.results);
      setHasSearched(true);
    } catch {
      // Show demo results if API fails
      const demoResults = [
        {
          content: `The Payment Card Industry Data Security Standard (PCI-DSS) is a set of security standards designed to ensure that all companies that accept, process, store or transmit credit card information maintain a secure environment. The standard was created by major credit card companies including Visa, MasterCard, American Express, and Discover.`,
          metadata: {
            source: 'pci_dss_requirements.md',
            section: 'Introduction',
          },
          relevance_score: 0.688,
        },
        {
          content: `Requirement 4: Protect Cardholder Data During Transmission Over Open, Public Networks. Use TLS 1.2 or higher for all transmissions of cardholder data over public networks. The use of SSL and early TLS is prohibited.`,
          metadata: {
            source: 'pci_dss_requirements.md',
            section: 'Requirement 4',
          },
          relevance_score: 0.419,
        },
        {
          content: `Encryption at rest is required for all stored cardholder data. Strong cryptography with associated key-management processes and procedures must be implemented to protect cardholder data during storage.`,
          metadata: {
            source: 'encryption_guidelines.md',
            section: 'Data At Rest',
          },
          relevance_score: 0.356,
        },
      ];
      setResults(demoResults);
      setHasSearched(true);
      toast({
        title: 'Demo Mode',
        description: 'Showing demo search results (API not connected)',
      });
    }
  };

  const handleUseInTask = (_content: string) => {
    // In a real implementation, this would navigate to dashboard with pre-filled context
    toast({
      title: 'Context Added',
      description: 'Document added to task context',
    });
  };

  return (
    <div className="mx-auto max-w-container px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-h2 text-foreground mb-2">Knowledge Base</h1>
          <p className="text-muted-foreground">
            Search and manage your RAG-indexed documents
          </p>
        </div>
        <IndexModal />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <div className="p-3 rounded-lg bg-primary/10">
              <Database className="h-6 w-6 text-primary" />
            </div>
            <div>
              <div className="text-2xl font-bold">1,247</div>
              <div className="text-sm text-muted-foreground">Chunks Indexed</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <div className="p-3 rounded-lg bg-success/10">
              <FileText className="h-6 w-6 text-success" />
            </div>
            <div>
              <div className="text-2xl font-bold">23</div>
              <div className="text-sm text-muted-foreground">Documents</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <div className="p-3 rounded-lg bg-info/10">
              <Folder className="h-6 w-6 text-info" />
            </div>
            <div>
              <div className="text-2xl font-bold">4</div>
              <div className="text-sm text-muted-foreground">Collections</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search Section */}
      <Card className="mb-8">
        <CardContent className="p-6">
          <SearchBar
            query={query}
            onQueryChange={setQuery}
            collection={collection}
            onCollectionChange={setCollection}
            onSearch={handleSearch}
            isLoading={ragSearch.isPending}
          />
        </CardContent>
      </Card>

      {/* Results */}
      {hasSearched && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-4">
            Search Results
            {results.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {results.length} results
              </Badge>
            )}
          </h2>
          <ResultsList results={results} query={query} onUseInTask={handleUseInTask} />
        </div>
      )}

      {/* Recent Documents (when no search) */}
      {!hasSearched && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { name: 'pci_dss_requirements.md', collection: 'Compliance', chunks: 45 },
                { name: 'rbi_guidelines.md', collection: 'Compliance', chunks: 32 },
                { name: 'payment_api_spec.md', collection: 'FinTech', chunks: 28 },
                { name: 'security_best_practices.md', collection: 'Security', chunks: 56 },
                { name: 'encryption_standards.md', collection: 'Security', chunks: 21 },
              ].map((doc, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted hover:bg-muted/80 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <div className="font-medium text-sm">{doc.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {doc.chunks} chunks indexed
                      </div>
                    </div>
                  </div>
                  <Badge variant="outline">{doc.collection}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
