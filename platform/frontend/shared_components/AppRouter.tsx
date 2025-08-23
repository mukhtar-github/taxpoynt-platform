/**
 * Application Router
 * ==================
 * 
 * Main routing configuration for TaxPoynt platform with legal pages.
 * Handles routing for Business Interface, SI Interface, APP Interface, and shared pages.
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Shared Legal Pages
import PrivacyPolicyPage from './pages/PrivacyPolicyPage';
import TermsOfServicePage from './pages/TermsOfServicePage';
import NDPRCompliancePage from './pages/NDPRCompliancePage';
import SecurityBankingFAQPage from './pages/SecurityBankingFAQPage';

// Business Interface Pages
import { HomePage } from '../business_interface/HomePage';
import { LandingPage } from '../business_interface/LandingPage';
import { SignInPage } from '../business_interface/auth/SignInPage';
import { SignUpPage } from '../business_interface/auth/SignUpPage';
import { BillingPage } from '../business_interface/billing_management/BillingPage';
import { ConsentIntegratedRegistration } from '../business_interface/onboarding_flows/ConsentIntegratedRegistration';

// SI Interface Pages (example imports - adjust as needed)
// import SIDashboard from '../si_interface/pages/SIDashboard';
// import MonoBankingDashboard from '../si_interface/components/financial_systems/banking_integration/MonoBankingDashboard';

// APP Interface Pages (to be imported when available)
// import APPDashboard from '../app_interface/pages/APPDashboard';

// Role Management
import { RoleDetectorProvider, PlatformRole } from '../role_management/role_detector';
import { AccessGuard } from '../role_management/access_guard';

const AppRouter: React.FC = () => {
  return (
    <Router>
      <RoleDetectorProvider>
        <Routes>
          {/* Root Route - Redirect to Landing */}
          <Route path="/" element={<Navigate to="/landing" replace />} />
          
          {/* Landing and Home */}
          <Route path="/landing" element={<LandingPage />} />
          <Route path="/home" element={<AccessGuard requiredRoles={[PlatformRole.USER]}><HomePage user={{name: 'User', company: 'Company', role: 'hybrid'}} stats={{invoicesThisMonth: 0, successfulTransmissions: 0, integrations: 0}} /></AccessGuard>} />
          
          {/* Authentication Routes */}
          <Route path="/auth/signin" element={<SignInPage onSignIn={async () => {}} />} />
          <Route path="/auth/signup" element={<SignUpPage onContinueToRegistration={() => {}} />} />
          <Route path="/auth/onboarding" element={<ConsentIntegratedRegistration />} />
          
          {/* Business Interface Routes */}
          <Route path="/business/*" element={
            <AccessGuard requiredRoles={[PlatformRole.USER]}>
              <Routes>
                <Route path="/" element={<HomePage user={{name: 'User', company: 'Company', role: 'hybrid'}} stats={{invoicesThisMonth: 0, successfulTransmissions: 0, integrations: 0}} />} />
                <Route path="/billing" element={<BillingPage selectedPackage={{id: 'basic', name: 'Basic Plan', price: {monthly: 29, annual: 290}, features: ['Basic features']}} currentRole='hybrid' userProfile={{companyName: 'Company', email: 'user@example.com', phone: '+1234567890'}} onPaymentComplete={() => {}} onCancel={() => {}} />} />
                <Route path="/onboarding" element={<ConsentIntegratedRegistration />} />
                {/* Add more business routes as needed */}
              </Routes>
            </AccessGuard>
          } />
          
          {/* System Integrator Interface Routes */}
          <Route path="/si/*" element={
            <AccessGuard requiredRoles={[PlatformRole.SYSTEM_INTEGRATOR]}>
              <Routes>
                <Route path="/" element={<div>SI Dashboard - Coming Soon</div>} />
                {/* <Route path="/dashboard" element={<SIDashboard />} /> */}
                {/* <Route path="/banking" element={<MonoBankingDashboard />} /> */}
                {/* Add more SI routes as needed */}
              </Routes>
            </AccessGuard>
          } />
          
          {/* Access Point Provider Interface Routes */}
          <Route path="/app/*" element={
            <AccessGuard requiredRoles={[PlatformRole.ACCESS_POINT_PROVIDER]}>
              <Routes>
                <Route path="/" element={<div>APP Dashboard - Coming Soon</div>} />
                {/* <Route path="/dashboard" element={<APPDashboard />} /> */}
                {/* Add more APP routes as needed */}
              </Routes>
            </AccessGuard>
          } />
          
          {/* Legal and Security Pages (Public Access) */}
          <Route path="/legal/privacy" element={<PrivacyPolicyPage />} />
          <Route path="/legal/terms" element={<TermsOfServicePage />} />
          <Route path="/legal/ndpr" element={<NDPRCompliancePage />} />
          <Route path="/security/banking-faq" element={<SecurityBankingFAQPage />} />
          
          {/* Legal Routes Redirect */}
          <Route path="/legal" element={<Navigate to="/legal/privacy" replace />} />
          <Route path="/security" element={<Navigate to="/security/banking-faq" replace />} />
          
          {/* About and Support Pages */}
          <Route path="/about" element={<div>About TaxPoynt - Coming Soon</div>} />
          <Route path="/support" element={<div>Support Center - Coming Soon</div>} />
          <Route path="/support/nigerian" element={<div>Nigerian Support - Coming Soon</div>} />
          
          {/* API Documentation */}
          <Route path="/docs/api" element={<div>API Documentation - Coming Soon</div>} />
          
          {/* Compliance Information */}
          <Route path="/compliance/firs" element={<div>FIRS Compliance - Coming Soon</div>} />
          <Route path="/compliance/cbn" element={<div>CBN Compliance - Coming Soon</div>} />
          
          {/* Catch-all Route - 404 */}
          <Route path="*" element={
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
                <p className="text-gray-600 mb-6">Page not found</p>
                <a 
                  href="/landing" 
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Return to Home
                </a>
              </div>
            </div>
          } />
        </Routes>
      </RoleDetectorProvider>
    </Router>
  );
};

export default AppRouter;