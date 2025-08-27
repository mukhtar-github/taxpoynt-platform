'use client';

import React from 'react';

export default function NDPRNoticePage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-6">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">NDPR Data Processing Notice</h1>
          
          <div className="prose prose-lg max-w-none">
            <p className="text-gray-600 mb-6">
              <strong>Effective Date:</strong> December 2024
            </p>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <p className="text-blue-800 font-medium">
                This notice is provided in compliance with the Nigeria Data Protection Regulation (NDPR) 2019.
              </p>
            </div>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Data Controller Information</h2>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-gray-700">
                  <strong>Data Controller:</strong> TaxPoynt Nigeria Limited<br/>
                  <strong>Registration Number:</strong> RC 1234567<br/>
                  <strong>Address:</strong> Lagos, Nigeria<br/>
                  <strong>Contact:</strong> privacy@taxpoynt.com<br/>
                  <strong>DPO:</strong> dpo@taxpoynt.com
                </p>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Purpose of Data Processing</h2>
              <p className="text-gray-700 mb-4">We process your personal data for the following purposes:</p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li><strong>Tax Compliance Services:</strong> To provide automated tax reporting and FIRS integration</li>
                <li><strong>Business System Integration:</strong> To connect your ERP, CRM, and POS systems</li>
                <li><strong>Financial Services:</strong> To integrate banking and payment processing systems</li>
                <li><strong>Regulatory Compliance:</strong> To meet FIRS, CBN, and other regulatory requirements</li>
                <li><strong>Service Delivery:</strong> To provide customer support and technical assistance</li>
                <li><strong>Platform Improvement:</strong> To enhance our services and develop new features</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. Legal Basis for Processing</h2>
              <p className="text-gray-700 mb-4">We process your data based on:</p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li><strong>Consent:</strong> For marketing communications and optional services</li>
                <li><strong>Contract Performance:</strong> To fulfill our service agreements</li>
                <li><strong>Legal Obligation:</strong> To comply with Nigerian tax and regulatory laws</li>
                <li><strong>Legitimate Interest:</strong> For fraud prevention and platform security</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. Categories of Personal Data</h2>
              <p className="text-gray-700 mb-4">We may process the following categories of data:</p>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Identity Data</h3>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Full name, date of birth, identification numbers</li>
                <li>Business name, RC number, TIN, VAT number</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-900 mb-2">Contact Data</h3>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Email address, phone number, postal address</li>
                <li>Business address and contact information</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-900 mb-2">Financial Data</h3>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Bank account details, transaction history</li>
                <li>Payment information, billing records</li>
                <li>Tax data and compliance records</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-900 mb-2">Technical Data</h3>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>IP address, login data, browser type</li>
                <li>Usage data, system logs, performance metrics</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. Data Recipients</h2>
              <p className="text-gray-700 mb-4">Your data may be shared with:</p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li><strong>Nigerian Government Agencies:</strong> FIRS, CBN, NITDA</li>
                <li><strong>Banking Partners:</strong> Mono, authorized banks, payment processors</li>
                <li><strong>Technology Partners:</strong> Cloud providers, security services</li>
                <li><strong>Professional Advisors:</strong> Legal, accounting, and consulting firms</li>
                <li><strong>Business Partners:</strong> ERP vendors, CRM providers (with consent)</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. International Transfers</h2>
              <p className="text-gray-700 mb-4">
                Data is primarily processed within Nigeria. International transfers occur only when necessary 
                for cloud services or technical support, with appropriate safeguards including:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Adequacy decisions or equivalent protection measures</li>
                <li>Standard contractual clauses approved by NITDA</li>
                <li>Certification under approved schemes</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Data Retention</h2>
              <p className="text-gray-700 mb-4">We retain your data for:</p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li><strong>Active Services:</strong> Duration of service agreement</li>
                <li><strong>Tax Records:</strong> 6-7 years as required by Nigerian tax law</li>
                <li><strong>Financial Records:</strong> 5 years for audit and compliance purposes</li>
                <li><strong>Technical Logs:</strong> 12-24 months for security and performance monitoring</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Your Rights Under NDPR</h2>
              <p className="text-gray-700 mb-4">You have the following rights:</p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li><strong>Right of Access:</strong> Request information about data processing</li>
                <li><strong>Right to Rectification:</strong> Correct inaccurate or incomplete data</li>
                <li><strong>Right to Erasure:</strong> Request deletion of your data</li>
                <li><strong>Right to Restrict Processing:</strong> Limit how we use your data</li>
                <li><strong>Right to Data Portability:</strong> Receive your data in a structured format</li>
                <li><strong>Right to Object:</strong> Object to processing based on legitimate interests</li>
                <li><strong>Right to Withdraw Consent:</strong> Withdraw consent at any time</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Data Security</h2>
              <p className="text-gray-700 mb-4">We implement comprehensive security measures:</p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>End-to-end encryption for data transmission and storage</li>
                <li>Multi-factor authentication and access controls</li>
                <li>Regular security audits and vulnerability assessments</li>
                <li>Employee training and confidentiality agreements</li>
                <li>Incident response and breach notification procedures</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">10. Contact Information</h2>
              <p className="text-gray-700 mb-4">
                To exercise your rights or for data protection inquiries:
              </p>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-gray-700">
                  <strong>Data Protection Officer</strong><br/>
                  Email: dpo@taxpoynt.com<br/>
                  Phone: +234-700-TAXPOYNT<br/>
                  <br/>
                  <strong>General Privacy Inquiries:</strong><br/>
                  Email: privacy@taxpoynt.com<br/>
                  <br/>
                  <strong>NITDA (Supervisory Authority):</strong><br/>
                  Email: info@nitda.gov.ng<br/>
                  Website: nitda.gov.ng
                </p>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">11. Changes to This Notice</h2>
              <p className="text-gray-700 mb-4">
                We may update this notice to reflect changes in our practices or regulatory requirements. 
                We will notify you of significant changes through email or platform notifications.
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}

