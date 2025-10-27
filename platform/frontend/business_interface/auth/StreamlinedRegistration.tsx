'use client';

/**
 * Streamlined Registration Component
 * ==================================
 * SI-focused registration with checklist preview and minimal required fields
 */

import React, { useEffect, useMemo, useState } from 'react';
import { AuthLayout } from '../../shared_components/auth/AuthLayout';
import { TaxPoyntButton } from '../../design_system/components/TaxPoyntButton';
import { FormField } from '../../design_system/components/FormField';
import { secureLogger } from '../../shared_components/utils/secureLogger';

interface PhaseSummary {
  id: string;
  title: string;
  description: string;
}

interface ChecklistHighlight {
  id: string;
  title: string;
  description: string;
}

export interface StreamlinedRegistrationProps {
  onCompleteRegistration: (registrationData: StreamlinedRegistrationData) => Promise<void>;
  isLoading?: boolean;
  error?: string;
  initialServicePackage?: 'si' | 'app' | 'hybrid';
  nextPath?: string;
}

export interface StreamlinedRegistrationData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  business_name: string;
  companyType?: string;
  companySize?: string;
  service_package: 'si' | 'app' | 'hybrid';
  terms_accepted: boolean;
  privacy_accepted: boolean;
  trial_started: boolean;
  trial_start_date: string;
  [key: string]: any;
}

const PHASE_SUMMARY: PhaseSummary[] = [
  {
    id: 'phase-one',
    title: 'Phase 1 · Integration choice',
    description: 'Pick what to connect first and preview the tailored checklist.',
  },
  {
    id: 'phase-two',
    title: 'Phase 2 · Connect systems',
    description: 'Link ERPs, CRMs, and financial feeds with autosave on every step.',
  },
  {
    id: 'phase-three',
    title: 'Phase 3 · Launch readiness',
    description: 'Complete compliance checks and unlock analytics for go-live.',
  },
];

const CHECKLIST_HIGHLIGHTS: ChecklistHighlight[] = [
  {
    id: 'autosave',
    title: 'Autosave across devices',
    description: 'Every task you complete is stored so you can resume from any browser.',
  },
  {
    id: 'progress',
    title: 'Progress you can trust',
    description: 'The SI dashboard mirrors each phase, so teams share one source of truth.',
  },
  {
    id: 'support',
    title: 'Guided assistance',
    description: 'Contextual help and escalation paths are embedded in every phase.',
  },
];

