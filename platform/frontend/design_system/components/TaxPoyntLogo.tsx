/**
 * TaxPoynt Logo Component
 * ======================
 * Professional logo component with multiple variants and sizes
 * Nigerian-optimized with sparkling effects and professional branding
 */

import React, { forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const taxPoyntLogoVariants = cva(
  "inline-flex items-center transition-all duration-300",
  {
    variants: {
      variant: {
        full: "flex-col sm:flex-row space-y-1 sm:space-y-0 sm:space-x-3",
        compact: "flex-row space-x-2",
        iconOnly: "justify-center",
        textOnly: "font-bold",
      },
      size: {
        sm: "text-lg",
        default: "text-xl",
        lg: "text-2xl md:text-3xl",
        xl: "text-3xl md:text-4xl",
        hero: "text-4xl md:text-5xl",
      },
      theme: {
        light: "text-primary",
        dark: "text-white",
        gradient: "bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent",
        glow: "text-primary drop-shadow-lg",
      }
    },
    defaultVariants: {
      variant: "full",
      size: "default",
      theme: "light",
    },
  }
);

export interface TaxPoyntLogoProps extends VariantProps<typeof taxPoyntLogoVariants> {
  showTagline?: boolean;
  showIcon?: boolean;
  className?: string;
  onClick?: () => void;
  sparkles?: boolean;
}

const TaxPoyntLogo = forwardRef<HTMLDivElement, TaxPoyntLogoProps>(
  ({ 
    variant = "full",
    size = "default", 
    theme = "light",
    showTagline = false,
    showIcon = true,
    className,
    onClick,
    sparkles = false,
    ...props 
  }, ref) => {
    
    const logoClasses = taxPoyntLogoVariants({ variant, size, theme, className });
    
    // Icon component
    const LogoIcon = () => (
      <div className={`
        relative rounded-lg flex items-center justify-center
        ${size === 'sm' ? 'w-7 h-7' : ''}
        ${size === 'default' ? 'w-8 h-8' : ''}
        ${size === 'lg' ? 'w-10 h-10 md:w-12 md:h-12' : ''}
        ${size === 'xl' ? 'w-12 h-12 md:w-14 md:h-14' : ''}
        ${size === 'hero' ? 'w-14 h-14 md:w-16 md:h-16' : ''}
        ${theme === 'dark' ? 'bg-primary' : 'bg-primary'}
      `}>
        <span className={`
          text-white font-bold
          ${size === 'sm' ? 'text-sm' : ''}
          ${size === 'default' ? 'text-base' : ''}
          ${size === 'lg' ? 'text-lg md:text-xl' : ''}
          ${size === 'xl' ? 'text-xl md:text-2xl' : ''}
          ${size === 'hero' ? 'text-2xl md:text-3xl' : ''}
        `}>
          T
        </span>
      </div>
    );

    // Text component
    const LogoText = () => (
      <div className="flex flex-col">
        <span className={`
          font-bold leading-tight
          ${size === 'sm' ? 'text-lg' : ''}
          ${size === 'default' ? 'text-xl' : ''}
          ${size === 'lg' ? 'text-2xl md:text-3xl' : ''}
          ${size === 'xl' ? 'text-3xl md:text-4xl' : ''}
          ${size === 'hero' ? 'text-4xl md:text-5xl' : ''}
        `}>
          TaxPoynt
        </span>
        {showTagline && (
          <span className={`
            font-medium opacity-70
            ${size === 'sm' ? 'text-xs' : ''}
            ${size === 'default' ? 'text-sm' : ''}
            ${size === 'lg' ? 'text-sm md:text-base' : ''}
            ${size === 'xl' ? 'text-base md:text-lg' : ''}
            ${size === 'hero' ? 'text-lg md:text-xl' : ''}
            ${theme === 'dark' ? 'text-blue-300' : 'text-primary-600'}
          `}>
            Nigerian E-invoice Leader
          </span>
        )}
      </div>
    );

    return (
      <div
        ref={ref}
        className={`relative group ${onClick ? 'cursor-pointer' : ''}`}
        onClick={onClick}
        {...props}
      >
        {/* Sparkling Effect */}
        {sparkles && (
          <div className="absolute -inset-2 opacity-75 group-hover:opacity-100 transition-opacity duration-300">
            <div className="absolute top-0 left-1/4 w-1 h-1 bg-blue-400 rounded-full animate-ping" style={{ animationDelay: '0s', animationDuration: '2s' }}></div>
            <div className="absolute top-2 right-1/4 w-1.5 h-1.5 bg-green-400 rounded-full animate-ping" style={{ animationDelay: '0.5s', animationDuration: '2.5s' }}></div>
            <div className="absolute bottom-1 left-1/2 w-1 h-1 bg-blue-500 rounded-full animate-ping" style={{ animationDelay: '1s', animationDuration: '3s' }}></div>
            <div className="absolute top-1/2 right-0 w-0.5 h-0.5 bg-green-500 rounded-full animate-ping" style={{ animationDelay: '1.5s', animationDuration: '2s' }}></div>
          </div>
        )}

        {/* Logo Content */}
        <div className={logoClasses}>
          {variant === 'iconOnly' && showIcon && <LogoIcon />}
          {variant === 'textOnly' && <LogoText />}
          {(variant === 'full' || variant === 'compact') && (
            <>
              {showIcon && <LogoIcon />}
              <LogoText />
            </>
          )}
        </div>
      </div>
    );
  }
);

TaxPoyntLogo.displayName = "TaxPoyntLogo";

export { TaxPoyntLogo, taxPoyntLogoVariants };

// Specialized logo variants for different contexts

// Landing Page Logo - with sparkles and glow
export const LandingLogo: React.FC<Omit<TaxPoyntLogoProps, 'sparkles' | 'theme'>> = (props) => (
  <TaxPoyntLogo sparkles={true} theme="glow" {...props} />
);

// Navigation Logo - compact for header use
export const NavLogo: React.FC<Omit<TaxPoyntLogoProps, 'variant' | 'size'>> = (props) => (
  <TaxPoyntLogo variant="compact" size="default" {...props} />
);

// Auth Logo - larger for auth pages
export const AuthLogo: React.FC<Omit<TaxPoyntLogoProps, 'size'>> = (props) => (
  <TaxPoyntLogo size="lg" {...props} />
);

// Footer Logo - minimal for footer
export const FooterLogo: React.FC<Omit<TaxPoyntLogoProps, 'variant' | 'size'>> = (props) => (
  <TaxPoyntLogo variant="compact" size="sm" {...props} />
);