'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface PoolGaugeProps {
  active: number;
  total: number;
}

export function PoolGauge({ active, total }: PoolGaugeProps) {
  const percentage = (active / total) * 100;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Agent Pool</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Gauge bar */}
          <div className="relative h-4 rounded-full bg-muted overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${percentage}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-primary to-success"
            />
            {/* Markers */}
            {[25, 50, 75].map((mark) => (
              <div
                key={mark}
                className="absolute top-0 bottom-0 w-px bg-background/50"
                style={{ left: `${mark}%` }}
              />
            ))}
          </div>

          {/* Stats */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              <span className="font-bold text-foreground">{active}</span>/{total} agents active
            </span>
            <span className="font-medium text-primary">{percentage.toFixed(0)}%</span>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-6 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-primary" />
              Active
            </div>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-muted" />
              Available
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
