/**
 * TaxPoynt Professional Landing Page
 * =================================
 * Clean, professional landing page focused on conversion and clarity.
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { 
  TaxPoyntButton, 
  Footer,
  PROBLEMS_DATA,
  ENTERPRISE_SOLUTIONS_DATA,
  ENTERPRISE_FEATURES_DATA,
  BEFORE_AFTER_DATA,
  SERVICE_PACKAGES_DATA
} from '../design_system';

export const LandingPage: React.FC = () => {
  const router = useRouter();

  type OnboardingService = 'si' | 'app' | 'hybrid';

  const startOnboarding = (service?: OnboardingService) => {
    if (service) {
      router.push(`/onboarding?service=${service}`);
    } else {
      router.push('/onboarding');
    }
  };

  const packageServiceMap: Record<string, OnboardingService> = {
    starter: 'app',
    professional: 'si',
    enterprise: 'si',
    hybrid: 'hybrid',
  };

  const SERVICE_INTRO_CARDS: Array<{
    id: OnboardingService;
    title: string;
    description: string;
    bullets: string[];
  }> = [
    {
      id: 'si',
      title: 'System Integrator',
      description: 'Connect ERPs, CRMs, POS, and banking systems to TaxPoynt with built-in validation.',
      bullets: ['Pre-built connectors', 'Workflow automation', 'Analytics on data quality'],
    },
    {
      id: 'app',
      title: 'Access Point Provider',
      description: 'Submit compliant invoices to FIRS with automatic validation, batching, and audit trails.',
      bullets: ['FIRS sandbox & production', 'Transmission monitoring', 'Policy-aligned retention'],
    },
    {
      id: 'hybrid',
      title: 'Hybrid Suite',
      description: 'Blend SI integrations with APP transmission controls for end-to-end visibility.',
      bullets: ['Shared dashboards', 'Participant routing', 'Unified SLA tracking'],
    },
  ];

  const TRUST_POINTS: Array<{ title: string; description: string }> = [
    {
      title: 'Certified APP partner',
      description: 'Audited by FIRS with hardened controls for high-volume submissions.',
    },
    {
      title: 'Regulatory-first architecture',
      description: 'Built around NDPR, CBN, and FIRS mandates with complete audit trails.',
    },
    {
      title: 'Local 24/7 support',
      description: 'Nigeria-based success team available via phone, chat, and email day or night.',
    },
  ];

  const TESTIMONIALS: Array<{ quote: string; author: string; role: string }> = [
    {
      quote: 'TaxPoynt unified our ERP and FIRS workflows in a single quarter. Compliance is now just another automated job.',
      author: 'Adaobi Okeke',
      role: 'Head of Finance, Horizon Foods',
    },
    {
      quote: 'We moved from manual uploads to fully automated batches, with visibility our executives can trust.',
      author: 'Kunle Adeyemi',
      role: 'CTO, Skyline Retail',
    },
  ];

  return (
    <div className="min-h-screen bg-white text-slate-900">
      
      {/* Navigation */}
      <nav className="px-6 py-5 border-b border-slate-200 bg-white/95 backdrop-blur-sm shadow-sm">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img 
              src="/logo.svg" 
              alt="TaxPoynt Logo" 
              className="h-8 w-auto"
            />
            <div>
              <div className="text-xl font-bold text-blue-600" style={{ textShadow: '0 1px 2px rgba(37, 99, 235, 0.3)' }}>TaxPoynt</div>
              <div className="text-sm text-blue-500 font-medium">Secure E-invoicing Solution</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/auth/signin')}
              className="text-blue-600 hover:text-blue-800 font-semibold transition-colors duration-200"
              style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}
            >
              Sign In
            </button>
            <TaxPoyntButton
              variant="primary"
              onClick={() => startOnboarding()}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold"
            >
              Get Started
            </TaxPoyntButton>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 py-20 bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto text-center space-y-8">
          <span className="inline-flex items-center justify-center rounded-full bg-blue-50 px-4 py-1 text-sm font-semibold text-blue-700">
            FIRS Certified Access Point Provider
          </span>
          <h1 className="text-4xl md:text-5xl font-black text-slate-900 tracking-tight">
            Automate compliant e-invoicing across SI, APP, and Hybrid services in minutes—not months.
          </h1>
          <p className="mx-auto max-w-3xl text-base md:text-lg text-slate-600">
            Connect existing systems, validate invoices automatically, and transmit to FIRS with full auditability. One guided onboarding wizard adapts to the role your team selects.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <TaxPoyntButton
              variant="primary"
              size="lg"
              onClick={() => startOnboarding('hybrid')}
              className="px-10"
            >
              Start Unified Onboarding
            </TaxPoyntButton>
            <TaxPoyntButton
              variant="outline"
              size="lg"
              onClick={() => document.getElementById('service-intros')?.scrollIntoView({ behavior: 'smooth' })}
              className="px-10"
            >
              Compare Service Paths
            </TaxPoyntButton>
          </div>
        </div>
      </section>

      {/* Service comparison */}
      <section id="service-intros" className="px-6 py-16 bg-slate-50 border-b border-slate-200">
        <div className="max-w-5xl mx-auto text-center mb-12 space-y-4">
          <h2 className="text-3xl font-bold text-slate-900">Choose the journey that fits your team</h2>
          <p className="text-slate-600">Every option launches the same onboarding wizard—we simply queue the steps you are most likely to need.</p>
        </div>
        <div className="max-w-6xl mx-auto grid gap-6 md:grid-cols-3">
          {SERVICE_INTRO_CARDS.map(card => (
            <div key={card.id} className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-xl font-semibold text-slate-900">{card.title}</h3>
                <span className="text-xs font-medium uppercase text-blue-600">{card.id}</span>
              </div>
              <p className="text-sm text-slate-600 mb-4">{card.description}</p>
              <ul className="mb-6 space-y-2 text-sm text-slate-600">
                {card.bullets.map(bullet => (
                  <li key={bullet} className="flex items-start gap-2">
                    <span className="mt-1 h-2 w-2 rounded-full bg-blue-500"></span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
              <TaxPoyntButton
                variant="secondary"
                className="mt-auto"
                onClick={() => startOnboarding(card.id)}
              >
                Start as {card.title}
              </TaxPoyntButton>
            </div>
          ))}
        </div>
      </section>

      {/* Trust indicators */}
      <section className="py-16 bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12 space-y-3">
            <h2 className="text-3xl font-bold text-slate-900">Why Nigerian enterprises trust TaxPoynt</h2>
            <p className="text-slate-600">Proven compliance, local support, and infrastructure designed for multi-system teams.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {TRUST_POINTS.map((point, index) => (
              <div key={point.title} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-6 text-left shadow-sm">
                <div className="text-sm font-semibold text-blue-600 mb-2">{`0${index + 1}`}</div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{point.title}</h3>
                <p className="text-sm text-slate-600">{point.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pain points */}
      <section className="py-16 bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 space-y-6">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-bold text-slate-900">Where teams feel the pain today</h2>
            <p className="text-slate-600">Top challenges we hear from finance and integration leaders across Nigeria.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {PROBLEMS_DATA.slice(0, 3).map((problem) => (
              <div key={problem.title} className="rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm">
                <div className="text-3xl mb-4">{problem.emoji}</div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{problem.title}</h3>
                <p className="text-sm text-slate-600 mb-4">{problem.quote}</p>
                <span className="text-xs font-medium uppercase tracking-wide text-slate-500">{problem.attribution}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Enterprise outcomes */}
      <section className="py-16 bg-slate-50 border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 space-y-6">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-bold text-slate-900">How TaxPoynt changes the story</h2>
            <p className="text-slate-600">Real outcomes from enterprises who automated compliance with TaxPoynt.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {ENTERPRISE_SOLUTIONS_DATA.slice(0, 3).map((solution) => (
              <div key={solution.title} className="rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm">
                <div className="text-3xl mb-4">{solution.emoji}</div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{solution.title}</h3>
                <p className="text-sm text-slate-600 mb-4">{solution.quote}</p>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{solution.metrics}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Platform capabilities */}
      <section className="py-16 bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 space-y-6">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-bold text-slate-900">All the capability you need in one platform</h2>
            <p className="text-slate-600">A single foundation for integrations, compliance automation, and scale.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {ENTERPRISE_FEATURES_DATA.slice(0, 3).map((feature) => (
              <div key={feature.title} className="rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm">
                <div className="text-3xl mb-4">{feature.icon}</div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-600 mb-4">{feature.description}</p>
                <ul className="space-y-1 text-xs text-slate-500">
                  {feature.capabilities.slice(0, 2).map((capability) => (
                    <li key={capability}>• {capability}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Before and after */}
      <section className="py-16 bg-slate-50 border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 space-y-6">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-bold text-slate-900">From manual headache to automated confidence</h2>
            <p className="text-slate-600">Quantifiable improvements once compliance becomes a first-class system.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            {BEFORE_AFTER_DATA.slice(0, 2).map((item) => (
              <div key={item.metric} className="rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{item.metric}</h3>
                <div className="grid grid-cols-2 gap-4 text-sm text-slate-600">
                  <div>
                    <span className="block text-xs font-medium uppercase text-slate-500 mb-1">Before</span>
                    <div className="text-slate-900 font-semibold">{item.before.value}</div>
                    <p className="mt-1 text-xs">{item.before.description}</p>
                  </div>
                  <div>
                    <span className="block text-xs font-medium uppercase text-emerald-600 mb-1">After</span>
                    <div className="text-slate-900 font-semibold">{item.after.value}</div>
                    <p className="mt-1 text-xs">{item.after.description}</p>
                  </div>
                </div>
                <div className="mt-4 text-xs font-medium uppercase text-blue-600">{item.improvement}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-16 bg-white border-b border-slate-200" id="pricing">
        <div className="max-w-6xl mx-auto px-6 space-y-6">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-bold text-slate-900">Pricing built for every stage</h2>
            <p className="text-slate-600">Select a plan to launch onboarding with the right defaults for your team.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {SERVICE_PACKAGES_DATA.map((pkg) => (
              <div key={pkg.id} className="rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900 mb-1">{pkg.name}</h3>
                <p className="text-sm text-slate-600 mb-4">{pkg.description}</p>
                <div className="text-2xl font-bold text-slate-900 mb-1">₦{pkg.price.monthly.toLocaleString()}</div>
                <div className="text-xs text-slate-500 mb-4">per month, billed annually</div>
                <ul className="space-y-1 text-sm text-slate-600 mb-6">
                  {pkg.features.slice(0, 3).map((feature) => (
                    <li key={feature}>• {feature}</li>
                  ))}
                </ul>
                <TaxPoyntButton
                  variant="primary"
                  className="w-full"
                  onClick={() => startOnboarding(packageServiceMap[pkg.id] ?? 'app')}
                >
                  Start as {pkg.name}
                </TaxPoyntButton>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-16 bg-slate-50 border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-6 space-y-8 text-center">
          <h2 className="text-3xl font-bold text-slate-900">Trusted by finance and technology leaders</h2>
          <div className="space-y-6">
            {TESTIMONIALS.map((item) => (
              <blockquote key={item.author} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <p className="text-base text-slate-700 mb-4">“{item.quote}”</p>
                <footer className="text-sm font-medium text-slate-500">{item.author} — {item.role}</footer>
              </blockquote>
            ))}
          </div>
        </div>
      </section>

      {/* Final call to action */}
      <section className="py-16 bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-6 text-center space-y-6">
          <h2 className="text-3xl font-bold text-slate-900">Ready to automate compliance?</h2>
          <p className="text-slate-600">Launch onboarding to get started or talk to our team about enterprise requirements.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <TaxPoyntButton
              variant="primary"
              size="lg"
              className="px-10"
              onClick={() => startOnboarding('hybrid')}
            >
              Start Unified Onboarding
            </TaxPoyntButton>
            <TaxPoyntButton
              variant="outline"
              size="lg"
              className="px-10"
              onClick={() => router.push('/contact')}
            >
              Talk to Sales
            </TaxPoyntButton>
          </div>
        </div>
      </section>

      {/* Footer */}
      <Footer variant="landing" />

    </div>
  );
};
