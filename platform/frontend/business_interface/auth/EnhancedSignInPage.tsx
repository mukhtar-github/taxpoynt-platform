/**
 * Enhanced Sign In Page
 * =====================
 * Modern sign-in page using our refined design system and AuthLayout
 */

import React from 'react';
import { AuthLayout, EnhancedSignInForm } from '../../shared_components/auth';
import type { SignInFormProps } from '../../shared_components/auth';

export interface EnhancedSignInPageProps extends SignInFormProps {}

export const EnhancedSignInPage: React.FC<EnhancedSignInPageProps> = (props) => {
  return (
    <AuthLayout
      title="Welcome Back"
      subtitle="Sign in to access your TaxPoynt dashboard"
      showBackToHome={true}
    >
      <EnhancedSignInForm {...props} />
    </AuthLayout>
  );
};
