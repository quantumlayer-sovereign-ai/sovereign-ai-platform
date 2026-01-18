'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Play, Loader2 } from 'lucide-react';
import { useAppStore } from '@/stores/app-store';

interface TaskInputProps {
  onExecute: (task: string) => void;
  isLoading?: boolean;
}

const complianceStandards = [
  { id: 'PCI-DSS', label: 'PCI-DSS' },
  { id: 'RBI', label: 'RBI Guidelines' },
  { id: 'DPDP', label: 'DPDP Act' },
];

const verticals = [
  { id: 'fintech', label: 'FinTech' },
  { id: 'healthcare', label: 'Healthcare' },
  { id: 'general', label: 'General' },
];

export function TaskInput({ onExecute, isLoading }: TaskInputProps) {
  const [task, setTask] = useState('');
  const {
    selectedVertical,
    setSelectedVertical,
    selectedStandards,
    toggleStandard,
    useRAG,
    setUseRAG,
  } = useAppStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (task.trim()) {
      onExecute(task);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="text-lg">Task Execution</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Textarea
            placeholder="Describe your task... (e.g., Build a secure payment API with PCI-DSS compliance)"
            value={task}
            onChange={(e) => setTask(e.target.value)}
            className="min-h-[100px] resize-none"
          />

          <div className="flex flex-wrap items-center gap-4">
            {/* Vertical Selector */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Vertical:</span>
              <Select value={selectedVertical} onValueChange={setSelectedVertical}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {verticals.map((v) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* RAG Toggle */}
            <div className="flex items-center gap-2">
              <Checkbox
                id="rag"
                checked={useRAG}
                onCheckedChange={(checked) => setUseRAG(checked as boolean)}
              />
              <label htmlFor="rag" className="text-sm text-muted-foreground cursor-pointer">
                Use RAG
              </label>
            </div>
          </div>

          {/* Compliance Standards */}
          <div className="flex flex-wrap items-center gap-4">
            <span className="text-sm text-muted-foreground">Compliance:</span>
            {complianceStandards.map((standard) => (
              <div key={standard.id} className="flex items-center gap-2">
                <Checkbox
                  id={standard.id}
                  checked={selectedStandards.includes(standard.id)}
                  onCheckedChange={() => toggleStandard(standard.id)}
                />
                <label htmlFor={standard.id} className="text-sm cursor-pointer">
                  {standard.label}
                </label>
              </div>
            ))}
          </div>

          <Button
            type="submit"
            disabled={!task.trim() || isLoading}
            className="w-full sm:w-auto"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Executing...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Execute Task
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
