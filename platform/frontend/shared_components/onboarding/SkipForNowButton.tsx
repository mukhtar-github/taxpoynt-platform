/**
 * Skip for Now Button Component
 * ============================
 * 
 * Standardized "Skip for Now" button for consistent styling and behavior
 * across all onboarding flows. Provides improved visibility and accessibility.
 * 
 * Features:
 * - Consistent styling with improved contrast
 * - Mobile-optimized touch targets
 * - Accessibility support with proper ARIA labels
 * - Customizable text and behavior
 * - Loading states and disabled support
 * - Analytics tracking for skip events
 */

import React from 'react';
import { TaxPoyntButton } from '../../design_system/components/TaxPoyntButton';
import { ArrowRight, Clock } from 'lucide-react';

interface SkipForNowButtonProps {
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  text?: string;
  description?: string;
  showIcon?: boolean;
  variant?: 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'default' | 'lg' | 'touch';
  fullWidth?: boolean;
  className?: string;
  analyticsEvent?: string; // For tracking skip events
  estimatedTime?: string; // e.g., "5 minutes" - shows what they're skipping
}

export const SkipForNowButton: React.FC<SkipForNowButtonProps> = ({
  onClick,
  disabled = false,
  loading = false,
  text = "Skip for Now",
  description,
  showIcon = true,
  variant = "secondary",
  size = "default",
  fullWidth = false,
  className = "",
  analyticsEvent,
  estimatedTime
}) => {

  const handleClick = () => {
    // Track analytics if event provided
    if (analyticsEvent) {
      // In a real implementation, this would send to analytics service
      console.log('📊 Skip button clicked:', analyticsEvent);
    }
    
    onClick();
  };

  const buttonContent = (
    <>
      {loading ? (
        <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent mr-2" />
      ) : showIcon ? (
        <ArrowRight className="h-4 w-4 mr-2" />
      ) : null}
      {loading ? 'Please wait...' : text}
    </>
  );

  return (
    <div className={`${fullWidth ? 'w-full' : ''} ${className}`}>
      <TaxPoyntButton
        variant={variant}
        size={size}
        onClick={handleClick}
        disabled={disabled || loading}
        fullWidth={fullWidth}
        className={`
          transition-all duration-200 
          ${variant === 'secondary' ? 'hover:shadow-md' : ''}
          ${size === 'touch' ? 'min-h-[44px]' : ''}
        `}
        aria-label={description ? `${text}: ${description}` : text}
      >
        {buttonContent}
      </TaxPoyntButton>
      
      {/* Optional description or time estimate */}
      {(description || estimatedTime) && (
        <div className="mt-2 text-center">
          {description && (
            <p className="text-sm text-gray-600 mb-1">
              {description}
            </p>
          )}
          {estimatedTime && (
            <div className="flex items-center justify-center text-xs text-gray-500">
              <Clock className="h-3 w-3 mr-1" />
              <span>Setup takes about {estimatedTime}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Specialized Skip Button Variants
 */

// Quick skip with minimal styling
export const QuickSkipButton: React.FC<Pick<SkipForNowButtonProps, 'onClick' | 'disabled' | 'className'>> = ({
  onClick,
  disabled = false,
  className = ""
}) => (
  <SkipForNowButton
    onClick={onClick}
    disabled={disabled}
    text="Skip"
    variant="ghost"
    size="sm"
    showIcon={false}
    className={className}
  />
);

// Skip with setup time indication
export const SkipWithTimeButton: React.FC<SkipForNowButtonProps> = (props) => (
  <SkipForNowButton
    {...props}
    description="You can set this up later from your dashboard"
    variant="secondary"
  />
);

// Mobile-optimized skip button
export const MobileSkipButton: React.FC<SkipForNowButtonProps> = (props) => (
  <SkipForNowButton
    {...props}
    size="touch"
    fullWidth={true}
    variant="secondary"
    className="sm:w-auto sm:fullWidth-false"
  />
);

// Skip button for critical steps (more prominent warning)
export const CriticalSkipButton: React.FC<SkipForNowButtonProps & { warningMessage?: string }> = ({
  warningMessage = "This step is recommended for optimal experience",
  ...props
}) => (
  <div className="space-y-2">
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
      <div className="flex items-start">
        <div className="text-yellow-600 mr-2 mt-0.5">⚠️</div>
        <p className="text-sm text-yellow-800">{warningMessage}</p>
      </div>
    </div>
    <SkipForNowButton
      {...props}
      variant="outline"
      description="Continue anyway - you can complete this later"
    />
  </div>
);

export default SkipForNowButton;
