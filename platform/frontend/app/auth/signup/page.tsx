'use client';

import React, { Suspense, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  StreamlinedRegistration,
  type StreamlinedRegistrationData,
} from '../../../business_interface/auth/StreamlinedRegistration';
import { authService } from '../../../shared_components/services/auth';

type ServicePackage = 'si' | 'app' | 'hybrid';

const isValidService = (value: string | null): value is ServicePackage =>
  value === 'si' || value === 'app' || value === 'hybrid';

const SignUpPageContent: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const initialServicePackage = useMemo(() => {
    const serviceParam = searchParams.get('service');
    return isValidService(serviceParam) ? serviceParam : undefined;
  }, [searchParams]);

  const handleRegistration = async (registrationData: StreamlinedRegistrationData) => {
    setIsSubmitting(true);
    setError(undefined);

    try {
      const response = await authService.register({
        email: registrationData.email.trim(),
        password: registrationData.password,
        first_name: registrationData.first_name.trim(),
        last_name: registrationData.last_name.trim(),
        phone: undefined,
        service_package: registrationData.service_package,
        business_name: registrationData.business_name.trim(),
        business_type: registrationData.companyType,
        terms_accepted: registrationData.terms_accepted,
        privacy_accepted: registrationData.privacy_accepted,
        marketing_consent: registrationData.trial_started,
        consents: {
          company_size: registrationData.companySize,
          company_type: registrationData.companyType,
          trial_started: registrationData.trial_started,
          trial_start_date: registrationData.trial_start_date,
        },
      });

      const serviceFromResponse = response.user.service_package;
      const nextService = isValidService(serviceFromResponse)
        ? serviceFromResponse
        : registrationData.service_package;

      router.push(`/onboarding?service=${nextService}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed. Please try again.';
      setError(message);
      throw err instanceof Error ? err : new Error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <StreamlinedRegistration
      onCompleteRegistration={handleRegistration}
      isLoading={isSubmitting}
      error={error}
      initialServicePackage={initialServicePackage}
    />
  );
};

const SignUpPageFallback: React.FC = () => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
  </div>
);

export default function SignUpPageWrapper() {
  return (
    <Suspense fallback={<SignUpPageFallback />}>
      <SignUpPageContent />
    </Suspense>
  );
}
