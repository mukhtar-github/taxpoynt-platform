/**
 * Solutions Section Component
 * ===========================
 * Extracted from LandingPage.tsx - How TaxPoynt solves enterprise problems
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { SolutionCard, TaxPoyntButton, ENTERPRISE_SOLUTIONS_DATA } from '../../design_system';
import { getSectionBackground, TYPOGRAPHY_STYLES, combineStyles } from '../../design_system/style-utilities';

export interface SolutionsSectionProps {
  className?: string;
}

export const SolutionsSection: React.FC<SolutionsSectionProps> = ({ className = '' }) => {
  const router = useRouter();
  const sectionBackground = getSectionBackground('green');
  
  const headlineStyle = combineStyles(
    TYPOGRAPHY_STYLES.sectionHeadline,
    {
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }
  );

  const ctaCardStyle = combineStyles(
    {
      background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(236,253,245,0.9) 50%, rgba(255,255,255,0.95) 100%)',
      backdropFilter: 'blur(16px)',
      boxShadow: '0 25px 50px -12px rgba(34, 197, 94, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
    }
  );

  return (
    <section 
      id="solutions"
      className={`py-20 relative overflow-hidden ${sectionBackground.className} ${className}`}
      style={sectionBackground.style}
      aria-labelledby="solutions-headline"
    >
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Enhanced Section Header */}
        <div className="text-center mb-20">
          {/* Premium Badge - Green Theme */}
          <div 
            className="inline-flex items-center px-8 py-4 border-2 border-green-200/50 text-green-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-green-200/40 transition-all duration-300 hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, rgba(236, 253, 245, 0.95) 0%, rgba(220, 252, 231, 0.95) 100%)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <span className="w-3 h-3 rounded-full mr-3 bg-green-700" aria-hidden="true"></span>
            TaxPoynt Enterprise Solutions
          </div>
          
          {/* Dramatic Headline */}
          <div className="relative mb-8">
            <h2 
              id="solutions-headline"
              className="text-5xl md:text-7xl font-black text-green-900 mb-4 leading-[0.9] tracking-tight"
              style={headlineStyle}
            >
              <span className="text-slate-700">Transform chaos into</span>
              <br />
              <span className="relative inline-block">
                <span 
                  className="text-green-600 italic font-black"
                  style={{ 
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(34, 197, 94, 0.4)'
                  }}
                >
                  competitive advantage
                </span>
                {/* Dramatic underline effect */}
                <div 
                  className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-green-500 via-emerald-500 to-green-500 rounded-full opacity-90" 
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
            See how TaxPoynt's <span className="text-green-600 font-bold">universal integration platform</span> eliminates every compliance pain point and turns tax management into a strategic business advantage.
          </p>
        </div>

        {/* Solutions Grid */}
        <div className="grid md:grid-cols-2 gap-12 mb-20">
          {ENTERPRISE_SOLUTIONS_DATA.map((solution, index) => (
            <SolutionCard
              key={index}
              emoji={solution.emoji}
              title={solution.title}
              problem={solution.problem}
              quote={solution.quote}
              attribution={solution.attribution}
              metrics={solution.metrics}
              className="hover:scale-102 transition-transform duration-300"
            />
          ))}
        </div>

        {/* Premium Bottom CTA Section */}
        <div className="text-center mt-24 mb-12">
          {/* Success Hook */}
          <div className="mb-12">
            <h3 
              className="text-3xl md:text-4xl font-black text-slate-800 mb-6"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              Ready to <span className="text-green-600">revolutionize</span> your compliance?
            </h3>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
              Join <span className="font-bold text-green-600">2,500+ Nigerian businesses</span> who've already transformed their tax processes. Average ROI: <span className="font-bold text-green-600">340% in 6 months</span>.
            </p>
          </div>

          {/* Dramatic Solution Summary Card */}
          <div className="relative max-w-4xl mx-auto mb-12">
            {/* Background Effects */}
            <div 
              className="absolute inset-0 bg-gradient-to-br from-green-500/15 via-emerald-500/10 to-teal-500/15 rounded-3xl blur-xl" 
              aria-hidden="true"
            ></div>
            
            {/* Main Solution Card */}
            <div 
              className="relative border-2 border-green-200/50 rounded-3xl p-8 md:p-12 shadow-2xl backdrop-blur-sm"
              style={ctaCardStyle}
            >
              
              {/* Solution Statement */}
              <div className="mb-8">
                <h4 
                  className="text-2xl md:text-3xl font-bold text-slate-700 mb-4"
                  style={TYPOGRAPHY_STYLES.optimizedText}
                >
                  The complete compliance automation solution
                </h4>
                <div className="text-xl md:text-2xl font-black text-green-600 mb-6">
                  ✅ Universal integration • ✅ Zero errors • ✅ Real-time compliance • ✅ Maximum ROI
                </div>
              </div>

              {/* Value Proposition */}
              <div className="mb-8">
                <p 
                  className="text-xl md:text-2xl font-bold text-slate-600 mb-4"
                  style={TYPOGRAPHY_STYLES.optimizedText}
                >
                  From <span className="text-red-500">manual chaos</span> to <span className="text-green-600">automated excellence</span> in 2 minutes
                </p>
                <p className="text-lg text-slate-600 max-w-3xl mx-auto">
                  Connect any business system. Submit perfect invoices. Stay 100% compliant. Focus on growing your business.
                </p>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <TaxPoyntButton
                  variant="primary"
                  size="lg"
                  onClick={() => router.push('/auth/signup')}
                  className="text-xl px-12 py-6 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-green-500/40 transition-all duration-300 hover:scale-105"
                >
                  ✨ Start Transformation
                </TaxPoyntButton>
                
                <TaxPoyntButton
                  variant="outline"
                  size="lg"
                  onClick={() => {
                    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="text-xl px-12 py-6 border-2 border-green-300 text-green-700 hover:bg-green-50 hover:border-green-400 hover:text-green-900 font-bold rounded-2xl shadow-lg hover:shadow-green-200/50 transition-all duration-300"
                >
                  Explore Features
                </TaxPoyntButton>
              </div>

              {/* Supporting Text */}
              <div className="mt-6 text-base text-slate-600">
                <span className="mr-2" aria-hidden="true">🚀</span>
                Free 14-day trial • No setup fees • Cancel anytime
                <span className="ml-2" aria-hidden="true">🚀</span>
              </div>
              
              {/* Subtle Pattern Overlay */}
              <div 
                className="absolute inset-0 bg-gradient-to-br from-green-50/20 via-transparent to-emerald-50/20 rounded-3xl pointer-events-none" 
                aria-hidden="true"
              ></div>
            </div>
          </div>

          {/* Success Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            {[
              { number: "340%", label: "Average ROI" },
              { number: "98%", label: "Error Reduction" },
              { number: "85%", label: "Time Saved" },
              { number: "2,500+", label: "Happy Clients" }
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div 
                  className="text-3xl md:text-4xl font-black text-green-600 mb-2"
                  style={{ textShadow: '0 2px 4px rgba(34, 197, 94, 0.3)' }}
                >
                  {stat.number}
                </div>
                <div className="text-slate-600 font-medium text-sm md:text-base">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>

          {/* Success Guarantee */}
          <div className="inline-flex items-center px-6 py-3 bg-green-100/80 text-green-800 rounded-full text-base font-bold border border-green-200/50">
            <span className="mr-2" aria-hidden="true">🎯</span>
            340% ROI Guarantee or Your Money Back
            <span className="ml-2" aria-hidden="true">🎯</span>
          </div>
        </div>
      </div>
    </section>
  );
};
