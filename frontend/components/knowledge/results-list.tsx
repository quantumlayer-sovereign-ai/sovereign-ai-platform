'use client';

import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FileText, ArrowRight, ExternalLink } from 'lucide-react';

interface RAGResult {
  content: string;
  metadata: Record<string, string>;
  relevance_score: number;
}

interface ResultsListProps {
  results: RAGResult[];
  query: string;
  onUseInTask?: (content: string) => void;
}

export function ResultsList({ results, query, onUseInTask }: ResultsListProps) {
  if (results.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <FileText className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-1">No results found</h3>
          <p className="text-sm text-muted-foreground text-center max-w-sm">
            Try adjusting your search query or selecting a different collection
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        Found {results.length} result{results.length !== 1 ? 's' : ''} for &quot;{query}&quot;
      </div>

      {results.map((result, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <Card className="hover:border-primary/30 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  <div className="p-2 rounded-lg bg-primary/10 flex-shrink-0">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-foreground truncate">
                        {result.metadata.source || result.metadata.filename || 'Document'}
                      </h4>
                      <Badge variant="secondary" className="text-xs">
                        {(result.relevance_score * 100).toFixed(1)}% match
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {result.content}
                    </p>
                    {result.metadata.section && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        Section: {result.metadata.section}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex flex-col gap-2 flex-shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onUseInTask?.(result.content)}
                  >
                    <ArrowRight className="h-3 w-3 mr-1" />
                    Use in Task
                  </Button>
                  <Button variant="ghost" size="sm">
                    <ExternalLink className="h-3 w-3 mr-1" />
                    View Full
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
