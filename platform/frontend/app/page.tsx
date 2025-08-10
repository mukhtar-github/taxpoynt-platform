import React from 'react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            TaxPoynt Platform
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enterprise Nigerian e-invoicing platform
          </p>
        </div>
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Platform Status
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                🚀 Frontend deployment successful
              </p>
            </div>
            <div className="grid grid-cols-1 gap-4">
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <h4 className="text-sm font-medium text-green-800">
                  ✅ Backend API
                </h4>
                <p className="text-sm text-green-700">Connected and operational</p>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <h4 className="text-sm font-medium text-blue-800">
                  🏗️ Architecture
                </h4>
                <p className="text-sm text-blue-700">Role-based microservices ready</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}