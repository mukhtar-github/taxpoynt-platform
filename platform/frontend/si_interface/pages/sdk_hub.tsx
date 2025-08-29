/**
 * SDK Hub Page
 * =============
 * Main page for System Integrators to access, download, and manage TaxPoynt SDKs
 */

import React from 'react';
import { DashboardLayout } from '../../shared_components/layouts/DashboardLayout';
import SDKHub from '../components/sdk_hub/SDKHub';
import { secureLogger } from '../../shared_components/utils/secureLogger';

export default function SDKHubPage() {
  const handleSDKDownload = (sdkId: string) => {
    secureLogger.userAction('SDK download initiated', { sdk_id: sdkId });
  };

  const handleSDKTest = (sdkId: string) => {
    secureLogger.userAction('SDK testing initiated', { sdk_id: sdkId });
  };

  return (
    <DashboardLayout role="si" activeTab="sdk-hub">
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <SDKHub 
            onSDKDownload={handleSDKDownload}
            onSDKTest={handleSDKTest}
          />
        </div>
      </div>
    </DashboardLayout>
  );
}
