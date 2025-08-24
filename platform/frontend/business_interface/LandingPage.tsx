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
  PROBLEMS_DATA,
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
      <nav className="px-6 py-4 border-b border-gray-200">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img 
              src="/logo.svg" 
              alt="TaxPoynt Logo" 
              className="h-8 w-auto"
            />
            <div>
              <div className="text-xl font-bold text-blue-600">TaxPoynt</div>
              <div className="text-sm text-blue-500">Secure E-invoicing Solution</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/auth/signin')}
              className="text-gray-600 hover:text-gray-900 font-medium"
              style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}
            >
              Sign In
            </button>
            <TaxPoyntButton
              variant="primary"
              onClick={() => router.push('/auth/signup')}
            >
              Get Started
            </TaxPoyntButton>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative px-6 py-24 overflow-hidden bg-gradient-to-br from-gray-100 via-gray-50 to-white min-h-screen flex items-center">
        
        {/* Subtle Background Patterns */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-blue-300 rounded-full filter blur-3xl animate-pulse" style={{ animationDuration: '4s' }}></div>
          <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-green-300 rounded-full filter blur-3xl animate-pulse" style={{ animationDuration: '5s' }}></div>
          <div className="absolute bottom-1/4 left-1/2 w-72 h-72 bg-indigo-300 rounded-full filter blur-3xl animate-pulse" style={{ animationDuration: '6s' }}></div>
        </div>
        
        <div className="max-w-5xl mx-auto text-center relative z-10">
          
          {/* Enhanced Badge */}
          <div className="inline-flex items-center px-6 py-3 bg-green-50 border border-green-300 text-green-800 rounded-full text-sm font-medium mb-8 shadow-lg hover:shadow-green-200 transition-all duration-300" 
               style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
            <span className="w-2 h-2 bg-green-500 rounded-full mr-3 animate-pulse"></span>
            FIRS Certified Access Point Provider
          </div>

          {/* Enhanced Headline */}
          <div className="mb-8">
            <div className="inline-block bg-gradient-to-r from-green-600 to-blue-600 text-white px-8 py-3 rounded-full text-base font-bold mb-6 shadow-xl hover:shadow-green-300 transition-all duration-300 hover:scale-105">
              Stop wasting time on compliance paperwork
            </div>
            <h1 className="text-5xl md:text-7xl font-black text-gray-900 mb-6 leading-tight" 
                style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
              Submit compliant e-invoices in 
              <br />
              <span className="text-green-600 font-black">
                seconds, not hours
              </span>
            </h1>
          </div>

          {/* Enhanced Subtitle */}
          <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-4xl mx-auto font-normal leading-relaxed" 
             style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
            Stop wasting hours on compliance paperwork. TaxPoynt connects your business software directly to government systems—one click and your e-invoices are submitted correctly, every time.
          </p>

          {/* Enhanced CTAs */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center mb-16">
            <HeroCTAButton
              onClick={() => router.push('/auth/signup')}
              className="text-xl px-12 py-5 bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-blue-300 transition-all duration-300 hover:scale-105 transform"
            >
              Start Free Trial
            </HeroCTAButton>
            <TaxPoyntButton
              variant="secondary"
              size="lg"
              onClick={() => {
                document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-xl px-12 py-5 border-2 border-gray-300 text-gray-700 hover:bg-gray-100 hover:border-gray-400 font-semibold rounded-2xl shadow-lg hover:shadow-gray-300 transition-all duration-300 hover:scale-105 transform"
            >
              Learn More
            </TaxPoyntButton>
          </div>

          {/* Removed trust indicators - moved to dedicated section */}
        </div>
      </section>

      {/* Professional Section Transition */}
      <div className="relative">
        {/* Multi-layered Shadow Effect */}
        <div className="absolute inset-0 bg-gradient-to-b from-gray-100 via-gray-50 to-transparent h-8 opacity-30"></div>
        <div className="absolute inset-0 bg-gradient-to-b from-gray-200 to-transparent h-12 opacity-20"></div>
        
        {/* Main Gradient Transition */}
        <div className="h-20 bg-gradient-to-b from-gray-50 via-gray-25 to-white relative">
          {/* Subtle Geometric Element */}
          <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-24 h-1 bg-gradient-to-r from-green-500 to-blue-500 rounded-full opacity-30"></div>
        </div>
        
        {/* Professional Drop Shadow */}
        <div className="absolute inset-x-0 bottom-0 h-4 bg-gradient-to-b from-black/5 to-transparent"></div>
      </div>

      {/* Section 2: Trust Indicators */}
      <section className="py-16 bg-white relative" style={{ 
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.1), 0 1px 3px rgba(0,0,0,0.05)' 
      }}>
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="!text-5xl md:!text-6xl !font-black italic text-green-600 mb-1" 
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     fontWeight: '900 !important',
                     fontSize: '3.5rem !important',
                     textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                     WebkitTextStroke: '1px rgba(34, 197, 94, 0.3)'
                   }}>
                Zero
              </div>
              <div className="text-gray-700 text-base md:text-lg font-semibold group-hover:text-green-600 transition-colors" 
                   style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                E-invoice submission errors
              </div>
            </div>
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="!text-5xl md:!text-6xl !font-black italic text-green-600 mb-1" 
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     fontWeight: '900 !important',
                     fontSize: '3.5rem !important',
                     textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                     WebkitTextStroke: '1px rgba(34, 197, 94, 0.3)'
                   }}>
                2 min
              </div>
              <div className="text-gray-700 text-base md:text-lg font-semibold group-hover:text-green-600 transition-colors" 
                   style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                From sale to compliance submission
              </div>
            </div>
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="!text-5xl md:!text-6xl !font-black italic text-green-600 mb-1" 
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     fontWeight: '900 !important',
                     fontSize: '3.5rem !important',
                     textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                     WebkitTextStroke: '1px rgba(34, 197, 94, 0.3)'
                   }}>
                100%
              </div>
              <div className="text-gray-700 text-base md:text-lg font-semibold group-hover:text-green-600 transition-colors" 
                   style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                Nigerian compliance coverage
              </div>
            </div>
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="!text-5xl md:!text-6xl !font-black italic text-green-600 mb-1" 
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     fontWeight: '900 !important',
                     fontSize: '3.5rem !important',
                     textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                     WebkitTextStroke: '1px rgba(34, 197, 94, 0.3)'
                   }}>
                Any
              </div>
              <div className="text-gray-700 text-base md:text-lg font-semibold group-hover:text-green-600 transition-colors" 
                   style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                Software you already use
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
      <section className="py-20 bg-gray-700">
        <div className="max-w-6xl mx-auto px-6">
          
          {/* Section Header */}
          <div className="text-center mb-16">
            <div className="inline-block bg-blue-100 text-blue-800 px-6 py-2 rounded-full text-sm font-semibold mb-6">
              The Nigerian Business Reality
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-white mb-6 leading-tight">
              E-invoicing compliance is 
              <span className="text-blue-400 italic"> crushing</span> Nigerian businesses
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
              Every day, thousands of Nigerian business owners struggle with the same compliance nightmare
            </p>
          </div>

          {/* Problems Grid - Using Design System */}
          <div className={buildGridClasses('problems')}>
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

          {/* Bottom CTA - Enhanced Visibility */}
          <div className="text-center mt-20 mb-8">
            <p className="text-2xl text-gray-100 mb-8 font-semibold">
              Sound familiar? <span className="text-blue-400 font-bold">You're not alone.</span>
            </p>
            <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-8 max-w-3xl mx-auto shadow-md">
              <p className="text-blue-900 text-xl font-semibold leading-relaxed">
                Over 2 million Nigerian businesses struggle with these exact same problems every single day.
              </p>
              <div className="mt-4 text-blue-700 text-lg">
                But there's a better way...
              </div>
            </div>
          </div>

        </div>
      </section>

    </div>
  );
};