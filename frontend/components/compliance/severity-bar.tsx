'use client';

import { motion } from 'framer-motion';

interface SeverityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

interface SeverityBarProps {
  counts: SeverityCounts;
}

const severityConfig = {
  critical: { color: 'bg-destructive', label: 'Critical', textColor: 'text-destructive' },
  high: { color: 'bg-orange-500', label: 'High', textColor: 'text-orange-500' },
  medium: { color: 'bg-warning', label: 'Medium', textColor: 'text-warning' },
  low: { color: 'bg-muted-foreground', label: 'Low', textColor: 'text-muted-foreground' },
};

export function SeverityBar({ counts }: SeverityBarProps) {
  const total = counts.critical + counts.high + counts.medium + counts.low;

  return (
    <div className="p-4 rounded-lg bg-muted">
      <div className="flex items-center justify-between gap-4">
        {(Object.keys(severityConfig) as Array<keyof typeof severityConfig>).map((severity) => (
          <motion.div
            key={severity}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2"
          >
            <span
              className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${severityConfig[severity].color} text-white text-sm font-bold`}
            >
              {counts[severity]}
            </span>
            <span className={`text-sm font-medium ${severityConfig[severity].textColor}`}>
              {severityConfig[severity].label}
            </span>
          </motion.div>
        ))}
      </div>

      {total > 0 && (
        <div className="mt-4 h-2 rounded-full bg-card overflow-hidden flex">
          {counts.critical > 0 && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(counts.critical / total) * 100}%` }}
              className="h-full bg-destructive"
            />
          )}
          {counts.high > 0 && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(counts.high / total) * 100}%` }}
              className="h-full bg-orange-500"
            />
          )}
          {counts.medium > 0 && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(counts.medium / total) * 100}%` }}
              className="h-full bg-warning"
            />
          )}
          {counts.low > 0 && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(counts.low / total) * 100}%` }}
              className="h-full bg-muted-foreground"
            />
          )}
        </div>
      )}
    </div>
  );
}
