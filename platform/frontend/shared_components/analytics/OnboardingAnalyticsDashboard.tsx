'use client';

/**
 * Onboarding Analytics Dashboard
 * =============================
 * 
 * Comprehensive dashboard for visualizing onboarding analytics data.
 * Provides real-time insights into completion rates, drop-off points, and user behavior.
 * 
 * Features:
 * - Real-time metrics display
 * - Interactive charts and graphs
 * - Funnel visualization
 * - User journey analysis
 * - Performance monitoring
 * - Export capabilities
 */

import React, { useState, useEffect, useMemo } from 'react';
import apiClient from '../api/client';
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Clock, 
  AlertTriangle, 
  CheckCircle,
  BarChart3,
  PieChart,
  Download,
  Filter,
  Calendar,
  RefreshCw
} from 'lucide-react';

interface DashboardMetrics {
  completionRate: number;
  averageCompletionTime: number;
  dropOffPoints: Array<{
    stepId: string;
    dropOffRate: number;
    userCount: number;
  }>;
  stepPerformance: Array<{
    step_id: string;
    completion_rate: number;
    average_duration: number;
    error_rate: number;
    skip_rate: number;
  }>;
  userSegments: Array<{
    role: string;
    completionRate: number;
    averageTime: number;
    commonDropOff: string;
  }>;
  totalUsers: number;
  totalSessions: number;
}

interface DashboardProps {
  className?: string;
}

interface FilterOptions {
  dateRange: { start: Date; end: Date };
  userRole: 'all' | 'si' | 'app' | 'hybrid';
  stepId?: string;
}

