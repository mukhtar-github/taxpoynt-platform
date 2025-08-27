/**
 * Pricing Section Component
 * =========================
 * Extracted from LandingPage.tsx - Service packages and pricing showcase
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { PricingCard, TaxPoyntButton, SERVICE_PACKAGES_DATA } from '../../design_system';
import { getSectionBackground, TYPOGRAPHY_STYLES, combineStyles } from '../../design_system/style-utilities';

export interface PricingSectionProps {
  className?: string;
}

export const PricingSection: React.FC<PricingSectionProps> = ({ className = '' }) => {
  const router = useRouter();
  const sectionBackground = getSectionBackground('teal');
  
  const headlineStyle = combineStyles(
    TYPOGRAPHY_STYLES.sectionHeadline,
    {
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }
  );

  const pricingData = [
    {
      name: "Starter",
      subtitle: "Perfect for small businesses",
      price: "₦15,000",
      period: "/month",
      originalPrice: "₦25,000",
      savings: "Save 40%",
      badge: "Most Popular",
      badgeColor: "bg-green-500",
      features: [
        "Up to 100 invoices/month",
        "Basic ERP integrations (Odoo, QuickBooks)",
        "Standard FIRS compliance",
        "Email support",
        "Mobile app access",
        "Basic reporting",
        "Real-time sync"
      ],
      limits: [
        "Single business location",
        "Standard processing speed"
      ],
      cta: "Start Free Trial",
      recommended: true
    },
    {
      name: "Professional",
      subtitle: "For growing enterprises",
      price: "₦45,000",
      period: "/month",
      originalPrice: "₦65,000",
      savings: "Save 31%",
      badge: "Enterprise Ready",
      badgeColor: "bg-blue-500",
      features: [
        "Up to 1,000 invoices/month",
        "Premium integrations (SAP, Salesforce)",
        "Advanced compliance features",
        "Priority support",
        "Custom workflows",
        "Advanced analytics",
        "Multi-currency support",
        "API access",
        "White-label options"
      ],
      limits: [
        "Up to 5 business locations",
        "Priority processing"
      ],
      cta: "Upgrade to Professional",
      recommended: false
    },
    {
      name: "Enterprise",
      subtitle: "For large organizations",
      price: "Custom",
      period: "pricing",
      originalPrice: null,
      savings: "Volume Discounts",
      badge: "Fortune 500",
      badgeColor: "bg-purple-500",
      features: [
        "Unlimited invoices",
        "All integrations included",
        "Dedicated compliance manager",
        "24/7 phone support",
        "Custom development",
        "Advanced security",
        "SLA guarantees",
        "Training included",
        "Dedicated infrastructure"
      ],
      limits: [
        "Unlimited locations",
        "Instant processing",
        "Dedicated account manager"
      ],
      cta: "Contact Sales",
      recommended: false
    }
  ];

  return (
    <section 
      id="pricing"
      className={`py-20 relative overflow-hidden ${sectionBackground.className} ${className}`}
      style={sectionBackground.style}
      aria-labelledby="pricing-headline"
    >
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Enhanced Section Header */}
        <div className="text-center mb-20">
          {/* Premium Badge - Teal Theme */}
          <div 
            className="inline-flex items-center px-8 py-4 border-2 border-teal-200/50 text-teal-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-teal-200/40 transition-all duration-300 hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, rgba(240, 253, 250, 0.95) 0%, rgba(204, 251, 241, 0.95) 100%)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <span className="w-3 h-3 rounded-full mr-3 bg-teal-700" aria-hidden="true"></span>
            Transparent Enterprise Pricing
          </div>
          
          {/* Dramatic Headline */}
          <div className="relative mb-8">
            <h2 
              id="pricing-headline"
              className="text-5xl md:text-7xl font-black text-teal-900 mb-4 leading-[0.9] tracking-tight"
              style={headlineStyle}
            >
              <span className="text-slate-700">Simple pricing that</span>
              <br />
              <span className="relative inline-block">
                <span 
                  className="text-teal-600 italic font-black"
                  style={{ 
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(20, 184, 166, 0.4)'
                  }}
                >
                  scales with you
                </span>
                {/* Dramatic underline effect */}
                <div 
                  className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 via-cyan-500 to-teal-500 rounded-full opacity-90" 
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
            Choose the perfect plan for your business. <span className="text-teal-600 font-bold">Start free</span>, upgrade anytime, cancel whenever you want.
          </p>
        </div>

        {/* Pricing Toggle */}
        <div className="flex justify-center mb-12">
          <div className="bg-white p-2 rounded-full shadow-lg border border-gray-200">
            <div className="flex">
              <button className="px-6 py-2 rounded-full bg-teal-500 text-white font-bold text-sm">
                Monthly Billing
              </button>
              <button className="px-6 py-2 rounded-full text-gray-600 font-bold text-sm hover:text-teal-600">
                Annual Billing <span className="text-green-600 text-xs">(Save 40%)</span>
              </button>
            </div>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 mb-20">
          {pricingData.map((plan, index) => (
            <div 
              key={index}
              className={`relative bg-white rounded-3xl shadow-xl border-2 transition-all duration-300 hover:shadow-2xl hover:-translate-y-2 ${
                plan.recommended 
                  ? 'border-green-300 transform scale-105' 
                  : 'border-gray-200 hover:border-teal-300'
              }`}
            >
              
              {/* Popular Badge */}
              {plan.recommended && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white px-6 py-2 rounded-full font-bold text-sm shadow-lg">
                    ⭐ Most Popular Choice
                  </div>
                </div>
              )}

              {/* Plan Badge */}
              <div className="absolute -top-2 right-4">
                <div className={`${plan.badgeColor} text-white px-4 py-1 rounded-full font-bold text-xs`}>
                  {plan.badge}
                </div>
              </div>

              <div className="p-8">
                
                {/* Plan Header */}
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-black text-slate-800 mb-2">
                    {plan.name}
                  </h3>
                  <p className="text-slate-600 mb-6">
                    {plan.subtitle}
                  </p>
                  
                  {/* Pricing */}
                  <div className="mb-4">
                    {plan.originalPrice && (
                      <div className="flex items-center justify-center mb-2">
                        <span className="text-lg text-gray-400 line-through mr-2">
                          {plan.originalPrice}
                        </span>
                        <span className="bg-red-100 text-red-600 px-2 py-1 rounded text-sm font-bold">
                          {plan.savings}
                        </span>
                      </div>
                    )}
                    
                    <div className="flex items-baseline justify-center">
                      <span className="text-4xl font-black text-teal-600">
                        {plan.price}
                      </span>
                      <span className="text-slate-500 ml-2">
                        {plan.period}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Features List */}
                <div className="mb-8">
                  <h4 className="font-bold text-slate-800 mb-4">Everything included:</h4>
                  <ul className="space-y-3">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-start">
                        <span className="text-green-500 mr-3 text-sm">✅</span>
                        <span className="text-slate-600 text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Limits */}
                {plan.limits.length > 0 && (
                  <div className="mb-8">
                    <h4 className="font-bold text-slate-800 mb-4">Plan includes:</h4>
                    <ul className="space-y-2">
                      {plan.limits.map((limit, limitIndex) => (
                        <li key={limitIndex} className="flex items-start">
                          <span className="text-blue-500 mr-3 text-sm">ℹ️</span>
                          <span className="text-slate-600 text-sm">{limit}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* CTA Button */}
                <TaxPoyntButton
                  variant={plan.recommended ? "primary" : "outline"}
                  onClick={() => {
                    if (plan.name === "Enterprise") {
                      router.push('/contact-sales');
                    } else {
                      router.push('/auth/signup');
                    }
                  }}
                  className={`w-full py-4 font-bold text-lg rounded-2xl transition-all duration-300 ${
                    plan.recommended 
                      ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white shadow-lg hover:shadow-green-500/40 hover:scale-105' 
                      : 'border-2 border-teal-300 text-teal-700 hover:bg-teal-50 hover:border-teal-400 hover:text-teal-900 hover:scale-105'
                  }`}
                >
                  {plan.cta}
                </TaxPoyntButton>

                {/* Free Trial Note */}
                {plan.name !== "Enterprise" && (
                  <p className="text-center text-sm text-slate-500 mt-4">
                    14-day free trial • No credit card required
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Enterprise Contact Section */}
        <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-3xl p-8 md:p-12 text-white mb-20">
          <div className="text-center">
            <h3 className="text-3xl md:text-4xl font-black mb-4">
              🏢 Enterprise & Government Solutions
            </h3>
            <p className="text-xl mb-8 opacity-90">
              Custom solutions for large organizations, government agencies, and Fortune 500 companies
            </p>
            
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              {[
                {
                  feature: "Volume Discounts",
                  detail: "Save up to 60% on enterprise volumes"
                },
                {
                  feature: "Dedicated Support",
                  detail: "24/7 dedicated compliance managers"
                },
                {
                  feature: "Custom Development",
                  detail: "Tailored integrations and features"
                }
              ].map((item, index) => (
                <div key={index} className="text-center">
                  <div className="font-bold text-lg mb-2">{item.feature}</div>
                  <div className="text-sm opacity-80">{item.detail}</div>
                </div>
              ))}
            </div>
            
            <TaxPoyntButton
              variant="secondary"
              size="lg"
              onClick={() => router.push('/enterprise-demo')}
              className="bg-white text-purple-600 hover:bg-gray-50 font-bold px-12 py-4 rounded-2xl shadow-lg hover:shadow-white/20 transition-all duration-300 hover:scale-105"
            >
              Schedule Enterprise Demo
            </TaxPoyntButton>
          </div>
        </div>

        {/* ROI Calculator */}
        <div className="mb-20">
          <h3 
            className="text-3xl md:text-4xl font-black text-center text-slate-800 mb-12"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Calculate Your <span className="text-teal-600">ROI</span>
          </h3>
          
          <div className="bg-white rounded-3xl p-8 shadow-xl border border-gray-100">
            <div className="grid md:grid-cols-2 gap-8">
              
              {/* Calculator Inputs */}
              <div>
                <h4 className="text-xl font-bold text-slate-800 mb-6">Your Current Situation</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Monthly invoices processed
                    </label>
                    <select className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500">
                      <option>50-100 invoices</option>
                      <option>100-500 invoices</option>
                      <option>500-1000 invoices</option>
                      <option>1000+ invoices</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Current rejection rate
                    </label>
                    <select className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500">
                      <option>20-40% rejections</option>
                      <option>40-60% rejections</option>
                      <option>60%+ rejections</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Hours spent weekly on tax compliance
                    </label>
                    <select className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500">
                      <option>5-10 hours</option>
                      <option>10-20 hours</option>
                      <option>20+ hours</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* ROI Results */}
              <div className="bg-gradient-to-br from-teal-50 to-cyan-50 p-6 rounded-2xl">
                <h4 className="text-xl font-bold text-slate-800 mb-6">Your Potential Savings</h4>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-white rounded-lg">
                    <span className="text-slate-600">Time saved monthly:</span>
                    <span className="font-bold text-green-600">32 hours</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white rounded-lg">
                    <span className="text-slate-600">Cost savings per year:</span>
                    <span className="font-bold text-green-600">₦2.4M</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white rounded-lg">
                    <span className="text-slate-600">ROI in 12 months:</span>
                    <span className="font-bold text-green-600">340%</span>
                  </div>
                  <div className="bg-green-100 p-4 rounded-lg text-center">
                    <div className="text-2xl font-black text-green-600 mb-1">
                      ₦2.4M
                    </div>
                    <div className="text-sm text-green-700">
                      Total annual savings with TaxPoynt
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="text-center mt-8">
              <TaxPoyntButton
                variant="primary"
                size="lg"
                onClick={() => router.push('/auth/signup')}
                className="bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700 text-white font-bold px-12 py-4 rounded-2xl shadow-lg hover:shadow-teal-500/40 transition-all duration-300 hover:scale-105"
              >
                Start Saving Today
              </TaxPoyntButton>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mb-20">
          <h3 
            className="text-3xl md:text-4xl font-black text-center text-slate-800 mb-12"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Pricing <span className="text-teal-600">Questions</span>?
          </h3>
          
          <div className="grid md:grid-cols-2 gap-8">
            {[
              {
                question: "Can I change plans anytime?",
                answer: "Yes! Upgrade or downgrade your plan anytime. Changes take effect immediately, and we'll prorate any billing differences."
              },
              {
                question: "What happens if I exceed my invoice limit?",
                answer: "You'll be automatically upgraded to the next tier for that month. No overage fees, just fair pricing that scales with your business."
              },
              {
                question: "Do you offer discounts for annual billing?",
                answer: "Yes! Annual billing saves you 40% compared to monthly billing. Plus, you get priority support and additional features."
              },
              {
                question: "Is there a setup fee?",
                answer: "No setup fees, ever. We include free onboarding, training, and integration support with all plans."
              },
              {
                question: "What's included in the free trial?",
                answer: "Full access to all Professional plan features for 14 days. No credit card required, no limitations, cancel anytime."
              },
              {
                question: "Do you offer refunds?",
                answer: "Yes! 30-day money-back guarantee on all plans. If you're not completely satisfied, we'll refund your payment."
              }
            ].map((faq, index) => (
              <div key={index} className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
                <h4 className="font-bold text-slate-800 mb-3">{faq.question}</h4>
                <p className="text-slate-600">{faq.answer}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Final Pricing CTA */}
        <div className="text-center">
          <div className="mb-8">
            <h3 
              className="text-3xl md:text-4xl font-black text-slate-800 mb-6"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              Ready to <span className="text-teal-600">get started</span>?
            </h3>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
              Join thousands of Nigerian businesses saving time and money with TaxPoynt. <span className="font-bold text-teal-600">Start your free trial today</span>.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <TaxPoyntButton
              variant="primary"
              size="lg"
              onClick={() => router.push('/auth/signup')}
              className="text-xl px-12 py-6 bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-teal-500/40 transition-all duration-300 hover:scale-105"
            >
              🚀 Start Free Trial
            </TaxPoyntButton>
            
            <TaxPoyntButton
              variant="outline"
              size="lg"
              onClick={() => router.push('/demo')}
              className="text-xl px-12 py-6 border-2 border-teal-300 text-teal-700 hover:bg-teal-50 hover:border-teal-400 hover:text-teal-900 font-bold rounded-2xl shadow-lg hover:shadow-teal-200/50 transition-all duration-300"
            >
              Watch Demo
            </TaxPoyntButton>
          </div>

          {/* Trust Signals */}
          <div className="inline-flex items-center px-6 py-3 bg-teal-100/80 text-teal-800 rounded-full text-base font-bold border border-teal-200/50">
            <span className="mr-2" aria-hidden="true">🔒</span>
            No credit card required • Cancel anytime • 30-day money back guarantee
            <span className="ml-2" aria-hidden="true">🔒</span>
          </div>
        </div>
      </div>
    </section>
  );
};
