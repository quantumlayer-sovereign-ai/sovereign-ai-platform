'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useTheme } from '@/components/providers';
import { Sparkles, LayoutDashboard, Shield, BookOpen, Users, Settings, Moon, Sun } from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Tasks', icon: LayoutDashboard },
  { href: '/agents', label: 'Agents', icon: Users },
  { href: '/compliance', label: 'Compliance', icon: Shield },
  { href: '/knowledge', label: 'Knowledge', icon: BookOpen },
];

export function Navigation() {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-card/80 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-container items-center justify-between px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 text-foreground hover:opacity-80 transition-opacity">
          <Sparkles className="h-6 w-6 text-primary" />
          <span className="font-semibold text-lg">Sovereign AI</span>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Right side actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="h-9 w-9"
          >
            {theme === 'light' ? (
              <Moon className="h-4 w-4" />
            ) : (
              <Sun className="h-4 w-4" />
            )}
          </Button>
          <Button variant="ghost" size="icon" className="h-9 w-9">
            <Settings className="h-4 w-4" />
          </Button>
          <div className="hidden sm:flex items-center gap-2 ml-2 px-3 py-1.5 rounded-md bg-success/10 text-success text-xs font-medium">
            <span className="h-2 w-2 rounded-full bg-success animate-pulse-dot" />
            Model: 7B
          </div>
        </div>
      </div>
    </header>
  );
}

export function LandingNavigation() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 w-full bg-transparent">
      <div className="mx-auto flex h-16 max-w-container items-center justify-between px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 text-white hover:opacity-80 transition-opacity">
          <Sparkles className="h-6 w-6" />
          <span className="font-semibold text-lg">Sovereign AI</span>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-6">
          <Link href="#features" className="text-white/80 hover:text-white text-sm font-medium transition-colors">
            Features
          </Link>
          <Link href="#pricing" className="text-white/80 hover:text-white text-sm font-medium transition-colors">
            Pricing
          </Link>
          <Link href="#docs" className="text-white/80 hover:text-white text-sm font-medium transition-colors">
            Docs
          </Link>
        </nav>

        {/* Right side actions */}
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="h-9 w-9 text-white hover:bg-white/10"
          >
            {theme === 'light' ? (
              <Moon className="h-4 w-4" />
            ) : (
              <Sun className="h-4 w-4" />
            )}
          </Button>
          <Link href="/dashboard">
            <Button variant="secondary" className="bg-white text-primary hover:bg-white/90">
              Login
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
