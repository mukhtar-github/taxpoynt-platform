/**
 * TaxPoynt Footer Component
 * =========================
 * Clean, simple, professional footer following design system principles.
 * "Simplicity is the ultimate sophistication" - Steve Jobs
 */

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

  // Core navigation links
  const navigationLinks = [
    { label: 'Products', href: '/products' },
    { label: 'Solutions', href: '/solutions' },
    { label: 'Pricing', href: '/pricing' },
    { label: 'Documentation', href: '/docs' },
    { label: 'Support', href: '/support' }
  ];

  // Legal links
  const legalLinks = [
    { label: 'Privacy Policy', href: '/privacy' },
    { label: 'Terms of Service', href: '/terms' },
    { label: 'Cookie Policy', href: '/cookies' },
    { label: 'Security', href: '/security' }
  ];

  // Company links
  const companyLinks = [
    { label: 'About', href: '/about' },
    { label: 'Contact', href: '/contact' },
    { label: 'Careers', href: '/careers' },
    { label: 'Blog', href: '/blog' }
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
    <footer className={`bg-gray-900 text-white ${className}`}>
      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
          
          {/* Company Info */}
          <div className="lg:col-span-2">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">T</span>
              </div>
              <span className="text-2xl font-bold">TaxPoynt</span>
            </div>
            <p className="text-gray-300 text-sm leading-relaxed mb-6 max-w-md">
              Nigeria's premier e-invoicing platform. Empowering businesses with automated tax compliance and seamless integration.
            </p>
            
            {/* Trust Badges */}
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center space-x-2 px-3 py-2 bg-green-600/20 rounded-full border border-green-500/30">
                <span className="text-green-400 text-sm">🛡️</span>
                <span className="text-green-300 text-xs font-medium">FIRS Certified</span>
              </div>
              <div className="flex items-center space-x-2 px-3 py-2 bg-blue-600/20 rounded-full border border-blue-500/30">
                <span className="text-blue-400 text-sm">🔒</span>
                <span className="text-blue-300 text-xs font-medium">ISO 27001</span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div>
            <h3 className="text-white font-semibold mb-4">Navigation</h3>
            <ul className="space-y-3">
              {navigationLinks.map((link) => (
                <li key={link.label}>
                  <button
                    onClick={() => handleNavigation(link.href)}
                    className="text-gray-300 hover:text-white transition-colors text-sm"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="text-white font-semibold mb-4">Company</h3>
            <ul className="space-y-3">
              {companyLinks.map((link) => (
                <li key={link.label}>
                  <button
                    onClick={() => handleNavigation(link.href)}
                    className="text-gray-300 hover:text-white transition-colors text-sm"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Newsletter Signup - Only for landing variant */}
        {variant === 'landing' && (
          <div className="mt-12 pt-8 border-t border-gray-800">
            <div className="text-center">
              <h3 className="text-white font-semibold mb-2">Stay Updated</h3>
              <p className="text-gray-400 text-sm mb-6">
                Get the latest updates on tax compliance and platform features.
              </p>
              <div className="flex max-w-md mx-auto">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="flex-1 px-4 py-3 bg-gray-800 text-white border border-gray-700 rounded-l-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  aria-label="Email for newsletter subscription"
                />
                <Button
                  variant="primary"
                  size="md"
                  className="rounded-l-none"
                >
                  Subscribe
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-gray-800 bg-gray-950">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            
            {/* Copyright & Legal */}
            <div className="flex flex-col md:flex-row items-center space-y-2 md:space-y-0 md:space-x-6">
              <div className="text-gray-400 text-sm">
                © {currentYear} TaxPoynt Limited. RC: 1234567
              </div>
              <div className="flex space-x-6 text-sm">
                {legalLinks.map((link) => (
                  <button
                    key={link.label}
                    onClick={() => handleNavigation(link.href)}
                    className="text-gray-400 hover:text-gray-300 transition-colors"
                  >
                    {link.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Social Links */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => window.open('https://linkedin.com/company/taxpoynt', '_blank')}
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="LinkedIn"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
              </button>
              <button
                onClick={() => window.open('https://twitter.com/taxpoynt', '_blank')}
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="Twitter"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.427 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                </svg>
              </button>
            </div>
          </div>

          {/* Compliance Notice - Only for landing variant */}
          {variant === 'landing' && (
            <div className="mt-6 pt-6 border-t border-gray-800">
              <div className="text-center text-xs text-gray-500 max-w-3xl mx-auto">
                <p>
                  <strong>Regulatory Compliance:</strong> TaxPoynt Limited is a registered company in Nigeria (RC: 1234567) 
                  and is an official FIRS-certified Access Point Provider. Our platform complies with all Nigerian tax 
                  regulations and data protection laws.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </footer>
  );
};

export default Footer;
