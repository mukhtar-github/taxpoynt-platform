'use client';

/**
 * SDK Documentation Page
 * ======================
 * Comprehensive documentation for all TaxPoynt SDKs
 * Includes examples, API references, and integration guides
 */

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton } from '../../design_system';
import apiClient from '../../shared_components/api/client';
import { secureLogger } from '../../shared_components/utils/secureLogger';

interface CodeExample {
  id: string;
  title: string;
  description: string;
  language: 'python' | 'javascript' | 'php' | 'bash';
  code: string;
  output?: string;
}

interface APIMethod {
  id: string;
  name: string;
  description: string;
  endpoint: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  parameters: Array<{
    name: string;
    type: string;
    required: boolean;
    description: string;
  }>;
  response: {
    success: any;
    error: any;
  };
  examples: CodeExample[];
}

interface SDKDocumentation {
  id: string;
  name: string;
  language: string;
  version: string;
  description: string;
  installation: string;
  quickStart: CodeExample[];
  apiMethods: APIMethod[];
  examples: CodeExample[];
  troubleshooting: Array<{
    issue: string;
    solution: string;
  }>;
}

interface BackendDocumentation {
  overview: {
    title: string;
    description: string;
    version: string;
    last_updated: string;
  };
  quick_start: {
    title: string;
    steps: string[];
    code_examples: Record<string, string>;
  };
  api_reference: {
    title: string;
    endpoints: Array<{
      name: string;
      method: string;
      path: string;
    }>;
  };
  examples: {
    title: string;
    snippets: Array<{
      name: string;
      code: string;
    }>;
  };
  troubleshooting: {
    title: string;
    common_issues: string[];
  };
}

