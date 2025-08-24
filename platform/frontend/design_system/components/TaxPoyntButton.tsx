/**
 * TaxPoynt Button Component
 * =========================
 * Extracted and enhanced from legacy Button.tsx with Nigerian mobile optimizations
 * Supports all platform needs: Landing page + Auth + Dashboards + Business interfaces
 */

import React, { forwardRef, ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

// Complete button variants system from legacy
const taxPoyntButtonVariants = cva(
  // Base styles - Enhanced with mobile-first + Nigerian optimizations
  "inline-flex items-center justify-center font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none active:scale-95",
  {
    variants: {
      variant: {
        // Primary - Main CTA buttons (landing page, auth)
        primary: "bg-primary text-white hover:bg-primary/90 shadow-sm hover:shadow-md font-semibold",
        
        // Secondary - Supporting actions
        secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200 border border-gray-300 font-medium",
        
        // Destructive - Delete/remove actions  
        destructive: "bg-error text-white hover:bg-error/90 shadow-sm hover:shadow-md font-semibold",
        
        // Outline - Secondary CTAs (landing page "Learn More")
        outline: "border-2 border-gray-300 bg-transparent hover:bg-gray-50 text-gray-700 font-medium hover:border-primary hover:text-primary",
        
        // Ghost - Minimal actions (navigation, dropdowns)
        ghost: "hover:bg-gray-100 text-gray-700 hover:text-gray-900",
        
        // Link - Text links that look like buttons
        link: "text-primary underline-offset-4 hover:underline font-medium hover:text-primary/80",

        // Success - Positive actions (dashboards)
        success: "bg-success text-white hover:bg-success/90 shadow-sm hover:shadow-md font-semibold",

        // Warning - Caution actions (dashboards)  
        warning: "bg-warning text-white hover:bg-warning/90 shadow-sm hover:shadow-md font-semibold",

        // Nigerian Green - Special branding (landing page hero)
        nigerian: "bg-nigerian-green text-white hover:bg-nigerian-green-dark shadow-sm hover:shadow-md font-semibold",
      },
      size: {
        // Small - Dashboard actions, mobile secondary
        sm: "h-8 px-3 text-sm rounded-md min-w-[64px]",
        
        // Default - Standard buttons across platform  
        default: "h-10 px-4 text-base rounded-lg min-w-[80px]",
        
        // Large - Primary CTAs, hero buttons, mobile primary
        lg: "h-12 px-6 text-lg rounded-lg min-w-[120px]",
        
        // Extra Large - Landing page hero CTAs
        xl: "h-14 px-8 text-xl rounded-xl min-w-[140px]",
        
        // Icon only - Square buttons for icons
        icon: "h-10 w-10 rounded-lg",
        
        // Touch - Mobile-optimized (44px minimum for Nigerian users)
        touch: "h-11 px-6 text-base rounded-lg min-w-[88px]",
        
        // Touch Large - Mobile hero CTAs  
        touchLg: "h-12 px-8 text-lg rounded-lg min-w-[120px]",
      },
      fullWidth: {
        true: "w-full",
        false: "",
      },
      loading: {
        true: "cursor-not-allowed",
        false: "",
      }
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
      fullWidth: false,
      loading: false,
    },
  }
);

export interface TaxPoyntButtonProps 
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof taxPoyntButtonVariants> {
  asChild?: boolean;
  loading?: boolean;
  loadingText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const TaxPoyntButton = forwardRef<HTMLButtonElement, TaxPoyntButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    fullWidth,
    loading = false,
    loadingText,
    leftIcon,
    rightIcon,
    children,
    disabled,
    ...props 
  }, ref) => {
    const isDisabled = loading || disabled;

    return (
      <button
        className={taxPoyntButtonVariants({ 
          variant, 
          size, 
          fullWidth,
          loading,
          className 
        })}
        ref={ref}
        disabled={isDisabled}
        {...props}
      >
        {loading && (
          <div className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent align-[-0.125em]" />
        )}
        
        {!loading && leftIcon && (
          <span className="mr-2 inline-flex">{leftIcon}</span>
        )}
        
        <span>
          {loading && loadingText ? loadingText : children}
        </span>
        
        {!loading && rightIcon && (
          <span className="ml-2 inline-flex">{rightIcon}</span>
        )}
      </button>
    );
  }
);

TaxPoyntButton.displayName = "TaxPoyntButton";

export { TaxPoyntButton, taxPoyntButtonVariants };

// Specialized button variants for common use cases

// Hero CTA Button - Landing page primary actions
interface HeroCTAButtonProps extends Omit<TaxPoyntButtonProps, 'variant' | 'size'> {
  variant?: 'primary' | 'nigerian';
}

export const HeroCTAButton: React.FC<HeroCTAButtonProps> = ({ 
  variant = 'primary',
  className = '',
  ...props 
}) => (
  <TaxPoyntButton
    variant={variant}
    size="xl"
    className={`shadow-2xl hover:shadow-green-500/50 transition-all duration-300 hover:scale-105 transform ${className}`}
    {...props}
  />
);

// Mobile Touch Button - Nigerian mobile optimized
export const MobileTouchButton: React.FC<TaxPoyntButtonProps> = ({ 
  size = 'touch',
  className = '',
  ...props 
}) => (
  <TaxPoyntButton
    size={size}
    className={`shadow-sm hover:shadow-md transition-all duration-200 ${className}`}
    {...props}
  />
);

// Dashboard Action Button - For business interfaces  
export const DashboardButton: React.FC<TaxPoyntButtonProps> = ({
  variant = 'secondary',
  size = 'default', 
  className = '',
  ...props
}) => (
  <TaxPoyntButton
    variant={variant}
    size={size}
    className={`transition-all duration-200 hover:shadow-sm ${className}`}
    {...props}
  />
);

// Auth Form Button - For login/signup forms
export const AuthFormButton: React.FC<TaxPoyntButtonProps> = ({
  variant = 'primary',
  size = 'lg',
  fullWidth = true,
  className = '',
  ...props
}) => (
  <TaxPoyntButton
    variant={variant}
    size={size}
    fullWidth={fullWidth}
    className={`font-semibold ${className}`}
    {...props}
  />
);