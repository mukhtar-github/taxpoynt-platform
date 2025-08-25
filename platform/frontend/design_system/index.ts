/**
 * TaxPoynt Complete Design System
 * ===============================
 * Full platform design system - Landing page + Auth + Dashboards + Business interfaces
 * All components extracted from legacy with Nigerian mobile-first optimizations
 */

// ========================================
// CORE COMPONENTS
// ========================================

// Cards
export { 
  LegacyCard, 
  LegacyCardHeader, 
  LegacyCardTitle, 
  LegacyCardDescription, 
  LegacyCardContent, 
  LegacyCardFooter,
  ProblemCard,
  SolutionCard,
  type LegacyCardProps 
} from './components/LegacyCard';

// Buttons
export {
  TaxPoyntButton,
  HeroCTAButton,
  MobileTouchButton, 
  DashboardButton,
  AuthFormButton,
  taxPoyntButtonVariants,
  type TaxPoyntButtonProps
} from './components/TaxPoyntButton';

// Inputs
export {
  TaxPoyntInput,
  AuthInput,
  MobileInput,
  DashboardInput,
  taxPoyntInputVariants,
  type TaxPoyntInputProps
} from './components/TaxPoyntInput';

// Tables
export {
  TaxPoyntTableContainer,
  TaxPoyntTable,
  TaxPoyntTableHeader,
  TaxPoyntTableBody,
  TaxPoyntTableRow,
  TaxPoyntTableHead,
  TaxPoyntTableCell,
  TaxPoyntTableCaption,
  TaxPoyntTableEmpty,
  TaxPoyntTableLoading,
  TaxPoyntTablePagination,
  DashboardTable,
  SimpleDataTable,
  MobileTable
} from './components/TaxPoyntTable';

// Navigation
export {
  TaxPoyntNavigation,
  LandingNavigation,
  DashboardNavigation,
  AuthNavigation,
  taxPoyntNavVariants,
  navItemVariants,
  type TaxPoyntNavigationProps,
  type NavItem
} from './components/TaxPoyntNavigation';

// Logo components removed - using real logo.svg directly

// ========================================
// CONTENT PATTERNS & CONSTANTS
// ========================================

export {
  EMOJIS,
  NIGERIAN_CITIES,
  BUSINESS_TYPES,
  PROBLEM_PATTERNS,
  PROBLEMS_DATA,
  ENTERPRISE_SOLUTIONS_DATA,
  SOLUTION_PATTERNS,
  COLOR_SCHEMES,
  TYPOGRAPHY_PATTERNS,
  ANIMATION_PATTERNS,
  GRID_PATTERNS
} from './content-patterns';

// ========================================
// DESIGN SYSTEM CONSTANTS
// ========================================

