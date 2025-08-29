/**
 * Streamlined Registration Component
 * ==================================
 * Simplified Stage 1 registration focusing on essential information only
 * Advanced details moved to service-specific onboarding flows
 */

import React, { useState } from 'react';
import { AuthLayout } from '../../shared_components/auth/AuthLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../design_system';

interface StreamlinedRegistrationProps {
  onCompleteRegistration: (registrationData: StreamlinedRegistrationData) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

interface StreamlinedRegistrationData {
  // Personal Information
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  
  // Basic Business Information
  business_name: string;
  service_package: 'si' | 'app' | 'hybrid';
  
  // Essential Consents
  terms_accepted: boolean;
  privacy_accepted: boolean;
  
  // Trial Information
  trial_started: boolean;
  trial_start_date: string;
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
    service_package: 'si',
    terms_accepted: false,
    privacy_accepted: false,
    trial_started: true,
    trial_start_date: new Date().toISOString()
  });
  
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

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
      console.log('🚀 Starting streamlined registration:', {
        ...formData,
        password: '***hidden***'
      });
      await onCompleteRegistration(formData);
    } catch (err) {
      console.error('Registration failed:', err);
    }
  };

  const renderPersonalStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to TaxPoynt! 👋</h2>
        <p className="text-gray-600">Let's start with your basic information</p>
      </div>

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
      
      <TaxPoyntInput
        label="Password"
        type="password"
        value={formData.password}
        onChange={(e) => setFormData({...formData, password: e.target.value})}
        variant={fieldErrors.password ? 'error' : 'default'}
        required
        helperText="At least 8 characters"
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

      <TaxPoyntInput
        label="Business Name"
        value={formData.business_name}
        onChange={(e) => setFormData({...formData, business_name: e.target.value})}
        variant={fieldErrors.business_name ? 'error' : 'default'}
        required
        helperText="We'll collect more business details later based on your service choice"
      />

      {fieldErrors.business_name && (
        <p className="text-sm text-red-600">{fieldErrors.business_name}</p>
      )}
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
