'use client';

/**
 * SDK Sandbox Page
 * ================
 * Interactive testing environment for TaxPoynt SDKs
 * Allows System Integrators to test API calls and SDK functionality
 */

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton } from '../../design_system';
import apiClient from '../../shared_components/api/client';
import { secureLogger } from '../../shared_components/utils/secureLogger';

interface SandboxTest {
  id: string;
  name: string;
  description: string;
  endpoint: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  requestBody?: string;
  response?: any;
  status: 'pending' | 'running' | 'success' | 'error';
  executionTime?: number;
}

interface APIScenario {
  name: string;
  description: string;
  endpoint: string;
  method: string;
  headers: Record<string, string>;
  body: any;
  expected_response: any;
}

interface SandboxScenariosResponse {
  success: boolean;
  data: {
    scenarios: Record<string, APIScenario>;
  };
  message: string;
}

interface TestResult {
  scenario: string;
  status: string;
  response_time_ms: number;
  status_code: number;
  response_body: any;
  headers_sent: Record<string, string>;
  body_sent: any;
  tested_at: string;
}

export default function SDKSandboxPage() {
  const [selectedSDK, setSelectedSDK] = useState('python-core');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('https://sandbox-api.taxpoynt.com');
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<SandboxTest[]>([]);
  const [activeTest, setActiveTest] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<Record<string, APIScenario>>({});
  const [loadingScenarios, setLoadingScenarios] = useState(true);

  const availableSDKs = [
    { id: 'python-core', name: 'Python Core SDK', language: 'Python' },
    { id: 'javascript-core', name: 'JavaScript Core SDK', language: 'JavaScript' },
    { id: 'mono-banking', name: 'Mono Banking SDK', language: 'Python' }
  ];

  // Fetch available test scenarios from backend
  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        setLoadingScenarios(true);
        const data = await apiClient.get<SandboxScenariosResponse>(
          '/si/sdk/sandbox/scenarios'
        );
        
        if (data.success) {
          setScenarios(data.data.scenarios);
          
          // Transform scenarios to test format
          const transformedTests: SandboxTest[] = Object.entries(data.data.scenarios).map(([key, scenario]) => ({
            id: key,
            name: scenario.name,
            description: scenario.description,
            endpoint: scenario.endpoint,
            method: scenario.method as 'GET' | 'POST' | 'PUT' | 'DELETE',
            requestBody: scenario.body ? JSON.stringify(scenario.body, null, 2) : undefined,
            status: 'pending' as const
          }));
          
          setTestResults(transformedTests);
          secureLogger.info('Sandbox scenarios loaded successfully', { count: transformedTests.length });
        } else {
          throw new Error(data.message || 'Failed to load scenarios');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load scenarios';
        secureLogger.error('Failed to fetch sandbox scenarios', { error: errorMessage });
        
        // Fallback to default tests if backend fails
        const defaultTests: SandboxTest[] = [
          {
            id: 'auth-test',
            name: 'Authentication Test',
            description: 'Test API key authentication and get user info',
            endpoint: '/api/v1/auth/me',
            method: 'GET',
            status: 'pending'
          },
          {
            id: 'business-systems',
            name: 'Business Systems List',
            description: 'Retrieve list of connected business systems',
            endpoint: '/api/v1/si/business-systems',
            method: 'GET',
            status: 'pending'
          }
        ];
        setTestResults(defaultTests);
      } finally {
        setLoadingScenarios(false);
      }
    };

    fetchScenarios();
  }, []);

  const handleRunTest = async (test: SandboxTest) => {
    if (!apiKey) {
      alert('Please enter your API key first');
      return;
    }

    setActiveTest(test.id);
    setIsLoading(true);

    // Update test status
    setTestResults(prev => 
      prev.map(t => 
        t.id === test.id 
          ? { ...t, status: 'running' as const }
          : t
      )
    );

    try {
      const startTime = Date.now();
      
      // Use backend sandbox test endpoint
      const testResult = await apiClient.post<TestResult>(
        '/si/sdk/sandbox/test',
        {
          scenario_name: test.id,
          api_key: apiKey,
          custom_headers: {
            'Content-Type': 'application/json'
          },
          custom_body: test.requestBody ? JSON.parse(test.requestBody) : undefined
        }
      );
      const executionTime = Date.now() - startTime;
      
      // Update test results
      setTestResults(prev => 
        prev.map(t => 
          t.id === test.id 
            ? { 
                ...t, 
                status: 'success' as const,
                response: testResult.response_body,
                executionTime
              }
            : t
        )
      );
      
      secureLogger.userAction('Sandbox test completed', { 
        testId: test.id, 
        status: 'success',
        executionTime 
      });
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Test failed';
      
      setTestResults(prev => 
        prev.map(t => 
          t.id === test.id 
            ? { 
                ...t, 
                status: 'error' as const,
                response: { error: errorMessage }
              }
            : t
        )
      );
      
      secureLogger.error('Sandbox test failed', { 
        testId: test.id, 
        error: errorMessage 
      });
    } finally {
      setIsLoading(false);
      setActiveTest(null);
    }
  };

  const handleRunAllTests = async () => {
    if (!apiKey) {
      alert('Please enter your API key first');
      return;
    }

    setIsLoading(true);
    
    for (const test of testResults) {
      await handleRunTest(test);
      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    setIsLoading(false);
  };

  const resetTests = () => {
    setTestResults(prev => 
      prev.map(test => ({ ...test, status: 'pending' as const, response: undefined, executionTime: undefined }))
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-600 bg-green-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'running': return '🔄';
      default: return '⏳';
    }
  };

  return (
    <DashboardLayout role="si">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🧪 SDK Sandbox</h1>
          <p className="text-gray-600">
            Test TaxPoynt SDKs and API endpoints in a safe sandbox environment
          </p>
        </div>

        {/* Configuration Panel */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SDK Selection
              </label>
              <select
                value={selectedSDK}
                onChange={(e) => setSelectedSDK(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {availableSDKs.map(sdk => (
                  <option key={sdk.id} value={sdk.id}>
                    {sdk.name} ({sdk.language})
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Base URL
              </label>
              <input
                type="text"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Test Controls */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">
            Available Tests ({testResults.length})
          </h2>
          
          <div className="flex gap-3">
            <TaxPoyntButton
              variant="outline"
              onClick={resetTests}
              disabled={isLoading}
            >
              Reset Tests
            </TaxPoyntButton>
            <TaxPoyntButton
              variant="primary"
              onClick={handleRunAllTests}
              disabled={isLoading || testResults.length === 0}
            >
              {isLoading ? 'Running...' : 'Run All Tests'}
            </TaxPoyntButton>
          </div>
        </div>

        {/* Loading State */}
        {loadingScenarios && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading test scenarios...</p>
          </div>
        )}

        {/* Test Results Grid */}
        {!loadingScenarios && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {testResults.map((test) => (
              <div
                key={test.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
              >
                {/* Test Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {test.name}
                    </h3>
                    <p className="text-sm text-gray-600 mb-2">
                      {test.description}
                    </p>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded">
                        {test.method}
                      </span>
                      <span className="text-gray-500 font-mono">
                        {test.endpoint}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(test.status)}`}>
                      {getStatusIcon(test.status)} {test.status}
                    </span>
                  </div>
                </div>

                {/* Request Body Preview */}
                {test.requestBody && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Request Body</h4>
                    <pre className="bg-gray-50 p-3 rounded text-sm text-gray-800 overflow-x-auto">
                      {test.requestBody}
                    </pre>
                  </div>
                )}

                {/* Response */}
                {test.response && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Response</h4>
                    <pre className="bg-gray-50 p-3 rounded text-sm text-gray-800 overflow-x-auto">
                      {JSON.stringify(test.response, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Execution Time */}
                {test.executionTime && (
                  <div className="text-sm text-gray-500 mb-4">
                    Execution time: {test.executionTime}ms
                  </div>
                )}

                {/* Test Actions */}
                <div className="flex justify-end">
                  <TaxPoyntButton
                    variant="outline"
                    onClick={() => handleRunTest(test)}
                    disabled={isLoading || activeTest === test.id}
                    size="sm"
                  >
                    {activeTest === test.id ? 'Running...' : 'Run Test'}
                  </TaxPoyntButton>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loadingScenarios && testResults.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">🧪</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Tests Available</h3>
            <p className="text-gray-600">
              No test scenarios are currently available. Please check back later.
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