export const TAXPOYNT_DESIGN_SYSTEM = {
  // Color System (from complete-design-tokens.css)
  colors: {
    // Primary Brand
    primary: '#3B82F6',
    primaryDark: '#2563EB',
    primaryLight: '#93C5FD',
    
    // Semantic Colors
    success: '#10B981',
    error: '#EF4444',
    warning: '#F59E0B',
    
    // Nigerian Colors
    nigerianGreen: '#008751',
    nigerianGreenLight: '#00A86B',
    nigerianGreenDark: '#006341',
    
    // Text Colors
    textPrimary: '#111827',
    textSecondary: '#4B5563',
    textMuted: '#9CA3AF',
    textLight: '#F9FAFB',
    
    // Background Colors
    background: '#FFFFFF',
    backgroundAlt: '#F9FAFB',
    backgroundSecondary: '#F3F4F6',
    backgroundDark: '#374151',
  },
  
  // Typography System
  typography: {
    fontFamilies: {
      heading: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      body: 'Source Sans Pro, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      mono: 'JetBrains Mono, Consolas, Monaco, monospace',
    },
    
    fontSizes: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',   // 14px  
      base: '1rem',     // 16px
      lg: '1.125rem',   // 18px
      xl: '1.25rem',    // 20px
      '2xl': '1.5rem',  // 24px
      '3xl': '1.875rem', // 30px
      '4xl': '2.25rem', // 36px
      '5xl': '3rem',    // 48px
      '6xl': '3.75rem', // 60px
      '7xl': '4.5rem',  // 72px
      '8xl': '6rem',    // 96px
    },
    
    fontWeights: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
      black: 900,
    },
    
    lineHeights: {
      none: 1,
      tight: 1.25,
      snug: 1.375,
      normal: 1.5,
      relaxed: 1.625,
      loose: 2,
    },
  },
  
  // Spacing System (8px grid)
  spacing: {
    0: '0',
    px: '1px',
    0.5: '0.125rem',  // 2px
    1: '0.25rem',     // 4px
    2: '0.5rem',      // 8px
    3: '0.75rem',     // 12px
    4: '1rem',        // 16px
    5: '1.25rem',     // 20px
    6: '1.5rem',      // 24px
    8: '2rem',        // 32px
    10: '2.5rem',     // 40px
    12: '3rem',       // 48px
    16: '4rem',       // 64px
    20: '5rem',       // 80px
    24: '6rem',       // 96px
  },
  
  // Border Radius System
  radius: {
    none: '0',
    sm: '0.125rem',   // 2px
    md: '0.25rem',    // 4px
    lg: '0.5rem',     // 8px - Legacy standard
    xl: '0.75rem',    // 12px
    '2xl': '1rem',    // 16px
    '3xl': '1.5rem',  // 24px
    full: '9999px',
  },
  
  // Shadow System
  shadows: {
    xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',           // Legacy card standard
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',         // Legacy hover standard
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',       // Elevated
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',       // Large
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',  // Extra large
  },
  
  // Animation System
  animations: {
    durations: {
      fast: '100ms',
      normal: '200ms',    // Legacy standard
      medium: '300ms',
      slow: '500ms',
    },
    
    easings: {
      linear: 'linear',
      out: 'cubic-bezier(0, 0, 0.2, 1)',
      in: 'cubic-bezier(0.4, 0, 1, 1)',
      inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    },
    
    // Common animation patterns
    cardHover: 'hover:shadow-md hover:-translate-y-1 transition-all duration-200',
    buttonActive: 'active:scale-95 transition-transform',
    fadeIn: 'transition-opacity duration-200 ease-out',
  },
  
  // Mobile-First Nigerian Optimizations
  mobile: {
    touchTargets: {
      default: '44px',  // iOS/Android minimum
      large: '48px',
      extraLarge: '52px',
    },
    
    carriers: ['MTN', 'Airtel', 'Glo', '9mobile'] as const,
    
    networkOptimizations: {
      dataSaverOpacity: 0.8,
      slowNetworkDelay: '300ms',
    },
  },
  
  // Breakpoints
  breakpoints: {
    xs: '475px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
  
  // Component Defaults
  components: {
    button: {
      defaultSize: 'default',
      defaultVariant: 'primary',
      touchSize: 'touch',
    },
    
    input: {
      defaultSize: 'default',
      touchSize: 'touch',
    },
    
    card: {
      defaultPadding: '16px',
      defaultRadius: '8px', // Legacy standard
      defaultShadow: 'sm',
    },
    
    table: {
      defaultRowHeight: '48px',
      defaultCellPadding: '16px',
    },
    
    navigation: {
      desktopHeight: '64px',
      mobileHeight: '56px',
    },
  },
  
} as const;

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Generate component class names
export const generateComponentClasses = (
  component: string,
  variant?: string,
  size?: string,
  ...additionalClasses: string[]
) => {
  const classes = [`tp-${component}`];
  
  if (variant) classes.push(`tp-${component}-${variant}`);
  if (size) classes.push(`tp-${component}-${size}`);
  
  return [...classes, ...additionalClasses].join(' ');
};

// Get responsive spacing
export const getResponsiveSpacing = (mobile: string, desktop: string) => {
  return `${TAXPOYNT_DESIGN_SYSTEM.spacing[mobile as keyof typeof TAXPOYNT_DESIGN_SYSTEM.spacing]} lg:${TAXPOYNT_DESIGN_SYSTEM.spacing[desktop as keyof typeof TAXPOYNT_DESIGN_SYSTEM.spacing]}`;
};

// Get color with opacity
export const getColorWithOpacity = (color: string, opacity: number) => {
  return `rgba(${color}, ${opacity})`;
};

// Nigerian carrier detection (client-side)
export const detectNigerianCarrier = (): string | null => {
  if (typeof navigator === 'undefined') return null;
  
  // Simple carrier detection based on common patterns
  const connection = (navigator as any).connection;
  if (connection && connection.effectiveType) {
    // This is a simplified example - in production you'd use more sophisticated detection
    return 'MTN'; // Default for demo
  }
  
  return null;
};

// ========================================
// CSS CLASS BUILDERS
// ========================================

export const buildCardClasses = (variant: string = 'default', size: string = 'default') => {
  return generateComponentClasses('card', variant, size, 'tp-hover-lift');
};

export const buildButtonClasses = (variant: string = 'primary', size: string = 'default') => {
  return generateComponentClasses('button', variant, size, 'tp-focus-ring');
};

export const buildInputClasses = (variant: string = 'default', size: string = 'default') => {
  return generateComponentClasses('input', variant, size, 'tp-focus-ring');
};

export const buildGridClasses = (type: 'problems' | 'features' | 'trust' | 'testimonials' | 'dashboard' | 'metrics') => {
  return `tp-grid-${type}`;
};

// ========================================
// TYPESCRIPT TOKEN DEFINITIONS (from tokens.ts)
// ========================================