export const OnboardingAnalyticsDashboard: React.FC<DashboardProps> = ({
  className = ''
}) => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterOptions>({
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
      end: new Date()
    },
    userRole: 'all'
  });
  const [realTimeData, setRealTimeData] = useState({
    activeUsers: 0,
    completionRateToday: 0,
    topDropOffStep: '',
    averageSessionTime: 0
  });

  // Load analytics data
  const loadAnalyticsData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams({
        start: filters.dateRange.start.toISOString(),
        end: filters.dateRange.end.toISOString(),
        ...(filters.userRole !== 'all' && { role: filters.userRole }),
        ...(filters.stepId && { step_id: filters.stepId })
      });

      const query = params.toString();
      const data = await apiClient.get<{ data: { metrics: DashboardMetrics } }>(
        `/analytics/onboarding/metrics${query ? `?${query}` : ''}`
      );
      setMetrics(data.data.metrics);

      // Load real-time dashboard data
      const dashboardData = await apiClient.get<{ data: { data: any } }>(
        '/analytics/onboarding/dashboard'
      );
      setRealTimeData(dashboardData.data.data);

    } catch (err) {
      console.error('Failed to load analytics data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load analytics data');
    } finally {
      setIsLoading(false);
    }
  };

  // Load data on mount and when filters change
  useEffect(() => {
    loadAnalyticsData();
  }, [filters]);

  // Auto-refresh real-time data
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const data = await apiClient.get<{ data: { data: any } }>(
          '/analytics/onboarding/dashboard'
        );
        setRealTimeData(data.data.data);
      } catch (error) {
        console.error('Failed to refresh real-time data:', error);
      }
    }, 60000); // Refresh every minute

    return () => clearInterval(interval);
  }, []);

  // Calculate trend indicators
  const trends = useMemo(() => {
    if (!metrics) return {};
    
    // These would typically come from historical data comparison
    return {
      completionRate: { value: 2.3, isUp: true },
      averageTime: { value: -1.2, isUp: false },
      totalUsers: { value: 15.7, isUp: true }
    };
  }, [metrics]);

  // Format time duration
  const formatDuration = (minutes: number): string => {
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  // Format percentage
  const formatPercentage = (value: number): string => {
    return `${Math.round(value * 10) / 10}%`;
  };

  // Export data
  const exportData = async () => {
    if (!metrics) return;
    
    const exportData = {
      metrics,
      realTimeData,
      filters,
      exportedAt: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `onboarding-analytics-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow p-8 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mr-3" />
          <span className="text-gray-600">Loading analytics data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-8 ${className}`}>
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Analytics</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadAnalyticsData}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className={`bg-white rounded-lg shadow p-8 ${className}`}>
        <div className="text-center text-gray-600">No analytics data available</div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Onboarding Analytics</h1>
            <p className="text-gray-600 mt-1">
              Real-time insights into user onboarding performance
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setFilters(prev => ({ ...prev }))} // Trigger refresh
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </button>
            
            <button
              onClick={exportData}
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Real-time Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Users className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4 flex-1">
              <p className="text-sm font-medium text-gray-600">Active Users Today</p>
              <div className="flex items-baseline">
                <p className="text-2xl font-semibold text-gray-900">{realTimeData.activeUsers}</p>
                {trends.totalUsers && (
                  <p className={`ml-2 flex items-baseline text-sm font-semibold ${
                    trends.totalUsers.isUp ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {trends.totalUsers.isUp ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
                    {Math.abs(trends.totalUsers.value)}%
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4 flex-1">
              <p className="text-sm font-medium text-gray-600">Completion Rate</p>
              <div className="flex items-baseline">
                <p className="text-2xl font-semibold text-gray-900">
                  {formatPercentage(realTimeData.completionRateToday)}
                </p>
                {trends.completionRate && (
                  <p className={`ml-2 flex items-baseline text-sm font-semibold ${
                    trends.completionRate.isUp ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {trends.completionRate.isUp ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
                    {Math.abs(trends.completionRate.value)}%
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Clock className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4 flex-1">
              <p className="text-sm font-medium text-gray-600">Avg. Session Time</p>
              <div className="flex items-baseline">
                <p className="text-2xl font-semibold text-gray-900">
                  {formatDuration(realTimeData.averageSessionTime)}
                </p>
                {trends.averageTime && (
                  <p className={`ml-2 flex items-baseline text-sm font-semibold ${
                    trends.averageTime.isUp ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {trends.averageTime.isUp ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
                    {Math.abs(trends.averageTime.value)}%
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
            <div className="ml-4 flex-1">
              <p className="text-sm font-medium text-gray-600">Top Drop-off Step</p>
              <p className="text-lg font-semibold text-gray-900">
                {realTimeData.topDropOffStep.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Step Performance */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Step Performance</h3>
            <BarChart3 className="h-5 w-5 text-gray-400" />
          </div>
          
          <div className="space-y-4">
            {metrics.stepPerformance.slice(0, 6).map((step) => (
              <div key={step.step_id} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900">
                      {step.step_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    <span className="text-sm text-gray-600">
                      {formatPercentage(step.completion_rate)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${step.completion_rate}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Avg: {formatDuration(step.average_duration / 60)}</span>
                    <span>Error: {formatPercentage(step.error_rate)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Drop-off Points */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Drop-off Analysis</h3>
            <PieChart className="h-5 w-5 text-gray-400" />
          </div>
          
          <div className="space-y-4">
            {metrics.dropOffPoints.slice(0, 5).map((point, index) => (
              <div key={point.stepId} className="flex items-center">
                <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center mr-3">
                  <span className="text-sm font-medium text-red-600">{index + 1}</span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">
                      {point.stepId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    <span className="text-sm text-gray-600">
                      {formatPercentage(point.dropOffRate)}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {point.userCount} users dropped off
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* User Segments */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">User Segments</h3>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Completion Rate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Average Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Common Drop-off
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {metrics.userSegments.map((segment) => (
                <tr key={segment.role}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {segment.role.toUpperCase()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${segment.completionRate}%` }}
                        />
                      </div>
                      {formatPercentage(segment.completionRate)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDuration(segment.averageTime)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {segment.commonDropOff.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div>
            <p className="text-3xl font-bold text-gray-900">{metrics.totalUsers}</p>
            <p className="text-sm text-gray-600">Total Users</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-gray-900">{metrics.totalSessions}</p>
            <p className="text-sm text-gray-600">Total Sessions</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-gray-900">
              {formatPercentage(metrics.completionRate)}
            </p>
            <p className="text-sm text-gray-600">Overall Completion Rate</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingAnalyticsDashboard;
