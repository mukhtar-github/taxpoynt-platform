/**
 * Streamlined Registration Component
 * ==================================
 * Simplified Stage 1 registration focusing on essential information only
 * Advanced details moved to service-specific onboarding flows
 */

import React, { useState, useEffect } from 'react';
import { AuthLayout } from '../../shared_components/auth/AuthLayout';
import { TaxPoyntButton } from '../../design_system/components/TaxPoyntButton';
import { TaxPoyntInput } from '../../design_system/components/TaxPoyntInput';
import { FormField } from '../../design_system/components/FormField';
import { useFormPersistence, CrossFormDataManager } from '../../shared_components/utils/formPersistence';
import { secureLogger } from '../../shared_components/utils/secureLogger';

interface StreamlinedRegistrationProps {
  onCompleteRegistration: (registrationData: StreamlinedRegistrationData) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

interface StreamlinedRegistrationData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  business_name: string;
  companyType?: string;
  companySize?: string;
  service_package: 'si' | 'app' | 'hybrid';
  terms_accepted: boolean;
  privacy_accepted: boolean;
  trial_started: boolean;
  trial_start_date: string;
  [key: string]: any; // Allow string indexing for form persistence
}

export const StreamlinedRegistration: React.FC<StreamlinedRegistrationProps> = ({
  onCompleteRegistration,
  isLoading = false,
  error
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<StreamlinedRegistrationData>({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    business_name: '',
    companyType: '',
    companySize: '',
    service_package: 'si',
    terms_accepted: false,
    privacy_accepted: false,
    trial_started: true,
    trial_start_date: new Date().toISOString()
  });
  
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Form persistence setup
  const formPersistence = useFormPersistence({
    storageKey: 'taxpoynt_streamlined_registration',
    persistent: false, // Use sessionStorage for privacy
    excludeFields: ['password', 'terms_accepted', 'privacy_accepted'],
    enableCrossFormSharing: true,
    autoSaveInterval: 3000 // Save every 3 seconds
  });

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
        // Never restore sensitive fields
        password: '',
        // Preserve existing consent state
        terms_accepted: savedData?.terms_accepted || formData.terms_accepted,
        privacy_accepted: savedData?.privacy_accepted || formData.privacy_accepted
      };
      setFormData(mergedData);
      secureLogger.formData('Form restored from saved data', { 
        has_saved_data: !!savedData,
        has_shared_data: Object.keys(sharedData).length > 0
      });
    }

    // Start auto-save
    formPersistence.startAutoSave(() => formData);

    // Cleanup on unmount
    return () => {
      formPersistence.stopAutoSave();
    };
  }, []);

  // Save form data when it changes
  useEffect(() => {
    if (Object.keys(formData).some(key => formData[key] !== '')) {
      // Save shared data for cross-form population
      CrossFormDataManager.saveSharedData({
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
        business_name: formData.business_name,
        companyType: formData.companyType,
        companySize: formData.companySize
      });
    }
  }, [formData]);

  const steps = [
    { id: 'personal', title: 'Personal Info', description: 'Your basic information' },
    { id: 'business', title: 'Business Info', description: 'Basic business details' },
    { id: 'service', title: 'Service Selection', description: 'Choose your TaxPoynt service' },
    { id: 'consent', title: 'Terms & Privacy', description: 'Accept our terms' }
  ];

  const validateCurrentStep = (): boolean => {
    const errors: Record<string, string> = {};
    
    switch (currentStep) {
      case 0: // Personal Info
        if (!formData.first_name.trim()) errors.first_name = 'First name is required';
        if (!formData.last_name.trim()) errors.last_name = 'Last name is required';
        if (!formData.email.trim()) errors.email = 'Email is required';
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) errors.email = 'Valid email required';
        if (!formData.password) errors.password = 'Password is required';
        else if (formData.password.length < 8) errors.password = 'Password must be at least 8 characters';
        break;
        
      case 1: // Business Info
        if (!formData.business_name.trim()) errors.business_name = 'Business name is required';
        if (!formData.companyType) errors.companyType = 'Company type is required';
        if (!formData.companySize) errors.companySize = 'Company size is required';
        break;
        
      case 2: // Service Selection - No validation needed, has default
        break;
        
      case 3: // Consent
        if (!formData.terms_accepted) errors.terms_accepted = 'Terms must be accepted';
        if (!formData.privacy_accepted) errors.privacy_accepted = 'Privacy policy must be accepted';
        break;
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (!validateCurrentStep()) return;
    
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
    if (!validateCurrentStep()) return;
    
    try {
      secureLogger.userAction('Starting streamlined registration', {
        service_package: formData.service_package,
        company_type: formData.companyType,
        company_size: formData.companySize
      });
      await onCompleteRegistration(formData);
    } catch (err) {
      secureLogger.error('Registration failed', err);
    }
  };

  const renderPersonalStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Let's get started 👋</h2>
        <p className="text-gray-600">Create your account to begin your 7-day free trial</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FormField
          label="First Name"
          name="first_name"
          type="text"
          value={formData.first_name}
          onChange={(value) => setFormData({...formData, first_name: value})}
          placeholder="John"
          required
          error={fieldErrors.first_name}
          showPersistenceIndicator={true}
          autoPopulateFromShared={true}
        />
        
        <FormField
          label="Last Name"
          name="last_name"
          type="text"
          value={formData.last_name}
          onChange={(value) => setFormData({...formData, last_name: value})}
          placeholder="Doe"
          required
          error={fieldErrors.last_name}
          showPersistenceIndicator={true}
          autoPopulateFromShared={true}
        />
      </div>

      <FormField
        label="Work Email"
        name="email"
        type="email"
        value={formData.email}
        onChange={(value) => setFormData({...formData, email: value})}
        placeholder="john@company.com"
        required
        error={fieldErrors.email}
        showPersistenceIndicator={true}
        autoPopulateFromShared={true}
      />
      
      <FormField
        label="Password"
        name="password"
        type="password"
        value={formData.password}
        onChange={(value) => setFormData({...formData, password: value})}
        placeholder="Create a secure password"
        required
        error={fieldErrors.password}
        helperText="At least 8 characters"
        showPersistenceIndicator={false}
        autoPopulateFromShared={false}
      />

      {/* Display errors */}
      {Object.entries(fieldErrors).map(([field, message]) => (
        <p key={field} className="text-sm text-red-600">{message}</p>
      ))}
    </div>
  );

  const renderBusinessStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Tell us about your business 🏢</h2>
        <p className="text-gray-600">Basic business information to get started</p>
      </div>

      <FormField
        label="Business Name"
        name="business_name"
        type="text"
        value={formData.business_name}
        onChange={(value) => setFormData({...formData, business_name: value})}
        placeholder="Your Company Ltd"
        required
        error={fieldErrors.business_name}
        helperText="We'll collect more business details later based on your service choice"
        showPersistenceIndicator={true}
        autoPopulateFromShared={true}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FormField
          label="Company Type"
          name="companyType"
          type="select"
          value={formData.companyType || ''}
          onChange={(value) => setFormData({...formData, companyType: value})}
          required
          error={fieldErrors.companyType}
          options={[
            { value: 'sole_proprietorship', label: 'Sole Proprietorship' },
            { value: 'partnership', label: 'Partnership' },
            { value: 'limited_company', label: 'Limited Company' },
            { value: 'public_company', label: 'Public Company' },
            { value: 'non_profit', label: 'Non-Profit' },
            { value: 'cooperative', label: 'Cooperative' }
          ]}
          showPersistenceIndicator={true}
          autoPopulateFromShared={true}
        />
        
        <FormField
          label="Company Size"
          name="companySize"
          type="select"
          value={formData.companySize || ''}
          onChange={(value) => setFormData({...formData, companySize: value})}
          required
          error={fieldErrors.companySize}
          options={[
            { value: 'startup', label: 'Startup (1-10 employees)' },
            { value: 'small', label: 'Small (11-50 employees)' },
            { value: 'medium', label: 'Medium (51-200 employees)' },
            { value: 'large', label: 'Large (201-1000 employees)' },
            { value: 'enterprise', label: 'Enterprise (1000+ employees)' }
          ]}
          showPersistenceIndicator={true}
          autoPopulateFromShared={true}
        />
      </div>
    </div>
  );

  const renderServiceStep = () => {
    const services = [
      {
        id: 'si',
        name: 'System Integration',
        description: 'Connect your ERP, CRM, POS, and financial systems',
        features: ['ERP Integration', 'Banking Connections', 'Data Mapping', 'Invoice Generation'],
        icon: '🔗',
        color: 'indigo',
        popular: false
      },
      {
        id: 'app',
        name: 'Access Point Provider',
        description: 'Direct FIRS invoice processing and compliance',
        features: ['FIRS Integration', 'Invoice Validation', 'Compliance Monitoring', 'Tax Reporting'],
        icon: '📄',
        color: 'green',
        popular: true
      },
      {
        id: 'hybrid',
        name: 'Hybrid Premium',
        description: 'Complete solution with both SI and APP capabilities',
        features: ['All SI Features', 'All APP Features', 'Priority Support', 'Advanced Analytics'],
        icon: '🚀',
        color: 'purple',
        popular: false
      }
    ];

    return (
      <div className="space-y-6">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose Your Service 🎯</h2>
          <p className="text-gray-600">Start your 7-day free trial with any service</p>
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mt-4">
            <span className="text-green-800 font-medium">🎉 7-Day Free Trial • No credit card required</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {services.map((service) => (
            <div
              key={service.id}
              onClick={() => setFormData({...formData, service_package: service.id as any})}
              className={`relative border-2 rounded-xl p-6 cursor-pointer transition-all ${
                formData.service_package === service.id
                  ? `border-${service.color}-500 bg-${service.color}-50 ring-2 ring-${service.color}-200`
                  : 'border-gray-200 hover:border-gray-300 hover:shadow-lg'
              }`}
            >
              {service.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                    Most Popular
                  </span>
                </div>
              )}
              
              <div className="text-center">
                <div className="text-4xl mb-3">{service.icon}</div>
                <h3 className="font-bold text-lg text-gray-900 mb-2">{service.name}</h3>
                <p className="text-gray-600 text-sm mb-4">{service.description}</p>
                
                <div className="space-y-2">
                  {service.features.map((feature, index) => (
                    <div key={index} className="text-xs text-gray-500 flex items-center justify-center">
                      <span className="text-green-500 mr-1">✓</span>
                      {feature}
                    </div>
                  ))}
                </div>
                
                {formData.service_package === service.id && (
                  <div className="mt-3">
                    <span className={`text-${service.color}-600 font-medium text-sm`}>
                      ✓ Selected
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <h4 className="font-medium text-blue-900 mb-2">📋 What happens next?</h4>
          <div className="text-sm text-blue-800">
            {formData.service_package === 'si' && (
              <p>After registration, you'll choose which systems to integrate (ERP, CRM, Banking) and complete the setup process.</p>
            )}
            {formData.service_package === 'app' && (
              <p>After registration, you'll complete business verification and set up direct FIRS invoice processing.</p>
            )}
            {formData.service_package === 'hybrid' && (
              <p>After registration, you'll choose which features to enable and complete comprehensive system setup.</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderConsentStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Almost Ready! 🎉</h2>
        <p className="text-gray-600">Please accept our terms to start your free trial</p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="space-y-4">
          <div className="flex items-start">
            <input
              type="checkbox"
              checked={formData.terms_accepted}
              onChange={(e) => setFormData({...formData, terms_accepted: e.target.checked})}
              className={`h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 mt-1 cursor-pointer ${
                fieldErrors.terms_accepted ? 'border-red-500' : ''
              }`}
              required
            />
            <span className="ml-3 text-sm text-gray-700">
              I agree to the{' '}
              <a 
                href="/legal/terms-of-service" 
                target="_blank" 
                className="text-blue-600 hover:text-blue-800 underline font-medium"
              >
                Terms of Service
              </a>
              {' '}(required)
            </span>
          </div>

          <div className="flex items-start">
            <input
              type="checkbox"
              checked={formData.privacy_accepted}
              onChange={(e) => setFormData({...formData, privacy_accepted: e.target.checked})}
              className={`h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 mt-1 cursor-pointer ${
                fieldErrors.privacy_accepted ? 'border-red-500' : ''
              }`}
              required
            />
            <span className="ml-3 text-sm text-gray-700">
              I acknowledge the{' '}
              <a 
                href="/legal/privacy-policy" 
                target="_blank" 
                className="text-blue-600 hover:text-blue-800 underline font-medium"
              >
                Privacy Policy
              </a>
              {' '}and{' '}
              <a 
                href="/legal/ndpr-notice" 
                target="_blank" 
                className="text-blue-600 hover:text-blue-800 underline font-medium"
              >
                NDPR Notice
              </a>
              {' '}(required)
            </span>
          </div>
        </div>

        {/* Display consent errors */}
        {(fieldErrors.terms_accepted || fieldErrors.privacy_accepted) && (
          <div className="mt-4 space-y-1">
            {fieldErrors.terms_accepted && (
              <p className="text-sm text-red-600">{fieldErrors.terms_accepted}</p>
            )}
            {fieldErrors.privacy_accepted && (
              <p className="text-sm text-red-600">{fieldErrors.privacy_accepted}</p>
            )}
          </div>
        )}
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
        <p className="text-sm text-yellow-800">
          <span className="font-medium">📋 Next Step:</span> After registration, you'll complete service-specific setup including business details and data consent based on your <span className="font-medium">{formData.service_package.toUpperCase()}</span> service selection.
        </p>
      </div>
    </div>
  );

  return (
    <AuthLayout
      title="Join TaxPoynt"
      subtitle="Start your 7-day free trial"
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
              <div className="text-red-700">{error}</div>
            </div>
          </div>
        )}

        {/* Step Content */}
        <div className="min-h-[400px]">
          {currentStep === 0 && renderPersonalStep()}
          {currentStep === 1 && renderBusinessStep()}
          {currentStep === 2 && renderServiceStep()}
          {currentStep === 3 && renderConsentStep()}
        </div>

        {/* Navigation */}
        <div className="flex justify-between pt-6">
          <TaxPoyntButton
            variant="secondary"
            onClick={handlePrevious}
            disabled={currentStep === 0}
          >
            Previous
          </TaxPoyntButton>
          
          <TaxPoyntButton
            variant="primary"
            onClick={handleNext}
            loading={isLoading}
            disabled={isLoading}
          >
            {currentStep === steps.length - 1 ? 'Start Free Trial' : 'Next'}
          </TaxPoyntButton>
        </div>
      </div>
    </AuthLayout>
  );
};

export default StreamlinedRegistration;
