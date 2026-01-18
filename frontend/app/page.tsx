import { LandingNavigation } from '@/components/navigation';
import { Hero, Features, Stats, CTA, Footer } from '@/components/landing';

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <LandingNavigation />
      <Hero />
      <Features />
      <Stats />
      <CTA />
      <Footer />
    </main>
  );
}
