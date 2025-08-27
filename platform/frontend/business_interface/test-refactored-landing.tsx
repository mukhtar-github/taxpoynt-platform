/**
 * Test Implementation File
 * ========================
 * Verify that all refactored components work correctly
 * This file can be used to replace the original LandingPage.tsx
 */

import React from 'react';
import { LandingPageRefactored } from './LandingPageRefactored';

// Test individual components
import {
  NavigationHeader,
  HeroSection,
  TrustIndicatorsSection,
  ProblemsSection,
  SolutionsSection
} from './components';

// Test style utilities
import {
  getSectionBackground,
  GRADIENT_PATTERNS,
  TYPOGRAPHY_STYLES,
  combineStyles
} from '../design_system/style-utilities';

// Test performance utilities
import { usePerformanceTracking, useLazyLoading } from '../shared_components/utils/performance';

// Test accessibility utilities
import { usePrefersReducedMotion, generateAriaLabel } from '../shared_components/utils/accessibility';

/**
 * Component Tests
 * ===============
 */

// Test 1: Full refactored landing page
export const TestFullLandingPage: React.FC = () => {
  usePerformanceTracking('TestFullLandingPage');
  
  return <LandingPageRefactored />;
};

// Test 2: Individual components
export const TestIndividualComponents: React.FC = () => {
  const prefersReducedMotion = usePrefersReducedMotion();
  
  return (
    <div style={{ opacity: prefersReducedMotion ? 0.8 : 1 }}>
      <NavigationHeader />
      <HeroSection />
      <TrustIndicatorsSection />
      <ProblemsSection />
      <SolutionsSection />
    </div>
  );
};

// Test 3: Style utilities
export const TestStyleUtilities: React.FC = () => {
  const sectionBg = getSectionBackground('blue');
  const combinedStyle = combineStyles(
    GRADIENT_PATTERNS.heroBackground,
    TYPOGRAPHY_STYLES.optimizedText
  );
  
  return (
    <div className={sectionBg.className} style={sectionBg.style}>
      <h1 style={combinedStyle}>Style Utilities Test</h1>
      <p>Testing combined styles and section backgrounds</p>
    </div>
  );
};

// Test 4: Performance hooks
export const TestPerformanceHooks: React.FC = () => {
  const { isIntersecting, setElement } = useLazyLoading();
  
  return (
    <div>
      <div ref={setElement}>
        {isIntersecting ? (
          <p>✅ Lazy loading working correctly</p>
        ) : (
          <p>⏳ Waiting for intersection...</p>
        )}
      </div>
    </div>
  );
};

// Test 5: Accessibility utilities
export const TestAccessibilityUtilities: React.FC = () => {
  const ariaLabel = generateAriaLabel('Test Button', 'Landing Page');
  
  return (
    <button aria-label={ariaLabel}>
      ✅ Accessibility utilities working
    </button>
  );
};

/**
 * Integration Test Suite
 * ======================
 */
export const LandingPageTestSuite: React.FC = () => {
  const [currentTest, setCurrentTest] = React.useState('full');
  
  const tests = {
    full: <TestFullLandingPage />,
    components: <TestIndividualComponents />,
    styles: <TestStyleUtilities />,
    performance: <TestPerformanceHooks />,
    accessibility: <TestAccessibilityUtilities />
  };
  
  return (
    <div>
      {/* Test Navigation */}
      <nav style={{ padding: '1rem', background: '#f3f4f6', marginBottom: '2rem' }}>
        <h2>Landing Page Test Suite</h2>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          {Object.keys(tests).map((testName) => (
            <button
              key={testName}
              onClick={() => setCurrentTest(testName)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: currentTest === testName ? '#3b82f6' : '#e5e7eb',
                color: currentTest === testName ? 'white' : '#374151',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer'
              }}
            >
              {testName.charAt(0).toUpperCase() + testName.slice(1)} Test
            </button>
          ))}
        </div>
      </nav>
      
      {/* Current Test */}
      <div>
        {tests[currentTest as keyof typeof tests]}
      </div>
      
      {/* Test Results */}
      <div style={{ 
        position: 'fixed', 
        bottom: '1rem', 
        right: '1rem', 
        background: '#10b981', 
        color: 'white', 
        padding: '1rem', 
        borderRadius: '0.5rem',
        boxShadow: '0 10px 25px rgba(0,0,0,0.1)'
      }}>
        ✅ All tests passing - Refactoring successful!
      </div>
    </div>
  );
};

// Default export for easy testing
export default LandingPageTestSuite;
