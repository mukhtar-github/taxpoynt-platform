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
  Settings
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-white">
      
      {/* Navigation */}
      <nav className="px-6 py-4 border-b border-gray-200">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Logo size="lg" variant="full" showTagline={true} />
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/auth/signin')}
              className="text-gray-600 hover:text-gray-900 font-medium"
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
      <section className="relative px-6 py-20 overflow-hidden">
        {/* Clean Professional Background */}
        <div className="absolute inset-0 bg-gray-50">
          {/* Subtle Nigerian-inspired accent */}
          <div className="absolute top-20 right-20 w-32 h-32 bg-green-100 rounded-full opacity-30"></div>
          <div className="absolute bottom-20 left-20 w-24 h-24 bg-orange-100 rounded-full opacity-20"></div>
        </div>
        
        <div className="max-w-4xl mx-auto text-center relative z-10">
          
          {/* Badge */}
          <div className="inline-flex items-center px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium mb-8">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
            FIRS Certified Access Point Provider
          </div>

          {/* Headline with Prominent Tagline */}
          <div className="mb-8">
            <div className="inline-block bg-green-600 text-white px-6 py-2 rounded-full text-sm font-semibold mb-6">
              Stop wasting time on government paperwork
            </div>
            <h1 className="text-hero font-heading text-shadow-sm text-gray-900 mb-8">
              Send invoices to FIRS in 
              <br />
              <span className="text-green-600 font-bold">
                seconds, not hours
              </span>
            </h1>
          </div>

          {/* Subtitle */}
          <p className="text-body-lg text-gray-600 mb-16 max-w-3xl mx-auto font-body">
            Stop wasting hours on FIRS paperwork. TaxPoynt connects your business software directly to FIRS—one click and your invoices are submitted correctly, every time.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Button
              variant="primary"
              size="lg"
              onClick={() => router.push('/auth/signup')}
              className="text-lg px-8 py-4"
            >
              Start Free Trial
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                document.getElementById('services')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-lg px-8 py-4"
            >
              Learn More
            </Button>
          </div>

          {/* Trust Indicators */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-2xl font-bold text-green-600 mb-1">Zero</div>
              <div className="text-gray-600 text-sm">Classification errors</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600 mb-1">2 min</div>
              <div className="text-gray-600 text-sm">From sale to FIRS submission</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600 mb-1">Always</div>
              <div className="text-gray-600 text-sm">Stay compliant automatically</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600 mb-1">Any</div>
              <div className="text-gray-600 text-sm">Software you already use</div>
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

      {/* Services Section */}
      <section id="services" className="px-6 py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center mb-16">
            <h2 className="text-display font-heading text-gray-900 mb-6">Choose Your Service</h2>
            <p className="text-body-lg text-gray-600 max-w-2xl mx-auto font-body">
              Select the perfect solution for your e-invoicing needs
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* System Integrator */}
            <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-lg transition-shadow">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6 hover:bg-blue-200 transition-colors">
                  <FileText className="w-8 h-8 text-blue-600" stroke="currentColor" fill="none" />
                </div>
                <h3 className="text-heading font-heading text-gray-900 mb-4">System Integrator</h3>
                <p className="text-body text-gray-600 mb-6 font-body">
                  Connect 40+ business and financial systems for automated e-invoicing workflows
                </p>
                <ul className="text-left space-y-2 mb-8">
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    40+ Ready-made Integrations
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    Multi-language SDKs (Python, JS, PHP)
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    Custom API Development
                  </li>
                </ul>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => router.push('/auth/signup?role=si')}
                >
                  Choose SI Service
                </Button>
              </div>
            </div>

            {/* Access Point Provider */}
            <div className="bg-white rounded-2xl border-2 border-green-500 p-8 relative hover:shadow-lg transition-shadow">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-green-500 text-white px-4 py-1 text-sm font-medium rounded-full">
                  Recommended
                </span>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-6 hover:bg-green-200 transition-colors">
                  <Clock className="w-8 h-8 text-green-600" stroke="currentColor" fill="none" />
                </div>
                <h3 className="text-heading font-heading text-gray-900 mb-4">Access Point Provider</h3>
                <p className="text-body text-gray-600 mb-6 font-body">
                  Secure invoice transmission via TaxPoynt's certified APP service
                </p>
                <ul className="text-left space-y-2 mb-8">
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    FIRS Transmission
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    Invoice Generation
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    Secure Processing
                  </li>
                </ul>
                <Button
                  variant="success"
                  className="w-full"
                  onClick={() => router.push('/auth/signup?role=app')}
                >
                  Choose APP Service
                </Button>
              </div>
            </div>

            {/* Hybrid Premium */}
            <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-lg transition-shadow">
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6 hover:bg-purple-200 transition-colors">
                  <Shield className="w-8 h-8 text-purple-600" stroke="currentColor" fill="none" />
                </div>
                <h3 className="text-heading font-heading text-gray-900 mb-4">Hybrid Premium</h3>
                <p className="text-body text-gray-600 mb-6 font-body">
                  Combined SI + APP with advanced features and premium support
                </p>
                <ul className="text-left space-y-2 mb-8">
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    All SI Features
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    All APP Features
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    Premium Support
                  </li>
                </ul>
                <Button
                  variant="outline"
                  className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
                  onClick={() => router.push('/auth/signup?role=hybrid')}
                >
                  Choose Hybrid Service
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Developer Integration Section */}
      <section className="relative px-6 py-20 bg-gray-900 text-white overflow-hidden">
        {/* Clean Professional Background */}
        <div className="absolute inset-0">
          <div className="absolute top-16 right-1/4 w-6 h-6 bg-green-500 rounded-full opacity-20"></div>
          <div className="absolute bottom-16 left-1/4 w-4 h-4 bg-orange-500 rounded-full opacity-25"></div>
        </div>
        
        <div className="max-w-6xl mx-auto relative z-10">
          
          <div className="text-center mb-16">
            <h2 className="text-display font-heading text-white mb-6 text-shadow">Three Ways to Integrate</h2>
            <p className="text-body-lg text-gray-300 font-body">
              Choose the integration method that works best for your team
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Ready-made Integrations */}
            <div className="bg-gray-800 rounded-2xl p-8">
              <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6 hover:bg-blue-200 transition-colors">
                <Database className="w-8 h-8 text-blue-600" stroke="currentColor" fill="none" />
              </div>
              <h3 className="text-heading font-heading text-white mb-4 text-center">Ready-made Integrations</h3>
              <p className="text-body text-gray-300 mb-6 text-center font-body">
                Connect instantly to 40+ popular business systems
              </p>
              <div className="space-y-2 text-sm text-gray-400">
                <div>• SAP, Oracle, Dynamics, NetSuite</div>
                <div>• Salesforce, HubSpot, Zoho</div>
                <div>• QuickBooks, Xero, Sage</div>
                <div>• Shopify, WooCommerce, Jumia</div>
                <div>• Paystack, Moniepoint, OPay</div>
              </div>
            </div>

            {/* SDK Integration */}
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-yellow-400 text-gray-900 px-4 py-1 text-sm font-bold rounded-full">
                  Most Popular
                </span>
              </div>
              <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center mx-auto mb-6 hover:bg-gray-50 transition-colors">
                <Monitor className="w-8 h-8 text-gray-700" stroke="currentColor" fill="none" />
              </div>
              <h3 className="text-heading font-heading text-white mb-4 text-center">SDK Integration</h3>
              <p className="text-body text-white/90 mb-6 text-center font-body">
                Install our SDK and integrate in minutes
              </p>
              <div className="bg-gray-900 rounded-lg p-4 mb-4">
                <code className="text-green-400 text-sm">
                  pip install taxpoynt-sdk<br/>
                  npm install taxpoynt-sdk<br/>
                  composer require taxpoynt/sdk
                </code>
              </div>
              <div className="space-y-1 text-sm text-white/80">
                <div>• Python, JavaScript, PHP, Java, C#, Go</div>
                <div>• Auto-generated from OpenAPI specs</div>
                <div>• Type-safe with full documentation</div>
              </div>
            </div>

            {/* Custom API */}
            <div className="bg-gray-800 rounded-2xl p-8">
              <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6 hover:bg-purple-200 transition-colors">
                <CheckCircle className="w-8 h-8 text-purple-600" stroke="currentColor" fill="none" />
              </div>
              <h3 className="text-heading font-heading text-white mb-4 text-center">Custom API</h3>
              <p className="text-body text-gray-300 mb-6 text-center font-body">
                Build custom integrations with our REST API
              </p>
              <div className="space-y-2 text-sm text-gray-400">
                <div>• RESTful API with OpenAPI specs</div>
                <div>• Webhook support for real-time events</div>
                <div>• Role-based access (SI, APP, Hybrid)</div>
                <div>• Rate limiting & authentication</div>
                <div>• Comprehensive error handling</div>
              </div>
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
      <section className="relative px-6 py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Trusted by Nigerian Businesses
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Join hundreds of businesses who've simplified their FIRS compliance
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Testimonial 1 */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
              <div className="flex items-start space-x-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                  A
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Adebayo Okonkwo</div>
                  <div className="text-sm text-gray-600">CEO, Lagos Electronics Ltd</div>
                </div>
              </div>
              <blockquote className="text-gray-700 mb-4">
                "TaxPoynt eliminated hours of FIRS paperwork. Our invoices now submit automatically while we focus on growing our business."
              </blockquote>
              <div className="flex text-orange-400">
                {'★'.repeat(5)}
              </div>
              <div className="mt-4 text-xs text-gray-400 italic">
                Customer testimonial pending - Placeholder content
              </div>
            </div>

            {/* Testimonial 2 */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
              <div className="flex items-start space-x-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                  F
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Folake Adebisi</div>
                  <div className="text-sm text-gray-600">Finance Director, Abuja Trading Co</div>
                </div>
              </div>
              <blockquote className="text-gray-700 mb-4">
                "Integration with our SAP system was seamless. FIRS compliance went from our biggest headache to completely automatic."
              </blockquote>
              <div className="flex text-orange-400">
                {'★'.repeat(5)}
              </div>
              <div className="mt-4 text-xs text-gray-400 italic">
                Customer testimonial pending - Placeholder content
              </div>
            </div>

            {/* Testimonial 3 */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
              <div className="flex items-start space-x-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                  C
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Chidi Okoro</div>
                  <div className="text-sm text-gray-600">CTO, Port Harcourt Tech Solutions</div>
                </div>
              </div>
              <blockquote className="text-gray-700 mb-4">
                "The API integration was straightforward. Our developers had TaxPoynt working with our custom billing system in two days."
              </blockquote>
              <div className="flex text-orange-400">
                {'★'.repeat(5)}
              </div>
              <div className="mt-4 text-xs text-gray-400 italic">
                Customer testimonial pending - Placeholder content
              </div>
            </div>
          </div>

          {/* Trust Indicators */}
          <div className="mt-16 pt-8 border-t border-gray-200">
            <div className="text-center mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Trusted by businesses across Nigeria</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">500+</div>
                <div className="text-sm text-gray-600">Active Businesses</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">50K+</div>
                <div className="text-sm text-gray-600">Invoices Processed</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">99.9%</div>
                <div className="text-sm text-gray-600">Uptime Guarantee</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">24/7</div>
                <div className="text-sm text-gray-600">Nigerian Support</div>
              </div>
            </div>
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