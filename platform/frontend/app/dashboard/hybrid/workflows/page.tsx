'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';
import { authService } from '../../../../shared_components/services/auth';
import { APIResponse } from '../../../../si_interface/types';
import apiClient from '../../../../shared_components/api/client';

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  type: 'si_to_app' | 'business_integration' | 'compliance_automation' | 'custom';
  steps: number;
  estimatedTime: string;
  complexity: 'simple' | 'moderate' | 'complex';
  category: string;
}

interface ActiveWorkflow {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'completed' | 'failed';
  progress: number;
  currentStep: string;
  startedAt: string;
  estimatedCompletion: string;
  type: string;
}

export default function HybridWorkflowsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [activeTab, setActiveTab] = useState<'templates' | 'active' | 'designer'>('active');
  const [workflows, setWorkflows] = useState<ActiveWorkflow[]>([]);
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);

  useEffect(() => {
    const currentUser = authService.getStoredUser();
    if (!currentUser || !authService.isAuthenticated()) {
      router.push('/auth/signin');
      return;
    }

    if (currentUser.role !== 'hybrid_user') {
      router.push('/dashboard');
      return;
    }

    setUser(currentUser);
    loadWorkflowData();
  }, [router]);

  const loadWorkflowData = async () => {
    try {
      setLoading(true);
      const [workflowsResponse, templatesResponse] = await Promise.all([
        apiClient.get<APIResponse<ActiveWorkflow[]>>('/api/v1/hybrid/workflows/active'),
        apiClient.get<APIResponse<WorkflowTemplate[]>>('/api/v1/hybrid/workflows/templates')
      ]);
      
      if (workflowsResponse.success && workflowsResponse.data && 
          templatesResponse.success && templatesResponse.data) {
        setWorkflows(workflowsResponse.data);
        setTemplates(templatesResponse.data);
        setIsDemo(false);
      } else {
        throw new Error('API response unsuccessful');
      }
    } catch (error) {
      console.error('Failed to load workflow data, using demo data:', error);
      setIsDemo(true);
      
      // Demo data fallback
      setWorkflows([
        {
          id: 'wf-001',
          name: 'ERP → FIRS Auto-Submission',
          status: 'running',
          progress: 75,
          currentStep: 'Generating FIRS invoices',
          startedAt: '2024-01-15 14:30:00',
          estimatedCompletion: '2024-01-15 15:45:00',
          type: 'si_to_app'
        },
        {
          id: 'wf-002',
          name: 'Monthly Compliance Report',
          status: 'completed',
          progress: 100,
          currentStep: 'Report delivered',
          startedAt: '2024-01-15 09:00:00',
          estimatedCompletion: '2024-01-15 10:30:00',
          type: 'compliance_automation'
        },
        {
          id: 'wf-003',
          name: 'Banking Data Reconciliation',
          status: 'paused',
          progress: 45,
          currentStep: 'Awaiting manual review',
          startedAt: '2024-01-15 11:20:00',
          estimatedCompletion: '2024-01-15 16:00:00',
          type: 'business_integration'
        }
      ]);

      setTemplates([
        {
          id: 'tpl-001',
          name: 'SI to APP Data Flow',
          description: 'Automated pipeline from system integration to FIRS submission',
          type: 'si_to_app',
          steps: 6,
          estimatedTime: '2-4 hours',
          complexity: 'moderate',
          category: 'End-to-End Processing'
        },
        {
          id: 'tpl-002',
          name: 'Multi-System Reconciliation',
          description: 'Compare and reconcile data across ERP, banking, and payment systems',
          type: 'business_integration',
          steps: 8,
          estimatedTime: '3-6 hours',
          complexity: 'complex',
          category: 'Data Integration'
        },
        {
          id: 'tpl-003',
          name: 'Compliance Monitoring',
          description: 'Automated compliance checking and reporting workflow',
          type: 'compliance_automation',
          steps: 4,
          estimatedTime: '1-2 hours',
          complexity: 'simple',
          category: 'Regulatory'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'completed': return 'text-green-600 bg-green-100';
      case 'paused': return 'text-orange-600 bg-orange-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple': return 'text-green-600 bg-green-100';
      case 'moderate': return 'text-yellow-600 bg-yellow-100';
      case 'complex': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (!user) {
    return (
      <DashboardLayout role="hybrid" activeTab="workflows">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p>Loading...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (loading) {
    return (
      <DashboardLayout role="hybrid" activeTab="workflows">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading workflow management...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout role="hybrid" activeTab="workflows">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Workflow Orchestration</h1>
            <p className="text-gray-600">
              Design and manage end-to-end business processes across SI and APP systems
              {isDemo && (
                <span className="ml-2 px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded-full">
                  Demo Data
                </span>
              )}
            </p>
          </div>
          <div className="flex space-x-4">
            <TaxPoyntButton
              variant="outline"
              onClick={() => router.back()}
            >
              ← Back to Dashboard
            </TaxPoyntButton>
            <TaxPoyntButton
              variant="primary"
              onClick={() => setActiveTab('designer')}
              className="bg-purple-600 hover:bg-purple-700"
            >
              🎨 Workflow Designer
            </TaxPoyntButton>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'active', label: 'Active Workflows', icon: '⚡' },
              { id: 'templates', label: 'Templates', icon: '📋' },
              { id: 'designer', label: 'Designer', icon: '🎨' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2
                  ${activeTab === tab.id
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Active Workflows Tab */}
        {activeTab === 'active' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center">
                  <div className="text-3xl font-bold text-blue-600">{workflows.filter(w => w.status === 'running').length}</div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-600">Running</div>
                    <div className="text-xs text-gray-500">Active workflows</div>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center">
                  <div className="text-3xl font-bold text-green-600">{workflows.filter(w => w.status === 'completed').length}</div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-600">Completed</div>
                    <div className="text-xs text-gray-500">Today</div>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center">
                  <div className="text-3xl font-bold text-orange-600">{workflows.filter(w => w.status === 'paused').length}</div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-600">Paused</div>
                    <div className="text-xs text-gray-500">Need attention</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Active Workflows</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Workflow
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Progress
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Current Step
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {workflows.map((workflow) => (
                      <tr key={workflow.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{workflow.name}</div>
                            <div className="text-sm text-gray-500">{workflow.type.replace('_', ' ').toUpperCase()}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(workflow.status)}`}>
                            {workflow.status.charAt(0).toUpperCase() + workflow.status.slice(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${workflow.progress}%` }}
                              ></div>
                            </div>
                            <span className="text-sm text-gray-600">{workflow.progress}%</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {workflow.currentStep}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button className="text-purple-600 hover:text-purple-900">View</button>
                            {workflow.status === 'paused' && (
                              <button className="text-green-600 hover:text-green-900">Resume</button>
                            )}
                            {workflow.status === 'running' && (
                              <button className="text-orange-600 hover:text-orange-900">Pause</button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Templates Tab */}
        {activeTab === 'templates' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <div key={template.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">{template.name}</h3>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getComplexityColor(template.complexity)}`}>
                    {template.complexity}
                  </span>
                </div>
                
                <p className="text-gray-600 text-sm mb-4">{template.description}</p>
                
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Steps:</span>
                    <span className="font-medium">{template.steps}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Est. Time:</span>
                    <span className="font-medium">{template.estimatedTime}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Category:</span>
                    <span className="font-medium">{template.category}</span>
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  <TaxPoyntButton
                    variant="outline"
                    size="sm"
                    onClick={() => console.log('Preview template:', template.id)}
                    className="flex-1"
                  >
                    Preview
                  </TaxPoyntButton>
                  <TaxPoyntButton
                    variant="primary"
                    size="sm"
                    onClick={() => console.log('Use template:', template.id)}
                    className="flex-1 bg-purple-600 hover:bg-purple-700"
                  >
                    Use Template
                  </TaxPoyntButton>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Designer Tab */}
        {activeTab === 'designer' && (
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="text-center">
              <div className="text-6xl mb-4">🎨</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Workflow Designer</h2>
              <p className="text-gray-600 mb-8">
                Create custom workflows by dragging and dropping components to design your business processes.
              </p>
              <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12">
                <p className="text-gray-500 mb-4">Interactive workflow designer coming soon!</p>
                <p className="text-sm text-gray-400">
                  You'll be able to visually design workflows that combine SI data processing with APP submission capabilities.
                </p>
              </div>
              
              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 border border-gray-200 rounded-lg">
                  <div className="text-2xl mb-2">🔗</div>
                  <h3 className="font-semibold text-gray-900">SI Components</h3>
                  <p className="text-sm text-gray-600">Data collection, transformation, and integration steps</p>
                </div>
                <div className="p-4 border border-gray-200 rounded-lg">
                  <div className="text-2xl mb-2">🏛️</div>
                  <h3 className="font-semibold text-gray-900">APP Components</h3>
                  <p className="text-sm text-gray-600">FIRS submission, validation, and compliance steps</p>
                </div>
                <div className="p-4 border border-gray-200 rounded-lg">
                  <div className="text-2xl mb-2">⚙️</div>
                  <h3 className="font-semibold text-gray-900">Logic Components</h3>
                  <p className="text-sm text-gray-600">Conditional logic, loops, and decision points</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
