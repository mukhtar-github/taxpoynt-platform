/**
 * Logo Component
 * ==============
 * TaxPoynt Logo with sparkling radiant effects
 * Maintains the existing sparkling animation and glow effects
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
      <div className={`relative group ${className}`}>
        {/* Sparkling Effect */}
        <div className="absolute -inset-2 opacity-75 group-hover:opacity-100 transition-opacity duration-300">
          <div className="absolute top-0 left-1/4 w-1 h-1 bg-blue-400 rounded-full animate-ping" style={{ animationDelay: '0s', animationDuration: '2s' }}></div>
          <div className="absolute top-2 right-1/4 w-1.5 h-1.5 bg-green-400 rounded-full animate-ping" style={{ animationDelay: '0.5s', animationDuration: '2.5s' }}></div>
          <div className="absolute bottom-1 left-1/2 w-1 h-1 bg-blue-500 rounded-full animate-ping" style={{ animationDelay: '1s', animationDuration: '3s' }}></div>
          <div className="absolute top-1/2 right-0 w-0.5 h-0.5 bg-green-500 rounded-full animate-ping" style={{ animationDelay: '1.5s', animationDuration: '2s' }}></div>
        </div>
        <img 
          src="/logo.svg" 
          alt="TaxPoynt Logo" 
          className={`${sizeClasses[size]} w-auto relative z-10`}
        />
      </div>
    );
  }

  return (
    <div className={`relative group ${className}`}>
      {/* Sparkling Effect */}
      <div className="absolute -inset-2 opacity-75 group-hover:opacity-100 transition-opacity duration-300">
        <div className="absolute top-0 left-1/4 w-1 h-1 bg-blue-400 rounded-full animate-ping" style={{ animationDelay: '0s', animationDuration: '2s' }}></div>
        <div className="absolute top-2 right-1/4 w-1.5 h-1.5 bg-green-400 rounded-full animate-ping" style={{ animationDelay: '0.5s', animationDuration: '2.5s' }}></div>
        <div className="absolute bottom-1 left-1/2 w-1 h-1 bg-blue-500 rounded-full animate-ping" style={{ animationDelay: '1s', animationDuration: '3s' }}></div>
        <div className="absolute top-1/2 right-0 w-0.5 h-0.5 bg-green-500 rounded-full animate-ping" style={{ animationDelay: '1.5s', animationDuration: '2s' }}></div>
      </div>
      
      <div className="flex items-center space-x-3 relative z-10" style={{ 
        color: '#3B82F6', 
        textShadow: '0 0 10px rgba(59, 130, 246, 0.3), 0 0 20px rgba(59, 130, 246, 0.1)',
        textRendering: 'optimizeLegibility', 
        WebkitFontSmoothing: 'antialiased' 
      }}>
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
    </div>
  );
};

export default Logo;