/**
 * TaxPoynt Form Field Component
 * =============================
 * Enhanced form field with persistence indicators and cross-form data sharing
 * Shows visual cues when fields are pre-filled from other forms
 */

import React, { useState, useEffect } from 'react';
import { 
  getPreFilledFieldStyles, 
  getPreFilledHelperText,
  CrossFormDataManager 
} from '../../shared_components/utils/formPersistence';

export interface FormFieldProps {
  label: string;
  name: string;
  type?: 'text' | 'email' | 'password' | 'tel' | 'select' | 'textarea';
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  helperText?: string;
  options?: Array<{ value: string; label: string }>;
  rows?: number;
  className?: string;
  showPersistenceIndicator?: boolean;
  autoPopulateFromShared?: boolean;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  name,
  type = 'text',
  value,
  onChange,
  placeholder,
  required = false,
  disabled = false,
  error,
  helperText,
  options = [],
  rows = 3,
  className = '',
  showPersistenceIndicator = true,
  autoPopulateFromShared = true
}) => {
  const [isPreFilled, setIsPreFilled] = useState(false);
  const [preFillSource, setPreFillSource] = useState<'shared' | 'persisted' | null>(null);
  const [showHelper, setShowHelper] = useState(false);

  // Check if field should be auto-populated from shared data
  useEffect(() => {
    if (autoPopulateFromShared && (!value || value === '') && CrossFormDataManager.hasSharedData(name)) {
      const sharedValue = CrossFormDataManager.getSharedField(name);
      if (sharedValue) {
        onChange(sharedValue);
        setIsPreFilled(true);
        setPreFillSource('shared');
        setShowHelper(true);
        
        // Hide helper after 5 seconds
        setTimeout(() => setShowHelper(false), 5000);
      }
    }
  }, [name, value, autoPopulateFromShared, onChange]);

  // Check if current value is from shared data
  useEffect(() => {
    if (showPersistenceIndicator && value && value !== '') {
      const sharedValue = CrossFormDataManager.getSharedField(name);
      if (sharedValue === value) {
        setIsPreFilled(true);
        setPreFillSource('shared');
      } else {
        setIsPreFilled(false);
        setPreFillSource(null);
      }
    }
  }, [name, value, showPersistenceIndicator]);

  const getFieldStyles = () => {
    const baseStyles = 'w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200';
    
    if (error) {
      return `${baseStyles} border-red-500 bg-red-50`;
    }
    
    if (isPreFilled && showPersistenceIndicator) {
      return `${baseStyles} ${getPreFilledFieldStyles(true, preFillSource || 'shared')}`;
    }
    
    return `${baseStyles} border-gray-300 bg-white`;
  };

  const renderInput = () => {
    const commonProps = {
      name,
      value,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => onChange(e.target.value),
      placeholder,
      required,
      disabled,
      className: getFieldStyles()
    };

    switch (type) {
      case 'select':
        return (
          <select {...commonProps}>
            <option value="">{placeholder || `Select ${label.toLowerCase()}`}</option>
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'textarea':
        return (
          <textarea 
            {...commonProps} 
            rows={rows}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onChange(e.target.value)}
          />
        );

      default:
        return (
          <input 
            {...commonProps} 
            type={type}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
          />
        );
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Label */}
      <label htmlFor={name} className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {/* Input Field */}
      <div className="relative">
        {renderInput()}
        
        {/* Persistence Indicator */}
        {isPreFilled && showPersistenceIndicator && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <div className="flex items-center space-x-1">
              {preFillSource === 'shared' && (
                <span className="text-green-500 text-sm" title="Data from other forms">
                  🔗
                </span>
              )}
              {preFillSource === 'persisted' && (
                <span className="text-blue-500 text-sm" title="Previously entered data">
                  💾
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Helper Text */}
      {(helperText || (isPreFilled && showHelper)) && (
        <div className="text-sm text-gray-500 flex items-center space-x-2">
          {helperText && <span>{helperText}</span>}
          {isPreFilled && showHelper && (
            <span className="text-green-600 font-medium">
              ✓ {getPreFilledHelperText(preFillSource || 'shared')}
            </span>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="text-sm text-red-600 flex items-center">
          <span className="mr-1">❌</span>
          {error}
        </div>
      )}

      {/* Persistence Status */}
      {isPreFilled && showPersistenceIndicator && (
        <div className="text-xs text-gray-500 flex items-center">
          <span className="mr-1">
            {preFillSource === 'shared' ? '🔗' : '💾'}
          </span>
          {preFillSource === 'shared' 
            ? 'Auto-filled from other forms' 
            : 'Previously entered data'
          }
        </div>
      )}
    </div>
  );
};

export default FormField;
