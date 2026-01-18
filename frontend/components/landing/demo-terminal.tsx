'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const terminalLines = [
  { text: '> Executing task: "Build secure payment API"', type: 'command' },
  { text: '✓ Spawned: fintech_architect, fintech_coder, security', type: 'success', delay: 800 },
  { text: '✓ RAG: Retrieved 5 PCI-DSS compliance docs', type: 'success', delay: 1200 },
  { text: '  → Building event-driven payment processor...', type: 'info', delay: 1600 },
  { text: '  → Implementing TLS 1.3 encryption...', type: 'info', delay: 2000 },
  { text: '  → Running compliance validation...', type: 'info', delay: 2400 },
  { text: '✓ Compliance: PCI-DSS PASSED', type: 'success', delay: 2800 },
  { text: '✓ Compliance: RBI Guidelines PASSED', type: 'success', delay: 3000 },
  { text: '⏱ Completed in 23.4s', type: 'complete', delay: 3400 },
];

export function DemoTerminal() {
  const [visibleLines, setVisibleLines] = useState<number>(0);
  const [isTyping, setIsTyping] = useState(true);
  const shouldRestart = visibleLines === 0;

  useEffect(() => {
    if (!shouldRestart) return;

    const timers: NodeJS.Timeout[] = [];

    terminalLines.forEach((line, index) => {
      const timer = setTimeout(() => {
        setVisibleLines((prev) => Math.max(prev, index + 1));
        if (index === terminalLines.length - 1) {
          setIsTyping(false);
          // Reset after a pause
          setTimeout(() => {
            setVisibleLines(0);
            setIsTyping(true);
          }, 3000);
        }
      }, line.delay || index * 400);
      timers.push(timer);
    });

    return () => timers.forEach(clearTimeout);
  }, [shouldRestart]);

  const getLineColor = (type: string) => {
    switch (type) {
      case 'command':
        return 'text-white';
      case 'success':
        return 'text-emerald-400';
      case 'info':
        return 'text-blue-300';
      case 'complete':
        return 'text-amber-400';
      default:
        return 'text-gray-300';
    }
  };

  return (
    <div className="relative mx-auto max-w-3xl">
      {/* Terminal window */}
      <div className="rounded-lg overflow-hidden shadow-2xl border border-white/10">
        {/* Title bar */}
        <div className="flex items-center gap-2 px-4 py-3 bg-gray-800/80">
          <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <div className="w-3 h-3 rounded-full bg-green-500" />
          </div>
          <span className="ml-4 text-sm text-gray-400 font-mono">sovereign-ai ~ task</span>
        </div>

        {/* Terminal content */}
        <div className="bg-gray-900/90 backdrop-blur-sm p-4 min-h-[280px] font-mono text-sm">
          <AnimatePresence>
            {terminalLines.slice(0, visibleLines).map((line, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className={`${getLineColor(line.type)} ${line.type === 'info' ? 'ml-2' : ''}`}
              >
                {line.text}
              </motion.div>
            ))}
          </AnimatePresence>
          {isTyping && (
            <span className="inline-block w-2 h-5 bg-white ml-1 animate-blink" />
          )}
        </div>
      </div>

      {/* Glow effect */}
      <div className="absolute -inset-4 bg-primary/20 blur-3xl -z-10 rounded-3xl" />
    </div>
  );
}
