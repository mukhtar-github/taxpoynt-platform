'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUserContext } from '../../../../shared_components/hooks/useUserContext';
import { AuthLayout } from '../../../../shared_components/auth/AuthLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';
import { OnboardingStateManager } from '../../../../shared_components/onboarding/ServiceOnboardingRouter';
import { 
  OnboardingProgressIndicator, 
  useMobileOptimization 
} from '../../../../shared_components/onboarding';
import apiClient from '../../../../shared_components/api/client';

interface CombinedSetupData {
  // Business Information
  business_name: string;
  business_type: string;
  tin: string;
  rc_number: string;
  address: string;
  state: string;
  lga: string;
  
  // SI Configuration
  si_services: string[];
  business_systems: string[];
  financial_systems: string[];
  
  // APP Configuration
  firs_environment: 'sandbox' | 'production';
  app_processing_preferences: string[];
  
  // Compliance & Consent
  data_processing_consent: boolean;
  cross_border_consent: boolean;
  regulatory_compliance_consent: boolean;
}

export default function HybridCombinedSetupPage() {
  const router = useRouter();
  const { user, loading: userLoading } = useUserContext();
  const { isMobile } = useMobileOptimization();
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [setupData, setSetupData] = useState<CombinedSetupData>({
    business_name: '',
    business_type: '',
    tin: '',
    rc_number: '',
    address: '',
    state: '',
    lga: '',
    si_services: [],
    business_systems: [],
    financial_systems: [],
    firs_environment: 'sandbox',
    app_processing_preferences: [],
    data_processing_consent: false,
    cross_border_consent: false,
    regulatory_compliance_consent: false
  });

  useEffect(() => {
    if (userLoading) return;
    
    if (!user) {
      router.push('/auth/signin');
      return;
    }

    if (user.role !== 'hybrid_user') {
      router.push('/dashboard');
      return;
    }
    
    // Pre-populate business name if available
    if (user.business_name) {
      setSetupData(prev => ({
        ...prev,
        business_name: user.business_name
      }));
    }
  }, [user, userLoading, router]);

  const updateSetupData = <K extends keyof CombinedSetupData>(field: K, value: CombinedSetupData[K]) => {
    setSetupData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  type ArrayFields = 'si_services' | 'business_systems' | 'financial_systems' | 'app_processing_preferences';

  const handleArrayToggle = (field: ArrayFields, value: string) => {
    setSetupData(prev => {
      const currentArray = prev[field];
      const newArray = currentArray.includes(value)
        ? currentArray.filter(item => item !== value)
        : [...currentArray, value];
      
      return {
        ...prev,
        [field]: newArray
      };
    });
  };

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 1: // Business Information
        return !!(setupData.business_name && setupData.business_type && setupData.tin);
      case 2: // SI Configuration
        return setupData.si_services.length > 0;
      case 3: // APP Configuration
        return setupData.app_processing_preferences.length > 0;
      case 4: // Compliance & Consent
        return setupData.data_processing_consent && 
               setupData.cross_border_consent && 
               setupData.regulatory_compliance_consent;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 4));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleComplete = async () => {
    if (!validateStep(4)) return;

    setIsLoading(true);
    try {
      console.log('🚀 Completing Hybrid combined setup:', setupData);
      
      await apiClient.post('/hybrid/onboarding/complete-setup', setupData);

      if (user?.id) {
        OnboardingStateManager.updateStep(user.id, 'onboarding_complete', true);
      }

      router.push('/dashboard/hybrid');
    } catch (error) {
      console.error('Setup completion failed:', error);
      // Demo completion fallback
      if (user?.id) {
        OnboardingStateManager.updateStep(user.id, 'onboarding_complete', true);
      }
      router.push('/dashboard/hybrid');
    } finally {
      setIsLoading(false);
    }
  };

  const businessTypes = [
    'Corporation', 'Limited Liability Company', 'Partnership', 'Sole Proprietorship',
    'Non-Profit Organization', 'Government Entity', 'Other'
  ];

  const siServices = [
    { id: 'business_systems', name: 'Business Systems Integration', description: 'ERP, CRM, POS systems' },
    { id: 'financial_systems', name: 'Financial Systems Integration', description: 'Banking, payment processors' },
    { id: 'data_transformation', name: 'Data Transformation', description: 'Format conversion, mapping' },
    { id: 'invoice_generation', name: 'Invoice Generation', description: 'FIRS-compliant invoice creation' }
  ];

  const businessSystems = [
    'SAP ERP', 'Odoo', 'Microsoft Dynamics', 'NetSuite', 'Salesforce CRM', 
    'Square POS', 'Custom ERP', 'Excel/CSV Import', 'Other'
  ];

  const financialSystems = [
    'Mono', 'Paystack', 'Flutterwave', 'Interswitch', 'OPay', 
    'Moniepoint', 'PalmPay', 'Bank Direct Integration', 'Other'
  ];

  const appProcessingPreferences = [
    { id: 'real_time', name: 'Real-time Processing', description: 'Immediate FIRS submission' },
    { id: 'batch_processing', name: 'Batch Processing', description: 'Scheduled bulk submissions' },
    { id: 'validation_only', name: 'Validation Only', description: 'Validate before submission' },
    { id: 'compliance_monitoring', name: 'Compliance Monitoring', description: 'Track regulatory status' }
  ];

  if (userLoading || !user) {
    return (
      <AuthLayout title="Loading" subtitle="Setting up your workspace">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p>Loading...</p>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Complete Your Hybrid Setup" subtitle="Configure your comprehensive SI + APP solution">
      <div className="max-w-4xl mx-auto">
        {/* Enhanced Progress Indicator */}
        <OnboardingProgressIndicator 
          currentStep={currentStep.toString()}
          completedSteps={[]}
          userRole="hybrid"
        />
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className={`${isMobile ? 'text-2xl' : 'text-3xl'} font-bold text-gray-900`}>
            Complete Your Hybrid Setup
          </h1>
          <p className={`mt-2 ${isMobile ? 'text-base' : 'text-lg'} text-gray-600`}>
            Configure your comprehensive SI + APP solution
          </p>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          
          {/* Step 1: Business Information */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Business Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <TaxPoyntInput
                  label="Business Name"
                  value={setupData.business_name}
                  onChange={(e) => updateSetupData('business_name', e.target.value)}
                  required
                />
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Business Type *
                  </label>
                  <select
                    value={setupData.business_type}
                    onChange={(e) => updateSetupData('business_type', e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    required
                  >
                    <option value="">Select business type</option>
                    {businessTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
                
                <TaxPoyntInput
                  label="Tax Identification Number (TIN)"
                  value={setupData.tin}
                  onChange={(e) => updateSetupData('tin', e.target.value)}
                  required
                />
                
                <TaxPoyntInput
                  label="RC Number"
                  value={setupData.rc_number}
                  onChange={(e) => updateSetupData('rc_number', e.target.value)}
                />
                
                <TaxPoyntInput
                  label="Business Address"
                  value={setupData.address}
                  onChange={(e) => updateSetupData('address', e.target.value)}
                />
                
                <TaxPoyntInput
                  label="State"
                  value={setupData.state}
                  onChange={(e) => updateSetupData('state', e.target.value)}
                />
              </div>
            </div>
          )}

          {/* Step 2: SI Configuration */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">System Integration (SI) Configuration</h2>
              
              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-4">Select SI Services</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {siServices.map(service => (
                    <div
                      key={service.id}
                      className={`
                        border rounded-lg p-4 cursor-pointer transition-all
                        ${setupData.si_services.includes(service.id)
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-300 hover:border-gray-400'
                        }
                      `}
                      onClick={() => handleArrayToggle('si_services', service.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900">{service.name}</h4>
                          <p className="text-sm text-gray-600">{service.description}</p>
                        </div>
                        <div className={`
                          w-5 h-5 rounded border-2 flex items-center justify-center
                          ${setupData.si_services.includes(service.id)
                            ? 'border-purple-500 bg-purple-500'
                            : 'border-gray-300'
                          }
                        `}>
                          {setupData.si_services.includes(service.id) && (
                            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {setupData.si_services.includes('business_systems') && (
                <div>
                  <h3 className="text-lg font-medium text-gray-800 mb-4">Business Systems to Integrate</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {businessSystems.map(system => (
                      <label key={system} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={setupData.business_systems.includes(system)}
                          onChange={() => handleArrayToggle('business_systems', system)}
                          className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                        />
                        <span className="text-sm text-gray-700">{system}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {setupData.si_services.includes('financial_systems') && (
                <div>
                  <h3 className="text-lg font-medium text-gray-800 mb-4">Financial Systems to Integrate</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {financialSystems.map(system => (
                      <label key={system} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={setupData.financial_systems.includes(system)}
                          onChange={() => handleArrayToggle('financial_systems', system)}
                          className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                        />
                        <span className="text-sm text-gray-700">{system}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 3: APP Configuration */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Access Point Provider (APP) Configuration</h2>
              
              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-4">FIRS Environment</h3>
                <div className="flex space-x-4">
                  {[
                    { value: 'sandbox', label: 'Sandbox (Testing)', description: 'Safe environment for testing' },
                    { value: 'production', label: 'Production (Live)', description: 'Live FIRS submissions' }
                  ].map(env => (
                    <div
                      key={env.value}
                      className={`
                        border rounded-lg p-4 cursor-pointer flex-1 transition-all
                        ${setupData.firs_environment === env.value
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-300 hover:border-gray-400'
                        }
                      `}
                      onClick={() => updateSetupData('firs_environment', env.value)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900">{env.label}</h4>
                          <p className="text-sm text-gray-600">{env.description}</p>
                        </div>
                        <div className={`
                          w-5 h-5 rounded-full border-2 flex items-center justify-center
                          ${setupData.firs_environment === env.value
                            ? 'border-purple-500 bg-purple-500'
                            : 'border-gray-300'
                          }
                        `}>
                          {setupData.firs_environment === env.value && (
                            <div className="w-2 h-2 bg-white rounded-full"></div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-4">Processing Preferences</h3>
                <div className="space-y-3">
                  {appProcessingPreferences.map(pref => (
                    <div
                      key={pref.id}
                      className={`
                        border rounded-lg p-4 cursor-pointer transition-all
                        ${setupData.app_processing_preferences.includes(pref.id)
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-300 hover:border-gray-400'
                        }
                      `}
                      onClick={() => handleArrayToggle('app_processing_preferences', pref.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900">{pref.name}</h4>
                          <p className="text-sm text-gray-600">{pref.description}</p>
                        </div>
                        <div className={`
                          w-5 h-5 rounded border-2 flex items-center justify-center
                          ${setupData.app_processing_preferences.includes(pref.id)
                            ? 'border-purple-500 bg-purple-500'
                            : 'border-gray-300'
                          }
                        `}>
                          {setupData.app_processing_preferences.includes(pref.id) && (
                            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Compliance & Consent */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Compliance & Consent</h2>
              
              <div className="space-y-4">
                <label className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    checked={setupData.data_processing_consent}
                    onChange={(e) => updateSetupData('data_processing_consent', e.target.checked)}
                    className="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500 mt-0.5"
                  />
                  <div>
                    <span className="font-medium text-gray-900">Data Processing Consent</span>
                    <p className="text-sm text-gray-600">
                      I consent to TaxPoynt processing my business data for invoice generation and FIRS submission purposes.
                    </p>
                  </div>
                </label>

                <label className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    checked={setupData.cross_border_consent}
                    onChange={(e) => updateSetupData('cross_border_consent', e.target.checked)}
                    className="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500 mt-0.5"
                  />
                  <div>
                    <span className="font-medium text-gray-900">Cross-Border Data Transfer</span>
                    <p className="text-sm text-gray-600">
                      I understand that data may be processed across different systems and authorize secure data transfer for integration purposes.
                    </p>
                  </div>
                </label>

                <label className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    checked={setupData.regulatory_compliance_consent}
                    onChange={(e) => updateSetupData('regulatory_compliance_consent', e.target.checked)}
                    className="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500 mt-0.5"
                  />
                  <div>
                    <span className="font-medium text-gray-900">Regulatory Compliance</span>
                    <p className="text-sm text-gray-600">
                      I acknowledge compliance with Nigerian tax regulations and FIRS e-invoicing requirements.
                    </p>
                  </div>
                </label>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">Setup Summary</h3>
                <div className="text-sm text-blue-800 space-y-1">
                  <p>• SI Services: {setupData.si_services.length} selected</p>
                  <p>• APP Environment: {setupData.firs_environment}</p>
                  <p>• Processing Preferences: {setupData.app_processing_preferences.length} selected</p>
                  <p>• Business Systems: {setupData.business_systems.length} selected</p>
                  <p>• Financial Systems: {setupData.financial_systems.length} selected</p>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
            <div>
              {currentStep > 1 && (
                <TaxPoyntButton
                  variant="outline"
                  onClick={handlePrevious}
                >
                  Previous
                </TaxPoyntButton>
              )}
            </div>
            
            <div className="flex space-x-4">
              <TaxPoyntButton
                variant="outline"
                onClick={() => router.push('/dashboard/hybrid')}
              >
                Skip for Now
              </TaxPoyntButton>
              
              {currentStep < 4 ? (
                <TaxPoyntButton
                  variant="primary"
                  onClick={handleNext}
                  disabled={!validateStep(currentStep)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  Next
                </TaxPoyntButton>
              ) : (
                <TaxPoyntButton
                  variant="primary"
                  onClick={handleComplete}
                  disabled={!validateStep(4) || isLoading}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  {isLoading ? 'Completing Setup...' : 'Complete Setup'}
                </TaxPoyntButton>
              )}
            </div>
          </div>
        </div>
      </div>
    </AuthLayout>
  );
}
