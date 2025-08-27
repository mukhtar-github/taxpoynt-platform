/**
 * TaxPoynt Professional Landing Page
 * =================================
 * Clean, professional landing page focused on conversion and clarity.
 */

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  TaxPoyntButton, 
  HeroCTAButton, 
  ProblemCard,
  SolutionCard,
  FeatureCard,
  BeforeAfterCard,
  PricingCard,
  PROBLEMS_DATA,
  ENTERPRISE_SOLUTIONS_DATA,
  ENTERPRISE_FEATURES_DATA,
  BEFORE_AFTER_DATA,
  SERVICE_PACKAGES_DATA,
  buildGridClasses,
  TAXPOYNT_DESIGN_SYSTEM 
} from '../design_system';

export const LandingPage: React.FC = () => {
  const router = useRouter();

  const handlePackageSelect = (packageId: string) => {
    // Navigate to signup with selected package (default to monthly)
    router.push(`/auth/signup?package=${packageId}&billing=monthly`);
  };

  return (
    <div className="min-h-screen bg-gray-50" style={{ 
      fontFeatureSettings: '"kern" 1, "liga" 1', 
      textRendering: 'optimizeLegibility', 
      WebkitFontSmoothing: 'antialiased', 
      MozOsxFontSmoothing: 'grayscale' 
    }}>
      
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
              onClick={() => router.push('/auth/signup')}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold"
            >
              Get Started
            </TaxPoyntButton>
          </div>
        </div>
      </nav>

      {/* Hero Section - Premium Enterprise Crown Jewel */}
      <section className="relative px-6 py-24 overflow-hidden bg-gradient-to-br from-indigo-50 via-blue-50/30 to-purple-50 min-h-screen flex items-center" 
               style={{ 
                 background: 'linear-gradient(135deg, #eef2ff 0%, #f0f9ff 30%, #faf5ff 70%, #ffffff 100%)',
                 boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.9)' 
               }}>
        
        {/* Premium Background Patterns */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-gradient-to-br from-blue-400/15 to-indigo-400/15 rounded-full filter blur-3xl"></div>
          <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-gradient-to-br from-emerald-400/10 to-green-400/10 rounded-full filter blur-3xl"></div>
          <div className="absolute bottom-1/4 left-1/2 w-72 h-72 bg-gradient-to-br from-violet-400/8 to-purple-400/8 rounded-full filter blur-3xl"></div>
          {/* Subtle texture overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-white/40 via-transparent to-indigo-50/20"></div>
        </div>
        
        <div className="max-w-6xl mx-auto text-center relative z-10">
          
          {/* Enhanced Section Header */}
          <div className="mb-16">
            {/* Premium Badge - Indigo Theme */}
            <div className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-indigo-50/95 to-blue-50/95 backdrop-blur-sm border-2 border-indigo-200/50 text-indigo-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-indigo-200/40 transition-all duration-300 hover:scale-105" 
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   background: 'linear-gradient(135deg, rgba(238, 242, 255, 0.95) 0%, rgba(239, 246, 255, 0.95) 100%)',
                   backdropFilter: 'blur(10px)'
                 }}>
              <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: '#3730a3' }}></span>
              FIRS Certified Access Point Provider
            </div>

            {/* Enterprise Impact Statement */}
            <div className="mb-8">
              <div className="inline-block bg-gradient-to-r from-purple-100/90 to-indigo-100/90 text-purple-700 px-12 py-4 rounded-full text-xl font-bold mb-8 shadow-xl hover:shadow-purple-200/40 transition-all duration-300 hover:scale-105 border border-purple-300/40 backdrop-blur-sm"
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     background: 'linear-gradient(135deg, rgba(243, 232, 255, 0.9) 0%, rgba(238, 242, 255, 0.9) 100%)'
                   }}>
                Transform compliance from cost center to competitive advantage
              </div>
            </div>
            
            {/* Dramatic Enterprise Headline */}
            <div className="relative mb-12">
              <h1 className="text-6xl md:text-8xl font-black text-indigo-900 mb-8 leading-[0.9] tracking-tight" 
                  style={{ 
                    textRendering: 'optimizeLegibility', 
                    WebkitFontSmoothing: 'antialiased',
                    fontWeight: 950,
                    textShadow: '0 4px 8px rgba(0,0,0,0.1)'
                  }}>
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
                  <div className="absolute -bottom-3 left-0 right-0 h-2 bg-gradient-to-r from-green-500 via-emerald-500 to-green-500 rounded-full opacity-90"></div>
                </span>
              </h1>
            </div>

            {/* Enhanced Enterprise Subtitle */}
            <p className="text-2xl md:text-3xl text-slate-600 mb-16 max-w-5xl mx-auto font-medium leading-relaxed" 
               style={{ 
                 textRendering: 'optimizeLegibility', 
                 WebkitFontSmoothing: 'antialiased',
                 textShadow: '0 2px 4px rgba(100, 116, 139, 0.2)'
               }}>
              Stop wasting <span className="text-indigo-600 font-bold">enterprise resources</span> on compliance paperwork. TaxPoynt's <span className="text-green-600 font-bold">universal integration platform</span> connects your business software directly to government systems—transforming hours of manual work into seconds of automated compliance.
            </p>
          </div>

          {/* Premium Enterprise CTA Section */}
          <div className="relative max-w-4xl mx-auto mb-20">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-blue-500/5 to-purple-500/10 rounded-3xl blur-xl"></div>
            
            {/* Main CTA Card */}
            <div className="relative bg-gradient-to-br from-white/95 via-indigo-50/90 to-white/95 
                            border-2 border-indigo-200/50 rounded-3xl p-8 md:p-12 
                            shadow-2xl backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(238,242,255,0.9) 50%, rgba(255,255,255,0.95) 100%)',
                   backdropFilter: 'blur(16px)',
                   boxShadow: '0 25px 50px -12px rgba(79, 70, 229, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
                 }}>
              
              {/* CTA Header */}
              <div className="mb-8">
                <p className="text-2xl md:text-3xl font-bold text-slate-600 mb-4"
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     textShadow: '0 2px 4px rgba(100, 116, 139, 0.1)'
                   }}>
                  Ready to transform your enterprise compliance?
                </p>
                <p className="text-3xl md:text-4xl font-black text-indigo-600"
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     fontWeight: 950,
                     textShadow: '0 2px 4px rgba(99, 102, 241, 0.3)'
                   }}>
                  Join thousands of enterprises already automated.
                </p>
              </div>

              {/* Premium CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-6 justify-center">
                <HeroCTAButton
                  onClick={() => router.push('/auth/signup')}
                  className="group relative text-2xl px-20 py-7 bg-gradient-to-r from-indigo-600 via-blue-600 to-purple-600 hover:from-indigo-700 hover:via-blue-700 hover:to-purple-700 text-white font-bold rounded-3xl shadow-2xl hover:shadow-indigo-500/50 transition-all duration-500 hover:scale-105 transform border border-white/20"
                  style={{
                    background: 'linear-gradient(135deg, #4f46e5 0%, #2563eb 50%, #7c3aed 100%)',
                    boxShadow: '0 25px 50px -12px rgba(79, 70, 229, 0.4), 0 10px 20px -4px rgba(0, 0, 0, 0.1), inset 0 2px 0 rgba(255, 255, 255, 0.2)',
                    textRendering: 'optimizeLegibility',
                    WebkitFontSmoothing: 'antialiased'
                  }}
                >
                  <span className="relative z-10 flex items-center justify-center">
                    ✨ Start Enterprise Transformation
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </HeroCTAButton>
                
                <TaxPoyntButton
                  variant="secondary"
                  size="lg"
                  onClick={() => {
                    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="text-2xl px-16 py-7 border-2 border-indigo-300 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-400 hover:text-indigo-900 font-bold rounded-3xl shadow-xl hover:shadow-indigo-300/50 transition-all duration-300 hover:scale-105 transform bg-white/90 backdrop-blur-sm"
                  style={{
                    textRendering: 'optimizeLegibility',
                    WebkitFontSmoothing: 'antialiased'
                  }}
                >
                  See Platform Capabilities
                </TaxPoyntButton>
              </div>

              {/* Supporting Text */}
              <div className="mt-8 text-lg text-slate-600 font-medium">
                <span className="mr-2">🚀</span>
                No setup fees • 14-day free trial • Cancel anytime
                <span className="ml-2">🚀</span>
              </div>
              
              {/* Subtle Pattern Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/20 via-transparent to-purple-50/20 rounded-3xl pointer-events-none"></div>
            </div>
          </div>

          {/* Removed basic trust indicators - moved to sophisticated dedicated section */}
        </div>
      </section>

      {/* Enhanced Section Transition */}
      <div className="relative h-32">
        {/* Multi-layered Depth Effect */}
        <div className="absolute inset-0 bg-gradient-to-b from-slate-100/30 via-slate-50/20 to-transparent h-12"></div>
        <div className="absolute inset-0 bg-gradient-to-b from-slate-200/20 to-transparent h-16"></div>
        
        {/* Main Gradient Transition */}
        <div className="h-full bg-gradient-to-b from-slate-50/40 via-white/60 to-white relative">
          {/* Enhanced Divider Line */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-px bg-gradient-to-r from-transparent via-slate-300/60 to-transparent"></div>
          
          {/* Premium Accent Elements */}
          <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 w-40 h-1 bg-gradient-to-r from-emerald-500 via-blue-500 to-purple-500 rounded-full opacity-30 shadow-lg blur-sm"></div>
          <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 w-24 h-0.5 bg-gradient-to-r from-emerald-400 via-blue-400 to-purple-400 rounded-full opacity-70"></div>
          
          {/* Subtle Pattern */}
          <div className="absolute inset-0 bg-gradient-to-br from-white/40 via-transparent to-slate-50/20"></div>
        </div>
        
        {/* Professional Drop Shadow */}
        <div className="absolute inset-x-0 bottom-0 h-6 bg-gradient-to-b from-black/3 to-transparent"></div>
      </div>

      {/* Section 2: Premium Trust Indicators - Upgraded to Match Solutions Quality */}
      <section className="py-20 bg-gradient-to-br from-blue-50 via-indigo-50/30 to-blue-50 relative overflow-hidden" style={{ 
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.8), 0 4px 12px rgba(59, 130, 246, 0.08)' 
      }}>
        <div className="max-w-6xl mx-auto px-6">
          
          {/* Enhanced Section Header */}
          <div className="text-center mb-20">
            {/* Premium Badge - Blue Theme */}
            <div className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-50/95 to-indigo-50/95 backdrop-blur-sm border-2 border-blue-200/50 text-blue-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-blue-200/40 transition-all duration-300 hover:scale-105"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   background: 'linear-gradient(135deg, rgba(239, 246, 255, 0.95) 0%, rgba(238, 242, 255, 0.95) 100%)',
                   backdropFilter: 'blur(10px)'
                 }}>
              <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: '#1e40af' }}></span>
              Enterprise Performance Metrics
            </div>
            
            {/* Dramatic Headline */}
            <div className="relative mb-8">
              <h2 className="text-5xl md:text-7xl font-black text-blue-900 mb-4 leading-[0.9] tracking-tight"
                  style={{ 
                    textRendering: 'optimizeLegibility', 
                    WebkitFontSmoothing: 'antialiased',
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}>
                <span className="text-slate-700">Results that speak</span>
                <br />
                <span className="relative inline-block">
                  <span className="text-blue-600 italic font-black"
                        style={{ 
                          fontWeight: 950,
                          textShadow: '0 2px 4px rgba(37, 99, 235, 0.3)'
                        }}>
                    for themselves
                  </span>
                  {/* Dramatic underline effect */}
                  <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-blue-500 rounded-full opacity-90"></div>
                </span>
              </h2>
            </div>
            
            {/* Enhanced Subtitle */}
            <p className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-medium"
               style={{ 
                 textRendering: 'optimizeLegibility', 
                 WebkitFontSmoothing: 'antialiased',
                 textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
               }}>
              See the <span className="text-blue-600 font-bold">measurable impact</span> TaxPoynt delivers to Nigerian enterprises every day.
            </p>
          </div>

          {/* Premium Trust Cards Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
            
            {/* Trust Card 1 - Zero Errors */}
            <div className="group relative p-8 bg-gradient-to-br from-blue-50 via-white to-indigo-50/50 rounded-2xl 
                            shadow-xl hover:shadow-2xl hover:shadow-blue-500/10 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-blue-200/50 hover:border-blue-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #eef2ff 100%)',
                   boxShadow: '0 10px 25px -5px rgba(59, 130, 246, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50/20 via-transparent to-indigo-50/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10 text-center">
                {/* Performance Badge */}
                <div className="mb-4">
                  <span className="inline-block px-3 py-1 bg-blue-100/80 text-blue-700 text-xs font-bold rounded-full border border-blue-200/50">
                    Error Rate
                  </span>
                </div>
                
                {/* Large Metric */}
                <div className="text-6xl md:text-7xl font-black text-blue-600 mb-4 leading-none"
                     style={{
                       fontWeight: 950,
                       textShadow: '0 4px 8px rgba(37, 99, 235, 0.3)'
                     }}>
                  Zero
                </div>
                
                {/* Description */}
                <div className="text-slate-700 font-semibold text-lg md:text-xl leading-tight mb-6"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                  E-invoice submission errors
                </div>
                
                {/* Impact Badge */}
                <div className="mb-4">
                  <div className="inline-block px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-full text-sm font-bold shadow-lg">
                    100% Success Rate
                  </div>
                </div>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/5 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            {/* Trust Card 2 - Speed */}
            <div className="group relative p-8 bg-gradient-to-br from-blue-50 via-white to-indigo-50/50 rounded-2xl 
                            shadow-xl hover:shadow-2xl hover:shadow-blue-500/10 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-blue-200/50 hover:border-blue-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #eef2ff 100%)',
                   boxShadow: '0 10px 25px -5px rgba(59, 130, 246, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50/20 via-transparent to-indigo-50/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10 text-center">
                {/* Performance Badge */}
                <div className="mb-4">
                  <span className="inline-block px-3 py-1 bg-blue-100/80 text-blue-700 text-xs font-bold rounded-full border border-blue-200/50">
                    Processing Time
                  </span>
                </div>
                
                {/* Large Metric */}
                <div className="text-6xl md:text-7xl font-black text-blue-600 mb-4 leading-none"
                     style={{
                       fontWeight: 950,
                       textShadow: '0 4px 8px rgba(37, 99, 235, 0.3)'
                     }}>
                  2min
                </div>
                
                {/* Description */}
                <div className="text-slate-700 font-semibold text-lg md:text-xl leading-tight mb-6"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                  From sale to compliance submission
                </div>
                
                {/* Impact Badge */}
                <div className="mb-4">
                  <div className="inline-block px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-full text-sm font-bold shadow-lg">
                    Lightning Fast
                  </div>
                </div>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/5 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            {/* Trust Card 3 - Coverage */}
            <div className="group relative p-8 bg-gradient-to-br from-blue-50 via-white to-indigo-50/50 rounded-2xl 
                            shadow-xl hover:shadow-2xl hover:shadow-blue-500/10 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-blue-200/50 hover:border-blue-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #eef2ff 100%)',
                   boxShadow: '0 10px 25px -5px rgba(59, 130, 246, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50/20 via-transparent to-indigo-50/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10 text-center">
                {/* Performance Badge */}
                <div className="mb-4">
                  <span className="inline-block px-3 py-1 bg-blue-100/80 text-blue-700 text-xs font-bold rounded-full border border-blue-200/50">
                    Compliance Coverage
                  </span>
                </div>
                
                {/* Large Metric */}
                <div className="text-6xl md:text-7xl font-black text-blue-600 mb-4 leading-none"
                     style={{
                       fontWeight: 950,
                       textShadow: '0 4px 8px rgba(37, 99, 235, 0.3)'
                     }}>
                  100%
                </div>
                
                {/* Description */}
                <div className="text-slate-700 font-semibold text-lg md:text-xl leading-tight mb-6"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                  Nigerian compliance coverage
                </div>
                
                {/* Impact Badge */}
                <div className="mb-4">
                  <div className="inline-block px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-full text-sm font-bold shadow-lg">
                    FIRS Certified
                  </div>
                </div>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/5 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            {/* Trust Card 4 - Integration */}
            <div className="group relative p-8 bg-gradient-to-br from-blue-50 via-white to-indigo-50/50 rounded-2xl 
                            shadow-xl hover:shadow-2xl hover:shadow-blue-500/10 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-blue-200/50 hover:border-blue-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #eef2ff 100%)',
                   boxShadow: '0 10px 25px -5px rgba(59, 130, 246, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50/20 via-transparent to-indigo-50/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10 text-center">
                {/* Performance Badge */}
                <div className="mb-4">
                  <span className="inline-block px-3 py-1 bg-blue-100/80 text-blue-700 text-xs font-bold rounded-full border border-blue-200/50">
                    System Integration
                  </span>
                </div>
                
                {/* Large Metric */}
                <div className="text-6xl md:text-7xl font-black text-blue-600 mb-4 leading-none"
                     style={{
                       fontWeight: 950,
                       textShadow: '0 4px 8px rgba(37, 99, 235, 0.3)'
                     }}>
                  Any
                </div>
                
                {/* Description */}
                <div className="text-slate-700 font-semibold text-lg md:text-xl leading-tight mb-6"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                  Software you already use
                </div>
                
                {/* Impact Badge */}
                <div className="mb-4">
                  <div className="inline-block px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-full text-sm font-bold shadow-lg">
                    150+ APIs
                  </div>
                </div>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/5 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

          </div>
        </div>
      </section>

      {/* Professional Transition to Problems Section */}
      <div className="relative">
        {/* Smooth gradient transition */}
        <div className="h-16 bg-gradient-to-b from-white via-gray-200 to-gray-700"></div>
        
        {/* Subtle shadow depth */}
        <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-b from-transparent to-black/10"></div>
      </div>

      {/* Section 3: Problems - Pain Points */}
      <section className="py-20 bg-gradient-to-br from-white via-slate-50/30 to-white relative overflow-hidden" style={{ 
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.8), 0 4px 12px rgba(0,0,0,0.08)' 
      }}>
        <div className="max-w-6xl mx-auto px-6">
          
          {/* Enhanced Section Header */}
          <div className="text-center mb-20">
            {/* Premium Badge - Blue/Green Theme */}
            <div className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-50/95 to-green-50/95 backdrop-blur-sm border-2 border-blue-200/50 text-blue-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-blue-200/40 transition-all duration-300 hover:scale-105"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   background: 'linear-gradient(135deg, rgba(239, 246, 255, 0.95) 0%, rgba(240, 253, 244, 0.95) 100%)',
                   backdropFilter: 'blur(10px)'
                 }}>
              <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: '#1e40af' }}></span>
              The Nigerian Business Reality
            </div>
            
            {/* Dramatic Headline */}
            <div className="relative mb-8">
              <h2 className="text-5xl md:text-7xl font-black text-gray-900 mb-4 leading-[0.9] tracking-tight"
                  style={{ 
                    textRendering: 'optimizeLegibility', 
                    WebkitFontSmoothing: 'antialiased',
                    fontWeight: 950,
                    textShadow: '0 1px 2px rgba(0,0,0,0.1)'
                  }}>
                <span className="text-slate-600">Nigerian businesses are</span>
                <br />
                <span className="relative inline-block">
                  <span className="text-green-600 italic font-black"
                        style={{ 
                          fontWeight: 950,
                          textShadow: '0 2px 4px rgba(34, 197, 94, 0.3)'
                        }}>
                    drowning
                  </span>
                  {/* Dramatic underline effect */}
                  <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-green-500 to-blue-500 rounded-full opacity-90"></div>
                </span>
                <span className="block mt-2 text-slate-600">in system integration complexity</span>
              </h2>
              
              {/* Subtle background glow - removed for better text visibility */}
            </div>
            
            {/* Enhanced Subtitle */}
            <p className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-medium"
               style={{ 
                 textRendering: 'optimizeLegibility', 
                 WebkitFontSmoothing: 'antialiased',
                 textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
               }}>
              But there's a better way - <span className="text-green-600 font-bold">unified automation</span> that transforms fragmented systems.
            </p>
          </div>

          {/* Problems Grid - Using Design System */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
            {PROBLEMS_DATA.slice(0, 6).map((problem, index) => (
              <ProblemCard
                key={index}
                emoji={problem.emoji}
                title={problem.title}
                quote={problem.quote}
                attribution={problem.attribution}
              />
            ))}
          </div>

          {/* Premium Bottom CTA Section */}
          <div className="text-center mt-24 mb-12">
            {/* Empathy Hook */}
            <div className="mb-8 mt-8">
              <p className="text-3xl md:text-4xl text-slate-600 mb-6 font-bold"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
                 }}>
                Sound familiar?
              </p>
              <p className="text-4xl md:text-5xl font-black text-green-600 mb-2"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   fontWeight: 950,
                   textShadow: '0 2px 4px rgba(34, 197, 94, 0.3)'
                 }}>
                You're not alone.
              </p>
            </div>
            
            {/* Statistics Card - Premium Design */}
            <div className="relative max-w-5xl mx-auto">
              {/* Background Effects */}
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/20 via-blue-500/10 to-emerald-500/20 rounded-3xl blur-xl"></div>
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-white/5 to-white/10 rounded-3xl"></div>
              
              {/* Main Card */}
              <div className="relative bg-gradient-to-br from-white/95 via-green-50/90 to-white/95 
                              border-2 border-green-200/50 rounded-3xl p-8 md:p-12 
                              shadow-2xl backdrop-blur-sm"
                   style={{
                     background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(240,253,244,0.9) 50%, rgba(255,255,255,0.95) 100%)',
                     backdropFilter: 'blur(16px)',
                     boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
                   }}>
                
                {/* Dramatic Statistics */}
                <div className="mb-8">
                  <div className="text-6xl md:text-7xl font-black text-slate-600 mb-4 leading-none"
                       style={{
                         fontWeight: 950,
                         textShadow: '0 4px 8px rgba(100, 116, 139, 0.3)'
                       }}>
                    2,000,000+
                  </div>
                  <p className="text-2xl md:text-3xl text-slate-600 font-bold leading-tight mb-2"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                    Nigerian businesses struggle with these
                  </p>
                  <p className="text-2xl md:text-3xl font-black text-green-700 leading-tight"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', fontWeight: 900 }}>
                    exact same problems every single day.
                  </p>
                </div>
                
                {/* Elegant Divider */}
                <div className="relative mb-8">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t-2 border-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
                  </div>
                  <div className="relative flex justify-center">
                    <span className="px-8 py-2 text-lg text-gray-400 font-medium">●  ●  ●</span>
                  </div>
                </div>
                
                {/* Hope Message & CTA */}
                <div className="text-center">
                  <p className="text-2xl md:text-3xl font-bold text-slate-600 mb-6"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       textShadow: '0 2px 4px rgba(100, 116, 139, 0.1)'
                     }}>
                    But there's a better way...
                  </p>
                  
                  {/* Clean Focused CTA Button */}
                  <button
                    onClick={() => router.push('/auth/signup')}
                    className="group relative inline-flex items-center justify-center px-16 py-6 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-700 hover:via-indigo-700 hover:to-blue-800 text-white font-bold rounded-2xl shadow-2xl hover:shadow-blue-500/40 transition-all duration-500 hover:scale-105 transform border border-blue-500/20 hover:border-blue-400/40 min-w-[400px] mb-4"
                    style={{
                      background: 'linear-gradient(135deg, #2563eb 0%, #4f46e5 50%, #1d4ed8 100%)',
                      boxShadow: '0 20px 40px -12px rgba(37, 99, 235, 0.4), 0 8px 16px -4px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                      textRendering: 'optimizeLegibility',
                      WebkitFontSmoothing: 'antialiased'
                    }}
                  >
                    <span className="relative z-10 text-2xl font-black">Start Your Free Trial Today</span>
                    <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>
                  
                  {/* Supporting Text Below Button */}
                  <div className="text-lg text-slate-600 font-medium">
                    <span className="mr-2">✨</span>
                    Join thousands who've already made the switch
                    <span className="ml-2">✨</span>
                  </div>
                </div>
                
                {/* Subtle Pattern Overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-green-50/20 via-transparent to-blue-50/20 rounded-3xl pointer-events-none"></div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Professional Transition to Solutions Section */}
      <div className="relative">
        {/* Smooth gradient transition */}
        <div className="h-16 bg-gradient-to-b from-white via-green-100 to-green-50"></div>
        
        {/* Subtle shadow depth */}
        <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-b from-transparent to-green-200/20"></div>
      </div>

      {/* Section 4: Solutions - How TaxPoynt Solves Enterprise Problems */}
      <section className="py-20 bg-gradient-to-br from-green-50 via-emerald-50/30 to-green-50 relative overflow-hidden" style={{ 
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.8), 0 4px 12px rgba(34, 197, 94, 0.08)' 
      }}>
        <div className="max-w-6xl mx-auto px-6">
          
          {/* Enhanced Section Header */}
          <div className="text-center mb-20">
            {/* Premium Badge - Green Theme */}
            <div className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-green-50/95 to-emerald-50/95 backdrop-blur-sm border-2 border-green-200/50 text-green-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-green-200/40 transition-all duration-300 hover:scale-105"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   background: 'linear-gradient(135deg, rgba(240, 253, 244, 0.95) 0%, rgba(236, 253, 245, 0.95) 100%)',
                   backdropFilter: 'blur(10px)'
                 }}>
              <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: '#166534' }}></span>
              The TaxPoynt Solution
            </div>
            
            {/* Dramatic Headline */}
            <div className="relative mb-8">
              <h2 className="text-5xl md:text-7xl font-black text-green-900 mb-4 leading-[0.9] tracking-tight"
                  style={{ 
                    textRendering: 'optimizeLegibility', 
                    WebkitFontSmoothing: 'antialiased',
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}>
                <span className="text-slate-700">Enterprise problems meet</span>
                <br />
                <span className="relative inline-block">
                  <span className="text-green-600 italic font-black"
                        style={{ 
                          fontWeight: 950,
                          textShadow: '0 2px 4px rgba(34, 197, 94, 0.3)'
                        }}>
                    unified solutions
                  </span>
                  {/* Dramatic underline effect */}
                  <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-green-500 via-emerald-500 to-green-500 rounded-full opacity-90"></div>
                </span>
                <span className="block mt-2 text-slate-700">that transform your business</span>
              </h2>
            </div>
            
            {/* Enhanced Subtitle */}
            <p className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-medium"
               style={{ 
                 textRendering: 'optimizeLegibility', 
                 WebkitFontSmoothing: 'antialiased',
                 textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
               }}>
              See how TaxPoynt's <span className="text-green-600 font-bold">universal integration platform</span> directly solves each enterprise challenge with proven results.
            </p>
          </div>

          {/* Solutions Grid - Using Design System */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
            {ENTERPRISE_SOLUTIONS_DATA.map((solution, index) => (
              <SolutionCard
                key={index}
                emoji={solution.emoji}
                title={solution.title}
                problem={solution.problem}
                quote={solution.quote}
                attribution={solution.attribution}
                metrics={solution.metrics}
              />
            ))}
          </div>

          {/* Premium Bottom CTA Section */}
          <div className="text-center mt-24 mb-12">
            {/* Success Hook */}
            <div className="mb-8 mt-8">
              <p className="text-3xl md:text-4xl text-slate-600 mb-6 font-bold"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
                 }}>
                Ready to transform your enterprise?
              </p>
              <p className="text-4xl md:text-5xl font-black text-green-600 mb-2"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   fontWeight: 950,
                   textShadow: '0 2px 4px rgba(34, 197, 94, 0.3)'
                 }}>
                Join the unified automation revolution.
              </p>
            </div>
            
            {/* Success Statistics Card */}
            <div className="relative max-w-5xl mx-auto">
              {/* Background Effects */}
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/20 via-emerald-500/10 to-green-500/20 rounded-3xl blur-xl"></div>
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-white/5 to-white/10 rounded-3xl"></div>
              
              {/* Main Card */}
              <div className="relative bg-gradient-to-br from-white/95 via-green-50/90 to-white/95 
                              border-2 border-green-200/50 rounded-3xl p-8 md:p-12 
                              shadow-2xl backdrop-blur-sm"
                   style={{
                     background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(240,253,244,0.9) 50%, rgba(255,255,255,0.95) 100%)',
                     backdropFilter: 'blur(16px)',
                     boxShadow: '0 25px 50px -12px rgba(34, 197, 94, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
                   }}>
                
                {/* Success Statistics */}
                <div className="mb-8">
                  <div className="text-6xl md:text-7xl font-black text-green-600 mb-4 leading-none"
                       style={{
                         fontWeight: 950,
                         textShadow: '0 4px 8px rgba(34, 197, 94, 0.3)'
                       }}>
                    99.9%
                  </div>
                  <p className="text-2xl md:text-3xl text-slate-600 font-bold leading-tight mb-2"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                    Enterprise uptime with TaxPoynt's
                  </p>
                  <p className="text-2xl md:text-3xl font-black text-green-700 leading-tight"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', fontWeight: 900 }}>
                    unified automation platform.
                  </p>
                </div>
                
                {/* Elegant Divider */}
                <div className="relative mb-8">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t-2 border-gradient-to-r from-transparent via-green-300 to-transparent"></div>
                  </div>
                  <div className="relative flex justify-center">
                    <span className="px-8 py-2 text-lg text-green-500 font-medium">●  ●  ●</span>
                  </div>
                </div>
                
                {/* Success Message & CTA */}
                <div className="text-center">
                  <p className="text-2xl md:text-3xl font-bold text-slate-600 mb-6"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       textShadow: '0 2px 4px rgba(100, 116, 139, 0.1)'
                     }}>
                    Your enterprise transformation starts here.
                  </p>
                  
                  {/* Clean Focused CTA Button */}
                  <button
                    onClick={() => router.push('/auth/signup')}
                    className="group relative inline-flex items-center justify-center px-16 py-6 bg-gradient-to-r from-green-600 via-emerald-600 to-green-700 hover:from-green-700 hover:via-emerald-700 hover:to-green-800 text-white font-bold rounded-2xl shadow-2xl hover:shadow-green-500/40 transition-all duration-500 hover:scale-105 transform border border-green-500/20 hover:border-green-400/40 min-w-[400px] mb-4"
                    style={{
                      background: 'linear-gradient(135deg, #16a34a 0%, #10b981 50%, #059669 100%)',
                      boxShadow: '0 20px 40px -12px rgba(34, 197, 94, 0.4), 0 8px 16px -4px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                      textRendering: 'optimizeLegibility',
                      WebkitFontSmoothing: 'antialiased'
                    }}
                  >
                    <span className="relative z-10 text-2xl font-black">Start Enterprise Transformation</span>
                    <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>
                  
                  {/* Supporting Text Below Button */}
                  <div className="text-lg text-slate-600 font-medium">
                    <span className="mr-2">🚀</span>
                    Join enterprises already transforming with TaxPoynt
                    <span className="ml-2">🚀</span>
                  </div>
                </div>
                
                {/* Subtle Pattern Overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-green-50/20 via-transparent to-emerald-50/20 rounded-3xl pointer-events-none"></div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Professional Transition to Features Section */}
      <div className="relative">
        {/* Smooth gradient transition */}
        <div className="h-16 bg-gradient-to-b from-green-50 via-slate-100 to-slate-50"></div>
        
        {/* Subtle shadow depth */}
        <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-b from-transparent to-slate-200/20"></div>
      </div>

      {/* Section 5: Features - Detailed Platform Capabilities */}
      <section id="features" className="py-20 bg-gradient-to-br from-slate-50 via-indigo-50/30 to-slate-50 relative overflow-hidden" style={{ 
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.8), 0 4px 12px rgba(71, 85, 105, 0.08)' 
      }}>
        <div className="max-w-6xl mx-auto px-6">
          
          {/* Enhanced Section Header */}
          <div className="text-center mb-20">
            {/* Premium Badge - Indigo Theme */}
            <div className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-indigo-50/95 to-slate-50/95 backdrop-blur-sm border-2 border-indigo-200/50 text-indigo-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-indigo-200/40 transition-all duration-300 hover:scale-105"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   background: 'linear-gradient(135deg, rgba(238, 242, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%)',
                   backdropFilter: 'blur(10px)'
                 }}>
              <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: '#3730a3' }}></span>
              Platform Capabilities
            </div>
            
            {/* Dramatic Headline */}
            <div className="relative mb-8">
              <h2 className="text-5xl md:text-7xl font-black text-slate-900 mb-4 leading-[0.9] tracking-tight"
                  style={{ 
                    textRendering: 'optimizeLegibility', 
                    WebkitFontSmoothing: 'antialiased',
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}>
                <span className="text-slate-600">Enterprise-grade platform</span>
                <br />
                <span className="relative inline-block">
                  <span className="text-indigo-600 italic font-black"
                        style={{ 
                          fontWeight: 950,
                          textShadow: '0 2px 4px rgba(79, 70, 229, 0.3)'
                        }}>
                    built for scale
                  </span>
                  {/* Dramatic underline effect */}
                  <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-slate-500 to-indigo-500 rounded-full opacity-90"></div>
                </span>
                <span className="block mt-2 text-slate-600">with unlimited capabilities</span>
              </h2>
            </div>
            
            {/* Enhanced Subtitle */}
            <p className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-medium"
               style={{ 
                 textRendering: 'optimizeLegibility', 
                 WebkitFontSmoothing: 'antialiased',
                 textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
               }}>
              Deep dive into TaxPoynt's <span className="text-indigo-600 font-bold">comprehensive feature set</span> that powers enterprise transformation across 6 critical business domains.
            </p>
          </div>

          {/* Features Grid - Using Design System */}
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
              />
            ))}
          </div>

          {/* Premium Bottom CTA Section */}
          <div className="text-center mt-24 mb-12">
            {/* Feature Hook */}
            <div className="mb-8 mt-8">
              <p className="text-3xl md:text-4xl text-slate-600 mb-6 font-bold"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
                 }}>
                Impressive capabilities. Real results.
              </p>
              <p className="text-4xl md:text-5xl font-black text-indigo-600 mb-2"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   fontWeight: 950,
                   textShadow: '0 2px 4px rgba(79, 70, 229, 0.3)'
                 }}>
                Experience enterprise excellence.
              </p>
            </div>
            
            {/* Platform Statistics Card */}
            <div className="relative max-w-5xl mx-auto">
              {/* Background Effects */}
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/20 via-slate-500/10 to-indigo-500/20 rounded-3xl blur-xl"></div>
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-white/5 to-white/10 rounded-3xl"></div>
              
              {/* Main Card */}
              <div className="relative bg-gradient-to-br from-white/95 via-indigo-50/90 to-white/95 
                              border-2 border-indigo-200/50 rounded-3xl p-8 md:p-12 
                              shadow-2xl backdrop-blur-sm"
                   style={{
                     background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(238,242,255,0.9) 50%, rgba(255,255,255,0.95) 100%)',
                     backdropFilter: 'blur(16px)',
                     boxShadow: '0 25px 50px -12px rgba(79, 70, 229, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
                   }}>
                
                {/* Platform Statistics */}
                <div className="mb-8">
                  <div className="text-6xl md:text-7xl font-black text-indigo-600 mb-4 leading-none"
                       style={{
                         fontWeight: 950,
                         textShadow: '0 4px 8px rgba(79, 70, 229, 0.3)'
                       }}>
                    150+
                  </div>
                  <p className="text-2xl md:text-3xl text-slate-600 font-bold leading-tight mb-2"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                    Pre-built API integrations ready for
                  </p>
                  <p className="text-2xl md:text-3xl font-black text-indigo-700 leading-tight"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', fontWeight: 900 }}>
                     your enterprise transformation.
                  </p>
                </div>
                
                {/* Elegant Divider */}
                <div className="relative mb-8">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t-2 border-gradient-to-r from-transparent via-indigo-300 to-transparent"></div>
                  </div>
                  <div className="relative flex justify-center">
                    <span className="px-8 py-2 text-lg text-indigo-500 font-medium">●  ●  ●</span>
                  </div>
                </div>
                
                {/* Platform Message & CTA */}
                <div className="text-center">
                  <p className="text-2xl md:text-3xl font-bold text-slate-600 mb-6"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       textShadow: '0 2px 4px rgba(100, 116, 139, 0.1)'
                     }}>
                    See these features in action with your data.
                  </p>
                  
                  {/* Clean Focused CTA Button */}
                  <button
                    onClick={() => router.push('/auth/signup')}
                    className="group relative inline-flex items-center justify-center px-16 py-6 bg-gradient-to-r from-indigo-600 via-slate-600 to-indigo-700 hover:from-indigo-700 hover:via-slate-700 hover:to-indigo-800 text-white font-bold rounded-2xl shadow-2xl hover:shadow-indigo-500/40 transition-all duration-500 hover:scale-105 transform border border-indigo-500/20 hover:border-indigo-400/40 min-w-[400px] mb-4"
                    style={{
                      background: 'linear-gradient(135deg, #4f46e5 0%, #64748b 50%, #4338ca 100%)',
                      boxShadow: '0 20px 40px -12px rgba(79, 70, 229, 0.4), 0 8px 16px -4px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                      textRendering: 'optimizeLegibility',
                      WebkitFontSmoothing: 'antialiased'
                    }}
                  >
                    <span className="relative z-10 text-2xl font-black">Request Live Demo</span>
                    <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>
                  
                  {/* Supporting Text Below Button */}
                  <div className="text-lg text-slate-600 font-medium">
                    <span className="mr-2">🎯</span>
                    See TaxPoynt features working with your business systems
                    <span className="ml-2">🎯</span>
                  </div>
                </div>
                
                {/* Subtle Pattern Overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/20 via-transparent to-slate-50/20 rounded-3xl pointer-events-none"></div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Professional Transition to Before/After Section */}
      <div className="relative">
        {/* Smooth gradient transition */}
        <div className="h-16 bg-gradient-to-b from-slate-50 via-purple-100 to-purple-50"></div>
        
        {/* Subtle shadow depth */}
        <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-b from-transparent to-purple-200/20"></div>
      </div>

      {/* Section 6: Before/After - Transformation Comparison */}
      <section className="py-20 bg-gradient-to-br from-purple-50 via-violet-50/30 to-purple-50 relative overflow-hidden" style={{ 
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.8), 0 4px 12px rgba(147, 51, 234, 0.08)' 
      }}>
        <div className="max-w-6xl mx-auto px-6">
          
          {/* Enhanced Section Header */}
          <div className="text-center mb-20">
            {/* Premium Badge - Purple Theme */}
            <div className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-purple-50/95 to-violet-50/95 backdrop-blur-sm border-2 border-purple-200/50 text-purple-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-purple-200/40 transition-all duration-300 hover:scale-105"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   background: 'linear-gradient(135deg, rgba(250, 245, 255, 0.95) 0%, rgba(245, 243, 255, 0.95) 100%)',
                   backdropFilter: 'blur(10px)'
                 }}>
              <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: '#6b21a8' }}></span>
              Business Transformation
            </div>
            
            {/* Dramatic Headline */}
            <div className="relative mb-8">
              <h2 className="text-5xl md:text-7xl font-black text-purple-900 mb-4 leading-[0.9] tracking-tight"
                  style={{ 
                    textRendering: 'optimizeLegibility', 
                    WebkitFontSmoothing: 'antialiased',
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}>
                <span className="text-slate-700">The dramatic difference</span>
                <br />
                <span className="relative inline-block">
                  <span className="text-purple-600 italic font-black"
                        style={{ 
                          fontWeight: 950,
                          textShadow: '0 2px 4px rgba(147, 51, 234, 0.3)'
                        }}>
                    TaxPoynt creates
                  </span>
                  {/* Dramatic underline effect */}
                  <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-violet-500 to-purple-500 rounded-full opacity-90"></div>
                </span>
                <span className="block mt-2 text-slate-700">in every business metric</span>
              </h2>
            </div>
            
            {/* Enhanced Subtitle */}
            <p className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-medium"
               style={{ 
                 textRendering: 'optimizeLegibility', 
                 WebkitFontSmoothing: 'antialiased',
                 textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
               }}>
              See the <span className="text-purple-600 font-bold">measurable transformation</span> TaxPoynt delivers across 6 critical business areas - from operational efficiency to employee satisfaction.
            </p>
          </div>

          {/* Before/After Grid - Using Design System */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
            {BEFORE_AFTER_DATA.map((comparison, index) => (
              <BeforeAfterCard
                key={index}
                metric={comparison.metric}
                before={comparison.before}
                after={comparison.after}
                improvement={comparison.improvement}
                category={comparison.category}
              />
            ))}
          </div>

          {/* Premium Bottom CTA Section */}
          <div className="text-center mt-24 mb-12">
            {/* Transformation Hook */}
            <div className="mb-8 mt-8">
              <p className="text-3xl md:text-4xl text-slate-600 mb-6 font-bold"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
                 }}>
                Ready for your transformation?
              </p>
              <p className="text-4xl md:text-5xl font-black text-purple-600 mb-2"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   fontWeight: 950,
                   textShadow: '0 2px 4px rgba(147, 51, 234, 0.3)'
                 }}>
                Start your Before/After story.
              </p>
            </div>
            
            {/* Transformation Statistics Card */}
            <div className="relative max-w-5xl mx-auto">
              {/* Background Effects */}
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-violet-500/10 to-purple-500/20 rounded-3xl blur-xl"></div>
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-white/5 to-white/10 rounded-3xl"></div>
              
              {/* Main Card */}
              <div className="relative bg-gradient-to-br from-white/95 via-purple-50/90 to-white/95 
                              border-2 border-purple-200/50 rounded-3xl p-8 md:p-12 
                              shadow-2xl backdrop-blur-sm"
                   style={{
                     background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(250,245,255,0.9) 50%, rgba(255,255,255,0.95) 100%)',
                     backdropFilter: 'blur(16px)',
                     boxShadow: '0 25px 50px -12px rgba(147, 51, 234, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
                   }}>
                
                {/* Transformation Statistics */}
                <div className="mb-8">
                  <div className="text-6xl md:text-7xl font-black text-purple-600 mb-4 leading-none"
                       style={{
                         fontWeight: 950,
                         textShadow: '0 4px 8px rgba(147, 51, 234, 0.3)'
                       }}>
                    6x
                  </div>
                  <p className="text-2xl md:text-3xl text-slate-600 font-bold leading-tight mb-2"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                    Average improvement across all business metrics
                  </p>
                  <p className="text-2xl md:text-3xl font-black text-purple-700 leading-tight"
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', fontWeight: 900 }}>
                    with TaxPoynt's unified platform.
                  </p>
                </div>
                
                {/* Elegant Divider */}
                <div className="relative mb-8">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t-2 border-gradient-to-r from-transparent via-purple-300 to-transparent"></div>
                  </div>
                  <div className="relative flex justify-center">
                    <span className="px-8 py-2 text-lg text-purple-500 font-medium">●  ●  ●</span>
                  </div>
                </div>
                
                {/* Transformation Message & CTA */}
                <div className="text-center">
                  <p className="text-2xl md:text-3xl font-bold text-slate-600 mb-6"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       textShadow: '0 2px 4px rgba(100, 116, 139, 0.1)'
                     }}>
                    Your transformation story starts with a single click.
                  </p>
                  
                  {/* Clean Focused CTA Button */}
                  <button
                    onClick={() => router.push('/auth/signup')}
                    className="group relative inline-flex items-center justify-center px-16 py-6 bg-gradient-to-r from-purple-600 via-violet-600 to-purple-700 hover:from-purple-700 hover:via-violet-700 hover:to-purple-800 text-white font-bold rounded-2xl shadow-2xl hover:shadow-purple-500/40 transition-all duration-500 hover:scale-105 transform border border-purple-500/20 hover:border-purple-400/40 min-w-[400px] mb-4"
                    style={{
                      background: 'linear-gradient(135deg, #9333ea 0%, #8b5cf6 50%, #7c3aed 100%)',
                      boxShadow: '0 20px 40px -12px rgba(147, 51, 234, 0.4), 0 8px 16px -4px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                      textRendering: 'optimizeLegibility',
                      WebkitFontSmoothing: 'antialiased'
                    }}
                  >
                    <span className="relative z-10 text-2xl font-black">Begin Your Transformation</span>
                    <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>
                  
                  {/* Supporting Text Below Button */}
                  <div className="text-lg text-slate-600 font-medium">
                    <span className="mr-2">🚀</span>
                    Join businesses already experiencing these transformations
                    <span className="ml-2">🚀</span>
                  </div>
                </div>
                
                {/* Subtle Pattern Overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-50/20 via-transparent to-violet-50/20 rounded-3xl pointer-events-none"></div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Professional Transition to Pricing Section */}
      <div className="relative">
        {/* Smooth gradient transition */}
        <div className="h-16 bg-gradient-to-b from-purple-50 via-teal-100 to-teal-50"></div>
        
        {/* Subtle shadow depth */}
        <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-b from-transparent to-teal-200/20"></div>
      </div>

      {/* Section 7: Service Packages/Pricing - Real TaxPoynt Pricing */}
      <section className="py-20 bg-gradient-to-br from-teal-50 via-cyan-50/30 to-teal-50 relative overflow-hidden" style={{ 
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.8), 0 4px 12px rgba(20, 184, 166, 0.08)' 
      }}>
        <div className="max-w-7xl mx-auto px-6">
          
          {/* Enhanced Section Header */}
          <div className="text-center mb-24">
            {/* Premium Badge - Teal Theme */}
            <div className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-teal-50/95 to-cyan-50/95 backdrop-blur-sm border-2 border-teal-200/50 text-teal-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-teal-200/40 transition-all duration-300 hover:scale-105"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   background: 'linear-gradient(135deg, rgba(240, 253, 250, 0.95) 0%, rgba(236, 254, 255, 0.95) 100%)',
                   backdropFilter: 'blur(10px)'
                 }}>
              <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: '#0f766e' }}></span>
              Service Packages
            </div>
            
            {/* Dramatic Headline */}
            <div className="relative mb-8">
              <h2 className="text-5xl md:text-7xl font-black text-teal-900 mb-4 leading-[0.9] tracking-tight"
                  style={{ 
                    textRendering: 'optimizeLegibility', 
                    WebkitFontSmoothing: 'antialiased',
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}>
                <span className="text-slate-700">Choose the perfect plan</span>
                <br />
                <span className="relative inline-block">
                  <span className="text-teal-600 italic font-black"
                        style={{ 
                          fontWeight: 950,
                          textShadow: '0 2px 4px rgba(20, 184, 166, 0.3)'
                        }}>
                    for your business
                  </span>
                  {/* Dramatic underline effect */}
                  <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 via-cyan-500 to-teal-500 rounded-full opacity-90"></div>
                </span>
                <span className="block mt-2 text-slate-700">with transparent Nigerian pricing</span>
              </h2>
            </div>
            
          </div>

          {/* Pricing Cards Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-32 pt-32">
            {SERVICE_PACKAGES_DATA.map((pkg, index) => (
              <PricingCard
                key={pkg.id}
                id={pkg.id}
                name={pkg.name}
                subtitle={pkg.subtitle}
                description={pkg.description}
                price={pkg.price}
                originalAnnual={pkg.originalAnnual}
                badge={pkg.badge}
                features={pkg.features}
                limits={pkg.limits}
                ideal={pkg.ideal}
                color={pkg.color}
                billingCycle="monthly"
                onSelectPackage={handlePackageSelect}
              />
            ))}
          </div>

          {/* Premium Bottom Section */}
          <div className="text-center mt-24 mb-12">
            {/* Pricing Hook */}
            <div className="mb-8 mt-8">
              <p className="text-3xl md:text-4xl text-slate-600 mb-6 font-bold"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
                 }}>
                Trusted by Nigerian businesses
              </p>
              <p className="text-4xl md:text-5xl font-black text-teal-600 mb-2"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   fontWeight: 950,
                   textShadow: '0 2px 4px rgba(20, 184, 166, 0.3)'
                 }}>
                Start your subscription today.
              </p>
            </div>
            
            {/* Trust & Guarantee Card */}
            <div className="relative max-w-5xl mx-auto">
              {/* Background Effects */}
              <div className="absolute inset-0 bg-gradient-to-br from-teal-500/20 via-cyan-500/10 to-teal-500/20 rounded-3xl blur-xl"></div>
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-white/5 to-white/10 rounded-3xl"></div>
              
              {/* Main Card */}
              <div className="relative bg-gradient-to-br from-white/95 via-teal-50/90 to-white/95 
                              border-2 border-teal-200/50 rounded-3xl p-8 md:p-12 
                              shadow-2xl backdrop-blur-sm"
                   style={{
                     background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(240,253,250,0.9) 50%, rgba(255,255,255,0.95) 100%)',
                     backdropFilter: 'blur(16px)',
                     boxShadow: '0 25px 50px -12px rgba(20, 184, 166, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
                   }}>
                
                {/* Trust Guarantees */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                  <div className="text-center">
                    <div className="text-4xl mb-3">🛡️</div>
                    <div className="text-2xl font-black text-teal-600 mb-2">30-Day</div>
                    <div className="text-lg text-slate-600 font-semibold">Money Back Guarantee</div>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl mb-3">💳</div>
                    <div className="text-2xl font-black text-teal-600 mb-2">Nigerian</div>
                    <div className="text-lg text-slate-600 font-semibold">Payment Methods</div>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl mb-3">📞</div>
                    <div className="text-2xl font-black text-teal-600 mb-2">24/7</div>
                    <div className="text-lg text-slate-600 font-semibold">Nigerian Support</div>
                  </div>
                </div>
                
                {/* Elegant Divider */}
                <div className="relative mb-8">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t-2 border-gradient-to-r from-transparent via-teal-300 to-transparent"></div>
                  </div>
                  <div className="relative flex justify-center">
                    <span className="px-8 py-2 text-lg text-teal-500 font-medium">●  ●  ●</span>
                  </div>
                </div>
                
                {/* Final CTA */}
                <div className="text-center">
                  <p className="text-xl md:text-2xl font-bold text-slate-600 mb-8"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       textShadow: '0 2px 4px rgba(100, 116, 139, 0.1)'
                     }}>
                    Questions? Speak with our Nigerian team.
                  </p>
                  
                  {/* CTA Buttons Container */}
                  <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    {/* Primary CTA - Start Free Trial */}
                    <button
                      onClick={() => router.push('/auth/signup')}
                      className="group relative inline-flex items-center justify-center px-16 py-6 bg-gradient-to-r from-teal-600 via-cyan-600 to-teal-700 hover:from-teal-700 hover:via-cyan-700 hover:to-teal-800 text-white font-bold rounded-2xl shadow-2xl hover:shadow-teal-500/40 transition-all duration-500 hover:scale-105 transform border border-teal-500/20 hover:border-teal-400/40 min-w-[280px]"
                      style={{
                        background: 'linear-gradient(135deg, #0d9488 0%, #0891b2 50%, #0f766e 100%)',
                        boxShadow: '0 20px 40px -12px rgba(13, 148, 136, 0.4), 0 8px 16px -4px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                        textRendering: 'optimizeLegibility',
                        WebkitFontSmoothing: 'antialiased'
                      }}
                    >
                      <span className="relative z-10 text-2xl font-black">Start Free Trial</span>
                      <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    </button>
                    
                    {/* Secondary CTA - Contact Sales */}
                    <button
                      onClick={() => router.push('/contact')}
                      className="group relative inline-flex items-center justify-center px-16 py-6 bg-white border-2 border-teal-600 text-teal-600 hover:bg-teal-50 hover:border-teal-700 font-bold rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 transform min-w-[280px]"
                      style={{
                        textRendering: 'optimizeLegibility',
                        WebkitFontSmoothing: 'antialiased',
                        boxShadow: '0 10px 25px -5px rgba(13, 148, 136, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
                      }}
                    >
                      <span className="relative z-10 text-2xl font-black">Contact Sales Team</span>
                    </button>
                  </div>
                  
                  {/* Supporting Text */}
                  <div className="mt-6 text-lg text-slate-600 font-medium">
                    <span className="mr-2">🇳🇬</span>
                    Local Nigerian support team ready to help
                    <span className="ml-2">📞</span>
                  </div>
                </div>
                
                {/* Subtle Pattern Overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-teal-50/20 via-transparent to-cyan-50/20 rounded-3xl pointer-events-none"></div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Professional Transition to Final CTA Section */}
      <div className="relative">
        {/* Smooth gradient transition */}
        <div className="h-16 bg-gradient-to-b from-teal-50 via-slate-100 to-slate-50"></div>
        
        {/* Subtle shadow depth */}
        <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-b from-transparent to-slate-200/20"></div>
      </div>

      {/* Section 8: Final CTA - Demo & Contact Options */}
      <section className="py-20 bg-gradient-to-br from-slate-50 via-gray-50/30 to-slate-50 relative overflow-hidden" style={{ 
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.8), 0 4px 12px rgba(71, 85, 105, 0.08)' 
      }}>
        <div className="max-w-6xl mx-auto px-6">
          
          {/* Enhanced Section Header */}
          <div className="text-center mb-20">
            {/* Premium Badge - Slate Theme */}
            <div className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-slate-50/95 to-gray-50/95 backdrop-blur-sm border-2 border-slate-200/50 text-slate-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-slate-200/40 transition-all duration-300 hover:scale-105"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   background: 'linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(249, 250, 251, 0.95) 100%)',
                   backdropFilter: 'blur(10px)'
                 }}>
              <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: '#475569' }}></span>
              Ready to Transform Your Business?
            </div>
            
            {/* Dramatic Headline */}
            <div className="relative mb-8">
              <h2 className="text-5xl md:text-7xl font-black text-slate-900 mb-4 leading-[0.9] tracking-tight"
                  style={{ 
                    textRendering: 'optimizeLegibility', 
                    WebkitFontSmoothing: 'antialiased',
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}>
                <span className="text-slate-600">Join thousands of businesses</span>
                <br />
                <span className="relative inline-block">
                  <span className="text-blue-600 italic font-black"
                        style={{ 
                          fontWeight: 950,
                          textShadow: '0 2px 4px rgba(37, 99, 235, 0.3)'
                        }}>
                    already transformed
                  </span>
                  {/* Dramatic underline effect */}
                  <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-green-500 to-blue-500 rounded-full opacity-90"></div>
                </span>
                <span className="block mt-2 text-slate-600">by TaxPoynt's platform</span>
              </h2>
            </div>
            
            {/* Enhanced Subtitle */}
            <p className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-medium"
               style={{ 
                 textRendering: 'optimizeLegibility', 
                 WebkitFontSmoothing: 'antialiased',
                 textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
               }}>
              Don't let compliance complexity hold back your business growth. <span className="text-blue-600 font-bold">Start your transformation</span> with Nigeria's leading e-invoicing platform.
            </p>
          </div>

          {/* CTA Options Grid */}
          <div className="grid md:grid-cols-2 gap-8 mb-20">
            
            {/* Demo Booking Card */}
            <div className="group relative p-8 bg-gradient-to-br from-blue-50 via-white to-indigo-50/50 rounded-3xl 
                            shadow-2xl hover:shadow-2xl hover:shadow-blue-500/20 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-blue-200/50 hover:border-blue-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #eef2ff 100%)',
                   boxShadow: '0 25px 50px -12px rgba(37, 99, 235, 0.15), 0 10px 20px -4px rgba(0, 0, 0, 0.1), inset 0 2px 0 rgba(255, 255, 255, 0.3)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50/20 via-transparent to-indigo-50/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10 text-center">
                {/* Icon */}
                <div className="mb-6">
                  <div className="w-20 h-20 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-3xl 
                                  flex items-center justify-center text-6xl mx-auto group-hover:shadow-lg 
                                  transition-all duration-300 border border-blue-100/50 group-hover:scale-105"
                       style={{
                         background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(79, 70, 229, 0.1) 100%)',
                         backdropFilter: 'blur(10px)'
                       }}>
                    🎯
                  </div>
                </div>
                
                {/* Title */}
                <h3 className="text-3xl md:text-4xl font-black text-blue-900 mb-4 leading-tight"
                    style={{ 
                      textRendering: 'optimizeLegibility', 
                      WebkitFontSmoothing: 'antialiased',
                      fontWeight: 950,
                      textShadow: '0 2px 4px rgba(37, 99, 235, 0.2)'
                    }}>
                  See TaxPoynt in Action
                </h3>
                
                {/* Description */}
                <p className="text-lg text-slate-600 mb-8 leading-relaxed"
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased'
                   }}>
                  Book a <span className="font-bold text-blue-700">personalized demo</span> with our Nigerian team. See exactly how TaxPoynt integrates with your business systems and transforms your compliance workflow.
                </p>
                
                {/* Benefits */}
                <div className="mb-8 text-left">
                  <div className="space-y-3">
                    {[
                      "Personalized demo with your data",
                      "Integration assessment for your systems", 
                      "Custom ROI calculation for your business",
                      "Live Q&A with TaxPoynt experts"
                    ].map((benefit, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <div className="w-3 h-3 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-slate-700 leading-relaxed">
                          {benefit}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* CTA Button */}
                <button
                  onClick={() => router.push('/demo')}
                  className="group relative w-full py-6 px-8 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-700 hover:via-indigo-700 hover:to-blue-800 text-white font-bold rounded-2xl shadow-2xl hover:shadow-blue-500/40 transition-all duration-500 hover:scale-105 transform border border-blue-500/20 text-xl"
                  style={{
                    background: 'linear-gradient(135deg, #2563eb 0%, #4f46e5 50%, #1d4ed8 100%)',
                    boxShadow: '0 20px 40px -12px rgba(37, 99, 235, 0.4), 0 8px 16px -4px rgba(0, 0, 0, 0.1), inset 0 2px 0 rgba(255, 255, 255, 0.2)',
                    textRendering: 'optimizeLegibility',
                    WebkitFontSmoothing: 'antialiased'
                  }}
                >
                  <span className="relative z-10 flex items-center justify-center">
                    📅 Book Your Demo Now
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </button>
                
                <p className="text-sm text-slate-500 mt-4">
                  30-minute session • No commitment required
                </p>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-blue-500/5 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            {/* Contact Sales Card */}
            <div className="group relative p-8 bg-gradient-to-br from-green-50 via-white to-emerald-50/50 rounded-3xl 
                            shadow-2xl hover:shadow-2xl hover:shadow-green-500/20 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-green-200/50 hover:border-green-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #f0fdf4 0%, #ffffff 50%, #ecfdf5 100%)',
                   boxShadow: '0 25px 50px -12px rgba(34, 197, 94, 0.15), 0 10px 20px -4px rgba(0, 0, 0, 0.1), inset 0 2px 0 rgba(255, 255, 255, 0.3)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-green-50/20 via-transparent to-emerald-50/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10 text-center">
                {/* Icon */}
                <div className="mb-6">
                  <div className="w-20 h-20 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-3xl 
                                  flex items-center justify-center text-6xl mx-auto group-hover:shadow-lg 
                                  transition-all duration-300 border border-green-100/50 group-hover:scale-105"
                       style={{
                         background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)',
                         backdropFilter: 'blur(10px)'
                       }}>
                    💬
                  </div>
                </div>
                
                {/* Title */}
                <h3 className="text-3xl md:text-4xl font-black text-green-900 mb-4 leading-tight"
                    style={{ 
                      textRendering: 'optimizeLegibility', 
                      WebkitFontSmoothing: 'antialiased',
                      fontWeight: 950,
                      textShadow: '0 2px 4px rgba(34, 197, 94, 0.2)'
                    }}>
                  Talk to Our Experts
                </h3>
                
                {/* Description */}
                <p className="text-lg text-slate-600 mb-8 leading-relaxed"
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased'
                   }}>
                  Get expert guidance from our <span className="font-bold text-green-700">Nigerian compliance specialists</span>. Discuss your specific needs and get a tailored solution recommendation.
                </p>
                
                {/* Benefits */}
                <div className="mb-8 text-left">
                  <div className="space-y-3">
                    {[
                      "Free consultation with compliance experts",
                      "Custom pricing for your business size",
                      "Implementation planning and timeline",
                      "Nigerian business compliance guidance"
                    ].map((benefit, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <div className="w-3 h-3 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-slate-700 leading-relaxed">
                          {benefit}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* CTA Button */}
                <button
                  onClick={() => router.push('/contact')}
                  className="group relative w-full py-6 px-8 bg-gradient-to-r from-green-600 via-emerald-600 to-green-700 hover:from-green-700 hover:via-emerald-700 hover:to-green-800 text-white font-bold rounded-2xl shadow-2xl hover:shadow-green-500/40 transition-all duration-500 hover:scale-105 transform border border-green-500/20 text-xl"
                  style={{
                    background: 'linear-gradient(135deg, #16a34a 0%, #10b981 50%, #059669 100%)',
                    boxShadow: '0 20px 40px -12px rgba(34, 197, 94, 0.4), 0 8px 16px -4px rgba(0, 0, 0, 0.1), inset 0 2px 0 rgba(255, 255, 255, 0.2)',
                    textRendering: 'optimizeLegibility',
                    WebkitFontSmoothing: 'antialiased'
                  }}
                >
                  <span className="relative z-10 flex items-center justify-center">
                    🇳🇬 Contact Sales Team
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </button>
                
                <p className="text-sm text-slate-500 mt-4">
                  Response within 2 hours • Local Nigerian support
                </p>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-green-500/5 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

          </div>

          {/* Final Reassurance Section */}
          <div className="text-center">
            {/* Trust Guarantees Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
              <div className="text-center">
                <div className="text-4xl mb-3">🛡️</div>
                <div className="text-lg font-black text-slate-700 mb-1">FIRS Certified</div>
                <div className="text-sm text-slate-600">Official Access Point Provider</div>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-3">💰</div>
                <div className="text-lg font-black text-slate-700 mb-1">Money Back</div>
                <div className="text-sm text-slate-600">30-day guarantee</div>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-3">📞</div>
                <div className="text-lg font-black text-slate-700 mb-1">Nigerian Support</div>
                <div className="text-sm text-slate-600">24/7 local assistance</div>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-3">⚡</div>
                <div className="text-lg font-black text-slate-700 mb-1">Fast Setup</div>
                <div className="text-sm text-slate-600">Live in 48 hours</div>
              </div>
            </div>
            
            {/* Final Call to Action */}
            <div className="max-w-3xl mx-auto">
              <p className="text-2xl md:text-3xl font-bold text-slate-600 mb-8"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
                 }}>
                Ready to eliminate compliance complexity forever?
              </p>
              
              {/* Primary Action */}
              <button
                onClick={() => router.push('/auth/signup')}
                className="group relative inline-flex items-center justify-center px-16 py-6 bg-gradient-to-r from-slate-600 via-gray-600 to-slate-700 hover:from-slate-700 hover:via-gray-700 hover:to-slate-800 text-white font-bold rounded-3xl shadow-2xl hover:shadow-slate-500/40 transition-all duration-500 hover:scale-105 transform border border-slate-500/20 hover:border-slate-400/40 min-w-[400px] mb-6"
                style={{
                  background: 'linear-gradient(135deg, #475569 0%, #6b7280 50%, #374151 100%)',
                  boxShadow: '0 25px 50px -12px rgba(71, 85, 105, 0.4), 0 10px 20px -4px rgba(0, 0, 0, 0.1), inset 0 2px 0 rgba(255, 255, 255, 0.2)',
                  textRendering: 'optimizeLegibility',
                  WebkitFontSmoothing: 'antialiased'
                }}
              >
                <span className="relative z-10 text-2xl font-black">🚀 Start Free Trial Now</span>
                <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              </button>
              
              {/* Supporting Text */}
              <div className="text-lg text-slate-600 font-medium">
                <span className="mr-2">✨</span>
                No setup fees • Cancel anytime • Nigerian payment methods accepted
                <span className="ml-2">✨</span>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Professional Transition to Testimonials Section */}
      <div className="relative">
        {/* Smooth gradient transition */}
        <div className="h-16 bg-gradient-to-b from-slate-50 via-amber-100 to-amber-50"></div>
        
        {/* Subtle shadow depth */}
        <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-b from-transparent to-amber-200/20"></div>
      </div>

      {/* Section 9: Testimonials - Customer Social Proof */}
      <section className="py-20 bg-gradient-to-br from-amber-50 via-orange-50/30 to-amber-50 relative overflow-hidden" style={{ 
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.8), 0 4px 12px rgba(245, 158, 11, 0.08)' 
      }}>
        <div className="max-w-6xl mx-auto px-6">
          
          {/* Enhanced Section Header */}
          <div className="text-center mb-20">
            {/* Premium Badge - Amber Theme */}
            <div className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-amber-50/95 to-orange-50/95 backdrop-blur-sm border-2 border-amber-200/50 text-amber-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-amber-200/40 transition-all duration-300 hover:scale-105"
                 style={{ 
                   textRendering: 'optimizeLegibility', 
                   WebkitFontSmoothing: 'antialiased',
                   background: 'linear-gradient(135deg, rgba(254, 252, 232, 0.95) 0%, rgba(255, 251, 235, 0.95) 100%)',
                   backdropFilter: 'blur(10px)'
                 }}>
              <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: '#d97706' }}></span>
              Success Stories from Nigerian Businesses
            </div>
            
            {/* Dramatic Headline */}
            <div className="relative mb-8">
              <h2 className="text-5xl md:text-7xl font-black text-amber-900 mb-4 leading-[0.9] tracking-tight"
                  style={{ 
                    textRendering: 'optimizeLegibility', 
                    WebkitFontSmoothing: 'antialiased',
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}>
                <span className="text-slate-700">Hear from businesses</span>
                <br />
                <span className="relative inline-block">
                  <span className="text-amber-600 italic font-black"
                        style={{ 
                          fontWeight: 950,
                          textShadow: '0 2px 4px rgba(245, 158, 11, 0.3)'
                        }}>
                    just like yours
                  </span>
                  {/* Dramatic underline effect */}
                  <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-orange-500 to-amber-500 rounded-full opacity-90"></div>
                </span>
                <span className="block mt-2 text-slate-700">who chose TaxPoynt</span>
              </h2>
            </div>
            
            {/* Enhanced Subtitle */}
            <p className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-medium"
               style={{ 
                 textRendering: 'optimizeLegibility', 
                 WebkitFontSmoothing: 'antialiased',
                 textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
               }}>
              Real Nigerian businesses sharing <span className="text-amber-600 font-bold">their transformation stories</span> and measurable results with TaxPoynt's platform.
            </p>
          </div>

          {/* Testimonials Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
            
            {/* Testimonial 1 - Lagos Tech Company */}
            <div className="group relative p-8 bg-gradient-to-br from-amber-50 via-white to-orange-50/50 rounded-3xl 
                            shadow-xl hover:shadow-2xl hover:shadow-amber-500/20 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-amber-200/50 hover:border-amber-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #fefce8 0%, #ffffff 50%, #fff7ed 100%)',
                   boxShadow: '0 10px 25px -5px rgba(245, 158, 11, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-amber-50/20 via-transparent to-orange-50/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10">
                {/* Rating Stars */}
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className="text-amber-400 text-xl">⭐</span>
                  ))}
                </div>
                
                {/* Quote */}
                <div className="relative mb-6">
                  <div className="absolute -left-2 -top-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                  <p className="text-lg text-slate-700 leading-relaxed relative z-10 italic mb-4"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       lineHeight: '1.6'
                     }}>
                    TaxPoynt transformed our compliance from a 40-hour weekly nightmare to a 2-hour automated process. Our development team can now focus on building products instead of managing invoices.
                  </p>
                  <div className="absolute -right-2 -bottom-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                </div>
                
                {/* Results Badge */}
                <div className="mb-6">
                  <div className="inline-block px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full text-sm font-bold shadow-lg">
                    95% Time Saved
                  </div>
                </div>
                
                {/* Attribution */}
                <div className="border-t border-amber-200/50 pt-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-400 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      AK
                    </div>
                    <div>
                      <div className="font-bold text-slate-900">Adebayo Kolawole</div>
                      <div className="text-amber-700 text-sm font-medium">CTO, TechVantage Solutions</div>
                      <div className="text-slate-500 text-xs">Lagos • 500+ employees</div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-amber-500/5 to-orange-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            {/* Testimonial 2 - Abuja Manufacturing */}
            <div className="group relative p-8 bg-gradient-to-br from-amber-50 via-white to-orange-50/50 rounded-3xl 
                            shadow-xl hover:shadow-2xl hover:shadow-amber-500/20 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-amber-200/50 hover:border-amber-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #fefce8 0%, #ffffff 50%, #fff7ed 100%)',
                   boxShadow: '0 10px 25px -5px rgba(245, 158, 11, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-amber-50/20 via-transparent to-orange-50/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10">
                {/* Rating Stars */}
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className="text-amber-400 text-xl">⭐</span>
                  ))}
                </div>
                
                {/* Quote */}
                <div className="relative mb-6">
                  <div className="absolute -left-2 -top-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                  <p className="text-lg text-slate-700 leading-relaxed relative z-10 italic mb-4"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       lineHeight: '1.6'
                     }}>
                    Before TaxPoynt, we had 3 staff members working full-time on compliance. Now the same work happens automatically while they focus on strategic operations that grow our business.
                  </p>
                  <div className="absolute -right-2 -bottom-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                </div>
                
                {/* Results Badge */}
                <div className="mb-6">
                  <div className="inline-block px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full text-sm font-bold shadow-lg">
                    3 Full-Time Roles Automated
                  </div>
                </div>
                
                {/* Attribution */}
                <div className="border-t border-amber-200/50 pt-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-400 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      FO
                    </div>
                    <div>
                      <div className="font-bold text-slate-900">Fatima Okafor</div>
                      <div className="text-amber-700 text-sm font-medium">Operations Director, NorthSteel Industries</div>
                      <div className="text-slate-500 text-xs">Abuja • 1,200+ employees</div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-amber-500/5 to-orange-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            {/* Testimonial 3 - Port Harcourt SME */}
            <div className="group relative p-8 bg-gradient-to-br from-amber-50 via-white to-orange-50/50 rounded-3xl 
                            shadow-xl hover:shadow-2xl hover:shadow-amber-500/20 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-amber-200/50 hover:border-amber-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #fefce8 0%, #ffffff 50%, #fff7ed 100%)',
                   boxShadow: '0 10px 25px -5px rgba(245, 158, 11, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-amber-50/20 via-transparent to-orange-50/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10">
                {/* Rating Stars */}
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className="text-amber-400 text-xl">⭐</span>
                  ))}
                </div>
                
                {/* Quote */}
                <div className="relative mb-6">
                  <div className="absolute -left-2 -top-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                  <p className="text-lg text-slate-700 leading-relaxed relative z-10 italic mb-4"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       lineHeight: '1.6'
                     }}>
                    As a growing SME, compliance was becoming our biggest bottleneck. TaxPoynt's platform scales with us - from 50 invoices to 500+ monthly without adding complexity or staff.
                  </p>
                  <div className="absolute -right-2 -bottom-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                </div>
                
                {/* Results Badge */}
                <div className="mb-6">
                  <div className="inline-block px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full text-sm font-bold shadow-lg">
                    10x Business Growth Enabled
                  </div>
                </div>
                
                {/* Attribution */}
                <div className="border-t border-amber-200/50 pt-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-400 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      EI
                    </div>
                    <div>
                      <div className="font-bold text-slate-900">Emmanuel Ikenna</div>
                      <div className="text-amber-700 text-sm font-medium">CEO, Rivers Commerce Hub</div>
                      <div className="text-slate-500 text-xs">Port Harcourt • Growing SME</div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-amber-500/5 to-orange-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            {/* Testimonial 4 - Kano Retail */}
            <div className="group relative p-8 bg-gradient-to-br from-amber-50 via-white to-orange-50/50 rounded-3xl 
                            shadow-xl hover:shadow-2xl hover:shadow-amber-500/20 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-amber-200/50 hover:border-amber-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #fefce8 0%, #ffffff 50%, #fff7ed 100%)',
                   boxShadow: '0 10px 25px -5px rgba(245, 158, 11, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-amber-50/20 via-transparent to-orange-50/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10">
                {/* Rating Stars */}
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className="text-amber-400 text-xl">⭐</span>
                  ))}
                </div>
                
                {/* Quote */}
                <div className="relative mb-6">
                  <div className="absolute -left-2 -top-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                  <p className="text-lg text-slate-700 leading-relaxed relative z-10 italic mb-4"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       lineHeight: '1.6'
                     }}>
                    TaxPoynt's Nigerian support team understands our business context. When we had questions about northern Nigeria commerce regulations, they provided expert guidance immediately.
                  </p>
                  <div className="absolute -right-2 -bottom-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                </div>
                
                {/* Results Badge */}
                <div className="mb-6">
                  <div className="inline-block px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full text-sm font-bold shadow-lg">
                    100% Compliance Accuracy
                  </div>
                </div>
                
                {/* Attribution */}
                <div className="border-t border-amber-200/50 pt-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-400 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      AU
                    </div>
                    <div>
                      <div className="font-bold text-slate-900">Aisha Usman</div>
                      <div className="text-amber-700 text-sm font-medium">Finance Manager, Northern Trade Networks</div>
                      <div className="text-slate-500 text-xs">Kano • 200+ employees</div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-amber-500/5 to-orange-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            {/* Testimonial 5 - Ibadan Restaurant Chain */}
            <div className="group relative p-8 bg-gradient-to-br from-amber-50 via-white to-orange-50/50 rounded-3xl 
                            shadow-xl hover:shadow-2xl hover:shadow-amber-500/20 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-amber-200/50 hover:border-amber-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #fefce8 0%, #ffffff 50%, #fff7ed 100%)',
                   boxShadow: '0 10px 25px -5px rgba(245, 158, 11, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-amber-50/20 via-transparent to-orange-50/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10">
                {/* Rating Stars */}
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className="text-amber-400 text-xl">⭐</span>
                  ))}
                </div>
                
                {/* Quote */}
                <div className="relative mb-6">
                  <div className="absolute -left-2 -top-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                  <p className="text-lg text-slate-700 leading-relaxed relative z-10 italic mb-4"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       lineHeight: '1.6'
                     }}>
                    Our restaurant chain processes 200+ daily transactions across multiple locations. TaxPoynt handles everything automatically - our managers focus on customer service, not paperwork.
                  </p>
                  <div className="absolute -right-2 -bottom-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                </div>
                
                {/* Results Badge */}
                <div className="mb-6">
                  <div className="inline-block px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full text-sm font-bold shadow-lg">
                    Zero Compliance Stress
                  </div>
                </div>
                
                {/* Attribution */}
                <div className="border-t border-amber-200/50 pt-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-400 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      OA
                    </div>
                    <div>
                      <div className="font-bold text-slate-900">Olumide Adebayo</div>
                      <div className="text-amber-700 text-sm font-medium">Operations Manager, Taste of Yoruba</div>
                      <div className="text-slate-500 text-xs">Ibadan • Restaurant Chain</div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-amber-500/5 to-orange-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            {/* Testimonial 6 - Enugu E-commerce */}
            <div className="group relative p-8 bg-gradient-to-br from-amber-50 via-white to-orange-50/50 rounded-3xl 
                            shadow-xl hover:shadow-2xl hover:shadow-amber-500/20 
                            transition-all duration-300 hover:-translate-y-1 
                            cursor-pointer border border-amber-200/50 hover:border-amber-300/50 
                            backdrop-blur-sm"
                 style={{
                   background: 'linear-gradient(135deg, #fefce8 0%, #ffffff 50%, #fff7ed 100%)',
                   boxShadow: '0 10px 25px -5px rgba(245, 158, 11, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
                 }}>
              
              {/* Premium Background Overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-amber-50/20 via-transparent to-orange-50/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Content */}
              <div className="relative z-10">
                {/* Rating Stars */}
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className="text-amber-400 text-xl">⭐</span>
                  ))}
                </div>
                
                {/* Quote */}
                <div className="relative mb-6">
                  <div className="absolute -left-2 -top-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                  <p className="text-lg text-slate-700 leading-relaxed relative z-10 italic mb-4"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       lineHeight: '1.6'
                     }}>
                    TaxPoynt's API integration with our Shopify store was seamless. Every online sale automatically generates compliant invoices. Our customers receive proper documentation instantly.
                  </p>
                  <div className="absolute -right-2 -bottom-2 text-4xl text-amber-200/60 font-bold leading-none">"</div>
                </div>
                
                {/* Results Badge */}
                <div className="mb-6">
                  <div className="inline-block px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full text-sm font-bold shadow-lg">
                    Instant E-commerce Integration
                  </div>
                </div>
                
                {/* Attribution */}
                <div className="border-t border-amber-200/50 pt-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-400 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      CN
                    </div>
                    <div>
                      <div className="font-bold text-slate-900">Chioma Nwosu</div>
                      <div className="text-amber-700 text-sm font-medium">Founder, Eastern Electronics Online</div>
                      <div className="text-slate-500 text-xs">Enugu • E-commerce Platform</div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-amber-500/5 to-orange-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

          </div>

          {/* Overall Statistics Section */}
          <div className="text-center">
            {/* Trust Statistics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
              <div className="text-center">
                <div className="text-5xl md:text-6xl font-black text-amber-600 mb-2"
                     style={{
                       fontWeight: 950,
                       textShadow: '0 4px 8px rgba(245, 158, 11, 0.3)'
                     }}>
                  2,500+
                </div>
                <div className="text-lg font-bold text-slate-700">Happy Businesses</div>
                <div className="text-sm text-slate-500">across Nigeria</div>
              </div>
              <div className="text-center">
                <div className="text-5xl md:text-6xl font-black text-amber-600 mb-2"
                     style={{
                       fontWeight: 950,
                       textShadow: '0 4px 8px rgba(245, 158, 11, 0.3)'
                     }}>
                  4.9/5
                </div>
                <div className="text-lg font-bold text-slate-700">Average Rating</div>
                <div className="text-sm text-slate-500">from 1,000+ reviews</div>
              </div>
              <div className="text-center">
                <div className="text-5xl md:text-6xl font-black text-amber-600 mb-2"
                     style={{
                       fontWeight: 950,
                       textShadow: '0 4px 8px rgba(245, 158, 11, 0.3)'
                     }}>
                  99.9%
                </div>
                <div className="text-lg font-bold text-slate-700">Success Rate</div>
                <div className="text-sm text-slate-500">invoice submissions</div>
              </div>
              <div className="text-center">
                <div className="text-5xl md:text-6xl font-black text-amber-600 mb-2"
                     style={{
                       fontWeight: 950,
                       textShadow: '0 4px 8px rgba(245, 158, 11, 0.3)'
                     }}>
                  48hrs
                </div>
                <div className="text-lg font-bold text-slate-700">Setup Time</div>
                <div className="text-sm text-slate-500">average implementation</div>
              </div>
            </div>
            
            {/* Final Testimonial CTA */}
            <div className="max-w-4xl mx-auto">
              <div className="relative p-12 bg-gradient-to-br from-white/95 via-amber-50/90 to-white/95 
                              border-2 border-amber-200/50 rounded-3xl shadow-2xl backdrop-blur-sm"
                   style={{
                     background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(254,252,232,0.9) 50%, rgba(255,255,255,0.95) 100%)',
                     backdropFilter: 'blur(16px)',
                     boxShadow: '0 25px 50px -12px rgba(245, 158, 11, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)'
                   }}>
                
                <div className="mb-8">
                  <p className="text-3xl md:text-4xl font-bold text-slate-600 mb-4"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       textShadow: '0 2px 4px rgba(100, 116, 139, 0.3)'
                     }}>
                    Join thousands of satisfied Nigerian businesses
                  </p>
                  <p className="text-4xl md:text-5xl font-black text-amber-600 leading-tight"
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       fontWeight: 950,
                       textShadow: '0 2px 4px rgba(245, 158, 11, 0.3)'
                     }}>
                    Your success story starts here.
                  </p>
                </div>
                
                {/* CTA Button */}
                <button
                  onClick={() => router.push('/auth/signup')}
                  className="group relative inline-flex items-center justify-center px-16 py-6 bg-gradient-to-r from-amber-600 via-orange-600 to-amber-700 hover:from-amber-700 hover:via-orange-700 hover:to-amber-800 text-white font-bold rounded-3xl shadow-2xl hover:shadow-amber-500/40 transition-all duration-500 hover:scale-105 transform border border-amber-500/20 hover:border-amber-400/40 min-w-[400px] text-2xl mb-6"
                  style={{
                    background: 'linear-gradient(135deg, #d97706 0%, #ea580c 50%, #c2410c 100%)',
                    boxShadow: '0 25px 50px -12px rgba(245, 158, 11, 0.4), 0 10px 20px -4px rgba(0, 0, 0, 0.1), inset 0 2px 0 rgba(255, 255, 255, 0.2)',
                    textRendering: 'optimizeLegibility',
                    WebkitFontSmoothing: 'antialiased'
                  }}
                >
                  <span className="relative z-10">⭐ Start Your Success Story</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </button>
                
                {/* Supporting Text */}
                <div className="text-lg text-slate-600 font-medium">
                  <span className="mr-2">🇳🇬</span>
                  Join 2,500+ Nigerian businesses already transforming with TaxPoynt
                  <span className="ml-2">⭐</span>
                </div>
                
                {/* Subtle Pattern Overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-amber-50/20 via-transparent to-orange-50/20 rounded-3xl pointer-events-none"></div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Professional Footer */}
      <footer className="bg-gradient-to-br from-slate-900 via-gray-900 to-slate-900 text-white relative overflow-hidden">
        
        {/* Premium Background Effects */}
        <div className="absolute inset-0">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-gradient-to-br from-blue-600/10 to-indigo-600/10 rounded-full filter blur-3xl"></div>
          <div className="absolute top-0 right-1/4 w-80 h-80 bg-gradient-to-br from-green-600/10 to-emerald-600/10 rounded-full filter blur-3xl"></div>
          <div className="absolute bottom-0 left-1/2 w-72 h-72 bg-gradient-to-br from-amber-600/10 to-orange-600/10 rounded-full filter blur-3xl transform -translate-x-1/2"></div>
        </div>
        
        {/* Main Footer Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 pt-16 pb-8">
          
          {/* Top Section */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-12 mb-12">
            
            {/* Company Info */}
            <div className="lg:col-span-1">
              {/* Logo & Brand */}
              <div className="flex items-center space-x-3 mb-6">
                <img 
                  src="/logo.svg" 
                  alt="TaxPoynt Logo" 
                  className="h-10 w-auto filter brightness-0 invert"
                />
                <div>
                  <div className="text-2xl font-bold text-white" style={{ textShadow: '0 1px 2px rgba(255, 255, 255, 0.1)' }}>TaxPoynt</div>
                  <div className="text-sm text-slate-300 font-medium">Nigeria's #1 E-invoicing Platform</div>
                </div>
              </div>
              
              <p className="text-slate-300 leading-relaxed mb-6" style={{ 
                textRendering: 'optimizeLegibility', 
                WebkitFontSmoothing: 'antialiased' 
              }}>
                Transform your business compliance from complexity to competitive advantage with Nigeria's leading FIRS-certified e-invoicing platform.
              </p>
              
              {/* Certifications */}
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-lg flex items-center justify-center text-sm font-bold">🛡️</div>
                  <span className="text-slate-300">FIRS Certified Access Point Provider</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg flex items-center justify-center text-sm font-bold">🇳🇬</div>
                  <span className="text-slate-300">Nigerian Business Compliance Expert</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-amber-500 to-orange-500 rounded-lg flex items-center justify-center text-sm font-bold">⭐</div>
                  <span className="text-slate-300">2,500+ Satisfied Nigerian Businesses</span>
                </div>
              </div>
            </div>
            
            {/* Product Links */}
            <div>
              <h4 className="text-lg font-bold text-white mb-6 border-b border-slate-700 pb-2">Product</h4>
              <div className="space-y-4">
                {[
                  { name: 'Platform Features', href: '#features' },
                  { name: 'Service Packages', href: '#pricing' },
                  { name: 'API Integration', href: '/integrations' },
                  { name: 'System Integrations', href: '/systems' },
                  { name: 'Compliance Tools', href: '/compliance' },
                  { name: 'Analytics Dashboard', href: '/analytics' },
                  { name: 'Mobile App', href: '/mobile' }
                ].map((link, index) => (
                  <div key={index}>
                    <a 
                      href={link.href}
                      className="text-slate-300 hover:text-white transition-colors duration-200 flex items-center group"
                      style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}
                    >
                      <span className="w-2 h-2 bg-slate-500 rounded-full mr-3 group-hover:bg-blue-400 transition-colors duration-200"></span>
                      {link.name}
                    </a>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Company Links */}
            <div>
              <h4 className="text-lg font-bold text-white mb-6 border-b border-slate-700 pb-2">Company</h4>
              <div className="space-y-4">
                {[
                  { name: 'About TaxPoynt', href: '/about' },
                  { name: 'Contact Us', href: '/contact' },
                  { name: 'Book Demo', href: '/demo' },
                  { name: 'Success Stories', href: '/testimonials' },
                  { name: 'Nigerian Team', href: '/team' },
                  { name: 'Careers', href: '/careers' },
                  { name: 'Press & Media', href: '/press' }
                ].map((link, index) => (
                  <div key={index}>
                    <a 
                      href={link.href}
                      className="text-slate-300 hover:text-white transition-colors duration-200 flex items-center group"
                      style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}
                    >
                      <span className="w-2 h-2 bg-slate-500 rounded-full mr-3 group-hover:bg-green-400 transition-colors duration-200"></span>
                      {link.name}
                    </a>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Support & Legal */}
            <div>
              <h4 className="text-lg font-bold text-white mb-6 border-b border-slate-700 pb-2">Support & Legal</h4>
              <div className="space-y-4 mb-8">
                {[
                  { name: 'Help Center', href: '/help' },
                  { name: 'Documentation', href: '/docs' },
                  { name: 'API Reference', href: '/api-docs' },
                  { name: 'System Status', href: '/status' },
                  { name: 'Terms of Service', href: '/terms' },
                  { name: 'Privacy Policy', href: '/privacy' },
                  { name: 'NDPA Compliance', href: '/ndpa' }
                ].map((link, index) => (
                  <div key={index}>
                    <a 
                      href={link.href}
                      className="text-slate-300 hover:text-white transition-colors duration-200 flex items-center group"
                      style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}
                    >
                      <span className="w-2 h-2 bg-slate-500 rounded-full mr-3 group-hover:bg-amber-400 transition-colors duration-200"></span>
                      {link.name}
                    </a>
                  </div>
                ))}
              </div>
              
              {/* Newsletter Signup */}
              <div className="bg-slate-800/50 rounded-xl p-6 backdrop-blur-sm border border-slate-700/50">
                <h5 className="text-white font-bold mb-3 flex items-center gap-2">
                  <span>📧</span> Stay Updated
                </h5>
                <p className="text-slate-300 text-sm mb-4">Get compliance updates and platform news delivered to your inbox</p>
                <div className="flex gap-2">
                  <input 
                    type="email" 
                    placeholder="Enter your email"
                    className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors duration-200 text-sm"
                  />
                  <button className="px-4 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white font-bold rounded-lg transition-all duration-200 hover:scale-105 shadow-lg">
                    ✨
                  </button>
                </div>
                <p className="text-slate-400 text-xs mt-2">No spam. Unsubscribe anytime.</p>
              </div>
            </div>
          </div>
          
          {/* Divider */}
          <div className="border-t border-slate-700 pt-8">
            
            {/* Contact Info Row */}
            <div className="grid md:grid-cols-3 gap-8 mb-8">
              
              {/* Address */}
              <div className="text-center md:text-left">
                <h5 className="text-white font-bold mb-4 flex items-center justify-center md:justify-start gap-2">
                  <span className="text-2xl">🏢</span> Nigerian Office
                </h5>
                <div className="text-slate-300 space-y-1 leading-relaxed">
                  <p className="font-medium">TaxPoynt Nigeria Limited</p>
                  <p>Plot 123, Cadastral Zone A01</p>
                  <p>Central Business District</p>
                  <p>Abuja, FCT 900001, Nigeria</p>
                  <p className="text-sm text-slate-400 mt-2">🏛️ Corporate Registration: RC 1234567</p>
                </div>
              </div>
              
              {/* Contact */}
              <div className="text-center">
                <h5 className="text-white font-bold mb-4 flex items-center justify-center gap-2">
                  <span className="text-2xl">📞</span> Contact Info
                </h5>
                <div className="text-slate-300 space-y-3">
                  <div className="flex items-center justify-center gap-3 hover:text-white transition-colors duration-200 cursor-pointer">
                    <span className="w-8 h-8 bg-blue-600/20 rounded-lg flex items-center justify-center">📧</span>
                    <a href="mailto:hello@taxpoynt.com" className="hover:text-blue-400 transition-colors duration-200">hello@taxpoynt.com</a>
                  </div>
                  <div className="flex items-center justify-center gap-3 hover:text-white transition-colors duration-200 cursor-pointer">
                    <span className="w-8 h-8 bg-green-600/20 rounded-lg flex items-center justify-center">☎️</span>
                    <a href="tel:+2341234567890" className="hover:text-green-400 transition-colors duration-200">+234 (0) 123 456 7890</a>
                  </div>
                  <div className="flex items-center justify-center gap-3">
                    <span className="w-8 h-8 bg-amber-600/20 rounded-lg flex items-center justify-center">💬</span>
                    <span className="text-sm">24/7 Live Chat Support</span>
                  </div>
                  <div className="flex items-center justify-center gap-3">
                    <span className="w-8 h-8 bg-purple-600/20 rounded-lg flex items-center justify-center">⏰</span>
                    <span className="text-sm">Response within 2 hours</span>
                  </div>
                </div>
              </div>
              
              {/* Social Links */}
              <div className="text-center md:text-right">
                <h5 className="text-white font-bold mb-4 flex items-center justify-center md:justify-end gap-2">
                  <span className="text-2xl">🌐</span> Follow Us
                </h5>
                <div className="flex justify-center md:justify-end gap-3 mb-4">
                  {[
                    { name: 'LinkedIn', icon: '💼', href: 'https://linkedin.com/company/taxpoynt', color: 'hover:bg-blue-600' },
                    { name: 'Twitter', icon: '🐦', href: 'https://twitter.com/taxpoynt', color: 'hover:bg-sky-500' },
                    { name: 'Facebook', icon: '📘', href: 'https://facebook.com/taxpoynt', color: 'hover:bg-blue-700' },
                    { name: 'YouTube', icon: '📺', href: 'https://youtube.com/@taxpoynt', color: 'hover:bg-red-600' }
                  ].map((social, index) => (
                    <a 
                      key={index}
                      href={social.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`w-12 h-12 bg-slate-800 ${social.color} rounded-lg flex items-center justify-center text-xl transition-all duration-200 hover:scale-110 hover:shadow-lg`}
                      title={social.name}
                    >
                      {social.icon}
                    </a>
                  ))}
                </div>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Connect with Nigeria's #1 E-invoicing Platform
                  <br />
                  <span className="text-xs">Join our community of 2,500+ businesses</span>
                </p>
              </div>
            </div>
            
            {/* Bottom Bar */}
            <div className="flex flex-col md:flex-row justify-between items-center gap-6 pt-8 border-t border-slate-700">
              
              {/* Copyright */}
              <div className="text-slate-400 text-sm text-center md:text-left">
                <p className="mb-1">&copy; {new Date().getFullYear()} TaxPoynt Nigeria Limited. All rights reserved.</p>
                <p className="text-xs">FIRS Certified Access Point Provider • Corporate RC: 1234567 • VAT: 12345678-0001</p>
              </div>
              
              {/* Security & Compliance Badges */}
              <div className="flex flex-wrap items-center justify-center gap-3">
                <div className="flex items-center gap-2 bg-slate-800/50 px-3 py-2 rounded-lg border border-slate-700/50">
                  <span className="text-green-400 text-sm">🔒</span>
                  <span className="text-slate-300 text-xs font-medium">SSL Secured</span>
                </div>
                <div className="flex items-center gap-2 bg-slate-800/50 px-3 py-2 rounded-lg border border-slate-700/50">
                  <span className="text-blue-400 text-sm">🛡️</span>
                  <span className="text-slate-300 text-xs font-medium">GDPR Compliant</span>
                </div>
                <div className="flex items-center gap-2 bg-slate-800/50 px-3 py-2 rounded-lg border border-slate-700/50">
                  <span className="text-purple-400 text-sm">🏛️</span>
                  <span className="text-slate-300 text-xs font-medium">NDPA Certified</span>
                </div>
                <div className="flex items-center gap-2 bg-slate-800/50 px-3 py-2 rounded-lg border border-slate-700/50">
                  <span className="text-amber-400 text-sm">⭐</span>
                  <span className="text-slate-300 text-xs font-medium">ISO 27001</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Bottom Gradient */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-500 to-transparent"></div>
      </footer>

    </div>
  );
};
