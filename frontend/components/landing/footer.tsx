'use client';

import Link from 'next/link';
import { Sparkles } from 'lucide-react';

export function Footer() {
  return (
    <footer className="py-12 bg-card border-t border-border">
      <div className="mx-auto max-w-container px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2 text-foreground">
            <Sparkles className="h-5 w-5 text-primary" />
            <span className="font-semibold">Sovereign AI</span>
          </div>

          <nav className="flex items-center gap-6">
            <Link href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Dashboard
            </Link>
            <Link href="/compliance" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Compliance
            </Link>
            <Link href="/knowledge" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Knowledge
            </Link>
            <Link href="/agents" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Agents
            </Link>
          </nav>

          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} Sovereign AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
