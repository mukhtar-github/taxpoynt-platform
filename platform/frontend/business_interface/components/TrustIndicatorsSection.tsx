/**
 * Trust Indicators Section Component
 * ==================================
 * Extracted from LandingPage.tsx - Performance metrics and credibility section
 */

import React from 'react';
import { getSectionBackground, TYPOGRAPHY_STYLES, combineStyles } from '../../design_system/style-utilities';

export interface TrustIndicatorsProps {
  className?: string;
}

interface TrustCardProps {
  badge: string;
  metric: string | number;
  description: string;
  impact: string;
  color?: 'blue' | 'indigo' | 'green' | 'purple';
}

const TrustCard: React.FC<TrustCardProps> = ({ 
  badge, 
  metric, 
  description, 
  impact, 
  color = 'blue' 
}) => {
  const cardStyle = combineStyles(
    {
      background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #eef2ff 100%)',
      boxShadow: '0 10px 25px -5px rgba(59, 130, 246, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
    }
  );

  const metricStyle = combineStyles(
    {
      fontWeight: 950,
      textShadow: '0 4px 8px rgba(37, 99, 235, 0.3)'
    }
  );

  return (
    <div 
      className="group relative p-8 rounded-2xl shadow-xl hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-300 hover:-translate-y-1 cursor-pointer border border-blue-200/50 hover:border-blue-300/50 backdrop-blur-sm"
      style={cardStyle}
      role="article"
      aria-labelledby={`metric-${badge.replace(/\s+/g, '-').toLowerCase()}`}
    >
      
      {/* Premium Background Overlay */}
      <div 
        className="absolute inset-0 bg-gradient-to-br from-blue-50/20 via-transparent to-indigo-50/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" 
        aria-hidden="true"
      ></div>
      
      {/* Content */}
      <div className="relative z-10 text-center">
        {/* Performance Badge */}
        <div className="mb-4">
          <span className="inline-block px-3 py-1 bg-blue-100/80 text-blue-700 text-xs font-bold rounded-full border border-blue-200/50">
            {badge}
          </span>
        </div>
        
        {/* Large Metric */}
        <div 
          id={`metric-${badge.replace(/\s+/g, '-').toLowerCase()}`}
          className="text-6xl md:text-7xl font-black text-blue-600 mb-4 leading-none"
          style={metricStyle}
        >
          {metric}
        </div>
        
        {/* Description */}
        <div 
          className="text-slate-700 font-semibold text-lg md:text-xl leading-tight mb-6"
          style={TYPOGRAPHY_STYLES.optimizedText}
        >
          {description}
        </div>
        
        {/* Impact Badge */}
        <div className="mb-4">
          <div className="inline-block px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-full text-sm font-bold shadow-lg">
            {impact}
          </div>
        </div>
      </div>
      
      {/* Hover Glow Effect */}
      <div 
        className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/5 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" 
        aria-hidden="true"
      ></div>
    </div>
  );
};

export const TrustIndicatorsSection: React.FC<TrustIndicatorsProps> = ({ className = '' }) => {
  const sectionBackground = getSectionBackground('blue');
  
  const headlineStyle = combineStyles(
    TYPOGRAPHY_STYLES.sectionHeadline,
    {
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }
  );

  const trustData: TrustCardProps[] = [
    {
      badge: "Error Rate",
      metric: "Zero",
      description: "E-invoice submission errors",
      impact: "100% Success Rate"
    },
    {
      badge: "Processing Time", 
      metric: "2min",
      description: "From sale to compliance submission",
      impact: "Lightning Fast"
    },
    {
      badge: "Compliance Coverage",
      metric: "100%",
      description: "Nigerian tax requirements covered",
      impact: "Full Compliance"
    },
    {
      badge: "Customer Satisfaction",
      metric: "99.8%",
      description: "Enterprise customer satisfaction rate",
      impact: "Proven Excellence"
    }
  ];

  return (
    <section 
      className={`py-20 relative overflow-hidden ${sectionBackground.className} ${className}`}
      style={sectionBackground.style}
      aria-labelledby="trust-indicators-headline"
    >
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Enhanced Section Header */}
        <div className="text-center mb-20">
          {/* Premium Badge - Blue Theme */}
          <div 
            className="inline-flex items-center px-8 py-4 border-2 border-blue-200/50 text-blue-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-blue-200/40 transition-all duration-300 hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, rgba(239, 246, 255, 0.95) 0%, rgba(238, 242, 255, 0.95) 100%)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <span className="w-3 h-3 rounded-full mr-3 bg-blue-700" aria-hidden="true"></span>
            Enterprise Performance Metrics
          </div>
          
          {/* Dramatic Headline */}
          <div className="relative mb-8">
            <h2 
              id="trust-indicators-headline"
              className="text-5xl md:text-7xl font-black text-blue-900 mb-4 leading-[0.9] tracking-tight"
              style={headlineStyle}
            >
              <span className="text-slate-700">Results that speak</span>
              <br />
              <span className="relative inline-block">
                <span 
                  className="text-blue-600 italic font-black"
                  style={{ 
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(37, 99, 235, 0.3)'
                  }}
                >
                  for themselves
                </span>
                {/* Dramatic underline effect */}
                <div 
                  className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-blue-500 rounded-full opacity-90" 
                  aria-hidden="true"
                ></div>
              </span>
            </h2>
          </div>
          
          {/* Enhanced Subtitle */}
          <p 
            className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-medium"
            style={combineStyles(TYPOGRAPHY_STYLES.optimizedText, {
              textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
            })}
          >
            See the <span className="text-blue-600 font-bold">measurable impact</span> TaxPoynt delivers to Nigerian enterprises every day.
          </p>
        </div>

        {/* Premium Trust Cards Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
          {trustData.map((trust, index) => (
            <TrustCard
              key={index}
              badge={trust.badge}
              metric={trust.metric}
              description={trust.description}
              impact={trust.impact}
            />
          ))}
        </div>

        {/* Premium Bottom Section */}
        <div className="text-center">
          {/* Supporting Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            {[
              { number: "50,000+", label: "Invoices Processed" },
              { number: "2,500+", label: "Active Businesses" },
              { number: "₦2.4B+", label: "Transaction Value" },
              { number: "24/7", label: "Nigeria Support" }
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div 
                  className="text-3xl md:text-4xl font-black text-blue-600 mb-2"
                  style={{ textShadow: '0 2px 4px rgba(37, 99, 235, 0.2)' }}
                >
                  {stat.number}
                </div>
                <div className="text-slate-600 font-medium text-sm md:text-base">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>

          {/* Trust Guarantee */}
          <div className="inline-flex items-center px-6 py-3 bg-green-100/80 text-green-800 rounded-full text-base font-bold border border-green-200/50">
            <span className="mr-2" aria-hidden="true">🛡️</span>
            99.9% Uptime Guarantee • Enterprise SLA
            <span className="ml-2" aria-hidden="true">🛡️</span>
          </div>
        </div>
      </div>
    </section>
  );
};
