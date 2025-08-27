/**
 * Final CTA Section Component
 * ===========================
 * Extracted from LandingPage.tsx - Demo and contact options with final conversion push
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { TaxPoyntButton } from '../../design_system';
import { getSectionBackground, TYPOGRAPHY_STYLES, combineStyles } from '../../design_system/style-utilities';

export interface FinalCTASectionProps {
  className?: string;
}

export const FinalCTASection: React.FC<FinalCTASectionProps> = ({ className = '' }) => {
  const router = useRouter();
  const sectionBackground = getSectionBackground('amber');
  
  const headlineStyle = combineStyles(
    TYPOGRAPHY_STYLES.sectionHeadline,
    {
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }
  );

  const ctaCardStyle = combineStyles(
    {
      background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,251,235,0.9) 50%, rgba(255,255,255,0.95) 100%)',
      backdropFilter: 'blur(16px)',
      boxShadow: '0 25px 50px -12px rgba(245, 158, 11, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
    }
  );

  return (
    <section 
      className={`py-20 relative overflow-hidden ${sectionBackground.className} ${className}`}
      style={sectionBackground.style}
      aria-labelledby="final-cta-headline"
    >
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Enhanced Section Header */}
        <div className="text-center mb-20">
          {/* Premium Badge - Amber Theme */}
          <div 
            className="inline-flex items-center px-8 py-4 border-2 border-amber-200/50 text-amber-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-amber-200/40 transition-all duration-300 hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, rgba(255, 251, 235, 0.95) 0%, rgba(254, 243, 199, 0.95) 100%)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <span className="w-3 h-3 rounded-full mr-3 bg-amber-700" aria-hidden="true"></span>
            Your Compliance Transformation Awaits
          </div>
          
          {/* Dramatic Headline */}
          <div className="relative mb-8">
            <h2 
              id="final-cta-headline"
              className="text-5xl md:text-7xl font-black text-amber-900 mb-4 leading-[0.9] tracking-tight"
              style={headlineStyle}
            >
              <span className="text-slate-700">Don't let another day pass</span>
              <br />
              <span className="text-red-600">losing money</span> to 
              <br />
              <span className="relative inline-block">
                <span 
                  className="text-amber-600 italic font-black"
                  style={{ 
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(245, 158, 11, 0.4)'
                  }}
                >
                  compliance chaos
                </span>
                {/* Dramatic underline effect */}
                <div 
                  className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-orange-500 to-amber-500 rounded-full opacity-90" 
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
            Every moment you delay costs your business money. TaxPoynt customers save <span className="text-amber-600 font-bold">₦2.4M annually</span> on average. Join them today.
          </p>
        </div>

        {/* Urgency Counter */}
        <div className="mb-20">
          <div className="bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-3xl p-8 text-center relative overflow-hidden">
            {/* Background pattern */}
            <div className="absolute inset-0 bg-gradient-to-br from-red-600/20 to-orange-600/20"></div>
            
            <div className="relative z-10">
              <h3 className="text-2xl md:text-3xl font-black mb-4">
                ⏰ Limited Time: Save 40% on Your First Year
              </h3>
              <p className="text-lg md:text-xl mb-6 opacity-90">
                Join the 2,500+ businesses already saving millions with TaxPoynt
              </p>
              
              {/* Fake countdown for urgency */}
              <div className="flex justify-center space-x-4 mb-6">
                {[
                  { label: "Days", value: "05" },
                  { label: "Hours", value: "14" },
                  { label: "Minutes", value: "32" },
                  { label: "Seconds", value: "18" }
                ].map((time, index) => (
                  <div key={index} className="bg-white/20 rounded-lg p-3 min-w-[60px]">
                    <div className="text-2xl font-black">{time.value}</div>
                    <div className="text-xs opacity-80">{time.label}</div>
                  </div>
                ))}
              </div>
              
              <p className="text-sm opacity-80">
                Offer expires soon • No code needed • Automatic discount applied
              </p>
            </div>
          </div>
        </div>

        {/* Three-Column CTA Options */}
        <div className="grid md:grid-cols-3 gap-8 mb-20">
          
          {/* Quick Start */}
          <div className="bg-white rounded-3xl p-8 shadow-xl border-2 border-green-200 relative overflow-hidden">
            <div className="absolute -top-2 right-4">
              <div className="bg-green-500 text-white px-4 py-1 rounded-full font-bold text-xs">
                Most Popular
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-6xl mb-4">🚀</div>
              <h3 className="text-2xl font-black text-slate-800 mb-4">
                Start Immediately
              </h3>
              <p className="text-slate-600 mb-6">
                Get up and running in under 2 minutes. Connect your first system and start submitting compliant invoices today.
              </p>
              
              <TaxPoyntButton
                variant="primary"
                onClick={() => router.push('/auth/signup')}
                className="w-full mb-4 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold py-4 rounded-2xl shadow-lg hover:shadow-green-500/40 transition-all duration-300 hover:scale-105"
              >
                Start Free Trial Now
              </TaxPoyntButton>
              
              <ul className="text-sm text-slate-600 space-y-1">
                <li>✅ No credit card required</li>
                <li>✅ 14-day full access</li>
                <li>✅ Setup in 2 minutes</li>
              </ul>
            </div>
          </div>

          {/* Watch Demo */}
          <div className="bg-white rounded-3xl p-8 shadow-xl border border-gray-200">
            <div className="text-center">
              <div className="text-6xl mb-4">📺</div>
              <h3 className="text-2xl font-black text-slate-800 mb-4">
                See It In Action
              </h3>
              <p className="text-slate-600 mb-6">
                Watch a 5-minute demo showing exactly how TaxPoynt transforms your compliance process from chaos to automation.
              </p>
              
              <TaxPoyntButton
                variant="outline"
                onClick={() => router.push('/demo')}
                className="w-full mb-4 border-2 border-blue-300 text-blue-700 hover:bg-blue-50 hover:border-blue-400 hover:text-blue-900 font-bold py-4 rounded-2xl shadow-lg hover:shadow-blue-200/50 transition-all duration-300"
              >
                Watch 5-Min Demo
              </TaxPoyntButton>
              
              <ul className="text-sm text-slate-600 space-y-1">
                <li>🎯 See real integrations</li>
                <li>🎯 Live FIRS submission</li>
                <li>🎯 ROI calculations</li>
              </ul>
            </div>
          </div>

          {/* Enterprise Demo */}
          <div className="bg-white rounded-3xl p-8 shadow-xl border border-gray-200">
            <div className="text-center">
              <div className="text-6xl mb-4">🏢</div>
              <h3 className="text-2xl font-black text-slate-800 mb-4">
                Enterprise Solution
              </h3>
              <p className="text-slate-600 mb-6">
                Schedule a personalized demo for your enterprise. Custom integrations, volume discounts, and dedicated support.
              </p>
              
              <TaxPoyntButton
                variant="outline"
                onClick={() => router.push('/enterprise-demo')}
                className="w-full mb-4 border-2 border-purple-300 text-purple-700 hover:bg-purple-50 hover:border-purple-400 hover:text-purple-900 font-bold py-4 rounded-2xl shadow-lg hover:shadow-purple-200/50 transition-all duration-300"
              >
                Schedule Enterprise Demo
              </TaxPoyntButton>
              
              <ul className="text-sm text-slate-600 space-y-1">
                <li>💼 Custom solutions</li>
                <li>💼 Volume discounts</li>
                <li>💼 Dedicated support</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Risk-Free Guarantees */}
        <div className="mb-20">
          <h3 
            className="text-3xl md:text-4xl font-black text-center text-slate-800 mb-12"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Your <span className="text-amber-600">Risk-Free</span> Guarantees
          </h3>
          
          <div className="grid md:grid-cols-4 gap-6">
            {[
              {
                icon: "🔒",
                title: "30-Day Money Back",
                detail: "Full refund if not completely satisfied"
              },
              {
                icon: "⚡",
                title: "48-Hour Results",
                detail: "See compliance improvements within 2 days"
              },
              {
                icon: "🛡️",
                title: "100% Uptime SLA",
                detail: "Enterprise-grade reliability guaranteed"
              },
              {
                icon: "🎯",
                title: "Zero Error Promise",
                detail: "100% FIRS acceptance rate or money back"
              }
            ].map((guarantee, index) => (
              <div 
                key={index}
                className="bg-white p-6 rounded-2xl shadow-lg text-center border border-amber-100"
              >
                <div className="text-4xl mb-4">{guarantee.icon}</div>
                <h4 className="text-lg font-bold text-slate-800 mb-2">
                  {guarantee.title}
                </h4>
                <p className="text-sm text-slate-600">
                  {guarantee.detail}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Final Urgency Push */}
        <div className="relative max-w-4xl mx-auto mb-12">
          {/* Background Effects */}
          <div 
            className="absolute inset-0 bg-gradient-to-br from-amber-500/15 via-orange-500/10 to-red-500/15 rounded-3xl blur-xl" 
            aria-hidden="true"
          ></div>
          
          {/* Main CTA Card */}
          <div 
            className="relative border-2 border-amber-200/50 rounded-3xl p-8 md:p-12 shadow-2xl backdrop-blur-sm"
            style={ctaCardStyle}
          >
            
            {/* Final Push */}
            <div className="text-center mb-8">
              <h3 
                className="text-3xl md:text-4xl font-bold text-slate-700 mb-4"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                The choice is yours:
              </h3>
              
              <div className="grid md:grid-cols-2 gap-8 mb-8">
                {/* Continue Current Pain */}
                <div className="bg-red-50 p-6 rounded-2xl border border-red-200">
                  <h4 className="text-lg font-bold text-red-600 mb-4">
                    ❌ Keep Losing Money
                  </h4>
                  <ul className="text-sm text-red-700 space-y-2">
                    <li>• Continue wasting 20+ hours weekly</li>
                    <li>• Keep losing ₦2.3M annually</li>
                    <li>• Struggle with 60% rejection rates</li>
                    <li>• Miss compliance deadlines</li>
                    <li>• Watch competitors get ahead</li>
                  </ul>
                </div>
                
                {/* Choose TaxPoynt */}
                <div className="bg-green-50 p-6 rounded-2xl border border-green-200">
                  <h4 className="text-lg font-bold text-green-600 mb-4">
                    ✅ Transform Your Business
                  </h4>
                  <ul className="text-sm text-green-700 space-y-2">
                    <li>• Automate compliance in 2 minutes</li>
                    <li>• Save ₦2.4M+ annually</li>
                    <li>• Achieve 100% acceptance rates</li>
                    <li>• Never miss deadlines again</li>
                    <li>• Gain competitive advantage</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Final CTA Buttons */}
            <div className="text-center">
              <div className="mb-6">
                <p 
                  className="text-xl md:text-2xl font-bold text-slate-600 mb-4"
                  style={TYPOGRAPHY_STYLES.optimizedText}
                >
                  Ready to stop losing money and start saving?
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
                <TaxPoyntButton
                  variant="primary"
                  size="lg"
                  onClick={() => router.push('/auth/signup')}
                  className="text-xl px-16 py-6 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-amber-500/40 transition-all duration-300 hover:scale-105"
                >
                  🎯 Yes, Transform My Business Now
                </TaxPoyntButton>
              </div>

              {/* Final Trust Signals */}
              <div className="space-y-3 text-sm text-slate-600">
                <div className="flex justify-center items-center space-x-6">
                  <span>✅ 2,500+ businesses trust us</span>
                  <span>✅ ₦8.1B+ processed</span>
                  <span>✅ 99.9% uptime</span>
                </div>
                <div className="flex justify-center items-center space-x-6">
                  <span>🔒 Bank-level security</span>
                  <span>🛡️ FIRS certified</span>
                  <span>🎯 100% success rate</span>
                </div>
              </div>
            </div>
            
            {/* Subtle Pattern Overlay */}
            <div 
              className="absolute inset-0 bg-gradient-to-br from-amber-50/20 via-transparent to-orange-50/20 rounded-3xl pointer-events-none" 
              aria-hidden="true"
            ></div>
          </div>
        </div>

        {/* Contact Information */}
        <div className="text-center">
          <h4 className="text-xl font-bold text-slate-800 mb-4">
            Still have questions? We're here to help.
          </h4>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-6">
            <a 
              href="tel:+2348123456789" 
              className="flex items-center space-x-2 text-amber-600 hover:text-amber-700 font-medium"
            >
              <span>📞</span>
              <span>+234 812 345 6789</span>
            </a>
            <a 
              href="mailto:hello@taxpoynt.com" 
              className="flex items-center space-x-2 text-amber-600 hover:text-amber-700 font-medium"
            >
              <span>✉️</span>
              <span>hello@taxpoynt.com</span>
            </a>
            <button 
              onClick={() => {
                // Open chat widget or redirect to support
                window.open('https://wa.me/2348123456789', '_blank');
              }}
              className="flex items-center space-x-2 text-amber-600 hover:text-amber-700 font-medium"
            >
              <span>💬</span>
              <span>Live Chat Support</span>
            </button>
          </div>
          
          <p className="text-slate-600">
            Available 24/7 • Nigerian-based support team • Response within 5 minutes
          </p>
        </div>
      </div>
    </section>
  );
};
