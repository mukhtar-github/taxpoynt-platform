/**
 * TaxPoynt Strategic Landing Page
 * ==============================
 * Simple but sophisticated landing page following Steve Jobs' principles.
 * Focuses on clear value proposition and strategic CTAs.
 * 
 * "Simplicity is the ultimate sophistication" - Steve Jobs
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../design_system/components/Button';
import { Logo } from '../design_system/components/Logo';
import { 
  FileText, 
  Clock, 
  Shield,
  Database,
  Monitor,
  CheckCircle,
  Calculator,
  Building,
  Receipt,
  Banknote,
  Settings,
  AlertTriangle
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const router = useRouter();

  // Add floating animation styles
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes float {
        0%, 100% { transform: translate(0px, 0px) rotate(0deg); }
        33% { transform: translate(30px, -30px) rotate(120deg); }
        66% { transform: translate(-20px, 20px) rotate(240deg); }
      }
    `;
    document.head.appendChild(style);
    
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-900" style={{ fontFeatureSettings: '"kern" 1, "liga" 1', textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', MozOsxFontSmoothing: 'grayscale' }}>
      
      {/* Navigation - Professional */}
      <nav className="px-6 py-4 border-b border-gray-200">
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
              className="text-gray-600 hover:text-gray-900 font-medium"
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
      <section className="relative px-6 py-24 overflow-hidden min-h-screen flex items-center">
        {/* Sophisticated Dark Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-gray-800 via-gray-700 to-gray-600">
          {/* Animated Background Patterns */}
          <div className="absolute inset-0 opacity-30">
            <div 
              className="absolute top-1/4 right-1/4 w-96 h-96 bg-green-500 rounded-full mix-blend-multiply filter blur-3xl animate-pulse"
              style={{
                animation: 'float 8s ease-in-out infinite',
                animationDelay: '0s'
              }}
            ></div>
            <div 
              className="absolute top-1/3 left-1/4 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl animate-pulse"
              style={{
                animation: 'float 10s ease-in-out infinite reverse',
                animationDelay: '2s'
              }}
            ></div>
            <div 
              className="absolute bottom-1/4 left-1/2 w-72 h-72 bg-orange-500 rounded-full mix-blend-multiply filter blur-3xl animate-pulse"
              style={{
                animation: 'float 12s ease-in-out infinite',
                animationDelay: '4s'
              }}
            ></div>
          </div>
          
          {/* Removed grid overlay for clean design */}
        </div>
        
        <div className="max-w-5xl mx-auto text-center relative z-10">
          
          {/* Enhanced Badge */}
          <div className="inline-flex items-center px-6 py-3 bg-white/90 backdrop-blur-sm border border-green-200 text-green-800 rounded-full text-sm font-medium mb-8 shadow-2xl hover:shadow-green-500/25 transition-all duration-300" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
            <span className="w-2 h-2 bg-green-500 rounded-full mr-3 animate-pulse"></span>
            FIRS Certified Access Point Provider
          </div>

          {/* Enhanced Headline with Animation */}
          <div className="mb-12">
            <div className="inline-block bg-gradient-to-r from-green-600 to-blue-700 text-white px-8 py-3 rounded-full text-base font-bold mb-8 shadow-2xl hover:shadow-green-500/50 transition-all duration-300 hover:scale-105">
              Stop wasting time on government paperwork
            </div>
            <h1 className="text-5xl md:text-7xl font-black text-white mb-8 leading-tight" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}>
              Send invoices to FIRS in 
              <br />
              <span className="text-green-400 font-black" style={{ textShadow: '0 2px 4px rgba(0,0,0,0.4)' }}>
                seconds, not hours
              </span>
            </h1>
          </div>

          {/* Enhanced Subtitle */}
          <p className="text-xl md:text-2xl text-gray-100 mb-20 max-w-4xl mx-auto font-normal leading-relaxed" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>
            Stop wasting hours on FIRS paperwork. TaxPoynt connects your business software directly to FIRS—one click and your invoices are submitted correctly, every time.
          </p>

          {/* Enhanced CTAs */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center mb-20">
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
                document.getElementById('services')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-xl px-12 py-5 border-2 border-white/30 text-white hover:bg-white/10 backdrop-blur-sm font-semibold rounded-2xl shadow-xl hover:shadow-white/25 transition-all duration-300 hover:scale-105 transform"
            >
              Learn More
            </Button>
          </div>

          {/* Enhanced Trust Indicators - Sharp Text */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="text-4xl font-black text-green-400 mb-2" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}>Zero</div>
              <div className="text-gray-100 text-sm font-semibold group-hover:text-white transition-colors" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>FIRS submission errors</div>
            </div>
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="text-4xl font-black text-blue-400 mb-2" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}>2 min</div>
              <div className="text-gray-100 text-sm font-semibold group-hover:text-white transition-colors" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>From sale to FIRS submission</div>
            </div>
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="text-4xl font-black text-green-400 mb-2" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}>100%</div>
              <div className="text-gray-100 text-sm font-semibold group-hover:text-white transition-colors" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>Nigerian compliance coverage</div>
            </div>
            <div className="group hover:scale-110 transition-all duration-300">
              <div className="text-4xl font-black text-blue-400 mb-2" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased', textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}>Any</div>
              <div className="text-gray-100 text-sm font-semibold group-hover:text-white transition-colors" style={{ textRendering: 'optimizeLegibility', WebkitFontSmoothing: 'antialiased' }}>Software you already use</div>
            </div>
          </div>
        </div>
      </section>

      {/* Problems Section - Show Current Pain Points */}
      <section className="relative px-6 py-24 overflow-hidden">
        {/* Sophisticated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-red-50 via-orange-25 to-yellow-50">
          {/* Floating Problem Indicators */}
          <div className="absolute inset-0 opacity-20">
            <div 
              className="absolute top-1/4 left-1/4 w-64 h-64 bg-red-400 rounded-full mix-blend-multiply filter blur-3xl"
              style={{
                animation: 'float 10s ease-in-out infinite',
                animationDelay: '1s'
              }}
            ></div>
            <div 
              className="absolute bottom-1/3 right-1/4 w-48 h-48 bg-orange-400 rounded-full mix-blend-multiply filter blur-3xl"
              style={{
                animation: 'float 12s ease-in-out infinite reverse',
                animationDelay: '3s'
              }}
            ></div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-6xl font-black text-gray-900 mb-8 leading-tight">
              E-invoicing Paperwork is Taking Your Business Time
            </h2>
            <p className="text-2xl text-gray-700 max-w-4xl mx-auto font-light leading-relaxed">
              Nigerian businesses waste countless hours on e-invoicing paperwork, making costly mistakes, and struggling with complex compliance requirements.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {/* Problem 1: Time Waste */}
            <div className="group bg-white/80 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-red-100 hover:shadow-red-500/20 transition-all duration-500 hover:scale-105 transform">
              <div className="w-20 h-20 bg-gradient-to-br from-red-500 to-orange-600 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform duration-300">
                <Clock className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-2xl font-black text-gray-900 mb-6 text-center">Hours of Manual Work</h3>
              <div className="space-y-3 text-gray-700">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>15+ hours per week on FIRS paperwork</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Manual invoice formatting and classification</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Manual copying of transaction data from bank statements</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Back-and-forth with accountants and staff</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Time away from growing your business</span>
                </div>
              </div>
            </div>

            {/* Problem 2: Costly Errors */}
            <div className="group bg-white/80 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-red-100 hover:shadow-red-500/20 transition-all duration-500 hover:scale-105 transform">
              <div className="w-20 h-20 bg-gradient-to-br from-red-600 to-pink-600 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform duration-300">
                <AlertTriangle className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-2xl font-black text-gray-900 mb-6 text-center">Expensive Mistakes</h3>
              <div className="space-y-3 text-gray-700">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Classification errors lead to penalties</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Invoice rejections cause delays</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Compliance issues risk your business</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Lost revenue from processing delays</span>
                </div>
              </div>
            </div>

            {/* Problem 3: Technical Complexity */}
            <div className="group bg-white/80 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-red-100 hover:shadow-red-500/20 transition-all duration-500 hover:scale-105 transform">
              <div className="w-20 h-20 bg-gradient-to-br from-orange-500 to-red-600 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform duration-300">
                <Settings className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-2xl font-black text-gray-900 mb-6 text-center">Complex Integration</h3>
              <div className="space-y-3 text-gray-700">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>E-invoicing compliance rules are complex and constantly changing</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Your current software doesn't connect</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Need expensive developers for integration</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <span>Constant updates and maintenance required</span>
                </div>
              </div>
            </div>
          </div>

          {/* Enhanced Emotional Impact */}
          <div className="mt-20 text-center bg-white/90 backdrop-blur-sm rounded-3xl p-12 shadow-2xl border border-red-200 hover:shadow-red-500/25 transition-all duration-500">
            <h3 className="text-3xl md:text-4xl font-black text-gray-900 mb-6 leading-tight">You Started Your Business to Serve Customers, Not Handle Paperwork</h3>
            <p className="text-xl text-gray-700 max-w-4xl mx-auto font-light leading-relaxed">
              Every hour spent on FIRS compliance is an hour not spent growing your business, serving customers, or focusing on what you do best.
            </p>
          </div>
        </div>
      </section>

      {/* Solution Section - How TaxPoynt Solves Each Problem */}
      <section className="relative px-6 py-24 overflow-hidden">
        {/* Sophisticated Green Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-green-50 via-blue-25 to-emerald-50">
          {/* Floating Solution Indicators */}
          <div className="absolute inset-0 opacity-20">
            <div 
              className="absolute top-1/4 right-1/4 w-72 h-72 bg-green-400 rounded-full mix-blend-multiply filter blur-3xl"
              style={{
                animation: 'float 14s ease-in-out infinite',
                animationDelay: '2s'
              }}
            ></div>
            <div 
              className="absolute bottom-1/3 left-1/4 w-56 h-56 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl"
              style={{
                animation: 'float 16s ease-in-out infinite reverse',
                animationDelay: '5s'
              }}
            ></div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-6xl font-black text-gray-900 mb-8 leading-tight">
              TaxPoynt Simplifies Every E-invoicing Challenge
            </h2>
            <p className="text-2xl text-gray-700 max-w-4xl mx-auto font-light leading-relaxed">
              We handle all the complexity so you can focus on your business. Here's exactly how we solve each problem:
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {/* Solution 1: Automate Manual Work */}
            <div className="group bg-white/80 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-green-100 hover:shadow-green-500/20 transition-all duration-500 hover:scale-105 transform">
              <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform duration-300">
                <CheckCircle className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-2xl font-black text-gray-900 mb-6 text-center">Complete Automation</h3>
              <div className="space-y-3 text-gray-700 mb-6">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>Financial data flows seamlessly into invoice processing</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>Invoices submit to FIRS automatically</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>No manual formatting or classification needed</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>Works with your existing workflow</span>
                </div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-600 mb-1">Save 12+ Hours/Week</div>
                <div className="text-sm text-green-700">Focus on growing your business instead</div>
              </div>
            </div>

            {/* Solution 2: Zero Errors */}
            <div className="group bg-white/80 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-green-100 hover:shadow-green-500/20 transition-all duration-500 hover:scale-105 transform">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-green-600 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform duration-300">
                <Shield className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-2xl font-black text-gray-900 mb-6 text-center">Perfect Compliance</h3>
              <div className="space-y-3 text-gray-700 mb-6">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>Intelligence-powered classification prevents errors</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>Real-time validation before submission</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>Automatic compliance updates</span>
                </div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-600 mb-1">Zero Errors</div>
                <div className="text-sm text-green-700">No more penalties or rejections</div>
              </div>
            </div>

            {/* Solution 3: Simple Integration */}
            <div className="group bg-white/80 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-green-100 hover:shadow-green-500/20 transition-all duration-500 hover:scale-105 transform">
              <div className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-blue-600 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform duration-300">
                <Monitor className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-2xl font-black text-gray-900 mb-6 text-center">One-Click Integration</h3>
              <div className="space-y-3 text-gray-700 mb-6">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>Works with 40+ popular business software</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>Secure transaction data automation technology</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>No developers or technical knowledge needed</span>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <span>We handle all updates and maintenance</span>
                </div>
              </div>
              
              {/* Security Badge */}
              <div className="bg-blue-50 rounded-lg p-4 mb-4 border border-blue-200">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <Shield className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-blue-800">Enterprise Security</div>
                    <div className="text-xs text-blue-600">Regulated • Encrypted • Read-only access</div>
                  </div>
                </div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-600 mb-1">2-Minute Setup</div>
                <div className="text-sm text-green-700">Start processing invoices today</div>
              </div>
            </div>
          </div>

          {/* Before vs After */}
          <div className="mt-16">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-red-50 rounded-2xl p-8 border border-red-200">
                <h3 className="text-xl font-bold text-red-800 mb-4 text-center">Before TaxPoynt</h3>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="text-red-500">❌</div>
                    <span className="text-gray-700">15+ hours/week on FIRS paperwork</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-red-500">❌</div>
                    <span className="text-gray-700">Constant fear of classification errors</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-red-500">❌</div>
                    <span className="text-gray-700">Expensive developers for integration</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-red-500">❌</div>
                    <span className="text-gray-700">Invoice rejections and delays</span>
                  </div>
                </div>
              </div>
              
              <div className="bg-green-50 rounded-2xl p-8 border border-green-200">
                <h3 className="text-xl font-bold text-green-800 mb-4 text-center">After TaxPoynt</h3>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="text-green-500">✅</div>
                    <span className="text-gray-700">2-minute automated submission</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-green-500">✅</div>
                    <span className="text-gray-700">100% compliance guaranteed</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-green-500">✅</div>
                    <span className="text-gray-700">No technical knowledge required</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-green-500">✅</div>
                    <span className="text-gray-700">Focus on growing your business</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Product Demo Section */}
      <section className="relative px-6 py-20 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              See TaxPoynt in Action
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Real dashboards, real workflows, real results for Nigerian businesses
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Dashboard Screenshot Placeholder */}
            <div className="order-2 lg:order-1">
              <div className="bg-gray-100 rounded-2xl p-8 border-2 border-dashed border-gray-300">
                <div className="aspect-video bg-white rounded-lg shadow-lg overflow-hidden">
                  <div className="bg-green-600 h-12 flex items-center px-4">
                    <div className="flex space-x-2">
                      <div className="w-3 h-3 bg-white/30 rounded-full"></div>
                      <div className="w-3 h-3 bg-white/30 rounded-full"></div>
                      <div className="w-3 h-3 bg-white/30 rounded-full"></div>
                    </div>
                    <div className="ml-4 text-white text-sm font-medium">TaxPoynt Dashboard</div>
                  </div>
                  <div className="p-6 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="h-6 w-32 bg-gray-200 rounded"></div>
                      <div className="h-6 w-20 bg-green-200 rounded"></div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="h-16 bg-blue-50 rounded-lg p-3">
                        <div className="h-3 w-16 bg-blue-200 rounded mb-2"></div>
                        <div className="h-6 w-12 bg-blue-300 rounded"></div>
                      </div>
                      <div className="h-16 bg-green-50 rounded-lg p-3">
                        <div className="h-3 w-16 bg-green-200 rounded mb-2"></div>
                        <div className="h-6 w-12 bg-green-300 rounded"></div>
                      </div>
                      <div className="h-16 bg-orange-50 rounded-lg p-3">
                        <div className="h-3 w-16 bg-orange-200 rounded mb-2"></div>
                        <div className="h-6 w-12 bg-orange-300 rounded"></div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="h-4 w-full bg-gray-200 rounded"></div>
                      <div className="h-4 w-3/4 bg-gray-200 rounded"></div>
                      <div className="h-4 w-1/2 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                </div>
                <div className="text-center mt-4 text-sm text-gray-500 font-medium">
                  Real Dashboard Screenshot Coming Soon
                </div>
              </div>
            </div>

            {/* Benefits List */}
            <div className="order-1 lg:order-2">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">
                What Nigerian businesses love about TaxPoynt:
              </h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <CheckCircle className="w-6 h-6 text-green-600 mt-0.5" />
                  <div>
                    <div className="font-semibold text-gray-900">Instant FIRS submission</div>
                    <div className="text-gray-600 text-sm">From sale to government in under 2 minutes</div>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="w-6 h-6 text-green-600 mt-0.5" />
                  <div>
                    <div className="font-semibold text-gray-900">Works with your current software</div>
                    <div className="text-gray-600 text-sm">SAP, QuickBooks, Paystack, or custom systems</div>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="w-6 h-6 text-green-600 mt-0.5" />
                  <div>
                    <div className="font-semibold text-gray-900">Never worry about compliance</div>
                    <div className="text-gray-600 text-sm">Automatic updates for all FIRS requirements</div>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="w-6 h-6 text-green-600 mt-0.5" />
                  <div>
                    <div className="font-semibold text-gray-900">Real-time status tracking</div>
                    <div className="text-gray-600 text-sm">Know exactly where every invoice stands</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced Service Section - Progressive Disclosure */}
      <section id="services" className="relative px-6 py-24 overflow-hidden">
        {/* Sophisticated Service Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-gray-50 via-green-25 to-blue-25">
          {/* Floating Service Elements */}
          <div className="absolute inset-0 opacity-10">
            <div 
              className="absolute top-1/3 left-1/3 w-96 h-96 bg-green-400 rounded-full mix-blend-multiply filter blur-3xl"
              style={{
                animation: 'float 22s ease-in-out infinite',
                animationDelay: '4s'
              }}
            ></div>
            <div 
              className="absolute bottom-1/4 right-1/3 w-80 h-80 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl"
              style={{
                animation: 'float 24s ease-in-out infinite reverse',
                animationDelay: '8s'
              }}
            ></div>
          </div>
        </div>

        <div className="max-w-5xl mx-auto text-center relative z-10">
          
          <div className="mb-20">
            <h2 className="text-4xl md:text-6xl font-black text-gray-900 mb-8 leading-tight">Complete E-invoicing Solution</h2>
            <p className="text-2xl text-gray-700 max-w-4xl mx-auto mb-12 font-light leading-relaxed">
              Everything you need for FIRS compliance in one simple platform. No confusing options, no complex choices.
            </p>
            
            {/* Enhanced Single Unified Service */}
            <div className="bg-white/80 backdrop-blur-sm rounded-4xl p-16 border border-green-200 max-w-4xl mx-auto shadow-2xl hover:shadow-green-500/20 transition-all duration-500 hover:scale-105 transform">
              <div className="w-24 h-24 bg-gradient-to-br from-green-500 to-blue-600 rounded-4xl flex items-center justify-center mx-auto mb-10 shadow-2xl hover:scale-110 transition-transform duration-300">
                <CheckCircle className="w-12 h-12 text-white" />
              </div>
              
              <h3 className="text-3xl md:text-4xl font-black text-gray-900 mb-8">TaxPoynt E-invoicing Platform</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left mb-8">
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-700">Automatic FIRS submission</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-700">40+ software integrations</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-700">Secure transaction automation</span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-700">100% compliance guaranteed</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-700">Enterprise security</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-700">24/7 Nigerian support</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6 mb-8 border border-green-200">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600 mb-1">2 min</div>
                    <div className="text-xs text-gray-600">Setup time</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600 mb-1">Zero</div>
                    <div className="text-xs text-gray-600">Errors</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600 mb-1">12+</div>
                    <div className="text-xs text-gray-600">Hours saved/week</div>
                  </div>
                </div>
              </div>

              <Button
                variant="primary"
                size="lg"
                onClick={() => router.push('/auth/signup')}
                className="text-lg px-12 py-4 mb-4"
              >
                Start Free Trial
              </Button>
              
              <p className="text-sm text-gray-500">
                No credit card required • 7-day free trial • Cancel anytime
              </p>
            </div>

            {/* Progressive Disclosure - Technical Options */}
            <div className="mt-12">
              <details className="group">
                <summary className="cursor-pointer text-blue-600 hover:text-blue-800 font-medium text-sm">
                  Advanced integration options for developers →
                </summary>
                <div className="mt-6 bg-gray-50 rounded-2xl p-8 text-left">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">API Integration</h4>
                      <div className="space-y-2 text-sm text-gray-600">
                        <div>• Developer-friendly API integration</div>
                        <div>• Multi-language SDKs</div>
                        <div>• Real-time webhook notifications</div>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">ERP Connectors</h4>
                      <div className="space-y-2 text-sm text-gray-600">
                        <div>• SAP, Oracle, Dynamics</div>
                        <div>• QuickBooks, Xero, Sage</div>
                        <div>• Advanced financial data sync</div>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Enterprise Features</h4>
                      <div className="space-y-2 text-sm text-gray-600">
                        <div>• Bulk processing capabilities</div>
                        <div>• Advanced compliance reporting</div>
                        <div>• Dedicated account manager</div>
                      </div>
                    </div>
                  </div>
                </div>
              </details>
            </div>
          </div>
        </div>
      </section>


      {/* Why TaxPoynt - Unique Value Props */}
      <section className="relative px-6 py-20 bg-white overflow-hidden">
        {/* Clean Background */}
        <div className="absolute inset-0">
          <div className="absolute top-10 left-1/4 w-4 h-4 bg-green-500 rounded-full opacity-20"></div>
          <div className="absolute bottom-10 right-1/4 w-6 h-6 bg-orange-500 rounded-full opacity-15"></div>
        </div>
        
        <div className="max-w-6xl mx-auto text-center relative z-10">
          
          <h2 className="text-display font-heading text-gray-900 mb-6">What Makes TaxPoynt Different?</h2>
          <p className="text-body-lg text-gray-600 mb-16 max-w-3xl mx-auto font-body">
            The only platform built specifically for Nigerian business reality
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-blue-700 transition-colors">
                <Calculator className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="text-subheading font-heading text-gray-900 mb-4">Built for Nigerian Business</h3>
              <p className="text-body text-gray-700 font-body">
                Never worry about classification errors again. We understand how Nigerian businesses actually work - from small shops to big corporations.
              </p>
            </div>
            
            <div className="bg-green-50 border border-green-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-green-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-green-700 transition-colors">
                <Building className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Works with Your Software</h3>
              <p className="text-gray-700 text-sm">
                Connect once and we handle everything. Works with Paystack, Mono, QuickBooks, and all the software you already use.
              </p>
            </div>
            
            <div className="bg-purple-50 border border-purple-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-purple-700 transition-colors">
                <CheckCircle className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Completely Automatic</h3>
              <p className="text-gray-700 text-sm">
                From sale to FIRS submission in under 2 minutes. 
                No paperwork, no manual work, no stress.
              </p>
            </div>
            
            <div className="bg-orange-50 border border-orange-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-orange-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-orange-700 transition-colors">
                <Receipt className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Complete Customer View</h3>
              <p className="text-gray-700 text-sm">
                See all your customer transactions in one place. Know exactly who bought what, when, and how they paid.
              </p>
            </div>
            
            <div className="bg-cyan-50 border border-cyan-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-cyan-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-cyan-700 transition-colors">
                <Banknote className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Stay Compliant Automatically</h3>
              <p className="text-gray-700 text-sm">
                Never worry about compliance again. We handle all Nigerian tax requirements automatically.
              </p>
            </div>
            
            <div className="bg-red-50 border border-red-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-red-700 transition-colors">
                <Settings className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Easy for Developers</h3>
              <p className="text-gray-700 text-sm">
                Your technical team will love us. Simple integration that works with any programming language.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="relative px-6 py-24 overflow-hidden">
        {/* Sophisticated Testimonial Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-purple-25 to-green-50">
          {/* Floating Trust Indicators */}
          <div className="absolute inset-0 opacity-15">
            <div 
              className="absolute top-1/4 left-1/4 w-80 h-80 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl"
              style={{
                animation: 'float 18s ease-in-out infinite',
                animationDelay: '3s'
              }}
            ></div>
            <div 
              className="absolute bottom-1/3 right-1/4 w-64 h-64 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl"
              style={{
                animation: 'float 20s ease-in-out infinite reverse',
                animationDelay: '7s'
              }}
            ></div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-6xl font-black text-gray-900 mb-8 leading-tight">
              Trusted by Nigerian Businesses
            </h2>
            <p className="text-2xl text-gray-700 max-w-4xl mx-auto font-light leading-relaxed">
              Join hundreds of businesses who've simplified their FIRS compliance
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {/* Testimonial 1 - Manufacturing */}
            <div className="group bg-white/90 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-gray-100 hover:shadow-blue-500/20 transition-all duration-500 hover:scale-105 transform">
              <div className="flex items-start space-x-5 mb-8">
                <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-700 rounded-full flex items-center justify-center text-white font-black text-xl group-hover:scale-110 transition-transform duration-300">
                  A
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-900">Adebayo Okonkwo</div>
                  <div className="text-base text-gray-600">CEO, Lagos Electronics Ltd</div>
                  <div className="text-sm text-green-600 font-semibold mt-2">Manufacturing • Lagos</div>
                </div>
              </div>
              <blockquote className="text-gray-700 mb-4">
                "TaxPoynt saved us 12 hours per week on FIRS paperwork. Our invoices now submit automatically while we focus on growing our business."
              </blockquote>
              <div className="flex items-center justify-between mb-4">
                <div className="flex text-orange-400">
                  {'★'.repeat(5)}
                </div>
                <div className="text-sm font-medium text-green-600">
                  Saved 12 hours/week
                </div>
              </div>
              <div className="mt-4 text-xs text-gray-400 italic">
                Representative testimonial - Actual customer quotes coming soon
              </div>
            </div>

            {/* Testimonial 2 - Retail */}
            <div className="group bg-white/90 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-gray-100 hover:shadow-blue-500/20 transition-all duration-500 hover:scale-105 transform">
              <div className="flex items-start space-x-5 mb-8">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center text-white font-black text-xl group-hover:scale-110 transition-transform duration-300">
                  F
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-900">Folake Adebisi</div>
                  <div className="text-base text-gray-600">Finance Director, Abuja Trading Co</div>
                  <div className="text-sm text-blue-600 font-semibold mt-2">Retail • Abuja</div>
                </div>
              </div>
              <blockquote className="text-gray-700 mb-4">
                "Integration with our SAP system was seamless. FIRS compliance went from our biggest headache to completely automatic."
              </blockquote>
              <div className="flex items-center justify-between mb-4">
                <div className="flex text-orange-400">
                  {'★'.repeat(5)}
                </div>
                <div className="text-sm font-medium text-blue-600">
                  Zero compliance issues
                </div>
              </div>
              <div className="mt-4 text-xs text-gray-400 italic">
                Representative testimonial - Actual customer quotes coming soon
              </div>
            </div>

            {/* Testimonial 3 - Technology */}
            <div className="group bg-white/90 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-gray-100 hover:shadow-blue-500/20 transition-all duration-500 hover:scale-105 transform">
              <div className="flex items-start space-x-5 mb-8">
                <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-orange-700 rounded-full flex items-center justify-center text-white font-black text-xl group-hover:scale-110 transition-transform duration-300">
                  C
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-900">Chidi Okoro</div>
                  <div className="text-base text-gray-600">CTO, Port Harcourt Tech Solutions</div>
                  <div className="text-sm text-orange-600 font-semibold mt-2">Technology • Port Harcourt</div>
                </div>
              </div>
              <blockquote className="text-gray-700 mb-4">
                "The API integration was straightforward. Our developers had TaxPoynt working with our custom billing system in two days."
              </blockquote>
              <div className="flex items-center justify-between mb-4">
                <div className="flex text-orange-400">
                  {'★'.repeat(5)}
                </div>
                <div className="text-sm font-medium text-orange-600">
                  2-day implementation
                </div>
              </div>
              <div className="mt-4 text-xs text-gray-400 italic">
                Representative testimonial - Actual customer quotes coming soon
              </div>
            </div>
          </div>

          {/* Additional Testimonials Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
            {/* Testimonial 4 - Services */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
              <div className="flex items-start space-x-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                  T
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Tunde Ajayi</div>
                  <div className="text-sm text-gray-600">Managing Partner, Ajayi Consulting</div>
                  <div className="text-xs text-purple-600 font-medium mt-1">Professional Services • Lagos</div>
                </div>
              </div>
              <blockquote className="text-gray-700 mb-4">
                "As a small consulting firm, we couldn't afford compliance mistakes. TaxPoynt handles everything automatically, giving us peace of mind."
              </blockquote>
              <div className="flex items-center justify-between mb-4">
                <div className="flex text-orange-400">
                  {'★'.repeat(5)}
                </div>
                <div className="text-sm font-medium text-purple-600">
                  100% peace of mind
                </div>
              </div>
              <div className="mt-4 text-xs text-gray-400 italic">
                Representative testimonial - Actual customer quotes coming soon
              </div>
            </div>

            {/* Testimonial 5 - Healthcare */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
              <div className="flex items-start space-x-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-teal-400 to-teal-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                  K
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Dr. Kemi Olatunji</div>
                  <div className="text-sm text-gray-600">Director, Wellness Medical Center</div>
                  <div className="text-xs text-teal-600 font-medium mt-1">Healthcare • Ibadan</div>
                </div>
              </div>
              <blockquote className="text-gray-700 mb-4">
                "Patient care is our priority, not paperwork. TaxPoynt lets our admin team focus on what matters while handling FIRS compliance seamlessly."
              </blockquote>
              <div className="flex items-center justify-between mb-4">
                <div className="flex text-orange-400">
                  {'★'.repeat(5)}
                </div>
                <div className="text-sm font-medium text-teal-600">
                  Focus on patients, not paperwork
                </div>
              </div>
              <div className="mt-4 text-xs text-gray-400 italic">
                Representative testimonial - Actual customer quotes coming soon
              </div>
            </div>
          </div>

          {/* Company Logos Section */}
          <div className="mt-16 pt-8 border-t border-gray-200">
            <div className="text-center mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Trusted by businesses across Nigeria</h3>
              <p className="text-sm text-gray-600">From startups to enterprises, companies rely on TaxPoynt</p>
            </div>
            
            {/* Logo Grid - Professional Placeholders */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 items-center opacity-60">
              {/* Placeholder Logo 1 - Manufacturing */}
              <div className="flex items-center justify-center h-16 bg-gray-100 rounded-lg border border-gray-200">
                <div className="text-center">
                  <div className="w-8 h-8 bg-green-500 rounded-full mx-auto mb-1"></div>
                  <div className="text-xs font-medium text-gray-600">Manufacturing Co.</div>
                </div>
              </div>
              
              {/* Placeholder Logo 2 - Tech Startup */}
              <div className="flex items-center justify-center h-16 bg-gray-100 rounded-lg border border-gray-200">
                <div className="text-center">
                  <div className="w-8 h-8 bg-blue-500 rounded-full mx-auto mb-1"></div>
                  <div className="text-xs font-medium text-gray-600">Tech Solutions</div>
                </div>
              </div>
              
              {/* Placeholder Logo 3 - Trading Company */}
              <div className="flex items-center justify-center h-16 bg-gray-100 rounded-lg border border-gray-200">
                <div className="text-center">
                  <div className="w-8 h-8 bg-orange-500 rounded-full mx-auto mb-1"></div>
                  <div className="text-xs font-medium text-gray-600">Trading Ltd</div>
                </div>
              </div>
              
              {/* Placeholder Logo 4 - Healthcare */}
              <div className="flex items-center justify-center h-16 bg-gray-100 rounded-lg border border-gray-200">
                <div className="text-center">
                  <div className="w-8 h-8 bg-teal-500 rounded-full mx-auto mb-1"></div>
                  <div className="text-xs font-medium text-gray-600">Health Center</div>
                </div>
              </div>
              
              {/* Placeholder Logo 5 - Consulting */}
              <div className="flex items-center justify-center h-16 bg-gray-100 rounded-lg border border-gray-200">
                <div className="text-center">
                  <div className="w-8 h-8 bg-purple-500 rounded-full mx-auto mb-1"></div>
                  <div className="text-xs font-medium text-gray-600">Consulting</div>
                </div>
              </div>
              
              {/* Placeholder Logo 6 - Retail */}
              <div className="flex items-center justify-center h-16 bg-gray-100 rounded-lg border border-gray-200">
                <div className="text-center">
                  <div className="w-8 h-8 bg-pink-500 rounded-full mx-auto mb-1"></div>
                  <div className="text-xs font-medium text-gray-600">Retail Group</div>
                </div>
              </div>
            </div>
            
            {/* Professional Disclaimer */}
            <div className="text-center mt-6">
              <p className="text-xs text-gray-400 italic">
                Representative client logos - Actual customer logos will be displayed upon consent
              </p>
            </div>
          </div>

          {/* Trust Indicators */}
          <div className="mt-16 pt-8 border-t border-gray-200">
            <div className="text-center mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Trusted by businesses across Nigeria</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">10,000+</div>
                <div className="text-sm text-gray-600">Invoices processed error-free</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">Since 2024</div>
                <div className="text-sm text-gray-600">FIRS certified partner</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">All</div>
                <div className="text-sm text-gray-600">Nigerian tax requirements met automatically</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">24/7</div>
                <div className="text-sm text-gray-600">Nigerian Support</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section - Address Common Concerns */}
      <section className="px-6 py-20 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Common Questions About TaxPoynt
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Get answers to the questions Nigerian business owners ask most
            </p>
          </div>

          <div className="space-y-6">
            {/* FAQ 1 - Security Concerns */}
            <details className="group bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <summary className="cursor-pointer font-semibold text-lg text-gray-900 flex items-center justify-between">
                Is my financial data safe with TaxPoynt?
                <span className="ml-4 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="mt-4 text-gray-700">
                <p>Yes, absolutely. We use enterprise-grade security with read-only access to your financial data. We can see your transactions to generate invoices, but we cannot move money or access your accounts. All data is encrypted and stored securely in Nigerian data centers.</p>
              </div>
            </details>

            {/* FAQ 2 - Integration Complexity */}
            <details className="group bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <summary className="cursor-pointer font-semibold text-lg text-gray-900 flex items-center justify-between">
                How difficult is it to integrate with my existing software?
                <span className="ml-4 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="mt-4 text-gray-700">
                <p>Most integrations take under 10 minutes. If you use popular software like QuickBooks or SAP, it's usually just a simple connection process. For custom systems, our team handles the technical setup for you at no extra cost.</p>
              </div>
            </details>

            {/* FAQ 3 - Compliance Concerns */}
            <details className="group bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <summary className="cursor-pointer font-semibold text-lg text-gray-900 flex items-center justify-between">
                What if FIRS changes their requirements?
                <span className="ml-4 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="mt-4 text-gray-700">
                <p>We handle all compliance updates automatically. As a FIRS-certified Access Point Provider, we're notified of changes before they take effect. Your invoices will always meet current requirements without any action needed from you.</p>
              </div>
            </details>

            {/* FAQ 4 - Cost/ROI Concerns */}
            <details className="group bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <summary className="cursor-pointer font-semibold text-lg text-gray-900 flex items-center justify-between">
                Is TaxPoynt worth the cost for a small business?
                <span className="ml-4 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="mt-4 text-gray-700">
                <p>Most small businesses save 12+ hours per week on FIRS paperwork. Even at minimum wage, that's ₦36,000+ in time savings weekly. Plus, avoiding just one compliance penalty pays for months of TaxPoynt service.</p>
              </div>
            </details>

            {/* FAQ 5 - Technical Support */}
            <details className="group bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <summary className="cursor-pointer font-semibold text-lg text-gray-900 flex items-center justify-between">
                What if I need help or something goes wrong?
                <span className="ml-4 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="mt-4 text-gray-700">
                <p>We provide 24/7 support by Nigerian customer service representatives who understand your business context. Most issues are resolved within minutes, and our team proactively monitors for any submission problems.</p>
              </div>
            </details>

            {/* FAQ 6 - Trial/Commitment */}
            <details className="group bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <summary className="cursor-pointer font-semibold text-lg text-gray-900 flex items-center justify-between">
                Can I try TaxPoynt before committing?
                <span className="ml-4 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="mt-4 text-gray-700">
                <p>Yes! We offer a 7-day free trial with no credit card required. You can process real invoices, test all features, and see the time savings firsthand. Cancel anytime during the trial with no charges.</p>
              </div>
            </details>

            {/* FAQ 7 - Business Size */}
            <details className="group bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <summary className="cursor-pointer font-semibold text-lg text-gray-900 flex items-center justify-between">
                Does TaxPoynt work for my type of business?
                <span className="ml-4 text-gray-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="mt-4 text-gray-700">
                <p>TaxPoynt works for any business that needs to submit invoices to FIRS - from small shops to large corporations. We handle retail, manufacturing, services, healthcare, technology, and every other industry. If you sell anything in Nigeria, we can help.</p>
              </div>
            </details>
          </div>

          {/* Still Have Questions CTA */}
          <div className="mt-16 text-center bg-blue-50 rounded-2xl p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Still have questions?</h3>
            <p className="text-gray-600 mb-6">
              Our Nigerian customer success team is here to help you understand how TaxPoynt fits your specific business needs.
            </p>
            <Button
              variant="outline"
              onClick={() => router.push('/contact')}
              className="border-blue-600 text-blue-600 hover:bg-blue-600 hover:text-white"
            >
              Talk to Our Team
            </Button>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative px-6 py-20 bg-green-600 overflow-hidden">
        {/* Clean CTA Background */}
        <div className="absolute inset-0">
          <div className="absolute top-10 right-10 w-8 h-8 bg-white/20 rounded-full"></div>
          <div className="absolute bottom-10 left-10 w-12 h-12 bg-orange-400/30 rounded-full"></div>
        </div>
        
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-display font-heading text-white mb-6 text-shadow">
            Ready to Transform Your E-Invoicing?
          </h2>
          <p className="text-body-lg text-green-100 mb-12 max-w-2xl mx-auto font-body">
            Join hundreds of Nigerian businesses saving time and ensuring compliance with TaxPoynt
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              variant="secondary"
              size="lg"
              onClick={() => router.push('/auth/signup')}
              className="text-lg px-8 py-4 bg-white text-green-600 hover:bg-gray-50 font-semibold"
            >
              Start Free Trial
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => router.push('/contact')}
              className="text-lg px-8 py-4 border-white text-white hover:bg-white hover:text-green-600 font-semibold"
            >
              Talk to Sales
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-12 bg-gray-900 text-white">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <Logo size="md" variant="full" color="white" showTagline={true} className="mb-4 md:mb-0" />
            
            <div className="flex items-center space-x-6 text-sm text-gray-400">
              <a href="/privacy" className="hover:text-white">Privacy</a>
              <a href="/terms" className="hover:text-white">Terms</a>
              <a href="/support" className="hover:text-white">Support</a>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            <p>&copy; 2024 TaxPoynt. All rights reserved. FIRS Certified Access Point Provider.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};