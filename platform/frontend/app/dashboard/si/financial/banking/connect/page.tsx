'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import MonoBankingDashboard from '../../../../../si_interface/components/financial_systems/banking_integration/MonoBankingDashboard';

export default function BankingConnectPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.back()}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              ← Back to Dashboard
            </button>
            <div className="h-6 border-l border-gray-300"></div>
            <h1 className="text-xl font-semibold text-gray-900">
              Banking Integration
            </h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto">
        <MonoBankingDashboard />
      </div>
    </div>
  );
}