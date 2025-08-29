/**
 * Footer Demo Page
 * ================
 * Demonstrates the different footer variants and their usage
 */

import React from 'react';
import { Footer } from '../../design_system';

export default function FooterDemoPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900">Footer Component Demo</h1>
          <p className="text-gray-600 mt-2">
            Showcasing the different footer variants and their usage patterns
          </p>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Default Footer */}
        <section className="mb-16">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Default Footer</h2>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <Footer />
          </div>
        </section>

        {/* Landing Footer */}
        <section className="mb-16">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Landing Footer (with newsletter signup)</h2>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <Footer variant="landing" />
          </div>
        </section>

        {/* Minimal Footer */}
        <section className="mb-16">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Minimal Footer (light theme)</h2>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <Footer variant="minimal" />
          </div>
        </section>

        {/* Usage Examples */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Usage Examples</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Default Variant</h3>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
{`<Footer />
// Full footer with company info, navigation, and legal links`}
              </pre>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Landing Variant</h3>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
{`<Footer variant="landing" />
// Includes newsletter signup and compliance notice`}
              </pre>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Minimal Variant</h3>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
{`<Footer variant="minimal" />
// Light theme, compact design for internal pages`}
              </pre>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">With Custom Classes</h3>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
{`<Footer className="mt-16" />
// Add custom spacing or styling`}
              </pre>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Key Features</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 text-xl">🎨</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Design System Compliant</h3>
              <p className="text-gray-600 text-sm">
                Follows TaxPoynt design principles and uses consistent styling
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-green-600 text-xl">♿</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Accessible</h3>
              <p className="text-gray-600 text-sm">
                Proper ARIA labels, semantic HTML, and keyboard navigation
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-purple-600 text-xl">🔧</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Flexible</h3>
              <p className="text-gray-600 text-sm">
                Multiple variants and customizable styling options
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
