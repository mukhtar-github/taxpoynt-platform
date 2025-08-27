/**
 * Problems Section Component
 * ==========================
 * Extracted from LandingPage.tsx - Pain points identification section
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { ProblemCard, TaxPoyntButton, PROBLEMS_DATA } from '../../design_system';
import { getSectionBackground, TYPOGRAPHY_STYLES, combineStyles } from '../../design_system/style-utilities';

export interface ProblemsSectionProps {
  className?: string;
}

export const ProblemsSection: React.FC<ProblemsSectionProps> = ({ className = '' }) => {
  const router = useRouter();
  const sectionBackground = getSectionBackground('slate');
  
  const headlineStyle = combineStyles(
    TYPOGRAPHY_STYLES.sectionHeadline,
    {
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }
  );

  const ctaCardStyle = combineStyles(
    {
      background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,250,252,0.9) 50%, rgba(255,255,255,0.95) 100%)',
      backdropFilter: 'blur(16px)',
      boxShadow: '0 25px 50px -12px rgba(71, 85, 105, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
    }
  );

  return (
    <section 
      className={`py-20 relative overflow-hidden ${sectionBackground.className} ${className}`}
      style={sectionBackground.style}
      aria-labelledby="problems-headline"
    >
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Enhanced Section Header */}
        <div className="text-center mb-20">
          {/* Premium Badge - Blue/Green Theme */}
          <div 
            className="inline-flex items-center px-8 py-4 border-2 border-slate-200/50 text-slate-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-slate-200/40 transition-all duration-300 hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.95) 100%)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <span className="w-3 h-3 rounded-full mr-3 bg-slate-700" aria-hidden="true"></span>
            Enterprise Compliance Challenges
          </div>
          
          {/* Dramatic Headline */}
          <div className="relative mb-8">
            <h2 
              id="problems-headline"
              className="text-5xl md:text-7xl font-black text-slate-900 mb-4 leading-[0.9] tracking-tight"
              style={headlineStyle}
            >
              <span className="text-red-600">Stop losing money</span>
              <br />
              <span className="relative inline-block">
                <span 
                  className="text-slate-700 italic font-black"
                  style={{ 
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(71, 85, 105, 0.3)'
                  }}
                >
                  to compliance chaos
                </span>
                {/* Dramatic underline effect */}
                <div 
                  className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-red-500 via-orange-500 to-red-500 rounded-full opacity-90" 
                  aria-hidden="true"
                ></div>
              </span>
            </h2>
          </div>
          
          {/* Enhanced Subtitle */}
          <p 
            className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-medium"
            style={combineStyles(TYPOGRAPHY_STYLES.optimizedText, {
              textShadow: '0 2px 4px rgba(100, 116, 139, 0.2)'
            })}
          >
            Every day your business wastes resources on <span className="text-red-600 font-bold">manual compliance</span>, you're losing competitive advantage. These problems are costing Nigerian enterprises millions.
          </p>
        </div>

        {/* Problems Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
          {PROBLEMS_DATA.map((problem, index) => (
            <ProblemCard
              key={index}
              emoji={problem.emoji}
              title={problem.title}
              quote={problem.quote}
              attribution={problem.attribution}
              className="hover:scale-102 transition-transform duration-300"
            />
          ))}
        </div>

        {/* Premium Bottom CTA Section */}
        <div className="text-center mt-24 mb-12">
          {/* Empathy Hook */}
          <div className="mb-12">
            <h3 
              className="text-3xl md:text-4xl font-black text-slate-800 mb-6"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              <span className="text-red-600">Sound familiar?</span> You're not alone.
            </h3>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
              <span className="font-bold text-slate-800">73% of Nigerian businesses</span> struggle with e-invoicing compliance. The average SME loses <span className="font-bold text-red-600">₦2.3M annually</span> to inefficient tax processes.
            </p>
          </div>

          {/* Dramatic Problem Summary Card */}
          <div className="relative max-w-4xl mx-auto mb-12">
            {/* Background Effects */}
            <div 
              className="absolute inset-0 bg-gradient-to-br from-red-500/10 via-orange-500/5 to-yellow-500/10 rounded-3xl blur-xl" 
              aria-hidden="true"
            ></div>
            
            {/* Main Problem Card */}
            <div 
              className="relative border-2 border-red-200/50 rounded-3xl p-8 md:p-12 shadow-2xl backdrop-blur-sm"
              style={ctaCardStyle}
            >
              
              {/* Problem Statement */}
              <div className="mb-8">
                <h4 
                  className="text-2xl md:text-3xl font-bold text-slate-700 mb-4"
                  style={TYPOGRAPHY_STYLES.optimizedText}
                >
                  The compliance chaos is killing Nigerian businesses
                </h4>
                <div className="text-xl md:text-2xl font-black text-red-600 mb-6">
                  ❌ Manual processes • ❌ Constant errors • ❌ Wasted time • ❌ Lost revenue
                </div>
              </div>

              {/* Solution Teaser */}
              <div className="mb-8">
                <p 
                  className="text-xl md:text-2xl font-bold text-slate-600 mb-4"
                  style={TYPOGRAPHY_STYLES.optimizedText}
                >
                  What if there was a <span className="text-green-600">better way</span>?
                </p>
                <p className="text-lg text-slate-600 max-w-3xl mx-auto">
                  Imagine submitting compliant e-invoices in seconds, not hours. Zero errors, zero stress, complete automation.
                </p>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <TaxPoyntButton
                  variant="primary"
                  size="lg"
                  onClick={() => router.push('/auth/signup')}
                  className="text-xl px-12 py-6 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-green-500/30 transition-all duration-300 hover:scale-105"
                >
                  🚀 End the Chaos Now
                </TaxPoyntButton>
                
                <TaxPoyntButton
                  variant="outline"
                  size="lg"
                  onClick={() => {
                    document.getElementById('solutions')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="text-xl px-12 py-6 border-2 border-green-300 text-green-700 hover:bg-green-50 hover:border-green-400 hover:text-green-900 font-bold rounded-2xl shadow-lg hover:shadow-green-200/50 transition-all duration-300"
                >
                  See the Solution
                </TaxPoyntButton>
              </div>

              {/* Supporting Text */}
              <div className="mt-6 text-base text-slate-600">
                <span className="mr-2" aria-hidden="true">⚡</span>
                2-minute setup • Zero manual work • Immediate compliance
                <span className="ml-2" aria-hidden="true">⚡</span>
              </div>
              
              {/* Subtle Pattern Overlay */}
              <div 
                className="absolute inset-0 bg-gradient-to-br from-green-50/20 via-transparent to-emerald-50/20 rounded-3xl pointer-events-none" 
                aria-hidden="true"
              ></div>
            </div>
          </div>

          {/* Social Proof Snippet */}
          <div className="inline-flex items-center px-6 py-3 bg-orange-100/80 text-orange-800 rounded-full text-base font-bold border border-orange-200/50">
            <span className="mr-2" aria-hidden="true">⚠️</span>
            Don't let compliance chaos cost you another ₦2.3M this year
            <span className="ml-2" aria-hidden="true">⚠️</span>
          </div>
        </div>
      </div>
    </section>
  );
};
