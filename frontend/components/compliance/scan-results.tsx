'use client';

import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, AlertTriangle, Info, ChevronRight } from 'lucide-react';
import { ComplianceIssue } from '@/lib/api';

interface ScanResultsProps {
  issues: ComplianceIssue[];
}

const severityIcons = {
  critical: AlertCircle,
  high: AlertTriangle,
  medium: AlertTriangle,
  low: Info,
};

const severityColors = {
  critical: 'text-destructive bg-destructive/10 border-destructive/30',
  high: 'text-orange-500 bg-orange-500/10 border-orange-500/30',
  medium: 'text-warning bg-warning/10 border-warning/30',
  low: 'text-muted-foreground bg-muted border-border',
};

const severityLabels = {
  critical: 'CRITICAL',
  high: 'HIGH',
  medium: 'MEDIUM',
  low: 'LOW',
};

export function ScanResults({ issues }: ScanResultsProps) {
  if (issues.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <div className="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center mb-4">
            <svg
              className="w-8 h-8 text-success"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-1">All Clear!</h3>
          <p className="text-sm text-muted-foreground">No compliance issues detected</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {issues.map((issue, index) => {
        const Icon = severityIcons[issue.severity];
        const colors = severityColors[issue.severity];
        // Support both old and new field names for compatibility
        const ruleName = issue.rule_name || issue.rule_id || '';
        const description = issue.description || issue.message || '';
        const lineNumber = issue.line_number || issue.line;
        const remediation = issue.remediation || issue.recommendation;

        return (
          <motion.div
            key={`${ruleName}-${index}`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className={`border ${colors}`}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${colors.split(' ')[1]}`}>
                    <Icon className={`h-5 w-5 ${colors.split(' ')[0]}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge
                        variant="outline"
                        className={`text-xs font-bold ${colors}`}
                      >
                        {severityLabels[issue.severity]}
                      </Badge>
                      <span className="text-sm font-medium text-foreground">
                        {ruleName}
                      </span>
                    </div>

                    <p className="text-sm text-muted-foreground mb-2">
                      {description}
                    </p>

                    {issue.evidence && (
                      <div className="mt-2 text-sm font-mono text-muted-foreground bg-muted rounded px-2 py-1 inline-block">
                        {issue.evidence}
                      </div>
                    )}

                    {lineNumber && (
                      <div className="mt-2 text-sm font-mono text-muted-foreground bg-muted rounded px-2 py-1 inline-block">
                        Line {lineNumber}
                      </div>
                    )}

                    {remediation && (
                      <div className="mt-2 flex items-start gap-2 text-sm">
                        <ChevronRight className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
                        <span className="text-muted-foreground">{remediation}</span>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