export const TYPESCRIPT_TOKENS = {
  colors: {
    // TaxPoynt Brand Colors (from existing logo.svg)
    brand: {
      primary: '#0054B0',      // TaxPoynt Blue (from logo)
      secondary: '#003875',    // Darker blue variant
      accent: '#0066CC',       // Lighter blue variant
      light: '#E6F2FF',        // Very light blue
    },
    
    // Nigerian Colors (for compliance/FIRS theming)
    nigeria: {
      green: '#008751',        // Nigerian flag green
      emerald: '#00A86B',      // Emerald green variant
      forest: '#006341',       // Dark green
    },
    
    // Enterprise Neutrals
    neutral: {
      50: '#F8FAFC',
      100: '#F1F5F9',
      200: '#E2E8F0',
      300: '#CBD5E1',
      400: '#94A3B8',
      500: '#64748B',
      600: '#475569',
      700: '#334155',
      800: '#1E293B',
      900: '#0F172A',
    },
    
    // Semantic Colors
    semantic: {
      success: '#10B981',      // Green for success states
      warning: '#F59E0B',      // Amber for warnings
      error: '#EF4444',        // Red for errors
      info: '#3B82F6',         // Blue for information
    },
    
    // Role-Based Colors
    roles: {
      si: '#0054B0',           // System Integrator (TaxPoynt blue)
      app: '#008751',          // Access Point Provider (Nigerian green)
      hybrid: '#6366F1',       // Hybrid users (indigo)
      admin: '#7C3AED',        // Admin interface (purple)
    },
  },
  
  typography: {
    fonts: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
      mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      display: ['Inter', 'system-ui', 'sans-serif'],
    },
    
    sizes: {
      xs: '0.75rem',     // 12px
      sm: '0.875rem',    // 14px
      base: '1rem',      // 16px
      lg: '1.125rem',    // 18px
      xl: '1.25rem',     // 20px
      '2xl': '1.5rem',   // 24px
      '3xl': '1.875rem', // 30px
      '4xl': '2.25rem',  // 36px
      '5xl': '3rem',     // 48px
      '6xl': '3.75rem',  // 60px
    },
    
    weights: {
      light: '300',
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
      extrabold: '800',
    },
    
    lineHeights: {
      none: '1',
      tight: '1.25',
      snug: '1.375',
      normal: '1.5',
      relaxed: '1.625',
      loose: '2',
    },
  },
  
  // Role-specific theme variations
  roleThemes: {
    si: {
      primary: '#0054B0',
      accent: '#0066CC',
      background: '#E6F2FF',
    },
    
    app: {
      primary: '#008751',
      accent: '#00A86B',
      background: '#F0F8FF',
    },
    
    hybrid: {
      primary: '#6366F1',
      accent: '#8B5CF6',
      background: '#F8FAFF',
    },
    
    admin: {
      primary: '#7C3AED',
      accent: '#A855F7',
      background: '#FAF5FF',
    }
  }
} as const;

// ========================================
// TYPE EXPORTS
// ========================================

export type TaxPoyntColorScheme = 'problems' | 'solutions' | 'features' | 'testimonials';
export type TaxPoyntSize = 'sm' | 'default' | 'lg' | 'xl' | 'touch' | 'touchLg';
export type TaxPoyntVariant = 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'warning';
export type NigerianCarrier = 'MTN' | 'Airtel' | 'Glo' | '9mobile';

// Design system version
export const DESIGN_SYSTEM_VERSION = '1.0.0' as const;

// ========================================
// BACKWARD COMPATIBILITY EXPORTS
// ========================================

// Export individual properties for backward compatibility with proper nested structure
export const colors = {
  ...TAXPOYNT_DESIGN_SYSTEM.colors,
  // Add nested structures for legacy compatibility
  brand: TYPESCRIPT_TOKENS.colors.brand,
  neutral: TYPESCRIPT_TOKENS.colors.neutral,
  semantic: TYPESCRIPT_TOKENS.colors.semantic,
  roles: TYPESCRIPT_TOKENS.colors.roles,
  nigeria: TYPESCRIPT_TOKENS.colors.nigeria,
};

export const typography = {
  ...TAXPOYNT_DESIGN_SYSTEM.typography,
  // Add nested structures for legacy compatibility
  fonts: TYPESCRIPT_TOKENS.typography.fonts,
  sizes: TYPESCRIPT_TOKENS.typography.sizes,
  weights: TYPESCRIPT_TOKENS.typography.weights,
  lineHeights: TYPESCRIPT_TOKENS.typography.lineHeights,
};

export const spacing = TAXPOYNT_DESIGN_SYSTEM.spacing;
export const shadows = TAXPOYNT_DESIGN_SYSTEM.shadows;

export const animations = {
  ...TAXPOYNT_DESIGN_SYSTEM.animations,
  // Add backward compatibility for transition property
  transition: {
    fast: '150ms ease-in-out',
    base: '200ms ease-in-out',
    slow: '300ms ease-in-out',
  }
};

export const roleThemes = TYPESCRIPT_TOKENS.roleThemes;

// Additional exports for legacy compatibility
export const borders = {
  radius: TAXPOYNT_DESIGN_SYSTEM.radius,
  width: {
    0: '0',
    1: '1px',
    2: '2px',
    4: '4px',
    8: '8px',
  }
};