/**
 * TaxPoynt Style Utilities
 * =========================
 * Reusable style patterns to avoid code duplication across components
 * Especially for the LandingPage complex gradient and shadow patterns
 */

import { TAXPOYNT_DESIGN_SYSTEM, TYPESCRIPT_TOKENS } from './index';

// ========================================
// GRADIENT UTILITIES
// ========================================

export const GRADIENT_PATTERNS = {
  // Hero section gradients
  heroBackground: {
    background: 'linear-gradient(135deg, #eef2ff 0%, #f0f9ff 30%, #faf5ff 70%, #ffffff 100%)',
    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.9)'
  },

  // Section background gradients
  section: {
    indigo: {
      background: 'linear-gradient(135deg, rgba(238, 242, 255, 0.95) 0%, rgba(239, 246, 255, 0.95) 100%)',
      backdropFilter: 'blur(10px)'
    },
    blue: {
      background: 'linear-gradient(135deg, rgba(239, 246, 255, 0.95) 0%, rgba(238, 242, 255, 0.95) 100%)',
      backdropFilter: 'blur(10px)'
    },
    green: {
      background: 'linear-gradient(135deg, rgba(236, 253, 245, 0.95) 0%, rgba(220, 252, 231, 0.95) 100%)',
      backdropFilter: 'blur(10px)'
    },
    purple: {
      background: 'linear-gradient(135deg, rgba(243, 232, 255, 0.9) 0%, rgba(238, 242, 255, 0.9) 100%)',
      backdropFilter: 'blur(10px)'
    },
    teal: {
      background: 'linear-gradient(135deg, rgba(240, 253, 250, 0.95) 0%, rgba(204, 251, 241, 0.95) 100%)',
      backdropFilter: 'blur(10px)'
    },
    slate: {
      background: 'linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.95) 100%)',
      backdropFilter: 'blur(10px)'
    },
    amber: {
      background: 'linear-gradient(135deg, rgba(255, 251, 235, 0.95) 0%, rgba(254, 243, 199, 0.95) 100%)',
      backdropFilter: 'blur(10px)'
    }
  },

  // Button gradients
  button: {
    primary: 'linear-gradient(135deg, #4f46e5 0%, #2563eb 50%, #7c3aed 100%)',
    success: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    warning: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    danger: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
    nigerian: 'linear-gradient(135deg, #008751 0%, #006341 100%)'
  },

  // Card gradients
  card: {
    default: 'linear-gradient(135deg, #ffffff 0%, #ffffff 50%, #f8fafc 100%)',
    indigo: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #eef2ff 100%)',
    blue: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #eef2ff 100%)',
    green: 'linear-gradient(135deg, #ecfdf5 0%, #ffffff 50%, #f0fdf4 100%)',
    purple: 'linear-gradient(135deg, #faf5ff 0%, #ffffff 50%, #f3e8ff 100%)',
    elevated: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(238,242,255,0.9) 50%, rgba(255,255,255,0.95) 100%)'
  },

  // Background blur patterns
  backgroundBlur: {
    indigo: 'bg-gradient-to-br from-blue-400/15 to-indigo-400/15',
    emerald: 'bg-gradient-to-br from-emerald-400/10 to-green-400/10',
    violet: 'bg-gradient-to-br from-violet-400/8 to-purple-400/8',
    overlay: 'bg-gradient-to-br from-white/40 via-transparent to-indigo-50/20'
  }
} as const;

// ========================================
// SHADOW UTILITIES
// ========================================

export const SHADOW_PATTERNS = {
  // Premium shadows for cards and CTAs
  premium: {
    small: '0 10px 25px -5px rgba(59, 130, 246, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)',
    medium: '0 25px 50px -12px rgba(79, 70, 229, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
    large: '0 25px 50px -12px rgba(79, 70, 229, 0.4), 0 10px 20px -4px rgba(0, 0, 0, 0.1), inset 0 2px 0 rgba(255, 255, 255, 0.2)',
    colored: {
      indigo: '0 25px 50px -12px rgba(79, 70, 229, 0.4)',
      blue: '0 20px 40px -12px rgba(59, 130, 246, 0.4)',
      emerald: '0 20px 40px -12px rgba(16, 185, 129, 0.4)',
      violet: '0 20px 40px -12px rgba(139, 92, 246, 0.4)',
      amber: '0 20px 40px -12px rgba(245, 158, 11, 0.4)'
    }
  },

  // Text shadows
  text: {
    small: '0 1px 2px rgba(0,0,0,0.1)',
    medium: '0 2px 4px rgba(0,0,0,0.1)',
    large: '0 4px 8px rgba(0,0,0,0.1)',
    colored: {
      indigo: '0 4px 8px rgba(79, 70, 229, 0.3)',
      blue: '0 4px 8px rgba(59, 130, 246, 0.3)',
      green: '0 4px 8px rgba(34, 197, 94, 0.4)',
      purple: '0 2px 4px rgba(147, 51, 234, 0.3)'
    }
  }
} as const;

