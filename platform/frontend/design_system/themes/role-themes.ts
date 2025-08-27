/**
 * Role-Based Theme System
 * ========================
 * 
 * Unified theme system that provides consistent styling patterns
 * across different user roles while maintaining visual distinction.
 */

export type UserRole = 'si' | 'app' | 'hybrid' | 'admin';

export interface RoleTheme {
  primary: {
    gradient: string;
    solid: string;
    light: string;
    border: string;
    text: string;
    hover: string;
  };
  secondary: {
    background: string;
    border: string;
    text: string;
  };
  accent: {
    background: string;
    text: string;
    border: string;
  };
  status: {
    success: string;
    warning: string;
    error: string;
    info: string;
  };
  navigation: {
    background: string;
    border: string;
    active: string;
    hover: string;
    text: string;
    activeText: string;
  };
  card: {
    background: string;
    border: string;
    shadow: string;
    hoverShadow: string;
  };
}

export const ROLE_THEMES: Record<UserRole, RoleTheme> = {
  si: {
    primary: {
      gradient: 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)',
      solid: '#6366f1',
      light: '#eef2ff',
      border: '#c7d2fe',
      text: '#4338ca',
      hover: '#5b21b6'
    },
    secondary: {
      background: '#f8fafc',
      border: '#e2e8f0',
      text: '#64748b'
    },
    accent: {
      background: '#ddd6fe',
      text: '#5b21b6',
      border: '#c4b5fd'
    },
    status: {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6'
    },
    navigation: {
      background: '#1e293b',
      border: '#334155',
      active: '#6366f1',
      hover: '#475569',
      text: '#cbd5e1',
      activeText: '#ffffff'
    },
    card: {
      background: '#ffffff',
      border: '#e2e8f0',
      shadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
      hoverShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
    }
  },
  
  app: {
    primary: {
      gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
      solid: '#10b981',
      light: '#ecfdf5',
      border: '#a7f3d0',
      text: '#047857',
      hover: '#065f46'
    },
    secondary: {
      background: '#f0fdf4',
      border: '#dcfce7',
      text: '#65a30d'
    },
    accent: {
      background: '#a7f3d0',
      text: '#047857',
      border: '#6ee7b7'
    },
    status: {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#06b6d4'
    },
    navigation: {
      background: '#064e3b',
      border: '#065f46',
      active: '#10b981',
      hover: '#047857',
      text: '#a7f3d0',
      activeText: '#ffffff'
    },
    card: {
      background: '#ffffff',
      border: '#d1fae5',
      shadow: '0 1px 3px 0 rgba(16, 185, 129, 0.1), 0 1px 2px 0 rgba(16, 185, 129, 0.06)',
      hoverShadow: '0 10px 15px -3px rgba(16, 185, 129, 0.1), 0 4px 6px -2px rgba(16, 185, 129, 0.05)'
    }
  },
  
  hybrid: {
    primary: {
      gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
      solid: '#8b5cf6',
      light: '#faf5ff',
      border: '#d8b4fe',
      text: '#7c2d12',
      hover: '#6b21a8'
    },
    secondary: {
      background: '#faf5ff',
      border: '#e9d5ff',
      text: '#7c2d12'
    },
    accent: {
      background: '#ddd6fe',
      text: '#6b21a8',
      border: '#c4b5fd'
    },
    status: {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#8b5cf6'
    },
    navigation: {
      background: '#581c87',
      border: '#6b21a8',
      active: '#8b5cf6',
      hover: '#7c2d12',
      text: '#ddd6fe',
      activeText: '#ffffff'
    },
    card: {
      background: '#ffffff',
      border: '#e9d5ff',
      shadow: '0 1px 3px 0 rgba(139, 92, 246, 0.1), 0 1px 2px 0 rgba(139, 92, 246, 0.06)',
      hoverShadow: '0 10px 15px -3px rgba(139, 92, 246, 0.1), 0 4px 6px -2px rgba(139, 92, 246, 0.05)'
    }
  },
  
  admin: {
    primary: {
      gradient: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
      solid: '#dc2626',
      light: '#fef2f2',
      border: '#fecaca',
      text: '#991b1b',
      hover: '#7f1d1d'
    },
    secondary: {
      background: '#fafafa',
      border: '#e5e5e5',
      text: '#737373'
    },
    accent: {
      background: '#fecaca',
      text: '#991b1b',
      border: '#fca5a5'
    },
    status: {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#6b7280'
    },
    navigation: {
      background: '#7f1d1d',
      border: '#991b1b',
      active: '#dc2626',
      hover: '#a61e1e',
      text: '#fecaca',
      activeText: '#ffffff'
    },
    card: {
      background: '#ffffff',
      border: '#f3f4f6',
      shadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
      hoverShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
    }
  }
};

