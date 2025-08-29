/**
 * TaxPoynt Footer Component
 * =========================
 * Clean, simple, professional footer following design system principles.
 * "Simplicity is the ultimate sophistication" - Steve Jobs
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from './Button';

export interface FooterProps {
  className?: string;
  variant?: 'default' | 'minimal' | 'landing';
}

export const Footer: React.FC<FooterProps> = ({ 
  className = '', 
  variant = 'default' 
}) => {
  const router = useRouter();
  const currentYear = new Date().getFullYear();

  // Strategic content organization for professional polish
  const navigationLinks = [
    { label: 'Platform', href: '/platform', description: 'Core e-invoicing solution' },
    { label: 'Integrations', href: '/integrations', description: 'ERP & business systems' },
    { label: 'Pricing', href: '/pricing', description: 'Transparent pricing plans' },
    { label: 'Documentation', href: '/docs', description: 'Developer resources' },
    { label: 'Support', href: '/support', description: '24/7 expert assistance' }
  ];

  // Enhanced company information
  const companyLinks = [
    { label: 'About TaxPoynt', href: '/about', description: 'Our mission & vision' },
    { label: 'Contact Us', href: '/contact', description: 'Get in touch' },
    { label: 'Careers', href: '/careers', description: 'Join our team', badge: 'We\'re hiring!' },
    { label: 'Blog', href: '/blog', description: 'Latest insights' },
    { label: 'Press Kit', href: '/press', description: 'Media resources' }
  ];

  // Professional resources section
  const resourceLinks = [
    { label: 'API Reference', href: '/api', description: 'Complete API docs' },
    { label: 'SDK Downloads', href: '/sdk', description: 'Development tools' },
    { label: 'Case Studies', href: '/case-studies', description: 'Success stories' },
    { label: 'Webinars', href: '/webinars', description: 'Educational content' },
    { label: 'Status Page', href: '/status', description: 'System status', external: true }
  ];

  // Refined legal links
  const legalLinks = [
    { label: 'Privacy Policy', href: '/privacy' },
    { label: 'Terms of Service', href: '/terms' },
    { label: 'Data Processing', href: '/data-processing' },
    { label: 'Security', href: '/security' }
  ];

  const handleNavigation = (href: string) => {
    router.push(href);
  };

  if (variant === 'minimal') {
    return (
      <footer className={`bg-gray-50 border-t border-gray-200 ${className}`}>
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="text-gray-600 text-sm">
              © {currentYear} TaxPoynt Limited. All rights reserved.
            </div>
            <div className="flex space-x-6 text-sm">
              {legalLinks.map((link) => (
                <button
                  key={link.label}
                  onClick={() => handleNavigation(link.href)}
                  className="text-gray-500 hover:text-gray-700 transition-colors"
                >
                  {link.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </footer>
    );
  }

  return (
    <footer className={`bg-gradient-to-br from-gray-900 via-gray-900 to-gray-950 text-white relative overflow-hidden ${className}`}>
      {/* Subtle background pattern */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-transparent to-green-600/5"></div>
      <div className="absolute inset-0" style={{
        backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.03) 1px, transparent 0)`,
        backgroundSize: '32px 32px'
      }}></div>
      
      {/* Main Footer Content */}
      <div className="relative max-w-7xl mx-auto px-4 py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 lg:gap-16">
          
          {/* Company Info - Enhanced */}
          <div className="lg:col-span-2">
            {/* Logo & Brand */}
            <div className="flex items-center space-x-4 mb-8">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                  <span className="text-white font-bold text-xl">T</span>
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-gray-900"></div>
              </div>
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  TaxPoynt
                </h2>
                <p className="text-xs text-gray-400 mt-1">Certified Access Point Provider</p>
              </div>
            </div>

            {/* Enhanced description */}
            <p className="text-gray-300 text-base leading-relaxed mb-8 max-w-md">
              Nigeria's premier e-invoicing platform, trusted by thousands of businesses for seamless 
              <span className="text-green-400 font-medium"> tax compliance</span> and 
              <span className="text-blue-400 font-medium"> automated integration</span>.
            </p>
            
            {/* Professional Trust Badges */}
            <div className="space-y-4 mb-8">
              <div className="flex flex-wrap gap-3">
                <div className="flex items-center space-x-3 px-4 py-2.5 bg-gradient-to-r from-green-600/20 to-green-500/10 rounded-lg border border-green-500/30 backdrop-blur-sm">
                  <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="text-green-300 text-sm font-medium">FIRS Certified APP</span>
                </div>
                <div className="flex items-center space-x-3 px-4 py-2.5 bg-gradient-to-r from-blue-600/20 to-blue-500/10 rounded-lg border border-blue-500/30 backdrop-blur-sm">
                  <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <span className="text-blue-300 text-sm font-medium">ISO 27001 Compliant</span>
                </div>
              </div>
              
              {/* Business credentials */}
              <div className="flex items-center space-x-4 text-xs text-gray-400">
                <span className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                  </svg>
                  <span>RC: 7891234</span>
                </span>
                <span className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>Lagos, Nigeria</span>
                </span>
              </div>
            </div>

            {/* Contact Information */}
            <div className="space-y-3">
              <a href="mailto:hello@taxpoynt.com" className="flex items-center space-x-3 text-gray-300 hover:text-white transition-colors group">
                <div className="w-8 h-8 bg-gray-800 rounded-lg flex items-center justify-center group-hover:bg-blue-600 transition-colors">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <span className="text-sm">hello@taxpoynt.com</span>
              </a>
              <a href="tel:+2349012345678" className="flex items-center space-x-3 text-gray-300 hover:text-white transition-colors group">
                <div className="w-8 h-8 bg-gray-800 rounded-lg flex items-center justify-center group-hover:bg-green-600 transition-colors">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                </div>
                <span className="text-sm">+234 901 234 5678</span>
              </a>
            </div>
          </div>

          {/* Platform Links - Enhanced */}
          <div>
            <h3 className="text-white font-semibold text-lg mb-6 flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-3"></span>
              Platform
            </h3>
            <ul className="space-y-4">
              {navigationLinks.map((link) => (
                <li key={link.label}>
                  <button
                    onClick={() => handleNavigation(link.href)}
                    className="group text-left"
                  >
                    <div className="text-gray-300 hover:text-white transition-colors text-sm font-medium">
                      {link.label}
                    </div>
                    <div className="text-gray-500 text-xs mt-1 group-hover:text-gray-400 transition-colors">
                      {link.description}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources - New Section */}
          <div>
            <h3 className="text-white font-semibold text-lg mb-6 flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
              Resources
            </h3>
            <ul className="space-y-4">
              {resourceLinks.map((link) => (
                <li key={link.label}>
                  <button
                    onClick={() => link.external ? window.open(link.href, '_blank') : handleNavigation(link.href)}
                    className="group text-left flex items-center"
                  >
                    <div className="flex-1">
                      <div className="text-gray-300 hover:text-white transition-colors text-sm font-medium">
                        {link.label}
                      </div>
                      <div className="text-gray-500 text-xs mt-1 group-hover:text-gray-400 transition-colors">
                        {link.description}
                      </div>
                    </div>
                    {link.external && (
                      <svg className="w-3 h-3 text-gray-500 group-hover:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Company - Enhanced */}
          <div>
            <h3 className="text-white font-semibold text-lg mb-6 flex items-center">
              <span className="w-2 h-2 bg-purple-500 rounded-full mr-3"></span>
              Company
            </h3>
            <ul className="space-y-4">
              {companyLinks.map((link) => (
                <li key={link.label}>
                  <button
                    onClick={() => handleNavigation(link.href)}
                    className="group text-left"
                  >
                    <div className="flex items-center">
                      <div className="flex-1">
                        <div className="text-gray-300 hover:text-white transition-colors text-sm font-medium">
                          {link.label}
                        </div>
                        <div className="text-gray-500 text-xs mt-1 group-hover:text-gray-400 transition-colors">
                          {link.description}
                        </div>
                      </div>
                      {link.badge && (
                        <span className="ml-2 px-2 py-1 bg-green-600 text-white text-xs rounded-full font-medium">
                          {link.badge}
                        </span>
                      )}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Premium Newsletter Signup - Landing variant only */}
        {variant === 'landing' && (
          <div className="mt-16 pt-12 border-t border-gray-800/50">
            <div className="bg-gradient-to-br from-blue-600/10 via-purple-600/5 to-green-600/10 rounded-2xl p-8 border border-gray-800/50 backdrop-blur-sm">
              <div className="text-center">
                <div className="flex items-center justify-center space-x-3 mb-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM4.828 7l6.172 6.172M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4l5 5v5.172" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white">Stay Ahead of Compliance</h3>
                </div>
                
                <p className="text-gray-300 text-base mb-8 max-w-2xl mx-auto">
                  Join 5,000+ business owners getting weekly insights on tax compliance, 
                  platform updates, and exclusive resources to streamline your operations.
                </p>
                
                <div className="flex flex-col sm:flex-row max-w-lg mx-auto gap-4">
                  <div className="flex-1 relative">
                    <input
                      type="email"
                      placeholder="Enter your business email"
                      className="w-full px-6 py-4 bg-gray-800/80 text-white border border-gray-600/50 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 backdrop-blur-sm transition-all placeholder-gray-400"
                      aria-label="Email for newsletter subscription"
                    />
                    <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                      </svg>
                    </div>
                  </div>
                  
                  <Button
                    variant="primary"
                    size="md"
                    className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-xl font-semibold shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all"
                  >
                    Subscribe Free
                  </Button>
                </div>
                
                {/* Trust indicators */}
                <div className="flex items-center justify-center space-x-6 mt-6 text-xs text-gray-400">
                  <div className="flex items-center space-x-2">
                    <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span>No spam, ever</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span>Unsubscribe anytime</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <svg className="w-4 h-4 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span>Weekly insights</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Professional Bottom Bar */}
      <div className="relative border-t border-gray-800/50 bg-gradient-to-r from-gray-950 via-gray-900 to-gray-950">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 via-transparent to-green-600/5"></div>
        <div className="relative max-w-7xl mx-auto px-4 py-8">
          <div className="flex flex-col lg:flex-row justify-between items-center space-y-6 lg:space-y-0">
            
            {/* Enhanced Copyright & Legal */}
            <div className="flex flex-col md:flex-row items-center space-y-3 md:space-y-0 md:space-x-8">
              <div className="text-gray-400 text-sm font-medium">
                © {currentYear} TaxPoynt Limited. All rights reserved.
              </div>
              <div className="flex flex-wrap justify-center gap-6 text-sm">
                {legalLinks.map((link, index) => (
                  <div key={link.label} className="flex items-center">
                    <button
                      onClick={() => handleNavigation(link.href)}
                      className="text-gray-400 hover:text-gray-200 transition-colors relative group"
                    >
                      {link.label}
                      <div className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-500 transition-all group-hover:w-full"></div>
                    </button>
                    {index < legalLinks.length - 1 && (
                      <span className="text-gray-600 mx-3">•</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Enhanced Social Links */}
            <div className="flex items-center space-x-2">
              <span className="text-gray-400 text-sm mr-4">Follow us:</span>
              <div className="flex items-center space-x-3">
                {[
                  { 
                    name: 'LinkedIn', 
                    url: 'https://linkedin.com/company/taxpoynt',
                    icon: 'M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z',
                    color: 'hover:bg-blue-600'
                  },
                  { 
                    name: 'Twitter', 
                    url: 'https://twitter.com/taxpoynt',
                    icon: 'M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.427 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z',
                    color: 'hover:bg-sky-500'
                  },
                  { 
                    name: 'GitHub', 
                    url: 'https://github.com/taxpoynt',
                    icon: 'M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z',
                    color: 'hover:bg-gray-600'
                  },
                  { 
                    name: 'YouTube', 
                    url: 'https://youtube.com/@taxpoynt',
                    icon: 'M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z',
                    color: 'hover:bg-red-600'
                  }
                ].map((social) => (
                  <button
                    key={social.name}
                    onClick={() => window.open(social.url, '_blank')}
                    className={`w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center text-gray-400 transition-all duration-200 ${social.color} hover:text-white hover:scale-110 group`}
                    aria-label={social.name}
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d={social.icon}/>
                    </svg>
                    <div className="absolute -top-8 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                      {social.name}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Enhanced Compliance Notice - Landing variant only */}
          {variant === 'landing' && (
            <div className="mt-8 pt-8 border-t border-gray-800/30">
              <div className="bg-gradient-to-r from-gray-800/30 via-gray-800/20 to-gray-800/30 rounded-xl p-6 backdrop-blur-sm">
                <div className="text-center">
                  <div className="flex items-center justify-center space-x-2 mb-3">
                    <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <h4 className="text-white font-semibold text-sm">Regulatory Compliance & Trust</h4>
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed max-w-4xl mx-auto">
                    <strong className="text-green-400">TaxPoynt Limited</strong> (RC: 7891234) is a certified FIRS Access Point Provider, 
                    fully compliant with Nigerian tax regulations, NDPR data protection laws, and ISO 27001 security standards. 
                    We are committed to maintaining the highest levels of <strong className="text-blue-400">security</strong>, 
                    <strong className="text-purple-400"> compliance</strong>, and <strong className="text-green-400">service excellence</strong> 
                    for our clients across Nigeria.
                  </p>
                  <div className="flex items-center justify-center space-x-8 mt-4 text-xs text-gray-400">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>FIRS Certified</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>ISO 27001</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <span>NDPR Compliant</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                      <span>Nigerian Business</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </footer>
  );
};

export default Footer;
