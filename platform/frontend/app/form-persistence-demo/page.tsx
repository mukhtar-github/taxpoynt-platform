/**
 * Form Persistence Demo Page
 * ==========================
 * Demonstrates the cross-form data sharing and persistence system
 */

'use client';

import React, { useState } from 'react';
import { FormField } from '../../design_system/components/FormField';
import { CrossFormDataManager } from '../../shared_components/utils/formPersistence';

export default function FormPersistenceDemoPage() {
  const [form1Data, setForm1Data] = useState({
    email: '',
    first_name: '',
    last_name: '',
    business_name: '',
    companyType: '',
    companySize: ''
  });

  const [form2Data, setForm2Data] = useState({
    email: '',
    first_name: '',
    last_name: '',
    business_name: '',
    companyType: '',
    companySize: ''
  });

  const [activeForm, setActiveForm] = useState<'form1' | 'form2'>('form1');

  const handleForm1Change = (field: string, value: string) => {
    const newData = { ...form1Data, [field]: value };
    setForm1Data(newData);
    
    // Save to shared storage
    CrossFormDataManager.saveSharedData({
      email: newData.email,
      first_name: newData.first_name,
      last_name: newData.last_name,
      business_name: newData.business_name,
      companyType: newData.companyType,
      companySize: newData.companySize
    });
  };

  const handleForm2Change = (field: string, value: string) => {
    const newData = { ...form2Data, [field]: value };
    setForm2Data(newData);
    
    // Save to shared storage
    CrossFormDataManager.saveSharedData({
      email: newData.email,
      first_name: newData.first_name,
      last_name: newData.last_name,
      business_name: newData.business_name,
      companyType: newData.companyType,
      companySize: newData.companySize
    });
  };

  const clearSharedData = () => {
    CrossFormDataManager.clearSharedData();
    setForm1Data({
      email: '',
      first_name: '',
      last_name: '',
      business_name: '',
      companyType: '',
      companySize: ''
    });
    setForm2Data({
      email: '',
      first_name: '',
      last_name: '',
      business_name: '',
      companyType: '',
      companySize: ''
    });
  };

  const showSharedData = () => {
    const shared = CrossFormDataManager.getSharedData();
    console.log('🔗 Shared Form Data:', shared);
    alert(`Shared Data: ${JSON.stringify(shared, null, 2)}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Form Persistence Demo 🔗
          </h1>
          <p className="text-lg text-gray-600">
            Fill out one form and see the data automatically appear in the other form!
          </p>
          
          <div className="flex justify-center space-x-4 mt-6">
            <button
              onClick={() => setActiveForm('form1')}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeForm === 'form1'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              Form 1
            </button>
            <button
              onClick={() => setActiveForm('form2')}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeForm === 'form2'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              Form 2
            </button>
          </div>

          <div className="flex justify-center space-x-4 mt-4">
            <button
              onClick={showSharedData}
              className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700"
            >
              Show Shared Data
            </button>
            <button
              onClick={clearSharedData}
              className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700"
            >
              Clear All Data
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form 1 */}
          <div className={`bg-white rounded-2xl shadow-lg p-8 ${activeForm === 'form1' ? 'ring-2 ring-blue-500' : ''}`}>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Registration Form 1</h2>
            
            <div className="space-y-6">
              <FormField
                label="Email"
                name="email"
                type="email"
                value={form1Data.email}
                onChange={(value) => handleForm1Change('email', value)}
                placeholder="john@company.com"
                showPersistenceIndicator={true}
                autoPopulateFromShared={true}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  label="First Name"
                  name="first_name"
                  type="text"
                  value={form1Data.first_name}
                  onChange={(value) => handleForm1Change('first_name', value)}
                  placeholder="John"
                  showPersistenceIndicator={true}
                  autoPopulateFromShared={true}
                />
                
                <FormField
                  label="Last Name"
                  name="last_name"
                  type="text"
                  value={form1Data.last_name}
                  onChange={(value) => handleForm1Change('last_name', value)}
                  placeholder="Doe"
                  showPersistenceIndicator={true}
                  autoPopulateFromShared={true}
                />
              </div>

              <FormField
                label="Business Name"
                name="business_name"
                type="text"
                value={form1Data.business_name}
                onChange={(value) => handleForm1Change('business_name', value)}
                placeholder="Your Company Ltd"
                showPersistenceIndicator={true}
                autoPopulateFromShared={true}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  label="Company Type"
                  name="companyType"
                  type="select"
                  value={form1Data.companyType}
                  onChange={(value) => handleForm1Change('companyType', value)}
                  options={[
                    { value: 'sole_proprietorship', label: 'Sole Proprietorship' },
                    { value: 'partnership', label: 'Partnership' },
                    { value: 'limited_company', label: 'Limited Company' },
                    { value: 'public_company', label: 'Public Company' },
                    { value: 'non_profit', label: 'Non-Profit' },
                    { value: 'cooperative', label: 'Cooperative' }
                  ]}
                  showPersistenceIndicator={true}
                  autoPopulateFromShared={true}
                />
                
                <FormField
                  label="Company Size"
                  name="companySize"
                  type="select"
                  value={form1Data.companySize}
                  onChange={(value) => handleForm1Change('companySize', value)}
                  options={[
                    { value: 'startup', label: 'Startup (1-10)' },
                    { value: 'small', label: 'Small (11-50)' },
                    { value: 'medium', label: 'Medium (51-200)' },
                    { value: 'large', label: 'Large (201-1000)' },
                    { value: 'enterprise', label: 'Enterprise (1000+)' }
                  ]}
                  showPersistenceIndicator={true}
                  autoPopulateFromShared={true}
                />
              </div>
            </div>
          </div>

          {/* Form 2 */}
          <div className={`bg-white rounded-2xl shadow-lg p-8 ${activeForm === 'form2' ? 'ring-2 ring-blue-500' : ''}`}>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Registration Form 2</h2>
            
            <div className="space-y-6">
              <FormField
                label="Email"
                name="email"
                type="email"
                value={form2Data.email}
                onChange={(value) => handleForm2Change('email', value)}
                placeholder="jane@company.com"
                showPersistenceIndicator={true}
                autoPopulateFromShared={true}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  label="First Name"
                  name="first_name"
                  type="text"
                  value={form2Data.first_name}
                  onChange={(value) => handleForm2Change('first_name', value)}
                  placeholder="Jane"
                  showPersistenceIndicator={true}
                  autoPopulateFromShared={true}
                />
                
                <FormField
                  label="Last Name"
                  name="last_name"
                  type="text"
                  value={form2Data.last_name}
                  onChange={(value) => handleForm2Change('last_name', value)}
                  placeholder="Smith"
                  showPersistenceIndicator={true}
                  autoPopulateFromShared={true}
                />
              </div>

              <FormField
                label="Business Name"
                name="business_name"
                type="text"
                value={form2Data.business_name}
                onChange={(value) => handleForm2Change('business_name', value)}
                placeholder="Your Company Ltd"
                showPersistenceIndicator={true}
                autoPopulateFromShared={true}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  label="Company Type"
                  name="companyType"
                  type="select"
                  value={form2Data.companyType}
                  onChange={(value) => handleForm2Change('companyType', value)}
                  options={[
                    { value: 'sole_proprietorship', label: 'Sole Proprietorship' },
                    { value: 'partnership', label: 'Partnership' },
                    { value: 'limited_company', label: 'Limited Company' },
                    { value: 'public_company', label: 'Public Company' },
                    { value: 'non_profit', label: 'Non-Profit' },
                    { value: 'cooperative', label: 'Cooperative' }
                  ]}
                  showPersistenceIndicator={true}
                  autoPopulateFromShared={true}
                />
                
                <FormField
                  label="Company Size"
                  name="companySize"
                  type="select"
                  value={form2Data.companySize}
                  onChange={(value) => handleForm2Change('companySize', value)}
                  options={[
                    { value: 'startup', label: 'Startup (1-10)' },
                    { value: 'small', label: 'Small (11-50)' },
                    { value: 'medium', label: 'Medium (51-200)' },
                    { value: 'large', label: 'Large (201-1000)' },
                    { value: 'enterprise', label: 'Enterprise (1000+)' }
                  ]}
                  showPersistenceIndicator={true}
                  autoPopulateFromShared={true}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-12 bg-blue-50 border border-blue-200 rounded-2xl p-8">
          <h3 className="text-xl font-bold text-blue-900 mb-4">How It Works 🔗</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-blue-800">
            <div>
              <h4 className="font-semibold mb-2">Cross-Form Data Sharing:</h4>
              <ul className="space-y-1 text-sm">
                <li>• Fill out any field in Form 1</li>
                <li>• Switch to Form 2 - data appears automatically!</li>
                <li>• Fields show visual indicators (🔗) when pre-filled</li>
                <li>• Data persists across page refreshes</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Visual Indicators:</h4>
              <ul className="space-y-1 text-sm">
                <li>• 🔗 Green border = Data from other forms</li>
                <li>• 💾 Blue border = Previously entered data</li>
                <li>• Helper text shows data source</li>
                <li>• Fields fade slightly when pre-filled</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
