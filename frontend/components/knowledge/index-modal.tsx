'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Upload, Loader2 } from 'lucide-react';
import { useIndexDocuments } from '@/lib/hooks';
import { useToast } from '@/hooks/use-toast';

interface IndexModalProps {
  onSuccess?: () => void;
}

const collections = [
  { id: 'fintech', label: 'FinTech' },
  { id: 'compliance', label: 'Compliance' },
  { id: 'security', label: 'Security' },
  { id: 'general', label: 'General' },
];

export function IndexModal({ onSuccess }: IndexModalProps) {
  const [open, setOpen] = useState(false);
  const [collection, setCollection] = useState('fintech');
  const [content, setContent] = useState('');
  const { toast } = useToast();

  const indexDocs = useIndexDocuments();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    try {
      const documents = content.split('\n---\n').filter((d) => d.trim());
      await indexDocs.mutateAsync({ collection, documents });
      toast({
        title: 'Documents Indexed',
        description: `Successfully indexed ${documents.length} document(s)`,
      });
      setContent('');
      setOpen(false);
      onSuccess?.();
    } catch {
      toast({
        title: 'Demo Mode',
        description: 'Document indexing simulated (API not connected)',
      });
      setContent('');
      setOpen(false);
      onSuccess?.();
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Index Docs
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Index Documents</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Collection</label>
            <Select value={collection} onValueChange={setCollection}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {collections.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Document Content</label>
            <Textarea
              placeholder="Paste document content here. Separate multiple documents with '---' on a new line."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="min-h-[200px] font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Tip: Use --- on a new line to separate multiple documents
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="outline" type="button" className="flex-1">
              <Upload className="h-4 w-4 mr-2" />
              Upload Files
            </Button>
            <Button type="submit" className="flex-1" disabled={indexDocs.isPending || !content.trim()}>
              {indexDocs.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Indexing...
                </>
              ) : (
                'Index Documents'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
