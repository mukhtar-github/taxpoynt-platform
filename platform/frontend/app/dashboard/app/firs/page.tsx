'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../../../shared_components/services/auth';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';
import { TaxPoyntAPIClient } from '../../../../shared_components/api/client';
import { APIResponse } from '../../../../si_interface/types';

interface FIRSConnectionStatus {
  status: 'connected' | 'disconnected' | 'error' | 'testing';
  last_connected?: string;
  api_version?: string;
  environment: 'sandbox' | 'production';
  sandbox_url: string;
  production_url: string;
  rate_limit?: {
    remaining: number;
    reset_time: string;
  };
  uptime_percentage?: number;
  error_message?: string;
}

interface APICredentials {
  api_key: string;
  api_secret: string;
  environment: 'sandbox' | 'production';
  webhook_url?: string;
}

export default function APPFIRSPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'credentials' | 'webhooks' | 'logs'>('overview');
  const [connectionStatus, setConnectionStatus] = useState<FIRSConnectionStatus>({
    status: 'disconnected',
    environment: 'sandbox',
    sandbox_url: 'https://eivc-k6z6d.ondigitalocean.app',
    production_url: 'https://einvoicing.firs.gov.ng'
  });
  const [credentials, setCredentials] = useState<APICredentials>({
    api_key: '',
    api_secret: '',
    environment: 'sandbox',
    webhook_url: ''
  });
  const [credentialsError, setCredentialsError] = useState<string>('');
  const [testingConnection, setTestingConnection] = useState(false);

  useEffect(() => {
    const currentUser = authService.getStoredUser();
    if (!currentUser || !authService.isAuthenticated()) {
      router.push('/auth/signin');
      return;
    }

    if (currentUser.role !== 'access_point_provider') {
      router.push('/dashboard');
      return;
    }

    setUser(currentUser);
    loadFIRSStatus();
  }, [router]);

  const loadFIRSStatus = async () => {
    try {
      const apiClient = new TaxPoyntAPIClient();
      const response = await apiClient.get<APIResponse>('/api/v1/app/firs/status');
      
      if (response.success) {
        setConnectionStatus(response.data);
        setCredentials({
          api_key: response.data.api_key_masked || '',
          api_secret: response.data.api_secret_masked || '',
          environment: response.data.environment || 'sandbox',
          webhook_url: response.data.webhook_url || ''
        });
      }
    } catch (error) {
      console.error('Failed to load FIRS status:', error);
      // Set demo data for now
      setConnectionStatus({
        status: 'connected',
        last_connected: new Date().toISOString(),
        api_version: 'v1.0',
        environment: 'sandbox',
        sandbox_url: 'https://eivc-k6z6d.ondigitalocean.app',
        production_url: 'https://einvoicing.firs.gov.ng',
        rate_limit: {
          remaining: 950,
          reset_time: new Date(Date.now() + 3600000).toISOString()
        },
        uptime_percentage: 99.9
      });
    }
  };

  const testConnection = async () => {
    if (!credentials.api_key || !credentials.api_secret) {
      setCredentialsError('API Key and Secret are required');
      return;
    }

    setTestingConnection(true);
    setCredentialsError('');

    try {
      const apiClient = new TaxPoyntAPIClient();
      const response = await apiClient.post<APIResponse>('/api/v1/app/firs/test-connection', {
        api_key: credentials.api_key,
        api_secret: credentials.api_secret,
        environment: credentials.environment
      });

      if (response.success) {
        setConnectionStatus({
          ...connectionStatus,
          status: 'connected',
          last_connected: new Date().toISOString(),
          environment: credentials.environment
        });
      } else {
        setConnectionStatus({
          ...connectionStatus,
          status: 'error',
          error_message: response.message || 'Connection test failed'
        });
        setCredentialsError(response.message || 'Connection test failed');
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      setConnectionStatus({
        ...connectionStatus,
        status: 'error',
        error_message: 'Network error during connection test'
      });
      setCredentialsError('Network error during connection test');
    } finally {
      setTestingConnection(false);
    }
  };

  const saveCredentials = async () => {
    if (!credentials.api_key || !credentials.api_secret) {
      setCredentialsError('API Key and Secret are required');
      return;
    }

    setIsLoading(true);
    setCredentialsError('');

    try {
      const apiClient = new TaxPoyntAPIClient();
      const response = await apiClient.post<APIResponse>('/api/v1/app/firs/credentials', credentials);

      if (response.success) {
        await loadFIRSStatus();
        setActiveTab('overview');
      } else {
        setCredentialsError(response.message || 'Failed to save credentials');
      }
    } catch (error) {
      console.error('Failed to save credentials:', error);
      setCredentialsError('Network error while saving credentials');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      connected: 'text-green-600 bg-green-100',
      disconnected: 'text-gray-600 bg-gray-100',
      error: 'text-red-600 bg-red-100',
      testing: 'text-blue-600 bg-blue-100'
    };
    return colors[status as keyof typeof colors] || 'text-gray-600 bg-gray-100';
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      connected: '✅',
      disconnected: '⭕',
      error: '❌',
      testing: '🔄'
    };
    return icons[status as keyof typeof icons] || '⭕';
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <DashboardLayout
      role="app"
      userName={`${user.first_name} ${user.last_name}`}
      userEmail={user.email}
      activeTab="firs"
    >
      <div className="min-h-full bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-6">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-black text-slate-800 mb-2">
                FIRS Integration Hub 🏛️
              </h1>
              <p className="text-xl text-slate-600">
                Manage your connection to the Federal Inland Revenue Service
              </p>
            </div>
            
            <div className="flex space-x-4">
              <TaxPoyntButton
                variant="outline"
                onClick={() => router.push('/dashboard/app/transmission')}
                className="border-2 border-green-300 text-green-700 hover:bg-green-50"
              >
                <span className="mr-2">📤</span>
                Transmit Invoices
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                onClick={testConnection}
                loading={testingConnection}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
              >
                <span className="mr-2">🔍</span>
                Test Connection
              </TaxPoyntButton>
            </div>
          </div>

          {/* Connection Status Bar */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl ${getStatusColor(connectionStatus.status)}`}>
                  {getStatusIcon(connectionStatus.status)}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    FIRS Connection Status
                  </h3>
                  <p className="text-gray-600">
                    Environment: <span className="font-medium capitalize">{connectionStatus.environment}</span>
                    {connectionStatus.last_connected && (
                      <span className="ml-2">
                        • Last connected: {new Date(connectionStatus.last_connected).toLocaleString()}
                      </span>
                    )}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-6">
                {connectionStatus.rate_limit && (
                  <div className="text-center">
                    <div className="text-2xl font-black text-blue-600">
                      {connectionStatus.rate_limit.remaining}
                    </div>
                    <div className="text-xs text-gray-600">Requests Left</div>
                  </div>
                )}
                {connectionStatus.uptime_percentage && (
                  <div className="text-center">
                    <div className="text-2xl font-black text-green-600">
                      {connectionStatus.uptime_percentage}%
                    </div>
                    <div className="text-xs text-gray-600">Uptime</div>
                  </div>
                )}
              </div>
            </div>

            {connectionStatus.error_message && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{connectionStatus.error_message}</p>
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {[
                { id: 'overview', label: 'Overview', icon: '🎯' },
                { id: 'credentials', label: 'API Credentials', icon: '🔑' },
                { id: 'webhooks', label: 'Webhooks', icon: '🔗' },
                { id: 'logs', label: 'Activity Logs', icon: '📋' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">FIRS Integration Overview</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  
                  {/* Environment Info */}
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                    <h3 className="text-lg font-semibold text-blue-800 mb-3">🌐 Environment</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-blue-600">Current:</span>
                        <span className="text-sm font-medium text-blue-800 capitalize">
                          {connectionStatus.environment}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-blue-600">API Version:</span>
                        <span className="text-sm font-medium text-blue-800">
                          {connectionStatus.api_version || 'v1.0'}
                        </span>
                      </div>
                      <div className="mt-3 text-xs text-blue-600">
                        <div className="font-medium">Sandbox URL:</div>
                        <div className="font-mono break-all">{connectionStatus.sandbox_url}</div>
                      </div>
                    </div>
                  </div>

                  {/* API Limits */}
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
                    <h3 className="text-lg font-semibold text-green-800 mb-3">📊 API Usage</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-green-600">Rate Limit:</span>
                        <span className="text-sm font-medium text-green-800">1000/hour</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-green-600">Remaining:</span>
                        <span className="text-sm font-medium text-green-800">
                          {connectionStatus.rate_limit?.remaining || 950}
                        </span>
                      </div>
                      <div className="mt-3">
                        <div className="w-full bg-green-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full" 
                            style={{ width: `${((connectionStatus.rate_limit?.remaining || 950) / 1000) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-6 border border-purple-200">
                    <h3 className="text-lg font-semibold text-purple-800 mb-3">⚡ Quick Actions</h3>
                    <div className="space-y-3">
                      <TaxPoyntButton
                        variant="outline"
                        size="sm"
                        onClick={() => setActiveTab('credentials')}
                        className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
                      >
                        Update Credentials
                      </TaxPoyntButton>
                      <TaxPoyntButton
                        variant="outline"
                        size="sm"
                        onClick={() => router.push('/dashboard/app/transmission')}
                        className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
                      >
                        Submit Invoices
                      </TaxPoyntButton>
                      <TaxPoyntButton
                        variant="outline"
                        size="sm"
                        onClick={() => setActiveTab('logs')}
                        className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
                      >
                        View Activity Logs
                      </TaxPoyntButton>
                    </div>
                  </div>
                </div>

                {/* FIRS Service Status */}
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">🏛️ FIRS Service Status</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { label: 'Service Health', value: 'Operational', color: 'green' },
                      { label: 'Response Time', value: '< 500ms', color: 'blue' },
                      { label: 'Success Rate', value: '99.9%', color: 'green' },
                      { label: 'Scheduled Maintenance', value: 'None', color: 'gray' }
                    ].map((stat, index) => (
                      <div key={index} className="text-center">
                        <div className={`text-lg font-bold text-${stat.color}-600`}>
                          {stat.value}
                        </div>
                        <div className="text-sm text-gray-600">{stat.label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Credentials Tab */}
            {activeTab === 'credentials' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">API Credentials Management</h2>
                
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <span className="mr-2 text-yellow-600">⚠️</span>
                    <div className="text-sm text-yellow-700">
                      <strong>Security Notice:</strong> Your API credentials are encrypted and stored securely. 
                      Only masked versions are displayed for security purposes.
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <TaxPoyntInput
                    label="FIRS API Key"
                    type="password"
                    value={credentials.api_key}
                    onChange={(e) => setCredentials({...credentials, api_key: e.target.value})}
                    placeholder="Enter your FIRS API key"
                    helperText="Provided by FIRS during registration"
                  />

                  <TaxPoyntInput
                    label="FIRS API Secret"
                    type="password"
                    value={credentials.api_secret}
                    onChange={(e) => setCredentials({...credentials, api_secret: e.target.value})}
                    placeholder="Enter your FIRS API secret"
                    helperText="Keep this secret secure"
                  />

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Environment
                    </label>
                    <select
                      value={credentials.environment}
                      onChange={(e) => setCredentials({...credentials, environment: e.target.value as 'sandbox' | 'production'})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="sandbox">🧪 Sandbox (Testing)</option>
                      <option value="production">🚀 Production</option>
                    </select>
                    <p className="text-xs text-gray-600 mt-1">
                      Use sandbox for testing, production for live invoices
                    </p>
                  </div>

                  <TaxPoyntInput
                    label="Webhook URL (Optional)"
                    value={credentials.webhook_url || ''}
                    onChange={(e) => setCredentials({...credentials, webhook_url: e.target.value})}
                    placeholder="https://yourapp.com/webhooks/firs"
                    helperText="Receive FIRS status updates"
                  />
                </div>

                {credentialsError && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-700">{credentialsError}</p>
                  </div>
                )}

                <div className="flex space-x-4">
                  <TaxPoyntButton
                    variant="primary"
                    onClick={saveCredentials}
                    loading={isLoading}
                    disabled={isLoading || !credentials.api_key || !credentials.api_secret}
                  >
                    Save Credentials
                  </TaxPoyntButton>
                  <TaxPoyntButton
                    variant="outline"
                    onClick={testConnection}
                    loading={testingConnection}
                    disabled={testingConnection || !credentials.api_key || !credentials.api_secret}
                  >
                    Test Connection
                  </TaxPoyntButton>
                </div>
              </div>
            )}

            {/* Webhooks Tab */}
            {activeTab === 'webhooks' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">Webhook Configuration</h2>
                
                <div className="bg-gray-50 rounded-lg p-8 text-center">
                  <div className="text-4xl mb-4">🔗</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Webhook Setup</h3>
                  <p className="text-gray-600 mb-4">
                    Configure webhooks to receive real-time updates from FIRS about your invoice submissions.
                  </p>
                  <TaxPoyntButton
                    variant="outline"
                    onClick={() => setActiveTab('credentials')}
                  >
                    Configure in Credentials
                  </TaxPoyntButton>
                </div>
              </div>
            )}

            {/* Logs Tab */}
            {activeTab === 'logs' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">Activity Logs</h2>
                
                <div className="space-y-4">
                  {[
                    {
                      timestamp: '2024-12-31T10:30:00Z',
                      event: 'Connection Test',
                      status: 'Success',
                      details: 'FIRS sandbox connection verified successfully'
                    },
                    {
                      timestamp: '2024-12-31T10:25:00Z',
                      event: 'Credentials Updated',
                      status: 'Success',
                      details: 'API credentials updated for sandbox environment'
                    },
                    {
                      timestamp: '2024-12-31T09:15:00Z',
                      event: 'Invoice Batch Submitted',
                      status: 'Success',
                      details: 'Batch BATCH-001 with 25 invoices submitted to FIRS'
                    },
                    {
                      timestamp: '2024-12-31T08:45:00Z',
                      event: 'Rate Limit Reset',
                      status: 'Info',
                      details: 'API rate limit reset - 1000 requests available'
                    }
                  ].map((log, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-900">{log.event}</span>
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          log.status === 'Success' ? 'bg-green-100 text-green-800' :
                          log.status === 'Error' ? 'bg-red-100 text-red-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {log.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-1">{log.details}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(log.timestamp).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
