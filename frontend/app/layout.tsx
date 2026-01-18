import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
});

export const metadata: Metadata = {
  title: 'Sovereign AI | Enterprise AI for Regulated Industries',
  description: 'Build compliant AI workflows with multi-agent orchestration, RAG-powered knowledge, and built-in PCI-DSS/RBI compliance.',
  keywords: ['AI', 'Enterprise', 'Compliance', 'PCI-DSS', 'FinTech', 'Multi-Agent', 'RAG'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} antialiased min-h-screen`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
