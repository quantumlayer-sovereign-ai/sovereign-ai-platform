'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { CodeEditor, SeverityBar, ScanResults } from '@/components/compliance';
import { useComplianceCheck } from '@/lib/hooks';
import { useToast } from '@/hooks/use-toast';
import { Shield, Download, Copy, Check, Loader2 } from 'lucide-react';
import type { ComplianceResponse, ComplianceIssue } from '@/lib/api';

const sampleCode = `# Example code with security issues
password = "secret123"
card = "4111111111111111"
cvv = "123"

def get_user(id):
    query = f"SELECT * FROM users WHERE id={id}"
    return execute_query(query)

api_key = "sk_live_abc123xyz789"
`;

const standards = [
  { id: 'PCI-DSS', label: 'PCI-DSS' },
  { id: 'RBI', label: 'RBI Guidelines' },
  { id: 'DPDP', label: 'DPDP Act' },
  { id: 'SEBI', label: 'SEBI' },
];

export default function CompliancePage() {
  const [code, setCode] = useState(sampleCode);
  const [selectedStandards, setSelectedStandards] = useState(['PCI-DSS', 'RBI']);
  const [scanResults, setScanResults] = useState<ComplianceResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const complianceCheck = useComplianceCheck();

  const toggleStandard = (id: string) => {
    setSelectedStandards((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const handleScan = async () => {
    try {
      const result = await complianceCheck.mutateAsync({
        code,
        standards: selectedStandards,
      });
      setScanResults(result);
      toast({
        title: result.passed ? 'Scan Complete' : 'Issues Found',
        description: result.passed
          ? 'No compliance issues detected'
          : `Found ${Object.values(result.summary).reduce((a, b) => a + b, 0)} issues`,
        variant: result.passed ? 'default' : 'destructive',
      });
    } catch {
      // Show demo results if API fails
      const demoResults = {
        passed: false,
        issues: [
          {
            severity: 'critical' as const,
            rule_name: 'PCI-3.4',
            description: 'Cardholder Data Protection',
            line_number: 3,
            remediation: 'Use tokenization. Never store full card numbers.',
          },
          {
            severity: 'critical' as const,
            rule_name: 'PCI-3.2',
            description: 'No Storage of Sensitive Auth Data',
            line_number: 4,
            remediation: 'Never store CVV/CVC. Use payment gateway.',
          },
          {
            severity: 'critical' as const,
            rule_name: 'SEC-001',
            description: 'Hardcoded Password Detected',
            line_number: 2,
            remediation: 'Use environment variables or secret management.',
          },
          {
            severity: 'high' as const,
            rule_name: 'PCI-6.5.1',
            description: 'SQL Injection Prevention',
            line_number: 7,
            remediation: 'Use parameterized queries or ORM.',
          },
          {
            severity: 'high' as const,
            rule_name: 'SEC-002',
            description: 'Exposed API Key',
            line_number: 10,
            remediation: 'Store API keys in environment variables.',
          },
          {
            severity: 'high' as const,
            rule_name: 'RBI-DPR-1',
            description: 'Sensitive Data Logging Risk',
            line_number: 3,
            remediation: 'Implement data masking for logs.',
          },
          {
            severity: 'medium' as const,
            rule_name: 'SEC-003',
            description: 'Weak Password Pattern',
            line_number: 2,
            remediation: 'Enforce strong password policy.',
          },
        ],
        summary: {
          critical: 3,
          high: 3,
          medium: 1,
          low: 0,
        },
      };
      setScanResults(demoResults);
      toast({
        title: 'Demo Mode',
        description: 'Showing demo scan results (API not connected)',
      });
    }
  };

  const handleCopyRecommendations = () => {
    if (scanResults?.issues) {
      const text = scanResults.issues
        .map((i: ComplianceIssue) => `[${i.severity.toUpperCase()}] ${i.rule_name}: ${i.remediation || i.description}`)
        .join('\n');
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadReport = () => {
    if (scanResults) {
      const report = {
        timestamp: new Date().toISOString(),
        standards: selectedStandards,
        passed: scanResults.passed,
        summary: scanResults.summary,
        issues: scanResults.issues,
      };
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `compliance-report-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="mx-auto max-w-container px-6 py-8">
      <div className="mb-8">
        <h1 className="text-h2 text-foreground mb-2">Compliance Scanner</h1>
        <p className="text-muted-foreground">
          Scan your code for security vulnerabilities and regulatory compliance issues
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Code Editor Section */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="text-lg">Code Input</CardTitle>
              <div className="flex items-center gap-3">
                {standards.map((standard) => (
                  <div key={standard.id} className="flex items-center gap-2">
                    <Checkbox
                      id={standard.id}
                      checked={selectedStandards.includes(standard.id)}
                      onCheckedChange={() => toggleStandard(standard.id)}
                    />
                    <label
                      htmlFor={standard.id}
                      className="text-sm cursor-pointer"
                    >
                      {standard.label}
                    </label>
                  </div>
                ))}
              </div>
            </CardHeader>
            <CardContent>
              <CodeEditor value={code} onChange={setCode} language="python" />
              <div className="mt-4">
                <Button
                  onClick={handleScan}
                  disabled={complianceCheck.isPending || !code.trim()}
                  className="w-full sm:w-auto"
                >
                  {complianceCheck.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Scanning...
                    </>
                  ) : (
                    <>
                      <Shield className="mr-2 h-4 w-4" />
                      Scan Code
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Scan Results */}
          {scanResults && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">
                  Scan Results
                  <span
                    className={`ml-2 text-sm font-normal ${
                      scanResults.passed ? 'text-success' : 'text-destructive'
                    }`}
                  >
                    {scanResults.passed
                      ? 'PASSED'
                      : `FAILED (${scanResults.issues.length} issues)`}
                  </span>
                </h2>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyRecommendations}
                    disabled={!scanResults.issues?.length}
                  >
                    {copied ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDownloadReport}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <SeverityBar counts={scanResults.summary} />
              <ScanResults issues={scanResults.issues} />
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">About Compliance Scanning</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-4">
              <p>
                Our compliance scanner checks your code against industry standards
                and regulatory requirements.
              </p>
              <div>
                <h4 className="font-medium text-foreground mb-2">Supported Standards:</h4>
                <ul className="list-disc list-inside space-y-1">
                  <li>PCI-DSS v4.0 - Payment Card Security</li>
                  <li>RBI Guidelines - Reserve Bank of India</li>
                  <li>DPDP Act - Data Protection</li>
                  <li>SEBI - Securities Regulations</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-foreground mb-2">What we check:</h4>
                <ul className="list-disc list-inside space-y-1">
                  <li>Hardcoded credentials</li>
                  <li>SQL injection vulnerabilities</li>
                  <li>Sensitive data exposure</li>
                  <li>Encryption requirements</li>
                  <li>Logging compliance</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