export const StreamlinedRegistration: React.FC<StreamlinedRegistrationProps> = ({
  onCompleteRegistration,
  isLoading = false,
  error,
  initialServicePackage = 'si',
  nextPath = '/onboarding/si/integration-choice',
}) => {
  const [formData, setFormData] = useState<StreamlinedRegistrationData>({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    business_name: '',
    companyType: 'system_integrator',
    companySize: '1-10',
    service_package: initialServicePackage,
    terms_accepted: false,
    privacy_accepted: false,
    trial_started: false,
    trial_start_date: new Date().toISOString(),
  });

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    setFormData((prev) => ({
      ...prev,
      service_package: initialServicePackage,
    }));
  }, [initialServicePackage]);

  const serviceLabel = useMemo(() => {
    switch (formData.service_package) {
      case 'app':
        return 'Access Point Provider workspace';
      case 'hybrid':
        return 'Hybrid workspace';
      default:
        return 'System Integrator workspace';
    }
  }, [formData.service_package]);

  const updateField = (field: keyof StreamlinedRegistrationData) => (value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (fieldErrors[field]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const handleCheckboxChange = (field: 'terms_accepted' | 'privacy_accepted' | 'trial_started') =>
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const { checked } = event.target;
      setFormData((prev) => ({ ...prev, [field]: checked }));
      if (fieldErrors[field]) {
        setFieldErrors((prev) => {
          const next = { ...prev };
          delete next[field];
          return next;
        });
      }
    };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.first_name.trim()) {
      errors.first_name = 'First name is required';
    }
    if (!formData.last_name.trim()) {
      errors.last_name = 'Last name is required';
    }
    if (!formData.email.trim()) {
      errors.email = 'Work email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Enter a valid email address';
    }
    if (!formData.password) {
      errors.password = 'Create a password to continue';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }
    if (!formData.business_name.trim()) {
      errors.business_name = 'Business or workspace name is required';
    }
    if (!formData.terms_accepted) {
      errors.terms_accepted = 'You must accept the Terms of Service';
    }
    if (!formData.privacy_accepted) {
      errors.privacy_accepted = 'You must acknowledge the Privacy Policy';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    secureLogger.userAction('Submitting streamlined registration', {
      service_package: formData.service_package,
      has_business_name: Boolean(formData.business_name),
    });

    await onCompleteRegistration(formData);
  };

  return (
    <AuthLayout
      title="Create your SI workspace"
      subtitle="Verify your email next, then follow the three-phase checklist to launch."
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
            {error}
          </div>
        )}

        <div className="rounded-2xl border border-indigo-100 bg-indigo-50/70 p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">What to expect</p>
          <div className="mt-4 space-y-3">
            {PHASE_SUMMARY.map((phase) => (
              <div key={phase.id} className="rounded-xl bg-white/80 p-3 shadow-sm">
                <p className="text-sm font-semibold text-indigo-900">{phase.title}</p>
                <p className="text-xs text-indigo-700 leading-relaxed">{phase.description}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-900">Workspace preset</p>
                <p className="text-xs text-slate-600">{serviceLabel}</p>
              </div>
              <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-600">
                Step 0 · Registration
              </span>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                label="First name"
                name="first_name"
                value={formData.first_name}
                onChange={updateField('first_name')}
                placeholder="Ada"
                required
                error={fieldErrors.first_name}
              />
              <FormField
                label="Last name"
                name="last_name"
                value={formData.last_name}
                onChange={updateField('last_name')}
                placeholder="Okeke"
                required
                error={fieldErrors.last_name}
              />
            </div>

            <FormField
              label="Work email"
              name="email"
              type="email"
              value={formData.email}
              onChange={updateField('email')}
              placeholder="adaobi@example.com"
              required
              error={fieldErrors.email}
            />

            <FormField
              label="Create password"
              name="password"
              type="password"
              value={formData.password}
              onChange={updateField('password')}
              placeholder="Minimum 8 characters"
              required
              error={fieldErrors.password}
            />

            <FormField
              label="Business or workspace name"
              name="business_name"
              value={formData.business_name}
              onChange={updateField('business_name')}
              placeholder="Your organisation"
              required
              error={fieldErrors.business_name}
            />
          </div>
        </div>

        <div className="rounded-2xl border border-blue-100 bg-blue-50/70 p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Why the checklist matters</p>
          <ul className="mt-4 space-y-3">
            {CHECKLIST_HIGHLIGHTS.map((item) => (
              <li key={item.id} className="flex gap-3 rounded-xl bg-white/80 p-3 shadow-sm">
                <span className="mt-1 h-2 w-2 rounded-full bg-blue-500"></span>
                <div>
                  <p className="text-sm font-semibold text-blue-900">{item.title}</p>
                  <p className="text-xs text-blue-700 leading-relaxed">{item.description}</p>
                </div>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-xs text-blue-700">
            Next stop: <span className="font-semibold">{nextPath}</span> — we&rsquo;ll confirm your email and unlock the SI onboarding checklist.
          </p>
        </div>

        <div className="space-y-4">
          <label className="flex items-start gap-3 text-sm text-slate-700">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              checked={formData.terms_accepted}
              onChange={handleCheckboxChange('terms_accepted')}
              required
            />
            <span>
              I agree to the <a href="/legal/terms" className="text-indigo-600 hover:underline">TaxPoynt Terms of Service</a>.
              {fieldErrors.terms_accepted && (
                <span className="block text-xs text-red-600">{fieldErrors.terms_accepted}</span>
              )}
            </span>
          </label>

          <label className="flex items-start gap-3 text-sm text-slate-700">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              checked={formData.privacy_accepted}
              onChange={handleCheckboxChange('privacy_accepted')}
              required
            />
            <span>
              I acknowledge the <a href="/legal/privacy" className="text-indigo-600 hover:underline">Privacy Policy</a> covering data storage and processing.
              {fieldErrors.privacy_accepted && (
                <span className="block text-xs text-red-600">{fieldErrors.privacy_accepted}</span>
              )}
            </span>
          </label>
        </div>

        <TaxPoyntButton
          type="submit"
          variant="primary"
          className="w-full bg-indigo-600 hover:bg-indigo-700"
          disabled={isLoading}
        >
          {isLoading ? 'Creating workspace…' : 'Continue to email verification'}
        </TaxPoyntButton>
      </form>
    </AuthLayout>
  );
};

export default StreamlinedRegistration;
