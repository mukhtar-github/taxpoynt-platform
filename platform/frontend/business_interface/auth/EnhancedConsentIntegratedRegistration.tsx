/**
 * Enhanced Consent-Integrated Registration
 * ========================================
 * Professional upgrade of ConsentIntegratedRegistration using our refined design system
 * while maintaining full NDPR compliance and sophisticated consent management
 */

import React, { useState, useEffect } from 'react';
import { AuthLayout } from '../../shared_components/auth/AuthLayout';
import { useFormPersistence, CrossFormDataManager } from '../../shared_components/utils/formPersistence';
import { TaxPoyntButton, TaxPoyntInput } from '../../design_system';
import { secureLogger } from '../../shared_components/utils/secureLogger';
import { 
  TYPOGRAPHY_STYLES, 
  combineStyles, 
  ACCESSIBILITY_PATTERNS,
  getSectionBackground 
} from '../../design_system/style-utilities';
import { MonoConsentIntegration } from '../../si_interface/components/financial_systems/banking_integration/MonoConsentIntegration';

// Import the existing consent items and registration logic
interface ConsentItem {
  id: string;
  category: 'financial' | 'operational' | 'marketing' | 'analytics';
  title: string;
  description: string;
  required: boolean;
  legalBasis: string;
  dataTypes: string[];
  retentionPeriod: string;
  thirdParties?: string[];
}

const consentItems: ConsentItem[] = [
  {
    id: 'financial_data_access',
    category: 'financial',
    title: 'Financial System Data Access',
    description: 'Access to your ERP, accounting, and business system data for invoice generation and FIRS compliance.',
    required: true,
    legalBasis: 'Contract performance - Required for e-invoicing service delivery',
    dataTypes: ['Transaction records', 'Invoice data', 'Customer information', 'Product details'],
    retentionPeriod: '7 years (FIRS compliance requirement)',
    thirdParties: ['FIRS (Federal Inland Revenue Service)', 'Central Bank of Nigeria (for verification)']
  },
  {
    id: 'banking_integration_intent',
    category: 'financial',
    title: 'Banking Integration (Optional)',
    description: 'Intent to connect banking systems for automated transaction processing. Detailed banking consent will be requested separately.',
    required: false,
    legalBasis: 'Consent - Enhanced automation features',
    dataTypes: ['Banking integration preferences', 'Service configuration'],
    retentionPeriod: 'Duration of service agreement',
    thirdParties: ['Open Banking Providers (when selected)']
  },
  {
    id: 'compliance_monitoring',
    category: 'operational',
    title: 'Compliance Monitoring',
    description: 'Monitor your invoicing compliance status and provide automated FIRS submissions.',
    required: true,
    legalBasis: 'Legal obligation - FIRS e-invoicing compliance',
    dataTypes: ['Compliance status', 'Submission records', 'Audit trails'],
    retentionPeriod: '10 years (FIRS audit requirement)',
    thirdParties: ['FIRS (Federal Inland Revenue Service)']
  },
  {
    id: 'system_integration',
    category: 'operational',
    title: 'Business System Integration',
    description: 'Connect and synchronize data with your ERP, CRM, POS, and other business systems.',
    required: true,
    legalBasis: 'Contract performance - Core service functionality',
    dataTypes: ['System configurations', 'API credentials', 'Integration logs'],
    retentionPeriod: 'Duration of service agreement',
    thirdParties: ['Your selected ERP/CRM vendors (for data synchronization)']
  },
  {
    id: 'service_improvement',
    category: 'analytics',
    title: 'Service Improvement Analytics',
    description: 'Analyze usage patterns to improve our platform and provide better recommendations.',
    required: false,
    legalBasis: 'Legitimate interest - Service improvement',
    dataTypes: ['Usage analytics', 'Performance metrics', 'Feature utilization'],
    retentionPeriod: '2 years',
  },
  {
    id: 'marketing_communications',
    category: 'marketing',
    title: 'Marketing Communications',
    description: 'Receive updates about new features, Nigerian tax law changes, and TaxPoynt news.',
    required: false,
    legalBasis: 'Consent - Marketing communications',
    dataTypes: ['Contact preferences', 'Communication history'],
    retentionPeriod: 'Until consent withdrawn',
  }
];