/**
 * Get theme for a specific role
 */
export const getRoleTheme = (role: UserRole): RoleTheme => {
  return ROLE_THEMES[role] || ROLE_THEMES.si;
};

/**
 * Get CSS variables for a role theme (for use in CSS-in-JS)
 */
export const getRoleThemeVariables = (role: UserRole) => {
  const theme = getRoleTheme(role);
  
  return {
    '--tp-primary-gradient': theme.primary.gradient,
    '--tp-primary-solid': theme.primary.solid,
    '--tp-primary-light': theme.primary.light,
    '--tp-primary-border': theme.primary.border,
    '--tp-primary-text': theme.primary.text,
    '--tp-primary-hover': theme.primary.hover,
    
    '--tp-secondary-bg': theme.secondary.background,
    '--tp-secondary-border': theme.secondary.border,
    '--tp-secondary-text': theme.secondary.text,
    
    '--tp-accent-bg': theme.accent.background,
    '--tp-accent-text': theme.accent.text,
    '--tp-accent-border': theme.accent.border,
    
    '--tp-success': theme.status.success,
    '--tp-warning': theme.status.warning,
    '--tp-error': theme.status.error,
    '--tp-info': theme.status.info,
    
    '--tp-nav-bg': theme.navigation.background,
    '--tp-nav-border': theme.navigation.border,
    '--tp-nav-active': theme.navigation.active,
    '--tp-nav-hover': theme.navigation.hover,
    '--tp-nav-text': theme.navigation.text,
    '--tp-nav-active-text': theme.navigation.activeText,
    
    '--tp-card-bg': theme.card.background,
    '--tp-card-border': theme.card.border,
    '--tp-card-shadow': theme.card.shadow,
    '--tp-card-hover-shadow': theme.card.hoverShadow
  };
};

/**
 * Get background gradients for different sections based on role
 */
export const getRoleSectionBackground = (role: UserRole, section: 'main' | 'sidebar' | 'header' | 'card') => {
  const theme = getRoleTheme(role);
  
  const backgrounds = {
    main: {
      si: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
      app: 'linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%)',
      hybrid: 'linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)',
      admin: 'linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%)'
    },
    sidebar: {
      si: theme.navigation.background,
      app: theme.navigation.background,
      hybrid: theme.navigation.background,
      admin: theme.navigation.background
    },
    header: {
      si: '#ffffff',
      app: '#ffffff',
      hybrid: '#ffffff',
      admin: '#ffffff'
    },
    card: {
      si: theme.card.background,
      app: theme.card.background,
      hybrid: theme.card.background,
      admin: theme.card.background
    }
  };
  
  return backgrounds[section][role];
};

/**
 * Get role-specific button styles
 */
export const getRoleButtonStyles = (role: UserRole, variant: 'primary' | 'secondary' | 'outline' = 'primary') => {
  const theme = getRoleTheme(role);
  
  const styles = {
    primary: {
      background: theme.primary.gradient,
      color: '#ffffff',
      border: 'none',
      ':hover': {
        background: theme.primary.hover,
        transform: 'translateY(-1px)',
        boxShadow: theme.card.hoverShadow
      }
    },
    secondary: {
      background: theme.secondary.background,
      color: theme.secondary.text,
      border: `1px solid ${theme.secondary.border}`,
      ':hover': {
        background: theme.accent.background,
        color: theme.accent.text,
        borderColor: theme.accent.border
      }
    },
    outline: {
      background: 'transparent',
      color: theme.primary.text,
      border: `2px solid ${theme.primary.border}`,
      ':hover': {
        background: theme.primary.light,
        borderColor: theme.primary.solid
      }
    }
  };
  
  return styles[variant];
};

/**
 * Get role-specific card styles
 */
