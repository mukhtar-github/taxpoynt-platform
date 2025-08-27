/**
 * Features Section Component
 * ==========================
 * Extracted from LandingPage.tsx - Detailed platform capabilities showcase
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { FeatureCard, TaxPoyntButton, ENTERPRISE_FEATURES_DATA } from '../../design_system';
import { getSectionBackground, TYPOGRAPHY_STYLES, combineStyles } from '../../design_system/style-utilities';

export interface FeaturesSectionProps {
  className?: string;
}

export const FeaturesSection: React.FC<FeaturesSectionProps> = ({ className = '' }) => {
  const router = useRouter();
  const sectionBackground = getSectionBackground('indigo');
  
  const headlineStyle = combineStyles(
    TYPOGRAPHY_STYLES.sectionHeadline,
    {
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }
  );

  const ctaCardStyle = combineStyles(
    {
      background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(238,242,255,0.9) 50%, rgba(255,255,255,0.95) 100%)',
      backdropFilter: 'blur(16px)',
      boxShadow: '0 25px 50px -12px rgba(79, 70, 229, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
    }
  );

  return (
    <section 
      id="features"
      className={`py-20 relative overflow-hidden ${sectionBackground.className} ${className}`}
      style={sectionBackground.style}
      aria-labelledby="features-headline"
    >
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Enhanced Section Header */}
        <div className="text-center mb-20">
          {/* Premium Badge - Indigo Theme */}
          <div 
            className="inline-flex items-center px-8 py-4 border-2 border-indigo-200/50 text-indigo-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-indigo-200/40 transition-all duration-300 hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, rgba(238, 242, 255, 0.95) 0%, rgba(239, 246, 255, 0.95) 100%)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <span className="w-3 h-3 rounded-full mr-3 bg-indigo-700" aria-hidden="true"></span>
            Enterprise Platform Capabilities
          </div>
          
          {/* Dramatic Headline */}
          <div className="relative mb-8">
            <h2 
              id="features-headline"
              className="text-5xl md:text-7xl font-black text-indigo-900 mb-4 leading-[0.9] tracking-tight"
              style={headlineStyle}
            >
              <span className="text-slate-700">Every feature you need to</span>
              <br />
              <span className="relative inline-block">
                <span 
                  className="text-indigo-600 italic font-black"
                  style={{ 
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(79, 70, 229, 0.4)'
                  }}
                >
                  dominate compliance
                </span>
                {/* Dramatic underline effect */}
                <div 
                  className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-blue-500 to-indigo-500 rounded-full opacity-90" 
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
            TaxPoynt's <span className="text-indigo-600 font-bold">enterprise-grade platform</span> provides everything Nigerian businesses need for complete tax compliance automation.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 gap-12 mb-20">
          {ENTERPRISE_FEATURES_DATA.map((feature, index) => (
            <FeatureCard
              key={index}
              category={feature.category}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              capabilities={feature.capabilities}
              metrics={feature.metrics}
              className="hover:scale-102 transition-transform duration-300"
            />
          ))}
        </div>

        {/* Premium Features Showcase */}
        <div className="mb-20">
          <h3 
            className="text-3xl md:text-4xl font-black text-center text-slate-800 mb-12"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            <span className="text-indigo-600">Advanced</span> Enterprise Capabilities
          </h3>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: "🔄",
                title: "Real-time Sync",
                description: "Instant synchronization across all connected business systems",
                stats: "< 2 seconds"
              },
              {
                icon: "🛡️",
                title: "Enterprise Security",
                description: "Bank-level encryption with ISO 27001 compliance",
                stats: "256-bit SSL"
              },
              {
                icon: "📊",
                title: "Advanced Analytics",
                description: "Deep insights into compliance patterns and business performance",
                stats: "50+ metrics"
              },
              {
                icon: "🌍",
                title: "Multi-currency",
                description: "Support for international transactions and currencies",
                stats: "120+ currencies"
              },
              {
                icon: "⚡",
                title: "API-first Design",
                description: "RESTful APIs for seamless integration with any system",
                stats: "99.9% uptime"
              },
              {
                icon: "🎯",
                title: "Smart Validation",
                description: "AI-powered validation prevents errors before submission",
                stats: "Zero rejections"
              }
            ].map((capability, index) => (
              <div 
                key={index}
                className="bg-white p-6 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-indigo-100"
              >
                <div className="text-4xl mb-4 text-center">{capability.icon}</div>
                <h4 className="text-xl font-bold text-slate-800 mb-3 text-center">
                  {capability.title}
                </h4>
                <p className="text-slate-600 text-center mb-4 leading-relaxed">
                  {capability.description}
                </p>
                <div className="text-center">
                  <span className="inline-block px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-bold">
                    {capability.stats}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Integration Showcase */}
        <div className="mb-20">
          <h3 
            className="text-3xl md:text-4xl font-black text-center text-slate-800 mb-12"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Connect <span className="text-indigo-600">Everything</span> Seamlessly
          </h3>
          
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { name: "Odoo ERP", logo: "🏢", category: "ERP Systems" },
              { name: "SAP", logo: "💼", category: "Enterprise" },
              { name: "QuickBooks", logo: "📚", category: "Accounting" },
              { name: "Salesforce", logo: "☁️", category: "CRM" },
              { name: "Shopify", logo: "🛒", category: "E-commerce" },
              { name: "Square POS", logo: "💳", category: "Point of Sale" },
              { name: "Mono Banking", logo: "🏦", category: "Open Banking" },
              { name: "Paystack", logo: "💸", category: "Payments" }
            ].map((integration, index) => (
              <div 
                key={index}
                className="bg-white p-4 rounded-xl shadow-md hover:shadow-lg transition-all duration-300 text-center border border-gray-100"
              >
                <div className="text-3xl mb-2">{integration.logo}</div>
                <div className="font-bold text-slate-800 text-sm mb-1">{integration.name}</div>
                <div className="text-xs text-slate-500">{integration.category}</div>
              </div>
            ))}
          </div>
          
          <div className="text-center mt-8">
            <p className="text-lg text-slate-600 mb-4">
              <span className="font-bold text-indigo-600">100+ integrations</span> and counting
            </p>
            <div className="inline-flex items-center px-6 py-3 bg-indigo-100/80 text-indigo-800 rounded-full text-base font-bold border border-indigo-200/50">
              <span className="mr-2" aria-hidden="true">🔗</span>
              Can't find your system? We'll build the integration for free
              <span className="ml-2" aria-hidden="true">🔗</span>
            </div>
          </div>
        </div>

        {/* Premium Bottom CTA Section */}
        <div className="text-center mt-24 mb-12">
          {/* Features Hook */}
          <div className="mb-12">
            <h3 
              className="text-3xl md:text-4xl font-black text-slate-800 mb-6"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              Ready to experience <span className="text-indigo-600">enterprise-grade</span> compliance?
            </h3>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
              Join <span className="font-bold text-indigo-600">Fortune 500 companies</span> who trust TaxPoynt with their compliance. Every feature designed for <span className="font-bold text-indigo-600">Nigerian business excellence</span>.
            </p>
          </div>

          {/* Dramatic Features Summary Card */}
          <div className="relative max-w-4xl mx-auto mb-12">
            {/* Background Effects */}
            <div 
              className="absolute inset-0 bg-gradient-to-br from-indigo-500/15 via-blue-500/10 to-purple-500/15 rounded-3xl blur-xl" 
              aria-hidden="true"
            ></div>
            
            {/* Main Features Card */}
            <div 
              className="relative border-2 border-indigo-200/50 rounded-3xl p-8 md:p-12 shadow-2xl backdrop-blur-sm"
              style={ctaCardStyle}
            >
              
              {/* Features Statement */}
              <div className="mb-8">
                <h4 
                  className="text-2xl md:text-3xl font-bold text-slate-700 mb-4"
                  style={TYPOGRAPHY_STYLES.optimizedText}
                >
                  The most complete compliance platform in Nigeria
                </h4>
                <div className="text-xl md:text-2xl font-black text-indigo-600 mb-6">
                  🚀 Universal integration • 🛡️ Enterprise security • ⚡ Real-time sync • 🎯 Zero errors
                </div>
              </div>

              {/* Value Proposition */}
              <div className="mb-8">
                <p 
                  className="text-xl md:text-2xl font-bold text-slate-600 mb-4"
                  style={TYPOGRAPHY_STYLES.optimizedText}
                >
                  From <span className="text-red-500">manual chaos</span> to <span className="text-indigo-600">automated excellence</span>
                </p>
                <p className="text-lg text-slate-600 max-w-3xl mx-auto">
                  Every enterprise feature you need, perfectly integrated, completely automated.
                </p>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <TaxPoyntButton
                  variant="primary"
                  size="lg"
                  onClick={() => router.push('/auth/signup')}
                  className="text-xl px-12 py-6 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-indigo-500/40 transition-all duration-300 hover:scale-105"
                >
                  🎯 Start Enterprise Trial
                </TaxPoyntButton>
                
                <TaxPoyntButton
                  variant="outline"
                  size="lg"
                  onClick={() => {
                    document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="text-xl px-12 py-6 border-2 border-indigo-300 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-400 hover:text-indigo-900 font-bold rounded-2xl shadow-lg hover:shadow-indigo-200/50 transition-all duration-300"
                >
                  View Enterprise Pricing
                </TaxPoyntButton>
              </div>

              {/* Supporting Text */}
              <div className="mt-6 text-base text-slate-600">
                <span className="mr-2" aria-hidden="true">✨</span>
                Full-featured trial • No credit card • Enterprise support
                <span className="ml-2" aria-hidden="true">✨</span>
              </div>
              
              {/* Subtle Pattern Overlay */}
              <div 
                className="absolute inset-0 bg-gradient-to-br from-indigo-50/20 via-transparent to-blue-50/20 rounded-3xl pointer-events-none" 
                aria-hidden="true"
              ></div>
            </div>
          </div>

          {/* Feature Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            {[
              { number: "100+", label: "Integrations" },
              { number: "24/7", label: "Enterprise Support" },
              { number: "99.9%", label: "Uptime SLA" },
              { number: "< 2s", label: "Sync Speed" }
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div 
                  className="text-3xl md:text-4xl font-black text-indigo-600 mb-2"
                  style={{ textShadow: '0 2px 4px rgba(79, 70, 229, 0.3)' }}
                >
                  {stat.number}
                </div>
                <div className="text-slate-600 font-medium text-sm md:text-base">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>

          {/* Enterprise Promise */}
          <div className="inline-flex items-center px-6 py-3 bg-indigo-100/80 text-indigo-800 rounded-full text-base font-bold border border-indigo-200/50">
            <span className="mr-2" aria-hidden="true">🏆</span>
            Enterprise-grade platform trusted by Fortune 500 companies
            <span className="ml-2" aria-hidden="true">🏆</span>
          </div>
        </div>
      </div>
    </section>
  );
};