export interface EnhancedConsentIntegratedRegistrationProps {
  onCompleteRegistration: (registrationData: any) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

export const EnhancedConsentIntegratedRegistration: React.FC<EnhancedConsentIntegratedRegistrationProps> = ({
  onCompleteRegistration,
  isLoading = false,
  error
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  // Form persistence setup
  const formPersistence = useFormPersistence({
    storageKey: 'taxpoynt_registration_form',
    persistent: false, // Use sessionStorage for privacy
    excludeFields: ['password', 'confirmPassword', 'terms_accepted', 'privacy_accepted'],
    autoSaveInterval: 3000 // Save every 3 seconds
  });

  const [formData, setFormData] = useState<any>({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    phone: '',
    business_name: '',
    business_type: '',
    rc_number: '',
    address: '',
    state: '',
    lga: '',
    service_package: 'si',  // Changed from 'system_integrator' to match backend expectation
    terms_accepted: false,
    privacy_accepted: false,
    marketing_consent: false
  });

  // Separate state for critical consent fields to prevent accidental reset
  const [criticalConsents, setCriticalConsents] = useState({
    terms_accepted: false,
    privacy_accepted: false
  });
  
  const [consentChoices, setConsentChoices] = useState<Record<string, boolean>>({});
  const [fieldErrors, setFieldErrors] = useState<{[key: string]: string}>({});
  const [showBankingConsent, setShowBankingConsent] = useState(false);
  const [bankingConsentComplete, setBankingConsentComplete] = useState(false);

  const steps = [
    { id: 'account', title: 'Account Setup', description: 'Create your TaxPoynt account' },
    { id: 'business', title: 'Business Details', description: 'Tell us about your business' },
    { id: 'consent', title: 'Data & Privacy', description: 'Control how we use your data' },
    { id: 'complete', title: 'Complete', description: 'Finalize your registration' }
  ];

  // Initialize form with persistence and shared data
  useEffect(() => {
    // Load saved form data and merge with shared data
    const savedData = formPersistence.loadFormData();
    const sharedData = CrossFormDataManager.getSharedData();
    
    if (savedData || Object.keys(sharedData).length > 0) {
      const mergedData = {
        ...formData,
        ...sharedData,
        ...savedData,
        // Never restore sensitive fields or reset valid consent choices
        password: '',
        confirmPassword: '',
        // Preserve existing consent state if user already accepted
        terms_accepted: savedData?.terms_accepted || formData.terms_accepted,
        privacy_accepted: savedData?.privacy_accepted || formData.privacy_accepted
      };
      setFormData(mergedData);
      console.log('📝 Registration form restored from saved data');
    }

    // Start auto-save
    formPersistence.startAutoSave(() => formData);

    // Cleanup on unmount
    return () => {
      formPersistence.stopAutoSave();
    };
  }, []);

  // Initialize consent choices
  useEffect(() => {
    const initialConsents: Record<string, boolean> = {};
    consentItems.forEach(item => {
      initialConsents[item.id] = item.required; // Required consents pre-checked
    });
    setConsentChoices(initialConsents);
  }, []);

  // Save form data when it changes (with debouncing handled by auto-save)
  useEffect(() => {
    if (Object.keys(formData).some(key => formData[key] !== '')) {
      // Save shared data for cross-form population
      CrossFormDataManager.saveSharedData({
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone,
        business_name: formData.business_name,
        business_type: formData.business_type,
        rc_number: formData.rc_number,
        address: formData.address,
        state: formData.state,
        lga: formData.lga
      });
    }
  }, [formData]);

  const validateStep = (step: number): boolean => {
    const errors: {[key: string]: string} = {};
    
    if (step === 0) {
      // Account validation
      if (!formData.email) errors.email = 'Email is required';
      if (!formData.password || formData.password.length < 8) errors.password = 'Password must be at least 8 characters';
      if (formData.password !== formData.confirmPassword) errors.confirmPassword = 'Passwords do not match';
      if (!formData.first_name) errors.first_name = 'First name is required';
      if (!formData.last_name) errors.last_name = 'Last name is required';
    } else if (step === 1) {
      // Business validation
      if (!formData.business_name) errors.business_name = 'Business name is required';
      if (!formData.business_type) errors.business_type = 'Business type is required';
      if (!formData.rc_number) errors.rc_number = 'RC number is required';
      if (!formData.address) errors.address = 'Address is required';
    } else if (step === 2) {
      // Consent validation
      const requiredConsents = consentItems.filter(item => item.required);
      const missingConsents = requiredConsents.filter(item => !consentChoices[item.id]);
      if (missingConsents.length > 0) {
        errors.consent = 'All required consents must be accepted';
      }
      if (!criticalConsents.terms_accepted) errors.terms_accepted = 'Terms must be accepted';
      if (!criticalConsents.privacy_accepted) errors.privacy_accepted = 'Privacy policy must be accepted';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (!validateStep(currentStep)) return;
    
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    // Check banking integration consent flow
    if (consentChoices['banking_integration_intent'] && !bankingConsentComplete) {
      setShowBankingConsent(true);
      return;
    }

    try {
      // Final validation before submission
      if (!validateStep(2)) {
        console.error('❌ Registration validation failed at final step');
        return;
      }

      const registrationData = {
        ...formData,
        // Override with critical consent state to ensure they're included
        terms_accepted: criticalConsents.terms_accepted,
        privacy_accepted: criticalConsents.privacy_accepted,
        consents: consentChoices,
        banking_integration_enabled: consentChoices['banking_integration_intent'],
        banking_consent_complete: bankingConsentComplete,
        timestamp: new Date().toISOString(),
        ndpr_compliant: true
      };

      secureLogger.userAction('Submitting enhanced consent registration', {
        has_critical_consents: !!criticalConsents.terms_accepted && !!criticalConsents.privacy_accepted,
        banking_integration_enabled: consentChoices['banking_integration_intent'],
        ndpr_compliant: true
      });
      
      await onCompleteRegistration(registrationData);
      
      // Clear form data on successful registration
      formPersistence.clearFormData();
      secureLogger.success('Enhanced consent registration successful - form data cleared');
      
    } catch (err) {
      secureLogger.error('Enhanced consent registration failed', err);
      // Keep form data on failure so user doesn't lose their input
    }
  };

  const handleBankingConsentComplete = (consents: any) => {
    setBankingConsentComplete(true);
    setShowBankingConsent(false);
    handleSubmit();
  };

  const renderAccountStep = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TaxPoyntInput
          label="First Name"
          value={formData.first_name}
          onChange={(e) => setFormData({...formData, first_name: e.target.value})}
          variant={fieldErrors.first_name ? 'error' : 'default'}
          required
        />
        <TaxPoyntInput
          label="Last Name"
          value={formData.last_name}
          onChange={(e) => setFormData({...formData, last_name: e.target.value})}
          variant={fieldErrors.last_name ? 'error' : 'default'}
          required
        />
      </div>
      
      <TaxPoyntInput
        label="Work Email"
        type="email"
        value={formData.email}
        onChange={(e) => setFormData({...formData, email: e.target.value})}
        variant={fieldErrors.email ? 'error' : 'default'}
        required
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TaxPoyntInput
          label="Password"
          type="password"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          variant={fieldErrors.password ? 'error' : 'default'}
          required
        />
        <TaxPoyntInput
          label="Confirm Password"
          type="password"
          value={formData.confirmPassword}
          onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
          variant={fieldErrors.confirmPassword ? 'error' : 'default'}
          required
        />
      </div>

      {/* Account Type Selection */}
      <div>
        <label className="block text-sm font-bold text-slate-800 mb-3">
          Choose Your Account Type
        </label>
        <div className="grid grid-cols-1 gap-3">
          {[
            { 
              value: 'si', 
              label: 'System Integrator (SI)', 
              description: 'Connect multiple business systems',
              icon: '🔗',
              popular: true
            },
            { 
              value: 'app', 
              label: 'Access Point Provider (APP)', 
              description: 'Direct FIRS communication',
              icon: '🏛️'
            },
            { 
              value: 'hybrid', 
              label: 'Hybrid Solution', 
              description: 'Best of both worlds',
              icon: '⚡'
            }
          ].map((option) => (
            <label
              key={option.value}
              className={`flex items-center p-4 border-2 rounded-xl cursor-pointer transition-all ${
                formData.service_package === option.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <input
                type="radio"
                name="service_package"
                value={option.value}
                checked={formData.service_package === option.value}
                onChange={(e) => setFormData({...formData, service_package: e.target.value})}
                className="sr-only"
              />
              <span className="text-2xl mr-3">{option.icon}</span>
              <div className="flex-1">
                <div className="flex items-center">
                  <span className="font-bold text-slate-800">{option.label}</span>
                  {option.popular && (
                    <span className="ml-2 px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                      Most Popular
                    </span>
                  )}
                </div>
                <div className="text-sm text-slate-600">{option.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>
    </div>
  );

  const renderBusinessStep = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TaxPoyntInput
          label="Business Name"
          value={formData.business_name}
          onChange={(e) => setFormData({...formData, business_name: e.target.value})}
          variant={fieldErrors.business_name ? 'error' : 'default'}
          required
        />
        <TaxPoyntInput
          label="RC Number"
          value={formData.rc_number}
          onChange={(e) => setFormData({...formData, rc_number: e.target.value})}
          variant={fieldErrors.rc_number ? 'error' : 'default'}
          required
        />
      </div>
      
      <div>
        <label className="block text-sm font-bold text-slate-800 mb-2">Business Type</label>
        <select
          value={formData.business_type}
          onChange={(e) => setFormData({...formData, business_type: e.target.value})}
          className={`w-full px-4 py-3 border-2 rounded-xl transition-colors ${
            fieldErrors.business_type ? 'border-red-300' : 'border-gray-300 focus:border-blue-500'
          }`}
          required
        >
          <option value="">Select business type</option>
          <option value="manufacturing">Manufacturing</option>
          <option value="retail">Retail & E-commerce</option>
          <option value="services">Professional Services</option>
          <option value="technology">Technology</option>
          <option value="healthcare">Healthcare</option>
          <option value="other">Other</option>
        </select>
      </div>
      
      <TaxPoyntInput
        label="Business Address"
        value={formData.address}
        onChange={(e) => setFormData({...formData, address: e.target.value})}
        variant={fieldErrors.address ? 'error' : 'default'}
        required
      />
      
      <TaxPoyntInput
        label="Phone Number"
        type="tel"
        value={formData.phone}
        onChange={(e) => setFormData({...formData, phone: e.target.value})}
        placeholder="+234 800 000 0000"
      />
    </div>
  );

  const renderConsentStep = () => (
    <div className="space-y-6">
      {/* NDPR Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-start">
          <span className="text-2xl mr-3">🛡️</span>
          <div>
            <h3 className="font-bold text-blue-900 mb-2">Your Data, Your Control</h3>
            <p className="text-blue-800 text-sm">
              TaxPoynt follows strict NDPR (Nigerian Data Protection Regulation) compliance. 
              You control what data we can access and how we use it.
            </p>
          </div>
        </div>
      </div>

      {/* Consent Items */}
      <div className="space-y-4">
        {consentItems.map((item) => (
          <div key={item.id} className={`border-2 rounded-xl p-6 transition-all ${
            item.required ? 'border-blue-200 bg-blue-50' : 'border-gray-200 bg-white'
          }`}>
            <div className="flex items-start justify-between">
              <div className="flex-1 mr-4">
                <div className="flex items-center mb-2">
                  <h4 className="font-bold text-slate-800">{item.title}</h4>
                  {item.required && (
                    <span className="ml-2 px-2 py-1 text-xs font-bold bg-blue-100 text-blue-800 rounded-full">
                      Required
                    </span>
                  )}
                </div>
                <p className="text-slate-600 mb-3">{item.description}</p>
                
                <details className="text-sm text-slate-500">
                  <summary className="cursor-pointer hover:text-slate-700 font-medium">
                    View Privacy Details
                  </summary>
                  <div className="mt-2 space-y-2 pl-4 border-l-2 border-gray-200">
                    <div><strong>Legal Basis:</strong> {item.legalBasis}</div>
                    <div><strong>Data Types:</strong> {item.dataTypes.join(', ')}</div>
                    <div><strong>Retention:</strong> {item.retentionPeriod}</div>
                    {item.thirdParties && (
                      <div><strong>Shared With:</strong> {item.thirdParties.join(', ')}</div>
                    )}
                  </div>
                </details>
              </div>
              
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  disabled={item.required}
                  checked={consentChoices[item.id] || false}
                  onChange={(e) => setConsentChoices({
                    ...consentChoices,
                    [item.id]: e.target.checked
                  })}
                  className="h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                />
              </label>
            </div>
          </div>
        ))}
      </div>

      {/* Terms and Privacy */}
      <div className="space-y-4 pt-6 border-t border-gray-200">
                <div className="flex items-start">
          <input
            type="checkbox"
            checked={criticalConsents.terms_accepted}
            onChange={(e) => setCriticalConsents({...criticalConsents, terms_accepted: e.target.checked})}
            className={`h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 mt-1 cursor-pointer ${
              fieldErrors.terms_accepted ? 'border-red-500' : ''
            }`}
            required
          />
          <span className="ml-3 text-sm text-slate-600">
            I agree to the{' '}
            <a 
              href="/legal/terms-of-service" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline font-medium"
              onClick={(e) => e.stopPropagation()}
            >
              Terms of Service
            </a>
            {' '}and{' '}
            <a 
              href="/legal/privacy-policy" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline font-medium"
              onClick={(e) => e.stopPropagation()}
            >
              Privacy Policy
            </a>
            {' '}(required)
          </span>
          {fieldErrors.terms_accepted && (
            <p className="ml-7 mt-1 text-sm text-red-600">{fieldErrors.terms_accepted}</p>
          )}
        </div>

        <div className="flex items-start">
          <input
            type="checkbox"
            checked={criticalConsents.privacy_accepted}
            onChange={(e) => setCriticalConsents({...criticalConsents, privacy_accepted: e.target.checked})}
            className={`h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 mt-1 cursor-pointer ${
              fieldErrors.privacy_accepted ? 'border-red-500' : ''
            }`}
            required
          />
          <span className="ml-3 text-sm text-slate-600">
            I acknowledge the{' '}
            <a 
              href="/legal/ndpr-notice" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline font-medium"
              onClick={(e) => e.stopPropagation()}
            >
              NDPR data processing notice
            </a>
            {' '}(required)
          </span>
          {fieldErrors.privacy_accepted && (
            <p className="ml-7 mt-1 text-sm text-red-600">{fieldErrors.privacy_accepted}</p>
          )}
        </div>
      </div>
    </div>
  );

  if (showBankingConsent) {
    return (
      <AuthLayout
        title="Banking Integration"
        subtitle="Complete banking consent to finish registration"
      >
        <MonoConsentIntegration
          existingConsents={consentChoices}
          onConsentUpdate={handleBankingConsentComplete}
          onMonoWidgetReady={(url) => console.log('Mono ready:', url)}
          compactMode={false}
        />
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Join TaxPoynt"
      subtitle="Create your professional account"
      showBackToHome={true}
    >
      <div className="space-y-6">
        {/* Progress Indicator */}
        <div className="flex items-center justify-between mb-8">
          {steps.map((step, index) => (
            <React.Fragment key={step.id}>
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  index <= currentStep ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  {index + 1}
                </div>
                <div className="ml-2 text-sm">
                  <div className={`font-medium ${index <= currentStep ? 'text-blue-600' : 'text-gray-500'}`}>
                    {step.title}
                  </div>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div className={`flex-1 h-1 mx-4 ${
                  index < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                }`} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
            <div className="flex items-center">
              <span className="text-red-600 mr-3 text-xl">⚠️</span>
              <div>
                <div className="text-red-700 font-medium">{error}</div>
                <div className="text-red-600 text-sm mt-1">
                  Please check your information and try again. If the problem persists, contact support.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Field Errors Display */}
        {Object.keys(fieldErrors).length > 0 && (
          <div className="p-4 bg-orange-50 border border-orange-200 rounded-xl">
            <div className="flex items-start">
              <span className="text-orange-600 mr-3 text-xl">📝</span>
              <div>
                <div className="text-orange-800 font-medium mb-2">Please complete the following fields:</div>
                <ul className="text-orange-700 text-sm space-y-1">
                  {Object.entries(fieldErrors).map(([field, message]) => (
                    <li key={field}>• {message}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Step Content */}
        <div className="min-h-[400px]">
          {currentStep === 0 && renderAccountStep()}
          {currentStep === 1 && renderBusinessStep()}
          {currentStep === 2 && renderConsentStep()}
          {currentStep === 3 && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🎉</div>
              <h3 className="text-2xl font-bold text-slate-800 mb-2">Ready to Launch!</h3>
              <p className="text-slate-600">Complete your registration to start using TaxPoynt</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between pt-6 border-t border-gray-200">
          <TaxPoyntButton
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 0 || isLoading}
            className="border-2 border-gray-300 text-gray-700 hover:border-blue-500 hover:text-blue-600 bg-white"
          >
            Previous
          </TaxPoyntButton>
          
          <TaxPoyntButton
            variant="primary"
            onClick={handleNext}
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-md hover:shadow-lg"
          >
            {currentStep === steps.length - 1 
              ? (isLoading ? 'Creating Account...' : 'Complete Registration')
              : 'Continue'
            }
          </TaxPoyntButton>
        </div>
      </div>
    </AuthLayout>
  );
};
