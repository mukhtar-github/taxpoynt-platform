/**
 * Enhanced Sign Up Page
 * =====================
 * Modern sign-up page using our refined design system and AuthLayout
 */

import React from 'react';
import { AuthLayout, EnhancedSignUpForm } from '../../shared_components/auth';
import type { SignUpFormProps } from '../../shared_components/auth';

export interface EnhancedSignUpPageProps extends SignUpFormProps {}

export const EnhancedSignUpPage: React.FC<EnhancedSignUpPageProps> = (props) => {
  return (
    <AuthLayout
      title="Join TaxPoynt"
      subtitle="Start your 14-day free trial today"
      showBackToHome={true}
    >
      <EnhancedSignUpForm {...props} />
    </AuthLayout>
  );
};
