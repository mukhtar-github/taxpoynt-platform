/**
 * Before/After Section Component
 * ==============================
 * Extracted from LandingPage.tsx - Transformation comparison showcase
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { BeforeAfterCard, TaxPoyntButton, BEFORE_AFTER_DATA } from '../../design_system';
import { getSectionBackground, TYPOGRAPHY_STYLES, combineStyles } from '../../design_system/style-utilities';

export interface BeforeAfterSectionProps {
  className?: string;
}

export const BeforeAfterSection: React.FC<BeforeAfterSectionProps> = ({ className = '' }) => {
  const router = useRouter();
  const sectionBackground = getSectionBackground('purple');
  
  const headlineStyle = combineStyles(
    TYPOGRAPHY_STYLES.sectionHeadline,
    {
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }
  );

  const transformationData = [
    {
      before: {
        emoji: "😰",
        title: "Manual Chaos",
        points: [
          "3-4 hours daily on tax paperwork",
          "60% rejection rate from FIRS",
          "Constant format errors",
          "Missing compliance deadlines",
          "₦2.3M annual losses"
        ]
      },
      after: {
        emoji: "🚀",
        title: "Automated Excellence", 
        points: [
          "2 minutes automated submission",
          "100% acceptance rate",
          "Zero format errors",
          "Never miss deadlines",
          "₦8.1M additional revenue"
        ]
      }
    }
  ];

  return (
    <section 
      className={`py-20 relative overflow-hidden ${sectionBackground.className} ${className}`}
      style={sectionBackground.style}
      aria-labelledby="before-after-headline"
    >
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Enhanced Section Header */}
        <div className="text-center mb-20">
          {/* Premium Badge - Purple Theme */}
          <div 
            className="inline-flex items-center px-8 py-4 border-2 border-purple-200/50 text-purple-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-purple-200/40 transition-all duration-300 hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, rgba(243, 232, 255, 0.9) 0%, rgba(238, 242, 255, 0.9) 100%)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <span className="w-3 h-3 rounded-full mr-3 bg-purple-700" aria-hidden="true"></span>
            Business Transformation Results
          </div>
          
          {/* Dramatic Headline */}
          <div className="relative mb-8">
            <h2 
              id="before-after-headline"
              className="text-5xl md:text-7xl font-black text-purple-900 mb-4 leading-[0.9] tracking-tight"
              style={headlineStyle}
            >
              <span className="text-slate-700">From compliance</span>
              <br />
              <span className="text-red-600">nightmare</span> to 
              <br />
              <span className="relative inline-block">
                <span 
                  className="text-purple-600 italic font-black"
                  style={{ 
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(147, 51, 234, 0.4)'
                  }}
                >
                  business advantage
                </span>
                {/* Dramatic underline effect */}
                <div 
                  className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-500 rounded-full opacity-90" 
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
            See the <span className="text-purple-600 font-bold">dramatic transformation</span> Nigerian businesses experience with TaxPoynt automation.
          </p>
        </div>

        {/* Before/After Comparison */}
        <div className="mb-20">
          {transformationData.map((comparison, index) => (
            <div key={index} className="relative">
              
              {/* VS Badge */}
              <div className="flex justify-center mb-8">
                <div className="bg-gradient-to-r from-red-500 to-green-500 text-white px-8 py-4 rounded-full font-black text-xl shadow-xl">
                  BEFORE vs AFTER
                </div>
              </div>

              {/* Comparison Cards */}
              <div className="grid md:grid-cols-2 gap-8 relative">
                
                {/* Before Card */}
                <div className="relative">
                  <div className="absolute -top-4 left-4 bg-red-500 text-white px-4 py-2 rounded-full font-bold text-sm z-10">
                    BEFORE TaxPoynt
                  </div>
                  <div className="bg-white p-8 rounded-2xl shadow-xl border border-red-200 relative overflow-hidden">
                    {/* Red overlay for "before" state */}
                    <div className="absolute inset-0 bg-gradient-to-br from-red-50/50 to-orange-50/50 pointer-events-none"></div>
                    
                    <div className="relative z-10">
                      <div className="text-6xl mb-6 text-center">{comparison.before.emoji}</div>
                      <h3 className="text-2xl font-black text-red-600 mb-6 text-center">
                        {comparison.before.title}
                      </h3>
                      <ul className="space-y-4">
                        {comparison.before.points.map((point, pointIndex) => (
                          <li key={pointIndex} className="flex items-start">
                            <span className="text-red-500 mr-3 text-xl">❌</span>
                            <span className="text-slate-700 font-medium">{point}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* After Card */}
                <div className="relative">
                  <div className="absolute -top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-full font-bold text-sm z-10">
                    AFTER TaxPoynt
                  </div>
                  <div className="bg-white p-8 rounded-2xl shadow-xl border border-green-200 relative overflow-hidden">
                    {/* Green overlay for "after" state */}
                    <div className="absolute inset-0 bg-gradient-to-br from-green-50/50 to-emerald-50/50 pointer-events-none"></div>
                    
                    <div className="relative z-10">
                      <div className="text-6xl mb-6 text-center">{comparison.after.emoji}</div>
                      <h3 className="text-2xl font-black text-green-600 mb-6 text-center">
                        {comparison.after.title}
                      </h3>
                      <ul className="space-y-4">
                        {comparison.after.points.map((point, pointIndex) => (
                          <li key={pointIndex} className="flex items-start">
                            <span className="text-green-500 mr-3 text-xl">✅</span>
                            <span className="text-slate-700 font-medium">{point}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Transformation Arrow */}
                <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20 hidden md:block">
                  <div className="bg-gradient-to-r from-purple-500 to-indigo-500 text-white p-4 rounded-full shadow-2xl">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M13 7l5 5-5 5M6 12h12" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Transformation Metrics */}
        <div className="mb-20">
          <h3 
            className="text-3xl md:text-4xl font-black text-center text-slate-800 mb-12"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            The <span className="text-purple-600">Numbers</span> Don't Lie
          </h3>
          
          <div className="grid md:grid-cols-4 gap-8">
            {[
              {
                metric: "98%",
                improvement: "Error Reduction",
                detail: "From 60% rejection to 100% acceptance",
                color: "green"
              },
              {
                metric: "85%",
                improvement: "Time Saved",
                detail: "From 4 hours to 2 minutes",
                color: "blue"
              },
              {
                metric: "340%",
                improvement: "ROI Increase",
                detail: "₦8.1M additional revenue annually",
                color: "purple"
              },
              {
                metric: "100%",
                improvement: "Compliance Rate",
                detail: "Never miss a deadline again",
                color: "indigo"
              }
            ].map((stat, index) => (
              <div 
                key={index}
                className="bg-white p-6 rounded-2xl shadow-lg text-center border border-gray-100"
              >
                <div 
                  className={`text-5xl font-black mb-3 text-${stat.color}-600`}
                  style={{ textShadow: `0 2px 4px rgba(0,0,0,0.1)` }}
                >
                  {stat.metric}
                </div>
                <div className={`text-lg font-bold text-${stat.color}-600 mb-2`}>
                  {stat.improvement}
                </div>
                <div className="text-sm text-slate-600">
                  {stat.detail}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Customer Transformation Stories */}
        <div className="mb-20">
          <h3 
            className="text-3xl md:text-4xl font-black text-center text-slate-800 mb-12"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Real <span className="text-purple-600">Transformation</span> Stories
          </h3>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                company: "Lagos Manufacturing SME",
                before: "6 hours daily on compliance",
                after: "100% automated",
                savings: "₦4.2M annually",
                quote: "TaxPoynt gave us our time back to focus on growing our business."
              },
              {
                company: "Abuja Tech Startup",
                before: "45% FIRS rejection rate",
                after: "Zero rejections",
                savings: "₦1.8M saved",
                quote: "Finally, a solution that actually works for Nigerian businesses."
              },
              {
                company: "Port Harcourt Retailer",
                before: "Missing compliance deadlines",
                after: "Always compliant",
                savings: "₦2.1M recovered",
                quote: "Best investment we've made for our business operations."
              }
            ].map((story, index) => (
              <div 
                key={index}
                className="bg-white p-6 rounded-2xl shadow-lg border border-purple-100"
              >
                <div className="text-lg font-bold text-purple-600 mb-4">
                  {story.company}
                </div>
                
                <div className="space-y-3 mb-4">
                  <div className="flex items-center">
                    <span className="text-red-500 mr-2">❌</span>
                    <span className="text-sm text-slate-600">{story.before}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    <span className="text-sm text-slate-600">{story.after}</span>
                  </div>
                </div>
                
                <div className="text-center mb-4">
                  <div className="text-2xl font-black text-green-600 mb-1">
                    {story.savings}
                  </div>
                  <div className="text-sm text-slate-500">Annual Savings</div>
                </div>
                
                <blockquote className="text-sm text-slate-600 italic text-center border-l-4 border-purple-300 pl-4">
                  "{story.quote}"
                </blockquote>
              </div>
            ))}
          </div>
        </div>

        {/* Premium Bottom CTA Section */}
        <div className="text-center mt-24 mb-12">
          <div className="mb-12">
            <h3 
              className="text-3xl md:text-4xl font-black text-slate-800 mb-6"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              Ready for your <span className="text-purple-600">transformation</span>?
            </h3>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
              Join the <span className="font-bold text-purple-600">2,500+ Nigerian businesses</span> who've already transformed their compliance. Your success story starts today.
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <TaxPoyntButton
              variant="primary"
              size="lg"
              onClick={() => router.push('/auth/signup')}
              className="text-xl px-12 py-6 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-purple-500/40 transition-all duration-300 hover:scale-105"
            >
              🚀 Start My Transformation
            </TaxPoyntButton>
            
            <TaxPoyntButton
              variant="outline"
              size="lg"
              onClick={() => {
                document.getElementById('testimonials')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-xl px-12 py-6 border-2 border-purple-300 text-purple-700 hover:bg-purple-50 hover:border-purple-400 hover:text-purple-900 font-bold rounded-2xl shadow-lg hover:shadow-purple-200/50 transition-all duration-300"
            >
              Read More Success Stories
            </TaxPoyntButton>
          </div>

          {/* Transformation Guarantee */}
          <div className="inline-flex items-center px-6 py-3 bg-purple-100/80 text-purple-800 rounded-full text-base font-bold border border-purple-200/50">
            <span className="mr-2" aria-hidden="true">⚡</span>
            See results in 48 hours or money back guaranteed
            <span className="ml-2" aria-hidden="true">⚡</span>
          </div>
        </div>
      </div>
    </section>
  );
};
