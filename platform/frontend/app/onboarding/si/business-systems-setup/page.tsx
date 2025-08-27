'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ERPOnboarding } from '../../../../si_interface/workflows/erp_onboarding';

export default function BusinessSystemsSetupPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleOnboardingComplete = async (onboardingData: any) => {
    setIsLoading(true);
    
    try {
      // Save onboarding data to user profile
      console.log('Business Systems (ERP) Onboarding completed:', onboardingData);
      
      // Redirect to SI dashboard after successful onboarding
      router.push('/dashboard/si');
      
    } catch (error) {
      console.error('Business Systems onboarding failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipForNow = () => {
    // Allow user to skip onboarding and go directly to dashboard
    router.push('/dashboard/si');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Header with clear distinction */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <div className="bg-blue-100 p-2 rounded-lg mr-4">
              <span className="text-2xl">🏢</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Business Systems Integration
              </h1>
              <p className="text-blue-600 font-medium">ERP, CRM, POS & E-commerce Systems</p>
            </div>
          </div>
          <p className="text-lg text-gray-600">
            Configure your business system integrations for comprehensive data management and automated tax compliance
          </p>
        </div>

        {/* Integration overview */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">What You'll Set Up:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start">
              <span className="text-blue-500 mr-3 mt-1">📊</span>
              <div>
                <h4 className="font-medium text-gray-900">ERP Systems</h4>
                <p className="text-sm text-gray-600">Connect SAP, Odoo, NetSuite, QuickBooks, or custom ERP</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-green-500 mr-3 mt-1">👥</span>
              <div>
                <h4 className="font-medium text-gray-900">CRM Integration</h4>
                <p className="text-sm text-gray-600">Sync customer data from Salesforce, HubSpot, Zoho</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-purple-500 mr-3 mt-1">🛒</span>
              <div>
                <h4 className="font-medium text-gray-900">POS Systems</h4>
                <p className="text-sm text-gray-600">Integrate Square, Clover, Toast, or custom POS</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-orange-500 mr-3 mt-1">🌐</span>
              <div>
                <h4 className="font-medium text-gray-900">E-commerce</h4>
                <p className="text-sm text-gray-600">Connect Shopify, WooCommerce, Magento stores</p>
              </div>
            </div>
          </div>
        </div>

        {/* Important note */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <span className="text-amber-500 mr-3 mt-0.5">⚠️</span>
            <div>
              <h4 className="text-amber-800 font-medium mb-1">Business Systems Only</h4>
              <p className="text-amber-700 text-sm">
                This setup focuses on business data systems. For banking and payment integrations, 
                you can set those up separately through Financial Systems Integration.
              </p>
            </div>
          </div>
        </div>
        
        {/* Use existing ERP onboarding flow */}
        <ERPOnboarding 
          onComplete={handleOnboardingComplete}
          onSkip={handleSkipForNow}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
