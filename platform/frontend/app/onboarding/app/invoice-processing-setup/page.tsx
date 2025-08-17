'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function APPInvoiceProcessingSetupPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);

  const handleComplete = async () => {
    setIsLoading(true);
    
    try {
      // Save APP onboarding data
      console.log('APP Invoice Processing setup completed');
      
      // Redirect to APP dashboard
      router.push('/dashboard/app');
      
    } catch (error) {
      console.error('APP onboarding failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipForNow = () => {
    router.push('/dashboard/app');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Access Point Provider Setup
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            Configure your invoice processing and FIRS integration
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="space-y-6">
            {/* Step 1: FIRS Integration */}
            <div className="border-b pb-6">
              <h3 className="text-xl font-semibold mb-4">1. FIRS Integration Setup</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    FIRS API Key
                  </label>
                  <input 
                    type="password" 
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="Enter your FIRS API key"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Environment
                  </label>
                  <select className="w-full border border-gray-300 rounded-md px-3 py-2">
                    <option value="sandbox">Sandbox (Testing)</option>
                    <option value="production">Production</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Step 2: Invoice Processing Preferences */}
            <div className="border-b pb-6">
              <h3 className="text-xl font-semibold mb-4">2. Invoice Processing Preferences</h3>
              <div className="space-y-4">
                <div className="flex items-center">
                  <input type="checkbox" id="auto-validate" className="mr-3" />
                  <label htmlFor="auto-validate" className="text-sm text-gray-700">
                    Enable automatic invoice validation
                  </label>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" id="batch-processing" className="mr-3" />
                  <label htmlFor="batch-processing" className="text-sm text-gray-700">
                    Enable batch processing for high-volume invoices
                  </label>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" id="real-time-sync" className="mr-3" />
                  <label htmlFor="real-time-sync" className="text-sm text-gray-700">
                    Real-time synchronization with FIRS
                  </label>
                </div>
              </div>
            </div>

            {/* Step 3: Compliance Settings */}
            <div className="pb-6">
              <h3 className="text-xl font-semibold mb-4">3. Nigerian Compliance Settings</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    VAT Registration Number
                  </label>
                  <input 
                    type="text" 
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="Enter VAT number"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Tax Rate (%)
                  </label>
                  <input 
                    type="number" 
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="7.5"
                    defaultValue="7.5"
                  />
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between pt-6 border-t">
              <button 
                onClick={handleSkipForNow}
                className="px-6 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Skip for Now
              </button>
              <button 
                onClick={handleComplete}
                disabled={isLoading}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? 'Setting up...' : 'Complete Setup'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}