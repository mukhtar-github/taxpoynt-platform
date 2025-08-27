/**
 * Accessibility Utilities
 * =======================
 * Tools for improving accessibility across the application
 */

import { useEffect, useState } from 'react';

// ARIA label helpers
export const generateAriaLabel = (text: string, context?: string) => {
  const cleanText = text.replace(/[^\w\s]/g, '').trim();
  return context ? `${cleanText} - ${context}` : cleanText;
};

// Focus management
export const focusElement = (selector: string | Element, options?: FocusOptions) => {
  const element = typeof selector === 'string' 
    ? document.querySelector(selector) 
    : selector;
  
  if (element && 'focus' in element) {
    (element as HTMLElement).focus(options);
  }
};

// Trap focus within a container (for modals, dropdowns)
export const trapFocus = (containerElement: HTMLElement) => {
  const focusableElements = containerElement.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

  const handleTabKey = (e: KeyboardEvent) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    }
  };

  containerElement.addEventListener('keydown', handleTabKey);
  
  // Focus first element initially
  if (firstElement) {
    firstElement.focus();
  }

  // Return cleanup function
  return () => {
    containerElement.removeEventListener('keydown', handleTabKey);
  };
};

// Skip to content link
export const createSkipLink = (targetId: string, text: string = 'Skip to main content') => {
  const skipLink = document.createElement('a');
  skipLink.href = `#${targetId}`;
  skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 z-50 p-4 bg-white border rounded shadow';
  skipLink.textContent = text;
  skipLink.style.left = '-9999px';
  
  skipLink.addEventListener('focus', () => {
    skipLink.style.left = '0';
  });
  
  skipLink.addEventListener('blur', () => {
    skipLink.style.left = '-9999px';
  });

  return skipLink;
};

// Screen reader announcements
export const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

// Color contrast checker
export const checkColorContrast = (foreground: string, background: string): number => {
  // Convert hex to RGB
  const hexToRgb = (hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  };

  // Calculate relative luminance
  const getLuminance = (r: number, g: number, b: number) => {
    const sRGB = [r, g, b].map(c => {
      c /= 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * sRGB[0] + 0.7152 * sRGB[1] + 0.0722 * sRGB[2];
  };

  const fg = hexToRgb(foreground);
  const bg = hexToRgb(background);
  
  if (!fg || !bg) return 1;

  const l1 = getLuminance(fg.r, fg.g, fg.b);
  const l2 = getLuminance(bg.r, bg.g, bg.b);
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
};

// Keyboard navigation helper
export const useKeyboardNavigation = (keys: string[], callback: (key: string) => void) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (keys.includes(event.key)) {
        callback(event.key);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [keys, callback]);
};

// Detect if user prefers reduced motion
export const usePrefersReducedMotion = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReducedMotion;
};

// Detect if user prefers high contrast
export const usePrefersHighContrast = () => {
  const [prefersHighContrast, setPrefersHighContrast] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-contrast: high)');
    setPrefersHighContrast(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersHighContrast(event.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersHighContrast;
};

// Generate unique IDs for ARIA relationships
let idCounter = 0;
export const generateUniqueId = (prefix: string = 'tp') => {
  idCounter += 1;
  return `${prefix}-${idCounter}-${Date.now()}`;
};

// Validate ARIA attributes
export const validateAriaAttributes = (element: HTMLElement) => {
  const warnings: string[] = [];
  
  // Check for aria-label without role
  if (element.hasAttribute('aria-label') && !element.hasAttribute('role')) {
    warnings.push('Element has aria-label but no role attribute');
  }
  
  // Check for aria-describedby pointing to non-existent element
  const describedBy = element.getAttribute('aria-describedby');
  if (describedBy && !document.getElementById(describedBy)) {
    warnings.push(`aria-describedby points to non-existent element: ${describedBy}`);
  }
  
  // Check for aria-labelledby pointing to non-existent element
  const labelledBy = element.getAttribute('aria-labelledby');
  if (labelledBy && !document.getElementById(labelledBy)) {
    warnings.push(`aria-labelledby points to non-existent element: ${labelledBy}`);
  }
  
  return warnings;
};

// Focus visible polyfill for older browsers
export const addFocusVisiblePolyfill = () => {
  if (typeof window === 'undefined') return;
  
  let hadKeyboardEvent = true;
  
  const onPointerDown = () => {
    hadKeyboardEvent = false;
  };
  
  const onKeyDown = (e: KeyboardEvent) => {
    if (e.metaKey || e.altKey || e.ctrlKey) {
      return;
    }
    hadKeyboardEvent = true;
  };
  
  const onFocus = (e: FocusEvent) => {
    if (hadKeyboardEvent) {
      (e.target as HTMLElement).classList.add('focus-visible');
    }
  };
  
  const onBlur = (e: FocusEvent) => {
    (e.target as HTMLElement).classList.remove('focus-visible');
  };
  
  document.addEventListener('keydown', onKeyDown, true);
  document.addEventListener('mousedown', onPointerDown, true);
  document.addEventListener('pointerdown', onPointerDown, true);
  document.addEventListener('touchstart', onPointerDown, true);
  document.addEventListener('focus', onFocus, true);
  document.addEventListener('blur', onBlur, true);
};

export default {
  generateAriaLabel,
  focusElement,
  trapFocus,
  createSkipLink,
  announceToScreenReader,
  checkColorContrast,
  useKeyboardNavigation,
  usePrefersReducedMotion,
  usePrefersHighContrast,
  generateUniqueId,
  validateAriaAttributes,
  addFocusVisiblePolyfill
};
