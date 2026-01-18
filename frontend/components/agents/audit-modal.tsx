'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileSearch, CheckCircle, XCircle, Clock } from 'lucide-react';
import { motion } from 'framer-motion';

interface AuditEntry {
  id: string;
  timestamp: string;
  agent: string;
  action: string;
  status: 'success' | 'failure' | 'pending';
  duration?: number;
}

interface AuditModalProps {
  entries: AuditEntry[];
}

const statusConfig = {
  success: { icon: CheckCircle, color: 'text-success', bg: 'bg-success/10' },
  failure: { icon: XCircle, color: 'text-destructive', bg: 'bg-destructive/10' },
  pending: { icon: Clock, color: 'text-warning', bg: 'bg-warning/10' },
};

export function AuditModal({ entries }: AuditModalProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <FileSearch className="h-4 w-4 mr-2" />
          View Audit Trail
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Audit Trail</DialogTitle>
        </DialogHeader>
        <ScrollArea className="h-[400px] mt-4">
          <div className="relative pl-6">
            {/* Timeline line */}
            <div className="absolute left-[7px] top-0 bottom-0 w-0.5 bg-border" />

            {/* Entries */}
            <div className="space-y-6">
              {entries.map((entry, index) => {
                const config = statusConfig[entry.status];
                const Icon = config.icon;

                return (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="relative"
                  >
                    {/* Timeline dot */}
                    <div
                      className={`absolute -left-6 w-4 h-4 rounded-full border-2 border-background ${config.bg}`}
                    >
                      <Icon className={`h-2.5 w-2.5 ${config.color} m-0.5`} />
                    </div>

                    {/* Content */}
                    <div className="bg-muted rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs font-mono">
                            {entry.agent}
                          </Badge>
                          <span className="text-sm font-medium">{entry.action}</span>
                        </div>
                        <Badge
                          variant="secondary"
                          className={`${config.bg} ${config.color} text-xs`}
                        >
                          {entry.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>{new Date(entry.timestamp).toLocaleString()}</span>
                        {entry.duration && <span>{entry.duration.toFixed(2)}s</span>}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
