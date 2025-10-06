'use client';

import React from 'react';

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-6">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Privacy Policy</h1>
          
          <div className="prose prose-lg max-w-none">
            <p className="text-gray-600 mb-6">
              <strong>Last Updated:</strong> December 2024
            </p>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Introduction</h2>
              <p className="text-gray-700 mb-4">
                TaxPoynt Nigeria Limited (&ldquo;we&rdquo;, &ldquo;our&rdquo;, or &ldquo;us&rdquo;) is committed to protecting your privacy. 
                This Privacy Policy explains how we collect, use, disclose, and safeguard your information 
                when you use our tax technology platform.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Information We Collect</h2>
              <p className="text-gray-700 mb-4">We collect several types of information:</p>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Personal Information</h3>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Name, email address, phone number</li>
                <li>Business information (company name, RC number, TIN)</li>
                <li>Address and location data</li>
                <li>Banking and financial information (via secure integrations)</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-900 mb-2">Technical Information</h3>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>IP address, browser type, device information</li>
                <li>Usage data and analytics</li>
                <li>System integration logs and performance data</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. How We Use Your Information</h2>
              <p className="text-gray-700 mb-4">We use your information to:</p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Provide and maintain our tax compliance services</li>
                <li>Process transactions and manage billing</li>
                <li>Communicate with you about our services</li>
                <li>Comply with Nigerian tax regulations and FIRS requirements</li>
                <li>Improve our platform and develop new features</li>
                <li>Detect and prevent fraud or unauthorized activities</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. NDPR Compliance</h2>
              <p className="text-gray-700 mb-4">
                As a Nigerian company, we comply with the Nigeria Data Protection Regulation (NDPR). 
                Your rights under NDPR include:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li><strong>Right to Access:</strong> Request copies of your personal data</li>
                <li><strong>Right to Rectification:</strong> Request correction of inaccurate data</li>
                <li><strong>Right to Erasure:</strong> Request deletion of your data</li>
                <li><strong>Right to Data Portability:</strong> Request transfer of your data</li>
                <li><strong>Right to Object:</strong> Object to processing of your data</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. Data Sharing and Disclosure</h2>
              <p className="text-gray-700 mb-4">We may share your information with:</p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li><strong>Government Agencies:</strong> FIRS, CBN, and other regulatory bodies as required by law</li>
                <li><strong>Service Providers:</strong> Banking partners (Mono), payment processors, cloud providers</li>
                <li><strong>Business Partners:</strong> ERP providers, CRM systems (with your consent)</li>
                <li><strong>Legal Requirements:</strong> When required by court order or legal process</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Data Security</h2>
              <p className="text-gray-700 mb-4">
                We implement appropriate security measures including:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Encryption of data in transit and at rest</li>
                <li>Multi-factor authentication</li>
                <li>Regular security audits and penetration testing</li>
                <li>Access controls and employee training</li>
                <li>Secure data centers and infrastructure</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. International Transfers</h2>
              <p className="text-gray-700 mb-4">
                Your data is primarily processed within Nigeria. When data is transferred internationally 
                (e.g., to cloud service providers), we ensure adequate protection through:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Standard contractual clauses</li>
                <li>Adequacy decisions</li>
                <li>Certification schemes</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Data Retention</h2>
              <p className="text-gray-700 mb-4">
                We retain your data for as long as necessary to provide our services and comply with legal obligations. 
                Tax-related data may be retained for up to 7 years as required by Nigerian tax law.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Contact Us</h2>
              <p className="text-gray-700 mb-4">
                For privacy-related questions or to exercise your rights under NDPR, contact us:
              </p>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-gray-700">
                  <strong>Data Protection Officer</strong><br/>
                  TaxPoynt Nigeria Limited<br/>
                  Email: privacy@taxpoynt.com<br/>
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