// ========================================
// TYPOGRAPHY UTILITIES
// ========================================

// Base optimized text rendering
const optimizedTextBase = {
  fontFeatureSettings: '"kern" 1, "liga" 1',
  textRendering: 'optimizeLegibility',
  WebkitFontSmoothing: 'antialiased',
  MozOsxFontSmoothing: 'grayscale'
} as const;

export const TYPOGRAPHY_STYLES = {
  // Optimized text rendering
  optimizedText: optimizedTextBase,

  // Hero headline styles
  heroHeadline: {
    fontSize: 'clamp(3rem, 8vw, 6rem)', // Responsive sizing
    fontWeight: '950',
    lineHeight: '0.9',
    letterSpacing: '-0.02em',
    ...optimizedTextBase
  },

  // Section headline styles
  sectionHeadline: {
    fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
    fontWeight: '950',
    lineHeight: '0.9',
    letterSpacing: '-0.01em',
    ...optimizedTextBase
  },

  // Subtitle styles
  subtitle: {
    fontSize: 'clamp(1.25rem, 3vw, 2rem)',
    fontWeight: '500',
    lineHeight: '1.5',
    ...optimizedTextBase
  }
} as const;

// ========================================
// ANIMATION UTILITIES
// ========================================

export const STYLE_ANIMATION_PATTERNS = {
  // Hover effects
  hover: {
    lift: 'hover:shadow-lg hover:-translate-y-1 transition-all duration-300',
    liftLarge: 'hover:shadow-xl hover:-translate-y-2 transition-all duration-300',
    scale: 'hover:scale-105 transition-transform duration-300',
    scaleSmall: 'hover:scale-102 transition-transform duration-300',
    glow: 'hover:shadow-2xl transition-shadow duration-300'
  },

  // Loading states
  loading: {
    pulse: 'animate-pulse',
    spin: 'animate-spin',
    bounce: 'animate-bounce'
  },

  // Entrance animations
  entrance: {
    fadeIn: 'animate-in fade-in duration-500',
    slideInFromLeft: 'animate-in slide-in-from-left duration-500',
    slideInFromRight: 'animate-in slide-in-from-right duration-500',
    slideInFromBottom: 'animate-in slide-in-from-bottom duration-500'
  }
} as const;

// ========================================
// LAYOUT UTILITIES
// ========================================

export const LAYOUT_PATTERNS = {
  // Container patterns
  container: {
    default: 'max-w-6xl mx-auto px-6',
    wide: 'max-w-7xl mx-auto px-6',
    narrow: 'max-w-4xl mx-auto px-6',
    fluid: 'w-full px-6'
  },

  // Section spacing
  section: {
    padding: {
      small: 'py-12',
      medium: 'py-16',
      large: 'py-20',
      extraLarge: 'py-24'
    },
    margin: {
      small: 'my-8',
      medium: 'my-12',
      large: 'my-16',
      extraLarge: 'my-20'
    }
  },

  // Grid patterns
  grid: {
    problems: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8',
    features: 'grid grid-cols-1 md:grid-cols-2 gap-12',
    testimonials: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6',
    trust: 'grid grid-cols-2 md:grid-cols-4 gap-8',
    pricing: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8'
  }
} as const;

// ========================================
// UTILITY FUNCTIONS
// ========================================

/**
 * Generate CSS style object from gradient pattern
 */
export const getGradientStyle = (pattern: keyof typeof GRADIENT_PATTERNS.section | 'hero' | 'card') => {
  if (pattern === 'hero') {
    return GRADIENT_PATTERNS.heroBackground;
  }
  
  if (pattern === 'card') {
    return { background: GRADIENT_PATTERNS.card.default };
  }
  
  return GRADIENT_PATTERNS.section[pattern] || GRADIENT_PATTERNS.section.indigo;
};

