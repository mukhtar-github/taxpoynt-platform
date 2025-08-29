/**
 * SDK Hub Component for System Integrators
 * Provides SDK downloads, documentation, and integration tools
 */

import React, { useState, useEffect } from 'react';
import { TaxPoyntButton } from '../../../design_system';
import { secureLogger } from '../../../shared_components/utils/secureLogger';

interface SDKInfo {
  id: string;
  name: string;
  language: string;
  version: string;
  description: string;
  downloadUrl: string;
  documentationUrl: string;
  examples: string[];
  features: string[];
  requirements: string[];
  lastUpdated: string;
  downloads: number;
  rating: number;
}

interface SDKCatalogResponse {
  success: boolean;
  data: {
    sdk_catalog: Record<string, any>;
    total_count: number;
    languages_available: string[];
  };
  message: string;
}

export interface SDKHubProps {
  className?: string;
  onSDKDownload?: (sdkId: string) => void;
  onSDKTest?: (sdkId: string) => void;
}

export const SDKHub: React.FC<SDKHubProps> = ({
  className = '',
  onSDKDownload,
  onSDKTest
}) => {
  const [selectedSDK, setSelectedSDK] = useState<SDKInfo | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sdkCatalog, setSdkCatalog] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch SDK catalog from backend
  useEffect(() => {
    const fetchSDKCatalog = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch('/api/v1/si/sdk/catalog', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`Failed to fetch SDK catalog: ${response.status}`);
        }
        
        const data: SDKCatalogResponse = await response.json();
        
        if (data.success) {
          setSdkCatalog(data.data.sdk_catalog);
          secureLogger.info('SDK catalog fetched successfully', { count: data.data.total_count });
        } else {
          throw new Error(data.message || 'Failed to fetch SDK catalog');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
        setError(errorMessage);
        secureLogger.error('Failed to fetch SDK catalog', { error: errorMessage });
      } finally {
        setLoading(false);
      }
    };

    fetchSDKCatalog();
  }, []);

  // Transform backend data to frontend format
  const transformSDKData = (backendData: Record<string, any>): SDKInfo[] => {
    return Object.entries(backendData).map(([key, sdk]) => ({
      id: key,
      name: sdk.name,
      language: sdk.language,
      version: sdk.version,
      description: sdk.description,
      downloadUrl: `/api/v1/si/sdk/download/${key}`,
      documentationUrl: `/api/v1/si/sdk/documentation/${key}`,
      examples: sdk.examples || [],
      features: sdk.features || [],
      requirements: sdk.dependencies || [],
      lastUpdated: sdk.last_updated,
      downloads: sdk.download_count || 0,
      rating: 4.5 // Default rating since backend doesn't provide this yet
    }));
  };

  const sdkCategories = [
    {
      id: 'core',
      name: 'Core SDKs',
      icon: '🔧',
      sdks: transformSDKData(sdkCatalog)
    }
  ];

  const handleSDKDownload = async (sdkId: string) => {
    try {
      const sdk = sdkCategories[0].sdks.find(s => s.id === sdkId);
      if (!sdk) return;

      // Trigger download
      const response = await fetch(sdk.downloadUrl, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status}`);
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${sdk.name.replace(/\s+/g, '-').toLowerCase()}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Log successful download
      secureLogger.userAction('SDK downloaded', { sdkId, sdkName: sdk.name });
      
      // Call parent callback if provided
      if (onSDKDownload) {
        onSDKDownload(sdkId);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Download failed';
      secureLogger.error('SDK download failed', { sdkId, error: errorMessage });
      alert(`Download failed: ${errorMessage}`);
    }
  };

  const handleSDKTest = (sdkId: string) => {
    secureLogger.userAction('SDK test initiated', { sdkId });
    if (onSDKTest) {
      onSDKTest(sdkId);
    }
  };

  const filteredSDKs = sdkCategories
    .flatMap(category => category.sdks)
    .filter(sdk => 
      sdk.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sdk.language.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sdk.description.toLowerCase().includes(searchQuery.toLowerCase())
    );

  if (loading) {
    return (
      <div className={`sdk-hub ${className}`}>
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading SDK catalog...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`sdk-hub ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="text-red-600 text-lg font-semibold mb-2">Failed to Load SDKs</div>
          <div className="text-red-500 mb-4">{error}</div>
          <TaxPoyntButton 
            variant="primary" 
            onClick={() => window.location.reload()}
          >
            Retry
          </TaxPoyntButton>
        </div>
      </div>
    );
  }

  return (
    <div className={`sdk-hub ${className}`}>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">SDK Hub</h1>
        <p className="text-gray-600">
          Download and integrate TaxPoynt SDKs into your applications
        </p>
      </div>

      {/* Search and Filter */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search SDKs by name, language, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All Categories</option>
          {sdkCategories.map(category => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
        </select>
      </div>

      {/* SDK Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSDKs.map((sdk) => (
          <div
            key={sdk.id}
            className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow duration-200"
          >
            {/* SDK Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">{sdk.name}</h3>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                    {sdk.language}
                  </span>
                  <span>v{sdk.version}</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">Downloads</div>
                <div className="text-lg font-semibold text-gray-900">{sdk.downloads.toLocaleString()}</div>
              </div>
            </div>

            {/* Description */}
            <p className="text-gray-600 mb-4 line-clamp-2">{sdk.description}</p>

            {/* Features */}
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Features</h4>
              <div className="flex flex-wrap gap-1">
                {sdk.features.slice(0, 3).map((feature, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                  >
                    {feature}
                  </span>
                ))}
                {sdk.features.length > 3 && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                    +{sdk.features.length - 3} more
                  </span>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <TaxPoyntButton
                variant="primary"
                onClick={() => handleSDKDownload(sdk.id)}
                className="flex-1"
              >
                Download
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="outline"
                onClick={() => handleSDKTest(sdk.id)}
              >
                Test
              </TaxPoyntButton>
            </div>

            {/* Quick Links */}
            <div className="mt-4 pt-4 border-t border-gray-100 flex gap-3 text-sm">
              <a
                href={sdk.documentationUrl}
                className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
              >
                📚 Docs
              </a>
              <a
                href={`/si/sdk-sandbox?language=${sdk.language}`}
                className="text-green-600 hover:text-green-800 flex items-center gap-1"
              >
                🧪 Sandbox
              </a>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredSDKs.length === 0 && !loading && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">🔍</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No SDKs Found</h3>
          <p className="text-gray-600">
            Try adjusting your search criteria or browse all available SDKs
          </p>
        </div>
      )}
    </div>
  );
};

export default SDKHub;

