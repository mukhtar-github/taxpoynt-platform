/**
 * TaxPoynt Refactored Landing Page
 * ================================
 * Refactored version with extracted components, improved accessibility,
 * performance optimizations, and reduced code duplication
 */

import React, { Suspense, lazy } from 'react';
import {
  NavigationHeader,
  HeroSection,
  TrustIndicatorsSection,
  ProblemsSection,
  SolutionsSection,
  FeaturesSection,
  BeforeAfterSection,
  PricingSection,
  FinalCTASection,
  TestimonialsSection
} from './components';
import { Footer } from '../design_system';
import { TYPOGRAPHY_STYLES } from '../design_system/style-utilities';

// Note: Since we now have all components, we can import them directly
// If we want lazy loading for specific heavy sections, we can still use it selectively

// Loading fallback component
const SectionLoading: React.FC<{ height?: string }> = ({ height = 'h-96' }) => (
  <div className={`${height} bg-gray-50 animate-pulse flex items-center justify-center`}>
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

// Section transition component for smooth visual flow
const SectionTransition: React.FC = () => (
  <div className="relative h-32">
    {/* Multi-layered Depth Effect */}
    <div className="absolute inset-0 bg-gradient-to-b from-slate-100/30 via-slate-50/20 to-transparent h-12"></div>
    <div className="absolute inset-0 bg-gradient-to-b from-slate-200/20 to-transparent h-16"></div>
    
    {/* Main Gradient Transition */}
    <div className="h-full bg-gradient-to-b from-slate-50/40 via-white/60 to-white relative">
      {/* Enhanced Divider Line */}
      <div 
        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-px bg-gradient-to-r from-transparent via-slate-300/60 to-transparent"
        aria-hidden="true"
      ></div>
      
      {/* Premium Accent Elements */}
      <div 
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2 w-40 h-1 bg-gradient-to-r from-emerald-500 via-blue-500 to-purple-500 rounded-full opacity-30 shadow-lg blur-sm"
        aria-hidden="true"
      ></div>
      <div 
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2 w-24 h-0.5 bg-gradient-to-r from-emerald-400 via-blue-400 to-purple-400 rounded-full opacity-70"
        aria-hidden="true"
      ></div>
      
      {/* Subtle Pattern */}
      <div 
        className="absolute inset-0 bg-gradient-to-br from-white/40 via-transparent to-slate-50/20"
        aria-hidden="true"
      ></div>
    </div>
    
    {/* Professional Drop Shadow */}
    <div 
      className="absolute inset-x-0 bottom-0 h-6 bg-gradient-to-b from-black/3 to-transparent"
      aria-hidden="true"
    ></div>
  </div>
);

export const LandingPageRefactored: React.FC = () => {
  return (
    <main 
      className="min-h-screen bg-gray-50" 
      style={TYPOGRAPHY_STYLES.optimizedText}
      role="main"
    >
      
      {/* Navigation */}
      <NavigationHeader />

      {/* Hero Section */}
      <HeroSection />

      {/* Section Transition */}
      <SectionTransition />

      {/* Trust Indicators Section */}
      <TrustIndicatorsSection />

      {/* Section Transition */}
      <SectionTransition />

      {/* Problems Section */}
      <ProblemsSection />

      {/* Section Transition */}
      <SectionTransition />

      {/* Solutions Section */}
      <SolutionsSection />

      {/* Additional Sections */}
      <SectionTransition />
      <FeaturesSection />

      <SectionTransition />
      <BeforeAfterSection />

      <SectionTransition />
      <PricingSection />

      <SectionTransition />
      <TestimonialsSection />

      <SectionTransition />
      <FinalCTASection />

      {/* Footer - No transition needed */}
      <Footer variant="landing" />

      {/* Skip to top button for accessibility */}
      <button
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        className="fixed bottom-8 right-8 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 z-50"
        aria-label="Scroll to top of page"
      >
        <svg 
          className="w-6 h-6" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      </button>
    </main>
  );
};
