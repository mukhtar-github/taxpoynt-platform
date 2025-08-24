/**
 * TaxPoynt Professional Landing Page
 * =================================
 * Clean, professional landing page focused on conversion and clarity.
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../design_system/components/Button';
import { Logo } from '../design_system/components/Logo';

export const LandingPage: React.FC = () => {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-900" style={{ 
      fontFeatureSettings: '"kern" 1, "liga" 1', 
      textRendering: 'optimizeLegibility', 
      WebkitFontSmoothing: 'antialiased', 
      MozOsxFontSmoothing: 'grayscale' 
    }}>
      
      {/* Navigation */}
      <nav className="px-6 py-4 border-b border-gray-700">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="relative group">
            {/* Sparkling Effect */}
            <div className="absolute -inset-2 opacity-75 group-hover:opacity-100 transition-opacity duration-300">
              <div className="absolute top-0 left-1/4 w-1 h-1 bg-blue-400 rounded-full animate-ping" style={{ animationDelay: '0s', animationDuration: '2s' }}></div>
              <div className="absolute top-2 right-1/4 w-1.5 h-1.5 bg-green-400 rounded-full animate-ping" style={{ animationDelay: '0.5s', animationDuration: '2.5s' }}></div>
              <div className="absolute bottom-1 left-1/2 w-1 h-1 bg-blue-500 rounded-full animate-ping" style={{ animationDelay: '1s', animationDuration: '3s' }}></div>
              <div className="absolute top-1/2 right-0 w-0.5 h-0.5 bg-green-500 rounded-full animate-ping" style={{ animationDelay: '1.5s', animationDuration: '2s' }}></div>
            </div>
            <div style={{ 
              color: '#3B82F6', 
              textShadow: '0 0 10px rgba(59, 130, 246, 0.3), 0 0 20px rgba(59, 130, 246, 0.1)',
              textRendering: 'optimizeLegibility', 
              WebkitFontSmoothing: 'antialiased' 
            }}>
              <Logo size="lg" variant="full" showTagline={true} />
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/auth/signin')}
              className="text-gray-300 hover:text-white font-medium"
              style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}
            >
              Sign In
            </button>
            <Button
              variant="primary"
              onClick={() => router.push('/auth/signup')}
            >
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative px-6 py-24 overflow-hidden bg-gradient-to-br from-gray-400 via-gray-300 to-gray-200 min-h-screen flex items-center">
        
        {/* Animated Background Patterns */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-green-500 rounded-full mix-blend-multiply filter blur-3xl animate-pulse"></div>
          <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl animate-pulse"></div>
          <div className="absolute bottom-1/4 left-1/2 w-72 h-72 bg-orange-500 rounded-full mix-blend-multiply filter blur-3xl animate-pulse"></div>
        </div>
        
        <div className="max-w-5xl mx-auto text-center relative z-10">
          
          {/* Enhanced Badge */}
          <div className="inline-flex items-center px-6 py-3 bg-white/90 backdrop-blur-sm border border-green-200 text-green-800 rounded-full text-sm font-medium mb-8 shadow-2xl hover:shadow-green-500/25 transition-all duration-300" 
               style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
            <span className="w-2 h-2 bg-green-500 rounded-full mr-3 animate-pulse"></span>
            FIRS Certified Access Point Provider
          </div>

          {/* Enhanced Headline */}
          <div className="mb-8">
            <div className="inline-block bg-gradient-to-r from-green-600 to-blue-700 text-white px-8 py-3 rounded-full text-base font-bold mb-6 shadow-2xl hover:shadow-green-500/50 transition-all duration-300 hover:scale-105">
              Stop wasting time on compliance paperwork
            </div>
            <h1 className="text-5xl md:text-7xl font-black text-white mb-6 leading-tight" 
                style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}>
              Submit compliant e-invoices in 
              <br />
              <span className="text-green-400 font-black" style={{ textShadow: '0 2px 4px rgba(0,0,0,0.4)' }}>
                seconds, not hours
              </span>
            </h1>
          </div>

          {/* Enhanced Subtitle */}
          <p className="text-xl md:text-2xl text-gray-100 mb-8 max-w-4xl mx-auto font-normal leading-relaxed" 
             style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
            Stop wasting hours on compliance paperwork. TaxPoynt connects your business software directly to government systems—one click and your e-invoices are submitted correctly, every time.
          </p>

          {/* Enhanced CTAs */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center mb-16">
            <Button
              variant="primary"
              size="lg"
              onClick={() => router.push('/auth/signup')}
              className="text-xl px-12 py-5 bg-gradient-to-r from-green-600 to-blue-700 hover:from-green-700 hover:to-blue-800 text-white font-bold rounded-2xl shadow-2xl hover:shadow-green-500/50 transition-all duration-300 hover:scale-105 transform"
            >
              Start Free Trial
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-xl px-12 py-5 border-2 border-white/30 text-white hover:bg-white/10 backdrop-blur-sm font-semibold rounded-2xl shadow-xl hover:shadow-white/25 transition-all duration-300 hover:scale-105 transform"
            >
              Learn More
            </Button>
          </div>

          {/* Removed trust indicators - moved to dedicated section */}
        </div>
      </section>

      {/* Professional Section Transition */}
      <div className="relative">
        {/* Multi-layered Shadow Effect */}
        <div className="absolute inset-0 bg-gradient-to-b from-gray-400 via-gray-300 to-transparent h-8 opacity-20"></div>
        <div className="absolute inset-0 bg-gradient-to-b from-gray-900 to-transparent h-12 opacity-10"></div>
        
        {/* Main Gradient Transition */}
        <div className="h-20 bg-gradient-to-b from-gray-400 via-gray-200 via-gray-100 to-white relative">
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

          {/* Problems Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            
            {/* Problem 1: Time Waste */}
            <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-200 border border-gray-200">
              <div className="text-blue-500 text-4xl mb-4">⏰</div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Hours Wasted Daily</h3>
              <p className="text-gray-700 mb-4">
                "I spend 3-4 hours every day just formatting invoices and submitting them manually to FIRS. That's time I should be growing my business."
              </p>
              <div className="text-blue-600 font-semibold text-sm">- Lagos Restaurant Owner</div>
            </div>

            {/* Problem 2: Constant Errors */}
            <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-200 border border-gray-200">
              <div className="text-blue-500 text-4xl mb-4">❌</div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Constant Rejection Errors</h3>
              <p className="text-gray-700 mb-4">
                "My invoices get rejected 60% of the time. Wrong format, missing fields, validation errors. I never know what's wrong until it's too late."
              </p>
              <div className="text-blue-600 font-semibold text-sm">- Abuja Tech Company</div>
            </div>

            {/* Problem 3: Compliance Stress */}
            <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-200 border border-gray-200">
              <div className="text-blue-500 text-4xl mb-4">😰</div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Compliance Anxiety</h3>
              <p className="text-gray-700 mb-4">
                "I'm always worried about penalties and fines. The rules keep changing and I can't keep up. Sleep is becoming a luxury."
              </p>
              <div className="text-blue-600 font-semibold text-sm">- Kano Manufacturing SME</div>
            </div>

            {/* Problem 4: Manual Data Entry */}
            <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-200 border border-gray-200">
              <div className="text-blue-500 text-4xl mb-4">📝</div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Double Data Entry</h3>
              <p className="text-gray-700 mb-4">
                "I enter the same data in my accounting software, then manually re-type everything for FIRS compliance. It's exhausting and error-prone."
              </p>
              <div className="text-blue-600 font-semibold text-sm">- Port Harcourt Retailer</div>
            </div>

            {/* Problem 5: Missing Deadlines */}
            <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-200 border border-gray-200">
              <div className="text-blue-500 text-4xl mb-4">📅</div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Missing Deadlines</h3>
              <p className="text-gray-700 mb-4">
                "Between running my business and compliance paperwork, I sometimes miss submission deadlines. The penalties are crushing my cash flow."
              </p>
              <div className="text-blue-600 font-semibold text-sm">- Ibadan Wholesaler</div>
            </div>

            {/* Problem 6: No Integration */}
            <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-200 border border-gray-200">
              <div className="text-blue-500 text-4xl mb-4">🔗</div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Software Disconnect</h3>
              <p className="text-gray-700 mb-4">
                "My POS system, accounting software, and FIRS compliance are completely separate. Nothing talks to each other. It's chaos."
              </p>
              <div className="text-blue-600 font-semibold text-sm">- Enugu Service Provider</div>
            </div>

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