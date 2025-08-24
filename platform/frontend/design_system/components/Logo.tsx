/**
 * Logo Component
 * ==============
 * Clean, professional TaxPoynt Logo component
 * Uses real logo.svg without any unprofessional effects
 */

import React from 'react';

export interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'icon' | 'full';
  showTagline?: boolean;
  color?: 'default' | 'white';
  className?: string;
}

export const Logo: React.FC<LogoProps> = ({
  size = 'md',
  variant = 'full',
  showTagline = true,
  color = 'default',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'h-6',
    md: 'h-8',
    lg: 'h-10', 
    xl: 'h-12'
  };

  const textColor = color === 'white' ? 'text-white' : 'text-blue-400';
  const taglineColor = color === 'white' ? 'text-gray-200' : 'text-blue-300';

  if (variant === 'icon') {
    return (
      <img 
        src="/logo.svg" 
        alt="TaxPoynt Logo" 
        className={`${sizeClasses[size]} w-auto ${className}`}
      />
    );
  }

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <img 
        src="/logo.svg" 
        alt="TaxPoynt Logo" 
        className={`${sizeClasses[size]} w-auto`}
      />
      <div>
        <div className={`font-bold ${textColor} ${
          size === 'xl' ? 'text-2xl' : 
          size === 'lg' ? 'text-xl' : 
          size === 'md' ? 'text-lg' : 'text-base'
        }`}>
          TaxPoynt
        </div>
        {showTagline && (
          <div className={`text-sm ${taglineColor}`}>
            Secure E-invoicing Solution
          </div>
        )}
      </div>
    </div>
  );
};

export default Logo;