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
          <p className="text-xl md:text-2xl text-gray-100 mb-12 max-w-4xl mx-auto font-normal leading-relaxed" 
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

      {/* Professional Section Separator */}
      <div className="h-16 bg-gradient-to-b from-gray-200 via-gray-100 to-white"></div>

      {/* Section 2: Trust Indicators */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="text-5xl md:text-7xl font-black text-green-600 mb-4" 
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     fontWeight: '900',
                     textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                     WebkitTextStroke: '1px rgba(34, 197, 94, 0.3)'
                   }}>
                Zero
              </div>
              <div className="text-gray-700 text-sm md:text-base font-semibold group-hover:text-green-600 transition-colors" 
                   style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                E-invoice submission errors
              </div>
            </div>
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="text-5xl md:text-7xl font-black text-blue-600 mb-4" 
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     fontWeight: '900',
                     textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                     WebkitTextStroke: '1px rgba(37, 99, 235, 0.3)'
                   }}>
                2 min
              </div>
              <div className="text-gray-700 text-sm md:text-base font-semibold group-hover:text-blue-600 transition-colors" 
                   style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                From sale to compliance submission
              </div>
            </div>
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="text-5xl md:text-7xl font-black text-green-600 mb-4" 
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     fontWeight: '900',
                     textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                     WebkitTextStroke: '1px rgba(34, 197, 94, 0.3)'
                   }}>
                100%
              </div>
              <div className="text-gray-700 text-sm md:text-base font-semibold group-hover:text-green-600 transition-colors" 
                   style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                Nigerian compliance coverage
              </div>
            </div>
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="text-5xl md:text-7xl font-black text-blue-600 mb-4" 
                   style={{ 
                     textRendering: 'optimizeLegibility', 
                     WebkitFontSmoothing: 'antialiased',
                     fontWeight: '900',
                     textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                     WebkitTextStroke: '1px rgba(37, 99, 235, 0.3)'
                   }}>
                Any
              </div>
              <div className="text-gray-700 text-sm md:text-base font-semibold group-hover:text-blue-600 transition-colors" 
                   style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
                Software you already use
              </div>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
};