/**
 * TaxPoynt Professional Landing Page
 * =================================
 * Clean, professional landing page focused on conversion and clarity.
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { 
  TaxPoyntButton, 
  HeroCTAButton, 
  ProblemCard,
  SolutionCard,
  PROBLEMS_DATA,
  ENTERPRISE_SOLUTIONS_DATA,
  buildGridClasses,
  TAXPOYNT_DESIGN_SYSTEM 
} from '../design_system';

export const LandingPage: React.FC = () => {
  const router = useRouter();

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

      {/* Hero Section */}
      <section className="relative px-6 py-24 overflow-hidden bg-gradient-to-br from-slate-100 via-gray-50 to-white min-h-screen flex items-center" style={{ background: 'linear-gradient(135deg, #f1f5f9 0%, #f8fafc 50%, #ffffff 100%)' }}>
        
        {/* Premium Background Patterns */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-gradient-to-br from-blue-400/20 to-indigo-400/20 rounded-full filter blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
          <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-gradient-to-br from-emerald-400/15 to-green-400/15 rounded-full filter blur-3xl animate-pulse" style={{ animationDuration: '10s' }}></div>
          <div className="absolute bottom-1/4 left-1/2 w-72 h-72 bg-gradient-to-br from-violet-400/10 to-purple-400/10 rounded-full filter blur-3xl animate-pulse" style={{ animationDuration: '12s' }}></div>
          {/* Subtle texture overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-slate-100/20"></div>
        </div>
        
        <div className="max-w-5xl mx-auto text-center relative z-10">
          
          {/* Enhanced Badge */}
          <div className="inline-flex items-center px-8 py-4 bg-green-50/95 backdrop-blur-sm border border-green-300 text-green-800 rounded-full text-sm font-semibold mb-8 shadow-xl hover:shadow-green-200/50 transition-all duration-300 hover:scale-105" 
               style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
            <span className="w-2 h-2 rounded-full mr-3" style={{ backgroundColor: '#166534' }}></span>
            FIRS Certified Access Point Provider
          </div>

          {/* Enhanced Headline */}
          <div className="mb-8">
            <div className="inline-block bg-gradient-to-r from-sky-100 to-blue-100 text-blue-700 px-10 py-4 rounded-full text-lg font-bold mb-8 shadow-xl hover:shadow-blue-200/40 transition-all duration-300 hover:scale-105 border border-blue-300/40">
              Stop wasting time on compliance paperwork
            </div>
            <h1 className="text-6xl md:text-8xl font-black text-slate-600 mb-8 leading-[0.95] tracking-tight" 
                style={{ 
                  textRendering: 'optimizeLegibility', 
                  WebkitFontSmoothing: 'antialiased',
                  textShadow: '0 2px 4px rgba(0,0,0,0.05), 0 4px 8px rgba(0,0,0,0.03)',
                  fontWeight: 950
                }}>
<span className="text-slate-600">Submit compliant e-invoices in</span> 
              <br />
              <span className="text-green-600 font-black" style={{ fontWeight: 950, textShadow: '0 2px 4px rgba(34, 197, 94, 0.3)' }}>
                seconds, not hours
              </span>
            </h1>
          </div>

          {/* Enhanced Subtitle */}
          <p className="text-xl md:text-2xl text-slate-600 mb-12 max-w-4xl mx-auto font-medium leading-relaxed" 
             style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
            Stop wasting hours on compliance paperwork. TaxPoynt connects your business software directly to government systems—one click and your e-invoices are submitted correctly, every time.
          </p>

          {/* Premium CTAs */}
          <div className="flex flex-col sm:flex-row gap-8 justify-center mb-20">
            <HeroCTAButton
              onClick={() => router.push('/auth/signup')}
              className="group relative text-xl px-16 py-6 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-700 hover:via-indigo-700 hover:to-purple-700 text-white font-bold rounded-2xl shadow-2xl hover:shadow-indigo-500/40 transition-all duration-500 hover:scale-110 transform border border-white/20"
              style={{
                background: 'linear-gradient(135deg, #2563eb 0%, #4f46e5 50%, #7c3aed 100%)',
                boxShadow: '0 20px 40px -12px rgba(79, 70, 229, 0.4), 0 8px 16px -4px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.2)'
              }}
            >
              <span className="relative z-10 flex items-center justify-center">
                ✨ Start Free Trial
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            </HeroCTAButton>
            <TaxPoyntButton
              variant="secondary"
              size="lg"
              onClick={() => {
                document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-xl px-12 py-6 border-2 border-slate-300 text-slate-700 hover:bg-white hover:border-slate-400 hover:text-slate-900 font-semibold rounded-2xl shadow-lg hover:shadow-slate-300/50 transition-all duration-300 hover:scale-105 transform bg-white/80 backdrop-blur-sm"
            >
              Learn More
            </TaxPoyntButton>
          </div>

          {/* Removed trust indicators - moved to dedicated section */}
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

      {/* Section 2: Premium Trust Indicators */}
      <section className="py-20 bg-gradient-to-br from-white via-slate-50/30 to-white relative overflow-hidden" style={{ 
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.8), 0 4px 12px rgba(0,0,0,0.08)' 
      }}>
        {/* Subtle Background Patterns */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-green-300 rounded-full filter blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
          <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-blue-300 rounded-full filter blur-3xl animate-pulse" style={{ animationDuration: '10s' }}></div>
        </div>
        
        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-12 text-center">
            <div className="group relative p-8 rounded-2xl hover:shadow-2xl hover:shadow-green-500/20 transition-all duration-500 hover:-translate-y-2 cursor-pointer">
              {/* Premium Background Card */}
              <div className="absolute inset-0 bg-gradient-to-br from-white via-green-50/30 to-white rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 shadow-xl"></div>
              
              <div className="relative z-10">
                <div className="text-4xl md:text-5xl font-black text-green-600 mb-3 leading-none" 
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       fontWeight: '900',
                       textShadow: '0 2px 4px rgba(34, 197, 94, 0.15)',
                       filter: 'drop-shadow(0 1px 2px rgba(34, 197, 94, 0.1))'
                     }}>
                  Zero
                </div>
                <div className="text-slate-700 text-lg md:text-xl font-semibold group-hover:text-green-700 transition-colors duration-300 leading-tight" 
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                  E-invoice submission errors
                </div>
              </div>
            </div>
            <div className="group relative p-8 rounded-2xl hover:shadow-2xl hover:shadow-green-500/20 transition-all duration-500 hover:-translate-y-2 cursor-pointer">
              {/* Premium Background Card */}
              <div className="absolute inset-0 bg-gradient-to-br from-white via-green-50/30 to-white rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 shadow-xl"></div>
              
              <div className="relative z-10">
                <div className="text-4xl md:text-5xl font-black text-green-600 mb-3 leading-none" 
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       fontWeight: '900',
                       textShadow: '0 2px 4px rgba(34, 197, 94, 0.15)',
                       filter: 'drop-shadow(0 1px 2px rgba(34, 197, 94, 0.1))'
                     }}>
                  2 min
                </div>
                <div className="text-slate-700 text-lg md:text-xl font-semibold group-hover:text-green-700 transition-colors duration-300 leading-tight" 
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                  From sale to compliance submission
                </div>
              </div>
            </div>
            <div className="group relative p-8 rounded-2xl hover:shadow-2xl hover:shadow-green-500/20 transition-all duration-500 hover:-translate-y-2 cursor-pointer">
              {/* Premium Background Card */}
              <div className="absolute inset-0 bg-gradient-to-br from-white via-green-50/30 to-white rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 shadow-xl"></div>
              
              <div className="relative z-10">
                <div className="text-4xl md:text-5xl font-black text-green-600 mb-3 leading-none" 
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       fontWeight: '900',
                       textShadow: '0 2px 4px rgba(34, 197, 94, 0.15)',
                       filter: 'drop-shadow(0 1px 2px rgba(34, 197, 94, 0.1))'
                     }}>
                  100%
                </div>
                <div className="text-slate-700 text-lg md:text-xl font-semibold group-hover:text-green-700 transition-colors duration-300 leading-tight" 
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                  Nigerian compliance coverage
                </div>
              </div>
            </div>
            <div className="group relative p-8 rounded-2xl hover:shadow-2xl hover:shadow-green-500/20 transition-all duration-500 hover:-translate-y-2 cursor-pointer">
              {/* Premium Background Card */}
              <div className="absolute inset-0 bg-gradient-to-br from-white via-green-50/30 to-white rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 shadow-xl"></div>
              
              <div className="relative z-10">
                <div className="text-4xl md:text-5xl font-black text-green-600 mb-3 leading-none" 
                     style={{ 
                       textRendering: 'optimizeLegibility', 
                       WebkitFontSmoothing: 'antialiased',
                       fontWeight: '900',
                       textShadow: '0 2px 4px rgba(34, 197, 94, 0.15)',
                       filter: 'drop-shadow(0 1px 2px rgba(34, 197, 94, 0.1))'
                     }}>
                  Any
                </div>
                <div className="text-slate-700 text-lg md:text-xl font-semibold group-hover:text-green-700 transition-colors duration-300 leading-tight" 
                     style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                  Software you already use
                </div>
              </div>
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

    </div>
  );
};