export default function SDKDocumentationPage() {
  const [selectedSDK, setSelectedSDK] = useState('python');
  const [activeTab, setActiveTab] = useState('overview');
  const [documentation, setDocumentation] = useState<BackendDocumentation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const availableSDKs = [
    { id: 'python', name: 'Python SDK', language: 'Python' },
    { id: 'javascript', name: 'JavaScript SDK', language: 'JavaScript' }
  ];

  // Fetch documentation from backend
  useEffect(() => {
    const fetchDocumentation = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const data = await apiClient.get<{
          success: boolean;
          data: { documentation: BackendDocumentation };
          message?: string;
        }>(`/si/sdk/documentation/${selectedSDK}`);

        if (data.success) {
          setDocumentation(data.data.documentation);
          secureLogger.info('SDK documentation loaded successfully', { sdk: selectedSDK });
        } else {
          throw new Error(data.message || 'Failed to load documentation');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load documentation';
        setError(errorMessage);
        secureLogger.error('Failed to fetch SDK documentation', { sdk: selectedSDK, error: errorMessage });
      } finally {
        setLoading(false);
      }
    };

    if (selectedSDK) {
      fetchDocumentation();
    }
  }, [selectedSDK]);

  const handleSDKChange = (sdkId: string) => {
    setSelectedSDK(sdkId);
    setActiveTab('overview');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    secureLogger.userAction('Code copied to clipboard', { sdk: selectedSDK });
  };

  const getLanguageIcon = (language: string) => {
    switch (language.toLowerCase()) {
      case 'python': return '🐍';
      case 'javascript': return '🟨';
      case 'php': return '🐘';
      case 'bash': return '💻';
      default: return '📝';
    }
  };

  if (loading) {
    return (
      <DashboardLayout role="si">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading documentation...</span>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout role="si">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <div className="text-red-600 text-lg font-semibold mb-2">Failed to Load Documentation</div>
            <div className="text-red-500 mb-4">{error}</div>
            <TaxPoyntButton 
              variant="primary" 
              onClick={() => window.location.reload()}
            >
              Retry
            </TaxPoyntButton>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout role="si">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📚 SDK Documentation</h1>
          <p className="text-gray-600">
            Comprehensive guides and examples for TaxPoynt SDKs
          </p>
        </div>

        {/* SDK Selection */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Select SDK</h2>
          <div className="flex flex-wrap gap-3">
            {availableSDKs.map((sdk) => (
              <button
                key={sdk.id}
                onClick={() => handleSDKChange(sdk.id)}
                className={`px-4 py-2 rounded-lg border transition-colors ${
                  selectedSDK === sdk.id
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {getLanguageIcon(sdk.language)} {sdk.name}
              </button>
            ))}
          </div>
        </div>

        {documentation && (
          <>
            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                  {[
                    { id: 'overview', label: 'Overview', icon: '📖' },
                    { id: 'quick-start', label: 'Quick Start', icon: '🚀' },
                    { id: 'api-reference', label: 'API Reference', icon: '🔗' },
                    { id: 'examples', label: 'Examples', icon: '💡' },
                    { id: 'troubleshooting', label: 'Troubleshooting', icon: '🔧' }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                        activeTab === tab.id
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      {tab.icon} {tab.label}
                    </button>
                  ))}
                </nav>
              </div>

              {/* Tab Content */}
              <div className="p-6">
                {/* Overview Tab */}
                {activeTab === 'overview' && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      {documentation.overview.title}
                    </h2>
                    <p className="text-gray-600 mb-6">
                      {documentation.overview.description}
                    </p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="font-semibold text-gray-900 mb-2">Version</h3>
                        <p className="text-gray-600">{documentation.overview.version}</p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="font-semibold text-gray-900 mb-2">Last Updated</h3>
                        <p className="text-gray-600">{documentation.overview.last_updated}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Quick Start Tab */}
                {activeTab === 'quick-start' && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      {documentation.quick_start.title}
                    </h2>
                    
                    <div className="space-y-6">
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="font-semibold text-gray-900 mb-3">Steps</h3>
                        <ol className="list-decimal list-inside space-y-2 text-gray-700">
                          {documentation.quick_start.steps.map((step, index) => (
                            <li key={index}>{step}</li>
                          ))}
                        </ol>
                      </div>
                      
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="font-semibold text-gray-900 mb-3">Code Examples</h3>
                        {Object.entries(documentation.quick_start.code_examples).map(([key, code]) => (
                          <div key={key} className="mb-4">
                            <h4 className="font-medium text-gray-800 mb-2 capitalize">
                              {key.replace('_', ' ')}
                            </h4>
                            <div className="relative">
                              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                                {code}
                              </pre>
                              <button
                                onClick={() => copyToClipboard(code)}
                                className="absolute top-2 right-2 bg-gray-700 text-white px-2 py-1 rounded text-xs hover:bg-gray-600"
                              >
                                Copy
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* API Reference Tab */}
                {activeTab === 'api-reference' && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      {documentation.api_reference.title}
                    </h2>
                    
                    <div className="space-y-4">
                      {documentation.api_reference.endpoints.map((endpoint, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-4">
                          <div className="flex items-center gap-3 mb-2">
                            <span className={`px-2 py-1 rounded text-sm font-medium ${
                              endpoint.method === 'GET' ? 'bg-green-100 text-green-800' :
                              endpoint.method === 'POST' ? 'bg-blue-100 text-blue-800' :
                              endpoint.method === 'PUT' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {endpoint.method}
                            </span>
                            <h3 className="font-semibold text-gray-900">{endpoint.name}</h3>
                          </div>
                          <p className="text-gray-600 mb-2">{endpoint.path}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Examples Tab */}
                {activeTab === 'examples' && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      {documentation.examples.title}
                    </h2>
                    
                    <div className="space-y-4">
                      {documentation.examples.snippets.map((example, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-4">
                          <h3 className="font-semibold text-gray-900 mb-2">{example.name}</h3>
                          <div className="relative">
                            <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                              {example.code}
                            </pre>
                            <button
                              onClick={() => copyToClipboard(example.code)}
                              className="absolute top-2 right-2 bg-gray-700 text-white px-2 py-1 rounded text-xs hover:bg-gray-600"
                            >
                              Copy
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Troubleshooting Tab */}
                {activeTab === 'troubleshooting' && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      {documentation.troubleshooting.title}
                    </h2>
                    
                    <div className="space-y-4">
                      {documentation.troubleshooting.common_issues.map((issue, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-4">
                          <h3 className="font-semibold text-gray-900 mb-2">
                            Issue {index + 1}
                          </h3>
                          <p className="text-gray-700">{issue}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-4">🚀 Ready to Get Started?</h3>
              <div className="flex flex-wrap gap-4">
                <TaxPoyntButton
                  variant="primary"
                  onClick={() => window.open(`/si/sdk-hub`, '_blank')}
                >
                  Download SDK
                </TaxPoyntButton>
                <TaxPoyntButton
                  variant="outline"
                  onClick={() => window.open(`/si/sdk-sandbox`, '_blank')}
                >
                  Test in Sandbox
                </TaxPoyntButton>
                <TaxPoyntButton
                  variant="outline"
                  onClick={() => window.open(`/si/support`, '_blank')}
                >
                  Get Support
                </TaxPoyntButton>
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
