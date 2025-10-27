/**
 * Navigation Header Component
 * ===========================
 * Extracted from LandingPage.tsx - Main navigation with accessibility improvements
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { TaxPoyntButton } from '../../design_system';
import { OptimizedImage } from '../../design_system/components/OptimizedImage';
import { TYPOGRAPHY_STYLES } from '../../design_system/style-utilities';

export interface NavigationHeaderProps {
  className?: string;
}

export const NavigationHeader: React.FC<NavigationHeaderProps> = ({ className = '' }) => {
  const router = useRouter();

  return (
    <nav 
      className={`px-6 py-5 border-b border-slate-200 bg-white/95 backdrop-blur-sm shadow-sm ${className}`}
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        
        {/* Logo Section */}
        <div className="flex items-center space-x-3">
          <OptimizedImage
            src="/logo.svg" 
            alt="TaxPoynt - Secure E-invoicing Solution" 
            className="h-8 w-auto"
            width={32}
            height={32}
            priority={true}
            loading="eager"
          />
          <div>
            <div 
              className="text-xl font-bold text-blue-600" 
              style={{ 
                textShadow: '0 1px 2px rgba(37, 99, 235, 0.3)',
                ...TYPOGRAPHY_STYLES.optimizedText
              }}
            >
              TaxPoynt
            </div>
            <div className="text-sm text-blue-500 font-medium">
              Secure E-invoicing Solution
            </div>
          </div>
        </div>
        
        {/* Navigation Actions */}
        <div className="flex items-center space-x-4">
          <button
            onClick={() => router.push('/auth/signin')}
            className="text-blue-600 hover:text-blue-800 font-semibold transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-3 py-2"
            style={TYPOGRAPHY_STYLES.optimizedText}
            aria-label="Sign in to your TaxPoynt account"
          >
            Sign In
          </button>
          
          <TaxPoyntButton
            variant="primary"
            onClick={() => router.push('/auth/signup?service=si&next=/onboarding/si/integration-choice')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold focus:ring-blue-500"
            aria-label="Get started with TaxPoynt"
          >
            Get Started
          </TaxPoyntButton>
        </div>
      </div>
    </nav>
  );
};
