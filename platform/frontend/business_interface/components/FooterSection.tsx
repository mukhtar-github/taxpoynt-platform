/**
 * Footer Section Component
 * ========================
 * Extracted from LandingPage.tsx - Comprehensive contact and legal information
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { OptimizedImage } from '../../design_system';
import { TYPOGRAPHY_STYLES } from '../../design_system/style-utilities';

export interface FooterSectionProps {
  className?: string;
}

export const FooterSection: React.FC<FooterSectionProps> = ({ className = '' }) => {
  const router = useRouter();
  const currentYear = new Date().getFullYear();

  return (
    <footer 
      className={`bg-slate-900 text-white relative overflow-hidden ${className}`}
      role="contentinfo"
      aria-labelledby="footer-heading"
    >
      
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950" aria-hidden="true">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/10 via-transparent to-purple-900/10"></div>
      </div>

      <div className="relative z-10">
        
        {/* Main Footer Content */}
        <div className="max-w-6xl mx-auto px-6 py-16">
          
          {/* Footer Header */}
          <div className="text-center mb-16">
            <h2 
              id="footer-heading"
              className="sr-only"
            >
              TaxPoynt Footer Information
            </h2>
            
            {/* Logo and Tagline */}
            <div className="flex items-center justify-center space-x-4 mb-6">
              <OptimizedImage
                src="/logo.svg"
                alt="TaxPoynt Logo"
                width={48}
                height={48}
                className="w-12 h-12"
                priority={false}
              />
              <div>
                <div 
                  className="text-3xl font-bold text-white"
                  style={TYPOGRAPHY_STYLES.optimizedText}
                >
                  TaxPoynt
                </div>
                <div className="text-blue-300 text-sm font-medium">
                  Nigerian Tax Compliance Made Simple
                </div>
              </div>
            </div>
            
            <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
              Empowering Nigerian businesses with automated tax compliance. 
              <span className="text-blue-300 font-semibold"> Join 2,500+ companies</span> saving millions with TaxPoynt.
            </p>
          </div>

          {/* Footer Links Grid */}
          <div className="grid md:grid-cols-5 gap-8 mb-16">
            
            {/* Products & Solutions */}
            <div>
              <h3 className="text-lg font-bold text-white mb-4">Products</h3>
              <ul className="space-y-3">
                <li>
                  <button 
                    onClick={() => router.push('/products/si')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    System Integration
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/products/app')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Access Point Provider
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/products/hybrid')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Hybrid Solutions
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/enterprise')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Enterprise
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/api')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    API Platform
                  </button>
                </li>
              </ul>
            </div>

            {/* Integrations */}
            <div>
              <h3 className="text-lg font-bold text-white mb-4">Integrations</h3>
              <ul className="space-y-3">
                <li>
                  <button 
                    onClick={() => router.push('/integrations/erp')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    ERP Systems
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/integrations/accounting')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Accounting Software
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/integrations/banking')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Banking & Payments
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/integrations/ecommerce')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    E-commerce
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/integrations/custom')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Custom Integration
                  </button>
                </li>
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h3 className="text-lg font-bold text-white mb-4">Resources</h3>
              <ul className="space-y-3">
                <li>
                  <button 
                    onClick={() => router.push('/docs')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Documentation
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/guides')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Setup Guides
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/blog')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Blog & News
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/case-studies')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Case Studies
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/webinars')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Webinars
                  </button>
                </li>
              </ul>
            </div>

            {/* Support */}
            <div>
              <h3 className="text-lg font-bold text-white mb-4">Support</h3>
              <ul className="space-y-3">
                <li>
                  <button 
                    onClick={() => router.push('/support')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Help Center
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/contact')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Contact Support
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/training')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Training
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/community')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Community
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/system-status')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    System Status
                  </button>
                </li>
              </ul>
            </div>

            {/* Company */}
            <div>
              <h3 className="text-lg font-bold text-white mb-4">Company</h3>
              <ul className="space-y-3">
                <li>
                  <button 
                    onClick={() => router.push('/about')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    About Us
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/careers')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Careers
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/partners')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Partners
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/investors')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Investors
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => router.push('/press')}
                    className="text-gray-300 hover:text-blue-300 transition-colors duration-200 text-left"
                  >
                    Press Kit
                  </button>
                </li>
              </ul>
            </div>
          </div>

          {/* Contact Information */}
          <div className="border-t border-gray-700 pt-16 pb-8">
            <div className="grid md:grid-cols-3 gap-8 mb-12">
              
              {/* Lagos Office */}
              <div className="text-center md:text-left">
                <h4 className="text-lg font-bold text-white mb-4 flex items-center justify-center md:justify-start">
                  <span className="mr-2">🏢</span>
                  Lagos Headquarters
                </h4>
                <div className="space-y-2 text-gray-300">
                  <p>TaxPoynt Limited</p>
                  <p>12A Admiralty Way</p>
                  <p>Lekki Phase 1, Lagos</p>
                  <p>Nigeria</p>
                  <div className="mt-4">
                    <a 
                      href="tel:+2348123456789" 
                      className="text-blue-300 hover:text-blue-200 transition-colors"
                    >
                      +234 812 345 6789
                    </a>
                  </div>
                </div>
              </div>

              {/* Abuja Office */}
              <div className="text-center md:text-left">
                <h4 className="text-lg font-bold text-white mb-4 flex items-center justify-center md:justify-start">
                  <span className="mr-2">🏛️</span>
                  Abuja Office
                </h4>
                <div className="space-y-2 text-gray-300">
                  <p>Plot 123 Adetokunbo</p>
                  <p>Ademola Crescent</p>
                  <p>Wuse II, Abuja</p>
                  <p>FCT, Nigeria</p>
                  <div className="mt-4">
                    <a 
                      href="tel:+2349087654321" 
                      className="text-blue-300 hover:text-blue-200 transition-colors"
                    >
                      +234 908 765 4321
                    </a>
                  </div>
                </div>
              </div>

              {/* Digital Contact */}
              <div className="text-center md:text-left">
                <h4 className="text-lg font-bold text-white mb-4 flex items-center justify-center md:justify-start">
                  <span className="mr-2">💬</span>
                  Get In Touch
                </h4>
                <div className="space-y-3">
                  <div>
                    <p className="text-gray-400 text-sm">General Inquiries</p>
                    <a 
                      href="mailto:hello@taxpoynt.com" 
                      className="text-blue-300 hover:text-blue-200 transition-colors"
                    >
                      hello@taxpoynt.com
                    </a>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Enterprise Sales</p>
                    <a 
                      href="mailto:enterprise@taxpoynt.com" 
                      className="text-blue-300 hover:text-blue-200 transition-colors"
                    >
                      enterprise@taxpoynt.com
                    </a>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">24/7 Support</p>
                    <a 
                      href="mailto:support@taxpoynt.com" 
                      className="text-blue-300 hover:text-blue-200 transition-colors"
                    >
                      support@taxpoynt.com
                    </a>
                  </div>
                </div>
              </div>
            </div>

            {/* Social Media & Newsletter */}
            <div className="flex flex-col md:flex-row justify-between items-center mb-12">
              
              {/* Social Media Links */}
              <div className="flex items-center space-x-6 mb-6 md:mb-0">
                <span className="text-gray-300 font-medium">Follow us:</span>
                {[
                  { name: 'LinkedIn', icon: '💼', href: 'https://linkedin.com/company/taxpoynt' },
                  { name: 'Twitter', icon: '🐦', href: 'https://twitter.com/taxpoynt' },
                  { name: 'YouTube', icon: '📺', href: 'https://youtube.com/taxpoynt' },
                  { name: 'WhatsApp', icon: '💬', href: 'https://wa.me/2348123456789' },
                ].map((social) => (
                  <a
                    key={social.name}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-2xl hover:scale-110 transition-transform duration-200"
                    aria-label={`Follow TaxPoynt on ${social.name}`}
                  >
                    {social.icon}
                  </a>
                ))}
              </div>

              {/* Newsletter Signup */}
              <div className="flex items-center space-x-4">
                <span className="text-gray-300 font-medium">Stay updated:</span>
                <div className="flex">
                  <input
                    type="email"
                    placeholder="Enter your email"
                    className="px-4 py-2 bg-gray-800 text-white border border-gray-600 rounded-l-lg focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
                    aria-label="Email for newsletter subscription"
                  />
                  <button
                    type="submit"
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-r-lg transition-colors duration-200"
                    aria-label="Subscribe to newsletter"
                  >
                    Subscribe
                  </button>
                </div>
              </div>
            </div>

            {/* Trust Badges */}
            <div className="flex flex-wrap justify-center items-center gap-8 mb-12">
              {[
                { badge: "🛡️ FIRS Certified", desc: "Official Integration Partner" },
                { badge: "🔒 ISO 27001", desc: "Security Certified" },
                { badge: "⭐ 4.9/5 Rating", desc: "Customer Satisfaction" },
                { badge: "🏆 Award Winning", desc: "FinTech Solution 2024" },
                { badge: "💼 Enterprise Ready", desc: "Fortune 500 Trusted" }
              ].map((trust, index) => (
                <div key={index} className="text-center">
                  <div className="text-2xl mb-1">{trust.badge.split(' ')[0]}</div>
                  <div className="text-sm text-blue-300 font-medium">
                    {trust.badge.substring(2)}
                  </div>
                  <div className="text-xs text-gray-400">
                    {trust.desc}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-700 bg-slate-950/50">
          <div className="max-w-6xl mx-auto px-6 py-8">
            
            {/* Legal Links */}
            <div className="flex flex-col md:flex-row justify-between items-center">
              
              {/* Copyright */}
              <div className="text-gray-400 text-sm mb-4 md:mb-0">
                © {currentYear} TaxPoynt Limited. All rights reserved. RC: 1234567
              </div>

              {/* Legal Links */}
              <div className="flex flex-wrap justify-center gap-6 text-sm">
                {[
                  { label: 'Privacy Policy', path: '/privacy' },
                  { label: 'Terms of Service', path: '/terms' },
                  { label: 'Cookie Policy', path: '/cookies' },
                  { label: 'Data Protection', path: '/data-protection' },
                  { label: 'Compliance', path: '/compliance' },
                ].map((link) => (
                  <button
                    key={link.label}
                    onClick={() => router.push(link.path)}
                    className="text-gray-400 hover:text-blue-300 transition-colors duration-200"
                  >
                    {link.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Regulatory Compliance Notice */}
            <div className="mt-8 pt-6 border-t border-gray-700">
              <div className="text-center text-xs text-gray-500 max-w-4xl mx-auto leading-relaxed">
                <p className="mb-2">
                  <strong>Regulatory Compliance:</strong> TaxPoynt Limited is a registered company in Nigeria (RC: 1234567) 
                  and is an official FIRS-certified Access Point Provider. Our platform complies with all Nigerian tax 
                  regulations and data protection laws.
                </p>
                <p>
                  <strong>Disclaimer:</strong> TaxPoynt provides tax compliance automation tools. While our platform 
                  ensures technical compliance with FIRS requirements, users remain responsible for the accuracy of 
                  their business data and tax obligations. Professional tax advice should be sought for complex situations.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};
