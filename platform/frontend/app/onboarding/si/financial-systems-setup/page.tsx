'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { MonoBankingDashboard } from '../../../../si_interface/components/financial_systems/banking_integration/MonoBankingDashboard';

export default function FinancialSystemsSetupPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleOnboardingComplete = async (onboardingData: any) => {
    setIsLoading(true);
    
    try {
      console.log('Financial Systems (Banking) Onboarding completed:', onboardingData);
      router.push('/dashboard/si');
    } catch (error) {
      console.error('Financial Systems onboarding failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipForNow = () => {
    router.push('/dashboard/si');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Header with clear distinction */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <div className="bg-green-100 p-2 rounded-lg mr-4">
              <span className="text-2xl">💰</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Financial Systems Integration
              </h1>
              <p className="text-green-600 font-medium">Banking, Payments & Financial Data</p>
            </div>
          </div>
          <p className="text-lg text-gray-600">
            Connect your banking and payment systems for automated financial data sync and real-time transaction processing
          </p>
        </div>

        {/* Integration overview */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">What You'll Set Up:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start">
              <span className="text-green-500 mr-3 mt-1">🏦</span>
              <div>
                <h4 className="font-medium text-gray-900">Banking Integration</h4>
                <p className="text-sm text-gray-600">Connect bank accounts via Mono Open Banking API</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-blue-500 mr-3 mt-1">💳</span>
              <div>
                <h4 className="font-medium text-gray-900">Payment Processors</h4>
                <p className="text-sm text-gray-600">Integrate Paystack, Flutterwave, Razorpay</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-purple-500 mr-3 mt-1">🔄</span>
              <div>
                <h4 className="font-medium text-gray-900">Account Reconciliation</h4>
                <p className="text-sm text-gray-600">Automated transaction matching and categorization</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-orange-500 mr-3 mt-1">📊</span>
              <div>
                <h4 className="font-medium text-gray-900">Financial Analytics</h4>
                <p className="text-sm text-gray-600">Real-time financial reporting and tax calculations</p>
              </div>
            </div>
          </div>
        </div>

        {/* Important note */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <span className="text-blue-500 mr-3 mt-0.5">ℹ️</span>
            <div>
              <h4 className="text-blue-800 font-medium mb-1">Financial Systems Only</h4>
              <p className="text-blue-700 text-sm">
                This setup focuses on banking and payment integrations. For business data systems like ERP/CRM, 
                you can set those up separately through Business Systems Integration.
              </p>
            </div>
          </div>
        </div>

        {/* Banking onboarding steps */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">Banking Integration Setup</h3>
          
          {/* Step-by-step process */}
          <div className="space-y-6">
            {/* Step 1: Mono Setup */}
            <div className="flex items-start p-4 border border-gray-200 rounded-lg">
              <div className="bg-green-100 text-green-600 rounded-full w-8 h-8 flex items-center justify-center font-bold mr-4 flex-shrink-0">
                1
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-2">Mono Banking Setup</h4>
                <p className="text-gray-600 mb-3">
                  Connect your Nigerian bank accounts securely through Mono's Open Banking platform
                </p>
                <div className="flex items-center text-sm text-gray-500">
                  <span className="mr-4">⏱️ 10-15 minutes</span>
                  <span>🔒 Bank-grade security</span>
                </div>
              </div>
            </div>

            {/* Step 2: Payment Processors */}
            <div className="flex items-start p-4 border border-gray-200 rounded-lg">
              <div className="bg-blue-100 text-blue-600 rounded-full w-8 h-8 flex items-center justify-center font-bold mr-4 flex-shrink-0">
                2
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-2">Payment Processors</h4>
                <p className="text-gray-600 mb-3">
                  Configure Paystack, Flutterwave, or other payment gateways for transaction processing
                </p>
                <div className="flex items-center text-sm text-gray-500">
                  <span className="mr-4">⏱️ 5-10 minutes per processor</span>
                  <span>🛡️ PCI compliant</span>
                </div>
              </div>
            </div>

            {/* Step 3: Reconciliation Rules */}
            <div className="flex items-start p-4 border border-gray-200 rounded-lg">
              <div className="bg-purple-100 text-purple-600 rounded-full w-8 h-8 flex items-center justify-center font-bold mr-4 flex-shrink-0">
                3
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-2">Reconciliation Rules</h4>
                <p className="text-gray-600 mb-3">
                  Set up automatic transaction categorization and matching rules for seamless reconciliation
                </p>
                <div className="flex items-center text-sm text-gray-500">
                  <span className="mr-4">⏱️ 15-20 minutes</span>
                  <span>🎯 Smart matching</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
            <button
              onClick={handleSkipForNow}
              className="px-6 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Skip for Now
            </button>
            
            <button
              onClick={() => {
                console.log('Starting financial systems setup...');
                // For now, redirect to placeholder
                router.push('/dashboard/si');
              }}
              disabled={isLoading}
              className={`
                px-8 py-2 rounded-md font-medium transition-all duration-200
                ${!isLoading
                  ? 'bg-green-600 text-white hover:bg-green-700 shadow-md'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }
              `}
            >
              {isLoading ? 'Setting up...' : 'Start Banking Setup'}
            </button>
          </div>
        </div>

        {/* Help and support */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-start">
            <span className="text-gray-500 mr-3 mt-0.5">💬</span>
            <div>
              <h4 className="text-gray-900 font-medium mb-1">Need Help?</h4>
              <p className="text-gray-600 text-sm">
                Our team can help you set up banking integrations. Contact support for assistance with 
                bank connections, payment processor configurations, or reconciliation setup.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
