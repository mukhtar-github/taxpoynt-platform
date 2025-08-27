/**
 * Enhanced Auth Layout Component
 * ==============================
 * Unified layout for all authentication pages using our refined design system
 */

import React from 'react';
import Link from 'next/link';
import { OptimizedImage } from '../../design_system/components/OptimizedImage';
import { 
  TYPOGRAPHY_STYLES, 
  getSectionBackground, 
  combineStyles,
  ACCESSIBILITY_PATTERNS 
} from '../../design_system/style-utilities';

export interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle: string;
  showBackToHome?: boolean;
  className?: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title,
  subtitle,
  showBackToHome = true,
  className = ''
}) => {
  const sectionBackground = getSectionBackground('indigo');
  
  const headlineStyle = combineStyles(
    TYPOGRAPHY_STYLES.sectionHeadline,
    {
      fontSize: 'clamp(1.5rem, 4vw, 2.5rem)',
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }
  );

  return (
    <div 
      className={`min-h-screen relative overflow-hidden ${className}`}
      style={sectionBackground.style}
    >
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 via-blue-600 to-purple-700" aria-hidden="true">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/10 via-transparent to-purple-900/10"></div>
        <div className="absolute inset-0 backdrop-blur-sm"></div>
      </div>

      {/* Content Container */}
      <div className="relative z-10 min-h-screen flex">
        
        {/* Left Panel - Branding & Info */}
        <div className="hidden lg:flex lg:w-1/2 flex-col justify-center px-12 text-white">
          
          {/* Logo & Branding */}
          <div className="mb-8">
            <div className="flex items-center space-x-4 mb-6">
              <OptimizedImage
                src="/logo.svg"
                alt="TaxPoynt Logo"
                width={64}
                height={64}
                className="w-16 h-16"
                priority={true}
              />
              <div>
                <div 
                  className="text-4xl font-bold text-white"
                  style={TYPOGRAPHY_STYLES.optimizedText}
                >
                  TaxPoynt
                </div>
                <div className="text-blue-200 text-lg font-medium">
                  Nigerian Tax Compliance Made Simple
                </div>
              </div>
            </div>
          </div>

          {/* Value Proposition */}
          <div className="space-y-6">
            <h1 
              className="text-5xl font-black text-white leading-tight"
              style={headlineStyle}
            >
              Join <span className="text-yellow-400">2,500+</span> Nigerian businesses
              <br />
              <span className="text-blue-200">saving millions</span>
            </h1>
            
            <p 
              className="text-xl text-blue-100 leading-relaxed max-w-lg"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              Automate your tax compliance, eliminate errors, and focus on growing your business. 
              <span className="text-yellow-400 font-semibold"> FIRS-certified</span> and 
              <span className="text-yellow-400 font-semibold"> enterprise-ready</span>.
            </p>

            {/* Trust Indicators */}
            <div className="flex items-center space-x-8 mt-8">
              {[
                { icon: "🏆", text: "FIRS Certified", detail: "Official Partner" },
                { icon: "🔒", text: "Bank-Level Security", detail: "ISO 27001 Compliant" },
                { icon: "⚡", text: "99.9% Uptime", detail: "Enterprise SLA" },
                { icon: "🎯", text: "Zero Rejections", detail: "100% Accuracy" }
              ].map((trust, index) => (
                <div key={index} className="text-center">
                  <div className="text-2xl mb-1">{trust.icon}</div>
                  <div className="text-sm font-bold text-white">{trust.text}</div>
                  <div className="text-xs text-blue-200">{trust.detail}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Customer Quote */}
          <div className="mt-12 p-6 bg-white/10 rounded-2xl backdrop-blur-sm border border-white/20">
            <blockquote className="text-lg text-blue-100 italic mb-4">
              "TaxPoynt transformed our compliance from a 40-hour weekly nightmare to a 2-minute automated process. 
              Best ROI we've ever achieved."
            </blockquote>
            <div className="text-sm">
              <div className="font-bold text-white">Adebayo Ogundimu</div>
              <div className="text-blue-200">CFO, Lagos Manufacturing Ltd</div>
            </div>
          </div>
        </div>

        {/* Right Panel - Auth Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center px-6 lg:px-12">
          <div className="w-full max-w-md">
            
            {/* Mobile Logo (hidden on lg+) */}
            <div className="lg:hidden text-center mb-8">
              <div className="flex items-center justify-center space-x-3 mb-4">
                <OptimizedImage
                  src="/logo.svg"
                  alt="TaxPoynt Logo"
                  width={48}
                  height={48}
                  className="w-12 h-12"
                  priority={true}
                />
                <div>
                  <div 
                    className="text-2xl font-bold text-white"
                    style={TYPOGRAPHY_STYLES.optimizedText}
                  >
                    TaxPoynt
                  </div>
                  <div className="text-blue-200 text-sm font-medium">
                    Tax Compliance Made Simple
                  </div>
                </div>
              </div>
            </div>

            {/* Form Header */}
            <div className="text-center mb-8">
              <h2 
                className="text-3xl font-black text-white mb-2"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                {title}
              </h2>
              <p 
                className="text-blue-200 text-lg"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                {subtitle}
              </p>
            </div>

            {/* Auth Form Card */}
            <div className="bg-white/95 backdrop-blur-lg rounded-3xl shadow-2xl p-8 border border-white/30">
              {children}
            </div>

            {/* Back to Home Link */}
            {showBackToHome && (
              <div className="text-center mt-6">
                <Link
                  href="/"
                  className="inline-flex items-center text-blue-200 hover:text-white transition-colors duration-200"
                  style={ACCESSIBILITY_PATTERNS.focusRing}
                >
                  <span className="mr-2">←</span>
                  Back to Home
                </Link>
              </div>
            )}

            {/* Footer Trust Signals */}
            <div className="mt-8 text-center">
              <div className="inline-flex items-center space-x-4 text-xs text-blue-200">
                <div className="flex items-center">
                  <span className="mr-1">🔒</span>
                  SSL Secured
                </div>
                <div className="flex items-center">
                  <span className="mr-1">🏛️</span>
                  FIRS Certified
                </div>
                <div className="flex items-center">
                  <span className="mr-1">🛡️</span>
                  NDPR Compliant
                </div>
                <div className="flex items-center">
                  <span className="mr-1">⚡</span>
                  99.9% Uptime
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
