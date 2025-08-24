/**
 * TaxPoynt Input Component
 * ========================
 * Extracted and enhanced from legacy Input.tsx
 * Supports auth forms, dashboard forms, business interface forms
 */

import React, { InputHTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const taxPoyntInputVariants = cva(
  // Base styles from legacy Input.tsx
  "flex w-full rounded-lg border bg-white px-3 py-2 text-base ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200",
  {
    variants: {
      variant: {
        default: "border-gray-300 focus-visible:border-primary",
        error: "border-error focus-visible:ring-error bg-error/5",
        success: "border-success focus-visible:ring-success bg-success/5",
        warning: "border-warning focus-visible:ring-warning bg-warning/5",
      },
      size: {
        sm: "h-8 px-2 py-1 text-sm rounded-md",
        default: "h-10 px-3 py-2 text-base rounded-lg",
        lg: "h-12 px-4 py-3 text-lg rounded-lg",
        touch: "h-11 px-4 py-3 text-base rounded-lg", // Nigerian mobile optimized
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface TaxPoyntInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof taxPoyntInputVariants> {
  error?: boolean;
  success?: boolean;
  warning?: boolean;
  label?: string;
  helperText?: string;
  errorText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

const TaxPoyntInput = forwardRef<HTMLInputElement, TaxPoyntInputProps>(
  ({ 
    className, 
    variant, 
    size,
    error = false,
    success = false,
    warning = false,
    label,
    helperText,
    errorText,
    leftIcon,
    rightIcon,
    fullWidth = true,
    ...props 
  }, ref) => {
    // Determine variant based on state
    let finalVariant = variant;
    if (error) finalVariant = "error";
    else if (success) finalVariant = "success";
    else if (warning) finalVariant = "warning";

    const inputClasses = taxPoyntInputVariants({ 
      variant: finalVariant, 
      size, 
      className: fullWidth ? 'w-full' : className 
    });

    return (
      <div className={fullWidth ? 'w-full' : ''}>
        {/* Label */}
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {label}
          </label>
        )}

        {/* Input Container */}
        <div className="relative">
          {/* Left Icon */}
          {leftIcon && (
            <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
              {leftIcon}
            </div>
          )}

          {/* Input */}
          <input
            className={`${inputClasses} ${leftIcon ? 'pl-10' : ''} ${rightIcon ? 'pr-10' : ''}`}
            ref={ref}
            {...props}
          />

          {/* Right Icon */}
          {rightIcon && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400">
              {rightIcon}
            </div>
          )}
        </div>

        {/* Helper/Error Text */}
        {(helperText || errorText) && (
          <p className={`mt-2 text-sm ${
            error || errorText ? 'text-error' : 
            success ? 'text-success' : 
            warning ? 'text-warning' : 
            'text-gray-600'
          }`}>
            {errorText || helperText}
          </p>
        )}
      </div>
    );
  }
);

TaxPoyntInput.displayName = "TaxPoyntInput";

export { TaxPoyntInput, taxPoyntInputVariants };

// Specialized input variants

// Auth Input - For login/signup forms
export const AuthInput: React.FC<TaxPoyntInputProps> = ({
  size = 'lg',
  className = '',
  ...props
}) => (
  <TaxPoyntInput
    size={size}
    className={`font-medium ${className}`}
    {...props}
  />
);

// Mobile Input - Nigerian mobile optimized
export const MobileInput: React.FC<TaxPoyntInputProps> = ({
  size = 'touch',
  className = '',
  ...props
}) => (
  <TaxPoyntInput
    size={size}
    className={`transition-all duration-200 ${className}`}
    {...props}
  />
);

// Dashboard Input - For business interface forms
export const DashboardInput: React.FC<TaxPoyntInputProps> = ({
  size = 'default',
  className = '',
  ...props
}) => (
  <TaxPoyntInput
    size={size}
    className={`bg-gray-50 border-gray-200 hover:bg-white hover:border-gray-300 transition-all ${className}`}
    {...props}
  />
);