export const getRoleCardStyles = (role: UserRole, variant: 'default' | 'highlight' | 'success' | 'warning' = 'default') => {
  const theme = getRoleTheme(role);
  
  const styles = {
    default: {
      background: theme.card.background,
      border: `1px solid ${theme.card.border}`,
      boxShadow: theme.card.shadow,
      ':hover': {
        boxShadow: theme.card.hoverShadow,
        borderColor: theme.primary.border
      }
    },
    highlight: {
      background: `linear-gradient(135deg, ${theme.primary.light} 0%, ${theme.card.background} 100%)`,
      border: `2px solid ${theme.primary.border}`,
      boxShadow: theme.card.shadow,
      ':hover': {
        boxShadow: theme.card.hoverShadow,
        borderColor: theme.primary.solid
      }
    },
    success: {
      background: `linear-gradient(135deg, #ecfdf5 0%, ${theme.card.background} 100%)`,
      border: `1px solid #a7f3d0`,
      boxShadow: theme.card.shadow,
      ':hover': {
        boxShadow: theme.card.hoverShadow,
        borderColor: theme.status.success
      }
    },
    warning: {
      background: `linear-gradient(135deg, #fffbeb 0%, ${theme.card.background} 100%)`,
      border: `1px solid #fde68a`,
      boxShadow: theme.card.shadow,
      ':hover': {
        boxShadow: theme.card.hoverShadow,
        borderColor: theme.status.warning
      }
    }
  };
  
  return styles[variant];
};

/**
 * Create a React hook for role-based theming
 */
export const useRoleTheme = (role: UserRole) => {
  const theme = getRoleTheme(role);
  
  return {
    theme,
    getVariables: () => getRoleThemeVariables(role),
    getSectionBackground: (section: 'main' | 'sidebar' | 'header' | 'card') => 
      getRoleSectionBackground(role, section),
    getButtonStyles: (variant: 'primary' | 'secondary' | 'outline' = 'primary') => 
      getRoleButtonStyles(role, variant),
    getCardStyles: (variant: 'default' | 'highlight' | 'success' | 'warning' = 'default') => 
      getRoleCardStyles(role, variant),
    
    // Utility functions
    applyThemeToElement: (element: HTMLElement) => {
      const variables = getRoleThemeVariables(role);
      Object.entries(variables).forEach(([key, value]) => {
        element.style.setProperty(key, value);
      });
    },
    
    // CSS class helpers
    primaryButton: `bg-gradient-to-r from-${role === 'si' ? 'indigo' : role === 'app' ? 'green' : role === 'hybrid' ? 'purple' : 'red'}-600 to-${role === 'si' ? 'blue' : role === 'app' ? 'emerald' : role === 'hybrid' ? 'indigo' : 'pink'}-600 hover:from-${role === 'si' ? 'indigo' : role === 'app' ? 'green' : role === 'hybrid' ? 'purple' : 'red'}-700 hover:to-${role === 'si' ? 'blue' : role === 'app' ? 'emerald' : role === 'hybrid' ? 'indigo' : 'pink'}-700 text-white font-bold py-2 px-4 rounded-xl transition-all duration-200 transform hover:scale-105`,
    
    outlineButton: `border-2 border-${role === 'si' ? 'indigo' : role === 'app' ? 'green' : role === 'hybrid' ? 'purple' : 'red'}-300 text-${role === 'si' ? 'indigo' : role === 'app' ? 'green' : role === 'hybrid' ? 'purple' : 'red'}-700 hover:bg-${role === 'si' ? 'indigo' : role === 'app' ? 'green' : role === 'hybrid' ? 'purple' : 'red'}-50 font-medium py-2 px-4 rounded-xl transition-all duration-200`,
    
    cardBorder: `border border-${role === 'si' ? 'indigo' : role === 'app' ? 'green' : role === 'hybrid' ? 'purple' : 'red'}-100 hover:border-${role === 'si' ? 'indigo' : role === 'app' ? 'green' : role === 'hybrid' ? 'purple' : 'red'}-300`
  };
};

export default {
  ROLE_THEMES,
  getRoleTheme,
  getRoleThemeVariables,
  getRoleSectionBackground,
  getRoleButtonStyles,
  getRoleCardStyles,
  useRoleTheme
};
