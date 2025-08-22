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
  GitBranch, 
  Rocket, 
  Crown,
  Plug,
  Laptop,
  Zap,
  Brain,
  Link,
  Target,
  Globe,
  Code
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
        {/* Enhanced Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 to-purple-50/50">
          <div className="absolute top-20 left-1/4 w-96 h-96 bg-blue-500/30 rounded-full blur-3xl animate-pulse" style={{animationDuration: '4s'}}></div>
          <div className="absolute bottom-20 right-1/4 w-80 h-80 bg-purple-500/30 rounded-full blur-3xl animate-pulse" style={{animationDuration: '6s', animationDelay: '2s'}}></div>
        </div>
        
        <div className="max-w-4xl mx-auto text-center relative z-10">
          
          {/* Badge */}
          <div className="inline-flex items-center px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium mb-8">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
            FIRS Certified Access Point Provider
          </div>

          {/* Headline with Prominent Tagline */}
          <div className="mb-8">
            <div className="inline-block bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-2 rounded-full text-sm font-semibold mb-6">
              Stop wasting time on government paperwork
            </div>
            <h1 className="text-hero font-heading text-shadow-sm text-gray-900 mb-8">
              Send invoices to FIRS in 
              <br />
              <span className="bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
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
                  <GitBranch className="w-8 h-8 text-blue-600" stroke="currentColor" fill="none" />
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
                  <Rocket className="w-8 h-8 text-green-600" stroke="currentColor" fill="none" />
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
                  <Crown className="w-8 h-8 text-purple-600" stroke="currentColor" fill="none" />
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
        {/* Enhanced Dark Background Effects */}
        <div className="absolute inset-0">
          <div className="absolute top-10 right-1/3 w-72 h-72 bg-blue-600/30 rounded-full blur-3xl animate-pulse" style={{animationDuration: '8s'}}></div>
          <div className="absolute bottom-10 left-1/3 w-64 h-64 bg-purple-600/30 rounded-full blur-3xl animate-pulse" style={{animationDuration: '10s', animationDelay: '3s'}}></div>
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
                <Plug className="w-8 h-8 text-blue-600" stroke="currentColor" fill="none" />
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
            <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl p-8 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-yellow-400 text-gray-900 px-4 py-1 text-sm font-bold rounded-full">
                  Most Popular
                </span>
              </div>
              <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center mx-auto mb-6 hover:bg-gray-50 transition-colors">
                <Laptop className="w-8 h-8 text-gray-700" stroke="currentColor" fill="none" />
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
                <Zap className="w-8 h-8 text-purple-600" stroke="currentColor" fill="none" />
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
      <section className="relative px-6 py-20 bg-gradient-to-b from-gray-50 to-white overflow-hidden">
        {/* Subtle Background Effects */}
        <div className="absolute inset-0">
          <div className="absolute top-10 left-1/4 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-10 right-1/4 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl"></div>
        </div>
        
        <div className="max-w-6xl mx-auto text-center relative z-10">
          
          <h2 className="text-display font-heading text-gray-900 mb-6">What Makes TaxPoynt Different?</h2>
          <p className="text-body-lg text-gray-600 mb-16 max-w-3xl mx-auto font-body">
            The only platform built specifically for Nigerian business reality
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-blue-700 transition-colors">
                <Brain className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="text-subheading font-heading text-gray-900 mb-4">Built for Nigerian Business</h3>
              <p className="text-body text-gray-700 font-body">
                Never worry about classification errors again. We understand how Nigerian businesses actually work - from small shops to big corporations.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-green-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-green-700 transition-colors">
                <Link className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Works with Your Software</h3>
              <p className="text-gray-700 text-sm">
                Connect once and we handle everything. Works with Paystack, Mono, QuickBooks, and all the software you already use.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-purple-700 transition-colors">
                <Zap className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Completely Automatic</h3>
              <p className="text-gray-700 text-sm">
                From sale to FIRS submission in under 2 minutes. 
                No paperwork, no manual work, no stress.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-orange-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-orange-700 transition-colors">
                <Target className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Complete Customer View</h3>
              <p className="text-gray-700 text-sm">
                See all your customer transactions in one place. Know exactly who bought what, when, and how they paid.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-cyan-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-cyan-700 transition-colors">
                <Globe className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Stay Compliant Automatically</h3>
              <p className="text-gray-700 text-sm">
                Never worry about compliance again. We handle all Nigerian tax requirements automatically.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-600 rounded-xl flex items-center justify-center mx-auto mb-4 hover:bg-red-700 transition-colors">
                <Code className="w-6 h-6 text-white" stroke="currentColor" fill="none" />
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Easy for Developers</h3>
              <p className="text-gray-700 text-sm">
                Your technical team will love us. Simple integration that works with any programming language.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative px-6 py-20 bg-gradient-to-br from-blue-600 via-blue-700 to-purple-700 overflow-hidden">
        {/* Enhanced CTA Background */}
        <div className="absolute inset-0">
          <div className="absolute top-0 left-1/3 w-96 h-96 bg-white/15 rounded-full blur-3xl animate-pulse" style={{animationDuration: '6s'}}></div>
          <div className="absolute bottom-0 right-1/3 w-80 h-80 bg-purple-300/25 rounded-full blur-3xl animate-pulse" style={{animationDuration: '8s', animationDelay: '2s'}}></div>
        </div>
        
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-display font-heading text-white mb-6 text-shadow">
            Ready to Transform Your E-Invoicing?
          </h2>
          <p className="text-body-lg text-blue-100 mb-12 max-w-2xl mx-auto font-body">
            Join hundreds of Nigerian businesses saving time and ensuring compliance with TaxPoynt
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              variant="secondary"
              size="lg"
              onClick={() => router.push('/auth/signup')}
              className="text-lg px-8 py-4 bg-white text-blue-600 hover:bg-gray-50"
            >
              Start Free Trial
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => router.push('/contact')}
              className="text-lg px-8 py-4 border-white text-white hover:bg-white hover:text-blue-600"
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