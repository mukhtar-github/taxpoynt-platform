/**
 * System Integrator (SI) Interface - Main Component
 * ================================================
 * 
 * Professional SI dashboard with comprehensive integration tools.
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import { Logo } from '../design_system/components/Logo';

export const SIInterface: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center mb-6">
            <Logo size="lg" variant="full" showTagline={false} />
            <div className="ml-4">
              <span className="text-sm text-blue-600 font-body font-medium">SI Interface</span>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2 font-heading">
            System Integrator Dashboard
          </h1>
          <p className="text-gray-600 font-body">
            Manage business system integrations and automated e-invoicing workflows
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Integration Hub */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <span className="text-2xl mr-3">🔗</span>
                Integration Hub
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4 font-body">
                Connect and configure business systems for automated e-invoicing
              </p>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  ERP Systems: 15 Connected
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                  CRM Systems: 8 Connected
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-purple-400 rounded-full mr-2"></span>
                  POS Systems: 12 Connected
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Processing Center */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <span className="text-2xl mr-3">⚙️</span>
                Processing Center
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">
                Monitor document processing and validation workflows
              </p>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  Processing: 1,234 invoices/hour
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                  Validation: 99.8% success rate
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-orange-400 rounded-full mr-2"></span>
                  Queue: 45 pending
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Compliance Dashboard */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <span className="text-2xl mr-3">✅</span>
                Compliance Monitor
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">
                Nigerian regulatory compliance monitoring and reporting
              </p>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  FIRS Compliance: Active
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  VAT Compliance: Current
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  CBN Standards: Verified
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Financial Systems */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <span className="text-2xl mr-3">💰</span>
                Financial Systems
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">
                Banking integration and payment processing
              </p>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  Mono Banking: Connected
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  Paystack: Active
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                  Moniepoint: Ready
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Analytics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <span className="text-2xl mr-3">📊</span>
                Analytics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">
                Business insights and performance metrics
              </p>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  Revenue: ₦45.2M this month
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                  Transactions: 12,456
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-purple-400 rounded-full mr-2"></span>
                  Growth: +23% MoM
                </div>
              </div>
            </CardContent>
          </Card>

          {/* System Tools */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <span className="text-2xl mr-3">🛠️</span>
                System Tools
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">
                Advanced tools and system utilities
              </p>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  Schema Validator: Running
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                  Data Extractor: Ready
                </div>
                <div className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-purple-400 rounded-full mr-2"></span>
                  Certificates: Valid
                </div>
              </div>
            </CardContent>
          </Card>

        </div>
      </div>
    </div>
  );
};

export default SIInterface;