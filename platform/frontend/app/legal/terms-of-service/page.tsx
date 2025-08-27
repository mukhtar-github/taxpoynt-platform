'use client';

import React from 'react';

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-6">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Terms of Service</h1>
          
          <div className="prose prose-lg max-w-none">
            <p className="text-gray-600 mb-6">
              <strong>Last Updated:</strong> December 2024
            </p>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Agreement to Terms</h2>
              <p className="text-gray-700 mb-4">
                By accessing and using TaxPoynt platform ("Service"), you agree to be bound by these Terms of Service ("Terms"). 
                If you do not agree to these terms, please do not use our service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Description of Service</h2>
              <p className="text-gray-700 mb-4">
                TaxPoynt is a Nigerian tax technology platform that provides:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>System Integration (SI) services for connecting business systems</li>
                <li>Access Point Provider (APP) services for direct FIRS communication</li>
                <li>Hybrid solutions combining both SI and APP capabilities</li>
                <li>Tax compliance automation and reporting tools</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. User Accounts and Registration</h2>
              <p className="text-gray-700 mb-4">
                To access certain features of the Service, you must register for an account. You agree to:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Provide accurate, current, and complete information</li>
                <li>Maintain the security of your password and account</li>
                <li>Accept responsibility for all activities under your account</li>
                <li>Notify us immediately of any unauthorized use</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. Nigerian Tax Compliance</h2>
              <p className="text-gray-700 mb-4">
                TaxPoynt operates in compliance with Nigerian tax regulations, including:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Federal Inland Revenue Service (FIRS) requirements</li>
                <li>Value Added Tax (VAT) regulations</li>
                <li>Central Bank of Nigeria (CBN) guidelines</li>
                <li>Nigeria Data Protection Regulation (NDPR)</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. Data Security and Privacy</h2>
              <p className="text-gray-700 mb-4">
                We implement industry-standard security measures to protect your data. However, you acknowledge that:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>No internet transmission is completely secure</li>
                <li>You use the service at your own risk</li>
                <li>We are not liable for unauthorized access beyond our control</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Service Fees and Billing</h2>
              <p className="text-gray-700 mb-4">
                TaxPoynt offers various service packages with different pricing structures. By subscribing to paid services, you agree to:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Pay all applicable fees as described in your service agreement</li>
                <li>Automatic renewal unless cancelled</li>
                <li>Our right to modify pricing with 30 days notice</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Limitation of Liability</h2>
              <p className="text-gray-700 mb-4">
                To the maximum extent permitted by Nigerian law, TaxPoynt shall not be liable for any indirect, 
                incidental, special, or consequential damages arising from your use of the service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Governing Law</h2>
              <p className="text-gray-700 mb-4">
                These Terms shall be governed by and construed in accordance with the laws of the Federal Republic of Nigeria. 
                Any disputes shall be resolved in the courts of Lagos State, Nigeria.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Contact Information</h2>
              <p className="text-gray-700 mb-4">
                If you have any questions about these Terms of Service, please contact us:
              </p>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-gray-700">
                  <strong>TaxPoynt Nigeria Limited</strong><br/>
                  Email: legal@taxpoynt.com<br/>
                  Phone: +234-700-TAXPOYNT<br/>
                  Address: Lagos, Nigeria
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}