/**
 * Generate CSS style object from shadow pattern
 */
export const getShadowStyle = (type: 'premium' | 'text', variant: string, color?: string) => {
  if (type === 'premium') {
    if (color && SHADOW_PATTERNS.premium.colored[color as keyof typeof SHADOW_PATTERNS.premium.colored]) {
      return { boxShadow: SHADOW_PATTERNS.premium.colored[color as keyof typeof SHADOW_PATTERNS.premium.colored] };
    }
    return { boxShadow: SHADOW_PATTERNS.premium[variant as keyof typeof SHADOW_PATTERNS.premium] };
  }
  
  if (type === 'text') {
    if (color && SHADOW_PATTERNS.text.colored[color as keyof typeof SHADOW_PATTERNS.text.colored]) {
      return { textShadow: SHADOW_PATTERNS.text.colored[color as keyof typeof SHADOW_PATTERNS.text.colored] };
    }
    return { textShadow: SHADOW_PATTERNS.text[variant as keyof typeof SHADOW_PATTERNS.text] };
  }
  
  return {};
};

/**
 * Combine multiple style objects
 */
export const combineStyles = (...styles: (React.CSSProperties | undefined)[]) => {
  return styles.reduce((acc, style) => ({ ...acc, ...style }), {});
};

/**
 * Generate section background style
 */
export const getSectionBackground = (theme: keyof typeof GRADIENT_PATTERNS.section) => {
  const colors = {
    indigo: 'bg-gradient-to-br from-indigo-50 via-blue-50/30 to-purple-50',
    blue: 'bg-gradient-to-br from-blue-50 via-indigo-50/30 to-blue-50',
    green: 'bg-gradient-to-br from-green-50 via-emerald-50/30 to-green-50',
    purple: 'bg-gradient-to-br from-purple-50 via-violet-50/30 to-purple-50',
    teal: 'bg-gradient-to-br from-teal-50 via-cyan-50/30 to-teal-50',
    slate: 'bg-gradient-to-br from-slate-50 via-gray-50/30 to-slate-50',
    amber: 'bg-gradient-to-br from-amber-50 via-orange-50/30 to-amber-50'
  };

  const shadows = {
    indigo: '0 4px 12px rgba(79, 70, 229, 0.08)',
    blue: '0 4px 12px rgba(59, 130, 246, 0.08)',
    green: '0 4px 12px rgba(34, 197, 94, 0.08)',
    purple: '0 4px 12px rgba(147, 51, 234, 0.08)',
    teal: '0 4px 12px rgba(20, 184, 166, 0.08)',
    slate: '0 4px 12px rgba(71, 85, 105, 0.08)',
    amber: '0 4px 12px rgba(245, 158, 11, 0.08)'
  };

  return {
    className: `${colors[theme]} relative overflow-hidden`,
    style: {
      boxShadow: `inset 0 1px 0 rgba(255,255,255,0.8), ${shadows[theme]}`
    }
  };
};

/**
 * Generate responsive spacing
 */
export const getResponsiveSpacing = (mobile: string, desktop: string) => {
  return `${mobile} lg:${desktop}`;
};

// ========================================
// ACCESSIBILITY UTILITIES
// ========================================

export const ACCESSIBILITY_PATTERNS = {
  // ARIA labels for common elements
  aria: {
    navigation: 'Main navigation',
    search: 'Search',
    menu: 'Menu',
    close: 'Close',
    expand: 'Expand',
    collapse: 'Collapse'
  },

  // Focus styles
  focus: {
    visible: 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2',
    ring: 'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
  },
  
  // Focus ring as CSS-in-JS object
  focusRing: {
    outline: 'none',
    boxShadow: '0 0 0 2px rgba(59, 130, 246, 0.5)',
    borderRadius: '4px'
  },

  // Screen reader utilities
  screenReader: {
    only: 'sr-only',
    focusable: 'sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 z-50 p-4 bg-white border rounded shadow'
  }
} as const;

export default {
  GRADIENT_PATTERNS,
  SHADOW_PATTERNS,
  TYPOGRAPHY_STYLES,
  STYLE_ANIMATION_PATTERNS,
  LAYOUT_PATTERNS,
  ACCESSIBILITY_PATTERNS,
  getGradientStyle,
  getShadowStyle,
  combineStyles,
  getSectionBackground,
  getResponsiveSpacing
};
