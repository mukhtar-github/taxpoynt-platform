'use client';

import React, { useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { AuthLayout } from '../../../shared_components/auth/AuthLayout';
import { FormField } from '../../../design_system/components/FormField';
import { TaxPoyntButton } from '../../../design_system/components/TaxPoyntButton';
import { AutosaveStatusChip } from '../../../shared_components/onboarding';
import { authService } from '../../../shared_components/services/auth';
import { OnboardingStateManager } from '../../../shared_components/services/onboardingApi';

type AutosaveState = 'idle' | 'saving' | 'saved' | 'error';

const PHASE_INFO = [
  {
    id: 'verify',
    title: 'Confirm your account',
    description: 'We sent a verification code to your email. Enter it below to unlock onboarding.',
  },
  {
    id: 'consent',
    title: 'Compliance ready',
    description: 'Accept the Terms of Service and Privacy Policy so we can activate analytics and audit trails.',
  },
];

const CHECKLIST_TIPS = [
  'Autosave kicks in right after verification—no more repeated steps.',
  'Your onboarding checklist mirrors every phase so teammates stay in sync.',
  'Need help? Support links are in each phase once you land in the wizard.',
];

const VerifyEmailPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [code, setCode] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<AutosaveState>('idle');
  const [lastVerifiedAt, setLastVerifiedAt] = useState<Date | null>(null);

  const email = searchParams.get('email') ?? '';
  const service = searchParams.get('service') ?? 'si';
  const onboardingToken = searchParams.get('onboarding_token') ?? undefined;
  const next = searchParams.get('next') ?? '/onboarding/si/integration-choice';

  const normalizedEmail = email.trim();

  const headerSubtitle = useMemo(() => {
    if (!normalizedEmail) {
      return 'Enter the verification code sent to your email to continue.';
    }
    return `We sent a verification code to ${normalizedEmail}. Enter it below to unlock your checklist.`;
  }, [normalizedEmail]);

  const handleVerify = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!normalizedEmail) {
      setError('Email address is missing from the verification link.');
      return;
    }

    if (!code.trim()) {
      setError('Enter the verification code from your email.');
      return;
    }

    if (!acceptTerms || !acceptPrivacy) {
      setError('You must accept the Terms of Service and Privacy Policy to continue.');
      return;
    }

    setStatus('saving');

    try {
      const authData = await authService.verifyEmail({
        email: normalizedEmail,
        code: code.trim(),
        service_package: service,
        onboarding_token: onboardingToken,
        terms_accepted: acceptTerms,
        privacy_accepted: acceptPrivacy,
        metadata: {
          consent_accepted_at: new Date().toISOString(),
        },
      });

      setStatus('saved');
      setLastVerifiedAt(new Date());

      try {
        await OnboardingStateManager.updateStep(authData.user.id, 'email_verification', true);
        await OnboardingStateManager.updateStep(authData.user.id, 'terms_acceptance', true);
      } catch (updateError) {
        console.warn('Failed to persist onboarding step after verification:', updateError);
      }

      const redirectTarget = next.startsWith('/') ? next : `/${next}`;
      router.push(redirectTarget);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Verification failed. Please try again.';
      setError(message);
      setStatus('error');
    }
  };

  return (
    <AuthLayout
      title="Verify your email"
      subtitle={headerSubtitle}
      showBackToHome={false}
    >
      <form onSubmit={handleVerify} className="space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-semibold text-slate-900">Step 1 · Email verification</p>
            <p className="text-xs text-slate-600">
              Confirm your email and accept our policies to start the SI onboarding checklist.
            </p>
          </div>
          <AutosaveStatusChip status={status} lastSavedAt={lastVerifiedAt ?? undefined} />
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
            {error}
          </div>
        )}

        <div className="rounded-2xl border border-indigo-100 bg-indigo-50/70 p-6 space-y-3">
          {PHASE_INFO.map((phase) => (
            <div key={phase.id} className="rounded-xl bg-white/80 p-3 shadow-sm">
              <p className="text-sm font-semibold text-indigo-900">{phase.title}</p>
              <p className="text-xs text-indigo-700 leading-relaxed">{phase.description}</p>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 space-y-4">
          <FormField
            label="Verification code"
            name="verification_code"
            value={code}
            onChange={setCode}
            placeholder="Enter the 6-digit code"
            required
          />

          <p className="text-xs text-slate-500">
            Didn’t get the email? Check your spam folder or contact support at compliance@taxpoynt.com.
          </p>
        </div>

        <div className="rounded-2xl border border-blue-100 bg-blue-50/70 p-6 space-y-3 text-sm text-blue-800">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Why we require this</p>
          <ul className="space-y-2">
            {CHECKLIST_TIPS.map((tip) => (
              <li key={tip} className="flex items-start gap-2">
                <span className="mt-1 h-2 w-2 rounded-full bg-blue-500" />
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-3 text-sm text-slate-700">
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              checked={acceptTerms}
              onChange={(event) => setAcceptTerms(event.target.checked)}
            />
            <span>
              I agree to the <a href="/legal/terms" className="text-indigo-600 hover:underline">TaxPoynt Terms of Service</a>.
            </span>
          </label>

          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              checked={acceptPrivacy}
              onChange={(event) => setAcceptPrivacy(event.target.checked)}
            />
            <span>
              I acknowledge the <a href="/legal/privacy" className="text-indigo-600 hover:underline">Privacy Policy</a> covering data storage and processing.
            </span>
          </label>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <TaxPoyntButton
            type="button"
            variant="outline"
            className="border-indigo-200 text-indigo-700 hover:bg-indigo-50"
            onClick={() => {
              if (window.history.length > 1) {
                router.back();
              } else {
                const params = new URLSearchParams({ service });
                params.set('next', next);
                router.push(`/auth/signup?${params.toString()}`);
              }
            }}
          >
            Back
          </TaxPoyntButton>

          <TaxPoyntButton
            type="submit"
            variant="primary"
            className="w-full bg-indigo-600 hover:bg-indigo-700 sm:w-auto"
            disabled={status === 'saving'}
          >
            {status === 'saving' ? 'Verifying…' : 'Verify email and continue'}
          </TaxPoyntButton>
        </div>
      </form>
    </AuthLayout>
  );
};

export default VerifyEmailPage;
