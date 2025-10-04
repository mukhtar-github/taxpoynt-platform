'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUserContext } from '../../../../shared_components/hooks/useUserContext';
import { OnboardingStateManager } from '../../../../shared_components/onboarding/ServiceOnboardingRouter';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';
import { 
  OnboardingProgressIndicator, 
  SkipForNowButton, 
  useMobileOptimization 
} from '../../../../shared_components/onboarding';
import { TaxPoyntAPIClient } from '../../../../shared_components/api/client';
import { APIResponse } from '../../../../si_interface/types';
import { secureConfig, validateConfig } from '../../../../shared_components/utils/secureConfig';
import { secureLogger } from '../../../../shared_components/utils/secureLogger';

interface FIRSSetupData {
  firs_api_key: string;
  firs_api_secret: string;
  environment: 'sandbox' | 'production';
  auto_validate: boolean;
  batch_processing: boolean;
  real_time_sync: boolean;
  vat_number: string;
  default_tax_rate: number;
  webhook_url?: string;
  certificate_path?: string;
}

export default function APPInvoiceProcessingSetupPage() {
  const router = useRouter();
  const { user, loading: userLoading } = useUserContext();
  const { isMobile, mobileBreakpoint } = useMobileOptimization();
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'failed'>('idle');
  const [setupData, setSetupData] = useState<FIRSSetupData>({
    firs_api_key: '',
    firs_api_secret: '',
    environment: 'sandbox',
    auto_validate: true,
    batch_processing: true,
    real_time_sync: false,
    vat_number: '',
    default_tax_rate: 7.5,
    webhook_url: '',
    certificate_path: ''
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (userLoading) return;
    
    if (!user) {
      router.push('/auth/signin');
      return;
    }

    if (user.role !== 'access_point_provider') {
      router.push('/dashboard');
      return;
    }

    OnboardingStateManager.updateStep(user.id, 'invoice_processing_setup');
  }, [user, userLoading, router]);

  const validateStep = (step: number): boolean => {
    const errors: Record<string, string> = {};

    if (step === 1) {
      if (!setupData.firs_api_key.trim()) errors.firs_api_key = 'FIRS API Key is required';
      if (!setupData.firs_api_secret.trim()) errors.firs_api_secret = 'FIRS API Secret is required';
    } else if (step === 3) {
      if (!setupData.vat_number.trim()) errors.vat_number = 'VAT Number is required';
      if (setupData.default_tax_rate <= 0 || setupData.default_tax_rate > 100) {
        errors.default_tax_rate = 'Tax rate must be between 0 and 100';
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const testFIRSConnection = async () => {
    if (!validateStep(1)) return;

    // SECURITY: Validate configuration for sensitive data exposure
    const securityValidation = validateConfig(setupData);
    if (!securityValidation.isValid) {
      secureLogger.error('Security violation detected in FIRS setup', {
        violations: securityValidation.violations,
        recommendations: securityValidation.recommendations
      });
      setConnectionStatus('failed');
      return;
    }

    setConnectionStatus('testing');
    
    try {
      const apiClient = new TaxPoyntAPIClient();
      
      // SECURITY: Sanitize data before sending to API
      const sanitizedData = secureConfig.sanitizeConfig({
        api_key: setupData.firs_api_key,
        api_secret: setupData.firs_api_secret,
        environment: setupData.environment
      });
      
      const response = await apiClient.post<APIResponse>('/app/firs/test-connection', sanitizedData);
      
      if (response.success) {
        setConnectionStatus('success');
        secureLogger.userAction('FIRS connection test successful', { environment: setupData.environment });
        setTimeout(() => setCurrentStep(2), 1000);
      } else {
        setConnectionStatus('failed');
      }
    } catch (error) {
      secureLogger.error('FIRS connection test failed', error);
      setConnectionStatus('failed');
    }
  };

  const handleComplete = async () => {
    if (!validateStep(3)) return;

    // SECURITY: Final validation before saving sensitive configuration
    const securityValidation = validateConfig(setupData);
    if (!securityValidation.isValid) {
      secureLogger.error('Security violation detected before saving FIRS config', {
        violations: securityValidation.violations,
        recommendations: securityValidation.recommendations
      });
      setFieldErrors({ general: 'Security validation failed. Please check your configuration.' });
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    
    try {
      const apiClient = new TaxPoyntAPIClient();
      
      // SECURITY: Sanitize data before saving to backend
      const sanitizedSetupData = secureConfig.sanitizeConfig(setupData);
      
      // Save FIRS configuration
      await apiClient.post<APIResponse>('/app/setup/firs-configuration', {
        ...sanitizedSetupData,
        user_id: user?.id || ''
      });
      
      // Mark onboarding as complete
      if (user?.id) {
        OnboardingStateManager.completeOnboarding(user.id);
      }
      
      secureLogger.userAction('APP Invoice Processing setup completed successfully', { 
        user_id: user?.id || '',
        environment: setupData.environment 
      });
      router.push('/dashboard/app');
      
    } catch (error) {
      secureLogger.error('APP onboarding failed', error);
      setFieldErrors({ general: 'Setup failed. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipForNow = () => {
    if (user?.id) {
      OnboardingStateManager.completeOnboarding(user.id);
    }
    router.push('/dashboard/app');
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            FIRS Invoice Processing Setup 🏛️
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Configure your Access Point Provider environment for seamless invoice transmission to FIRS.
            This setup ensures compliance with Nigerian tax regulations.
          </p>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-6 max-w-2xl mx-auto">
            <div className="flex items-center justify-center text-green-800 text-sm">
              <span className="mr-2">✨</span>
              <span>Welcome, {user?.first_name || 'there'}! Setting up your <strong>APP</strong> invoice processing environment.</span>
            </div>
          </div>
        </div>

        {/* Progress Indicator */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-800">Setup Progress</h2>
            <span className="text-sm text-gray-600">Step {currentStep} of 3</span>
          </div>
          <div className="flex items-center space-x-4">
            {[1, 2, 3].map((step) => (
              <div key={step} className="flex items-center flex-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step <= currentStep 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {step < currentStep ? '✓' : step}
                </div>
                <div className={`flex-1 h-1 mx-2 ${
                  step < currentStep ? 'bg-green-600' : 'bg-gray-200'
                }`}></div>
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-3 text-xs text-gray-600">
            <span>FIRS Connection</span>
            <span>Processing Config</span>
            <span>Compliance Setup</span>
          </div>
        </div>
        
        {/* Step Content */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
          
            {/* Step 1: FIRS Integration */}
          {currentStep === 1 && (
                <div>
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  🔑 FIRS API Connection
                </h3>
                <p className="text-gray-600">
                  Connect to the FIRS sandbox environment for testing. Your API credentials are securely encrypted.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <TaxPoyntInput
                  label="FIRS API Key *"
                    type="password" 
                  value={setupData.firs_api_key}
                  onChange={(e) => setSetupData({...setupData, firs_api_key: e.target.value})}
                  variant={fieldErrors.firs_api_key ? 'error' : 'default'}
                    placeholder="Enter your FIRS API key"
                  helperText={fieldErrors.firs_api_key}
                />

                <TaxPoyntInput
                  label="FIRS API Secret *"
                  type="password"
                  value={setupData.firs_api_secret}
                  onChange={(e) => setSetupData({...setupData, firs_api_secret: e.target.value})}
                  variant={fieldErrors.firs_api_secret ? 'error' : 'default'}
                  placeholder="Enter your FIRS API secret"
                  helperText={fieldErrors.firs_api_secret}
                />

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Environment *
                  </label>
                  <select
                    value={setupData.environment}
                    onChange={(e) => setSetupData({...setupData, environment: e.target.value as 'sandbox' | 'production'})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  >
                    <option value="sandbox">🧪 Sandbox (Testing)</option>
                    <option value="production">🚀 Production</option>
                  </select>
                </div>

                <TaxPoyntInput
                  label="Webhook URL (Optional)"
                  value={setupData.webhook_url || ''}
                  onChange={(e) => setSetupData({...setupData, webhook_url: e.target.value})}
                  placeholder="https://yourapp.com/webhooks/firs"
                  helperText="For receiving FIRS submission status updates"
                />
              </div>

              {/* Connection Test */}
              <div className="bg-gray-50 rounded-lg p-6 mb-8">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-semibold text-gray-800">Test FIRS Connection</h4>
                  {connectionStatus === 'success' && (
                    <div className="flex items-center text-green-600 text-sm">
                      <span className="mr-2">✅</span>
                      Connection successful!
                    </div>
                  )}
                  {connectionStatus === 'failed' && (
                    <div className="flex items-center text-red-600 text-sm">
                      <span className="mr-2">❌</span>
                      Connection failed
                    </div>
                  )}
                </div>
                
                <TaxPoyntButton
                  variant="outline"
                  onClick={testFIRSConnection}
                  loading={connectionStatus === 'testing'}
                  disabled={!setupData.firs_api_key || !setupData.firs_api_secret}
                  className="w-full sm:w-auto"
                >
                  {connectionStatus === 'testing' ? 'Testing Connection...' : 'Test Connection'}
                </TaxPoyntButton>

                {connectionStatus === 'success' && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <h5 className="font-medium text-green-800 mb-2">Connection Details:</h5>
                    <ul className="text-sm text-green-700 space-y-1">
                      <li>• FIRS Sandbox URL: https://eivc-k6z6d.ondigitalocean.app</li>
                      <li>• API Version: v1.0</li>
                      <li>• SSL/TLS: Enabled</li>
                      <li>• Rate Limit: 1000 requests/hour</li>
                    </ul>
                  </div>
                )}
              </div>

              <div className="flex justify-end">
                <TaxPoyntButton
                  variant="primary"
                  onClick={() => {
                    if (connectionStatus === 'success') {
                      setCurrentStep(2);
                    } else {
                      testFIRSConnection();
                    }
                  }}
                  disabled={connectionStatus !== 'success'}
                  className="px-8"
                >
                  Continue to Processing Setup
                </TaxPoyntButton>
              </div>
            </div>
          )}

          {/* Step 2: Processing Configuration */}
          {currentStep === 2 && (
            <div>
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  ⚙️ Invoice Processing Configuration
                </h3>
                <p className="text-gray-600">
                  Configure how invoices are processed and transmitted to FIRS.
                </p>
            </div>

              <div className="space-y-6 mb-8">
                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-gray-800 mb-4">Processing Options</h4>
              <div className="space-y-4">
                    {[
                      { 
                        key: 'auto_validate', 
                        label: 'Automatic Invoice Validation', 
                        description: 'Validate invoices against FIRS schema before transmission',
                        icon: '✅'
                      },
                      { 
                        key: 'batch_processing', 
                        label: 'Batch Processing', 
                        description: 'Process multiple invoices simultaneously for efficiency',
                        icon: '📦'
                      },
                      { 
                        key: 'real_time_sync', 
                        label: 'Real-time Synchronization', 
                        description: 'Immediate transmission to FIRS (may impact performance)',
                        icon: '⚡'
                      }
                    ].map((option) => (
                      <div key={option.key} className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          id={option.key}
                          checked={setupData[option.key as keyof FIRSSetupData] as boolean}
                          onChange={(e) => setSetupData({...setupData, [option.key]: e.target.checked})}
                          className="mt-1 h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                        />
                        <div className="flex-1">
                          <label htmlFor={option.key} className="flex items-center cursor-pointer">
                            <span className="mr-2">{option.icon}</span>
                            <span className="font-medium text-gray-900">{option.label}</span>
                  </label>
                          <p className="text-sm text-gray-600 mt-1">{option.description}</p>
                        </div>
                      </div>
                    ))}
                </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-blue-800 mb-3">📊 Recommended Settings</h4>
                  <ul className="text-sm text-blue-700 space-y-2">
                    <li>• <strong>Automatic Validation:</strong> Enabled (reduces FIRS rejection rate)</li>
                    <li>• <strong>Batch Processing:</strong> Enabled (improves performance for high volumes)</li>
                    <li>• <strong>Real-time Sync:</strong> Disabled (better for stability in production)</li>
                  </ul>
                </div>
              </div>

              <div className="flex justify-between">
                <TaxPoyntButton
                  variant="outline"
                  onClick={() => setCurrentStep(1)}
                >
                  Back to Connection
                </TaxPoyntButton>
                <TaxPoyntButton
                  variant="primary"
                  onClick={() => setCurrentStep(3)}
                  className="px-8"
                >
                  Continue to Compliance
                </TaxPoyntButton>
              </div>
            </div>
          )}

            {/* Step 3: Compliance Settings */}
          {currentStep === 3 && (
                <div>
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  🏛️ Nigerian Tax Compliance
                </h3>
                <p className="text-gray-600">
                  Configure tax compliance settings required for FIRS submissions.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <TaxPoyntInput
                  label="VAT Registration Number *"
                  value={setupData.vat_number}
                  onChange={(e) => setSetupData({...setupData, vat_number: e.target.value})}
                  variant={fieldErrors.vat_number ? 'error' : 'default'}
                  placeholder="12345678-0001"
                  helperText={fieldErrors.vat_number || "Your business VAT registration number"}
                />

                <TaxPoyntInput
                  label="Default VAT Rate (%)"
                  type="number"
                  value={setupData.default_tax_rate.toString()}
                  onChange={(e) => setSetupData({...setupData, default_tax_rate: parseFloat(e.target.value) || 0})}
                  variant={fieldErrors.default_tax_rate ? 'error' : 'default'}
                  placeholder="7.5"
                  helperText={fieldErrors.default_tax_rate || "Standard Nigerian VAT rate"}
                />
              </div>

              {/* Nigerian Tax Information */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
                <h4 className="text-lg font-semibold text-yellow-800 mb-3">🇳🇬 Nigerian Tax Requirements</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-yellow-700">
                  <div>
                    <h5 className="font-medium mb-2">VAT Rates:</h5>
                    <ul className="space-y-1">
                      <li>• Standard Rate: 7.5%</li>
                      <li>• Zero-rated: 0%</li>
                      <li>• Exempt: N/A</li>
                    </ul>
                </div>
                <div>
                    <h5 className="font-medium mb-2">Compliance Notes:</h5>
                    <ul className="space-y-1">
                      <li>• VAT registration required for ₦25M+ turnover</li>
                      <li>• Monthly VAT returns due by 21st</li>
                      <li>• E-invoicing mandatory for large taxpayers</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Error Display */}
              {fieldErrors.general && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-700">{fieldErrors.general}</p>
            </div>
              )}

              <div className="flex justify-between">
                <TaxPoyntButton
                  variant="outline"
                  onClick={() => setCurrentStep(2)}
                  disabled={isLoading}
                >
                  Back to Processing
                </TaxPoyntButton>
                <div className="flex gap-4">
                  <TaxPoyntButton
                    variant="secondary"
                onClick={handleSkipForNow}
                    disabled={isLoading}
                  >
                    Complete Later
                  </TaxPoyntButton>
                  <TaxPoyntButton
                    variant="primary"
                onClick={handleComplete}
                    loading={isLoading}
                disabled={isLoading}
                    className="px-8"
                  >
                    Complete APP Setup
                  </TaxPoyntButton>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-8">
          <div className="bg-white rounded-lg border border-gray-200 p-4 max-w-2xl mx-auto">
            <h3 className="text-sm font-medium text-gray-800 mb-2">🔒 Security & Compliance</h3>
            <p className="text-xs text-gray-600">
              All API credentials are encrypted using AES-256. This setup complies with FIRS technical specifications 
              and Nigerian Data Protection Regulation (NDPR) requirements.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
