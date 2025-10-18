'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

import { secureLogger } from '../../../shared_components/utils/secureLogger';
import apiClient from '../../../shared_components/api/client';
import { Button } from '../../../shared_components/design_system/components/Button';

interface ForgotPasswordResponse {
  /** optional message for the user */
  message?: string;
  /** indicates success */
  success?: boolean;
  /** additional metadata */
  meta?: Record<string, unknown>;
}

export default function ForgotPasswordPage(): JSX.Element {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState<string>('');

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!email) {
      setStatus('error');
      setMessage('Please provide the email associated with your account.');
      return;
    }

    try {
      setStatus('submitting');
      setMessage('');

      const response = await apiClient.post<ForgotPasswordResponse>('/auth/forgot-password', { email });
      const success = response?.success ?? true;
      if (success) {
        const detail =
          response?.message ||
          response?.meta?.message ||
          'If the address matches an existing account, a reset link will arrive shortly.';
        setStatus('success');
        setMessage(detail);
      } else {
        const detail =
          response?.message ||
          response?.meta?.error ||
          'We could not process the request. Please try again later.';
        setStatus('error');
        setMessage(detail);
      }
    } catch (error: unknown) {
      secureLogger.error('Forgot password request failed', error);
      setStatus('error');
      setMessage('We could not process this request right now. Please try again later.');
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="mx-auto w-full max-w-4xl px-6 py-8 sm:px-10">
        <Link href="/auth/signin" className="text-sm font-semibold text-indigo-600 hover:text-indigo-500">
          ← Back to sign in
        </Link>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center px-6 pb-16 sm:px-10">
        <div className="w-full rounded-3xl bg-white p-8 shadow-lg ring-1 ring-slate-200 sm:p-10">
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-slate-900 sm:text-3xl">Reset your password</h1>
            <p className="mt-2 text-sm text-slate-600">
              Enter the email associated with your System Integrator account. If it exists, we’ll send a secure link to create a new password.
            </p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label className="block text-sm font-medium text-slate-700">Email address</label>
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                placeholder="you@example.com"
              />
            </div>

            {status !== 'idle' && (
              <div
                className={`rounded-lg border px-4 py-3 text-sm ${
                  status === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'
                }`}
              >
                {message}
              </div>
            )}

            <div className="flex items-center justify-between">
              <Button type="submit" disabled={status === 'submitting'}>
                {status === 'submitting' ? 'Submitting…' : 'Send reset link'}
              </Button>
              <button
                type="button"
                className="text-sm font-medium text-slate-600 hover:text-slate-500"
                onClick={() => router.push('/auth/signin')}
              >
                Back to sign in
              </button>
            </div>
          </form>

          <div className="mt-8 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-xs text-slate-500">
            If you no longer have access to this email address, contact support via{' '}
            <a href="mailto:support@taxpoynt.com" className="font-medium text-indigo-600 hover:text-indigo-500">
              support@taxpoynt.com
            </a>{' '}
            with proof of company ownership. For security reasons we cannot reset passwords over the phone.
          </div>
        </div>
      </main>
    </div>
  );
}

