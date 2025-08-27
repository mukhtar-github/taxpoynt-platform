/**
 * Hero Section Component
 * ======================
 * Extracted from LandingPage.tsx - Premium enterprise hero section
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { TaxPoyntButton, HeroCTAButton } from '../../design_system';
import { GRADIENT_PATTERNS, TYPOGRAPHY_STYLES, getSectionBackground, combineStyles } from '../../design_system/style-utilities';

export interface HeroSectionProps {
  className?: string;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ className = '' }) => {
  const router = useRouter();

  const heroBackgroundStyle = combineStyles(
    GRADIENT_PATTERNS.heroBackground,
    {
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center'
    }
  );

  const badgeStyle = combineStyles(
    GRADIENT_PATTERNS.section.indigo,
    {
      backdropFilter: 'blur(10px)'
    }
  );

  const impactBadgeStyle = combineStyles(
    GRADIENT_PATTERNS.section.purple
  );

  const heroHeadlineStyle = combineStyles(
    TYPOGRAPHY_STYLES.heroHeadline,
    {
      textShadow: '0 4px 8px rgba(0,0,0,0.1)'
    }
  );

  const ctaCardStyle = combineStyles(
    {
      background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(238,242,255,0.9) 50%, rgba(255,255,255,0.95) 100%)',
      backdropFilter: 'blur(16px)',
      boxShadow: '0 25px 50px -12px rgba(79, 70, 229, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
    }
  );

  const primaryCTAStyle = combineStyles(
    {
      background: 'linear-gradient(135deg, #4f46e5 0%, #2563eb 50%, #7c3aed 100%)',
      boxShadow: '0 25px 50px -12px rgba(79, 70, 229, 0.4), 0 10px 20px -4px rgba(0, 0, 0, 0.1), inset 0 2px 0 rgba(255, 255, 255, 0.2)'
    },
    TYPOGRAPHY_STYLES.optimizedText
  );

  return (
    <section 
      className={`relative px-6 py-24 overflow-hidden ${className}`}
      style={heroBackgroundStyle}
      aria-labelledby="hero-headline"
    >
      
      {/* Premium Background Patterns */}
      <div className="absolute inset-0" aria-hidden="true">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-gradient-to-br from-blue-400/15 to-indigo-400/15 rounded-full filter blur-3xl"></div>
        <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-gradient-to-br from-emerald-400/10 to-green-400/10 rounded-full filter blur-3xl"></div>
        <div className="absolute bottom-1/4 left-1/2 w-72 h-72 bg-gradient-to-br from-violet-400/8 to-purple-400/8 rounded-full filter blur-3xl"></div>
        <div className="absolute inset-0 bg-gradient-to-br from-white/40 via-transparent to-indigo-50/20"></div>
      </div>
      
      <div className="max-w-6xl mx-auto text-center relative z-10">
        
        {/* Enhanced Section Header */}
        <div className="mb-16">
          {/* Premium Badge - Indigo Theme */}
          <div 
            className="inline-flex items-center px-8 py-4 border-2 border-indigo-200/50 text-indigo-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-indigo-200/40 transition-all duration-300 hover:scale-105" 
            style={badgeStyle}
          >
            <span className="w-3 h-3 rounded-full mr-3 bg-indigo-700" aria-hidden="true"></span>
            FIRS Certified Access Point Provider
          </div>

          {/* Enterprise Impact Statement */}
          <div className="mb-8">
            <div 
              className="inline-block text-purple-700 px-12 py-4 rounded-full text-xl font-bold mb-8 shadow-xl hover:shadow-purple-200/40 transition-all duration-300 hover:scale-105 border border-purple-300/40 backdrop-blur-sm"
              style={impactBadgeStyle}
            >
              Transform compliance from cost center to competitive advantage
            </div>
          </div>
          
          {/* Dramatic Enterprise Headline */}
          <div className="relative mb-12">
            <h1 
              id="hero-headline"
              className="text-6xl md:text-8xl font-black text-indigo-900 mb-8 leading-[0.9] tracking-tight" 
              style={heroHeadlineStyle}
            >
              <span className="text-slate-700">Submit compliant e-invoices in</span> 
              <br />
              <span className="relative inline-block">
                <span className="text-green-600 italic font-black" style={{ 
                  fontWeight: 950, 
                  textShadow: '0 4px 8px rgba(34, 197, 94, 0.4)' 
                }}>
                  seconds, not hours
                </span>
                {/* Premium underline effect */}
                <div className="absolute -bottom-3 left-0 right-0 h-2 bg-gradient-to-r from-green-500 via-emerald-500 to-green-500 rounded-full opacity-90" aria-hidden="true"></div>
              </span>
            </h1>
          </div>

          {/* Enhanced Enterprise Subtitle */}
          <p 
            className="text-2xl md:text-3xl text-slate-600 mb-16 max-w-5xl mx-auto font-medium leading-relaxed" 
            style={combineStyles(TYPOGRAPHY_STYLES.optimizedText, {
              textShadow: '0 2px 4px rgba(100, 116, 139, 0.2)'
            })}
          >
            Stop wasting <span className="text-indigo-600 font-bold">enterprise resources</span> on compliance paperwork. TaxPoynt's <span className="text-green-600 font-bold">universal integration platform</span> connects your business software directly to government systems—transforming hours of manual work into seconds of automated compliance.
          </p>
        </div>

        {/* Premium Enterprise CTA Section */}
        <div className="relative max-w-4xl mx-auto mb-20">
          {/* Background Effects */}
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-blue-500/5 to-purple-500/10 rounded-3xl blur-xl" aria-hidden="true"></div>
          
          {/* Main CTA Card */}
          <div 
            className="relative border-2 border-indigo-200/50 rounded-3xl p-8 md:p-12 shadow-2xl backdrop-blur-sm"
            style={ctaCardStyle}
          >
            
            {/* CTA Header */}
            <div className="mb-8">
              <p 
                className="text-2xl md:text-3xl font-bold text-slate-600 mb-4"
                style={combineStyles(TYPOGRAPHY_STYLES.optimizedText, {
                  textShadow: '0 2px 4px rgba(100, 116, 139, 0.1)'
                })}
              >
                Ready to transform your enterprise compliance?
              </p>
              <p 
                className="text-3xl md:text-4xl font-black text-indigo-600"
                style={combineStyles(TYPOGRAPHY_STYLES.optimizedText, {
                  fontWeight: 950,
                  textShadow: '0 2px 4px rgba(99, 102, 241, 0.3)'
                })}
              >
                Join thousands of enterprises already automated.
              </p>
            </div>

            {/* Premium CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-6 justify-center">
              <HeroCTAButton
                onClick={() => router.push('/auth/signup')}
                className="group relative text-2xl px-20 py-7 text-white font-bold rounded-3xl shadow-2xl hover:shadow-indigo-500/50 transition-all duration-500 hover:scale-105 transform border border-white/20"
                style={primaryCTAStyle}
                aria-label="Start your enterprise transformation with TaxPoynt"
              >
                <span className="relative z-10 flex items-center justify-center">
                  ✨ Start Enterprise Transformation
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" aria-hidden="true"></div>
              </HeroCTAButton>
              
              <TaxPoyntButton
                variant="secondary"
                size="lg"
                onClick={() => {
                  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="text-2xl px-16 py-7 border-2 border-indigo-300 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-400 hover:text-indigo-900 font-bold rounded-3xl shadow-xl hover:shadow-indigo-300/50 transition-all duration-300 hover:scale-105 transform bg-white/90 backdrop-blur-sm"
                style={TYPOGRAPHY_STYLES.optimizedText}
                aria-label="Learn more about platform capabilities"
              >
                See Platform Capabilities
              </TaxPoyntButton>
            </div>

            {/* Supporting Text */}
            <div className="mt-8 text-lg text-slate-600 font-medium">
              <span className="mr-2" aria-hidden="true">🚀</span>
              No setup fees • 14-day free trial • Cancel anytime
              <span className="ml-2" aria-hidden="true">🚀</span>
            </div>
            
            {/* Subtle Pattern Overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/20 via-transparent to-purple-50/20 rounded-3xl pointer-events-none" aria-hidden="true"></div>
          </div>
        </div>
      </div>
    </section>
  );
};
