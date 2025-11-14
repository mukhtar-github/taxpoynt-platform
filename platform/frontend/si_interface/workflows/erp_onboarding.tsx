'use client';

import React, {
  useState,
  useEffect,
  useMemo,
  useRef,
  useCallback,
} from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../../design_system/components/Button';
import {
  onboardingApi,
  OnboardingState,
  ServiceSelectionPayload,
  CompanyProfilePayload,
} from '../../shared_components/services/onboardingApi';
import { onboardingStateQueue } from '../../shared_components/services/onboardingStateQueue';
import { authService } from '../../shared_components/services/auth';
import sessionPersistence from '../../shared_components/utils/onboardingSessionPersistence';

type EntryStepId = 'service-selection' | 'company-profile' | 'system-connectivity';

interface EntryStep {
  id: EntryStepId;
  title: string;
  description: string;
}

interface ServiceSelectionForm {
  selectedPackage: string;
  integrationTargets: string[];
  primaryUseCases: string[];
  goLiveTimeline: string;
  notes: string;
}

interface CompanyProfileForm {
  companyName: string;
  rcNumber: string;
  tin: string;
  contactEmail: string;
  contactPhone: string;
  address: string;
  industry: string;
  companySize: string;
  complianceContact: string;
}

interface SystemConnectivityForm {
  connectNow: boolean;
  hasSandboxAccess: boolean;
  needsAssistance: boolean;
}

export interface ERPOnboardingProps {
  organizationId?: string;
  onComplete?: (organizationId: string) => void;
  onSkip?: () => void;
  isLoading?: boolean;
  initialStepId?: string;
}

const ENTRY_STEPS: EntryStep[] = [
  {
    id: 'service-selection',
    title: 'Service Focus',
    description:
      'Tell us how you plan to use TaxPoynt so we can tailor your workspace and recommendations.',
  },
  {
    id: 'company-profile',
    title: 'Company Profile',
    description:
      'Confirm your organisation details. We reuse this for compliance, billing, and notifications.',
  },
  {
    id: 'system-connectivity',
    title: 'Connect Systems',
    description:
      'Decide how you want to connect your ERP or financial systems. You can always finish this later.',
  },
];

const ENTRY_STEP_IDS: EntryStepId[] = ENTRY_STEPS.map(step => step.id);

const LEGACY_STEP_MAP: Record<string, EntryStepId> = {
  organization_setup: 'service-selection',
  'organization-setup': 'service-selection',
  'service-selection': 'service-selection',
  compliance_verification: 'company-profile',
  'compliance-verification': 'company-profile',
  company_profile: 'company-profile',
  'company-profile': 'company-profile',
  erp_selection: 'system-connectivity',
  'erp-selection': 'system-connectivity',
  erp_configuration: 'system-connectivity',
  'erp-configuration': 'system-connectivity',
  system_connectivity: 'system-connectivity',
  'system-connectivity': 'system-connectivity',
};

const SERVICE_PACKAGES = [
  { value: 'si', label: 'System Integrator', description: 'You integrate ERP/CRM systems for clients.' },
  { value: 'app', label: 'Access Point Provider', description: 'You provide connector access to clients.' },
  { value: 'hybrid', label: 'Hybrid', description: 'You manage integrations and access for clients.' },
];

const INTEGRATION_OPTIONS = [
  'Odoo',
  'SAP Business One',
  'Microsoft Dynamics 365',
  'Custom ERP',
  'Point of Sale (POS)',
  'Other',
];

const PRIMARY_USE_CASES = [
  'Invoice Synchronisation',
  'Compliance Validation',
  'Automated Reporting',
  'Payments & Collections',
  'Analytics & Insights',
];

const defaultServiceSelection: ServiceSelectionForm = {
  selectedPackage: 'si',
  integrationTargets: [],
  primaryUseCases: [],
  goLiveTimeline: '',
  notes: '',
};

const defaultCompanyProfile: CompanyProfileForm = {
  companyName: '',
  rcNumber: '',
  tin: '',
  contactEmail: '',
  contactPhone: '',
  address: '',
  industry: '',
  companySize: '',
  complianceContact: '',
};

const defaultConnectivity: SystemConnectivityForm = {
  connectNow: true,
  hasSandboxAccess: false,
  needsAssistance: false,
};

const canonicalizeStep = (value?: string | null): EntryStepId => {
  if (!value) {
    return 'service-selection';
  }
  const normalized = value.trim().toLowerCase().replace(/\s+/g, '-');
  return LEGACY_STEP_MAP[normalized] ?? (ENTRY_STEP_IDS.includes(normalized as EntryStepId)
    ? (normalized as EntryStepId)
    : 'service-selection');
};

const extractErrorMessage = (error: unknown, fallback: string): string => {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  if (typeof error === 'string' && error.trim()) {
    return error.trim();
  }
  if (error && typeof error === 'object') {
    const detail = (error as Record<string, any>).detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail.trim();
    }
    const message = (error as Record<string, any>).message;
    if (typeof message === 'string' && message.trim()) {
      return message.trim();
    }
  }
  return fallback;
};

const buildServicePayload = (form: ServiceSelectionForm): ServiceSelectionPayload => ({
  selected_package: form.selectedPackage || undefined,
  integration_targets: form.integrationTargets.length ? form.integrationTargets : undefined,
  primary_use_cases: form.primaryUseCases.length ? form.primaryUseCases : undefined,
  go_live_timeline: form.goLiveTimeline || undefined,
  notes: form.notes || undefined,
});

const buildCompanyPayload = (form: CompanyProfileForm): CompanyProfilePayload => ({
  company_name: form.companyName,
  rc_number: form.rcNumber || undefined,
  tin: form.tin || undefined,
  contact_email: form.contactEmail || undefined,
  contact_phone: form.contactPhone || undefined,
  address: form.address || undefined,
  industry: form.industry || undefined,
  company_size: form.companySize || undefined,
  compliance_contact: form.complianceContact || undefined,
});

const buildConnectivityMetadata = (form: SystemConnectivityForm) => ({
  connect_now: form.connectNow,
  has_sandbox_access: form.hasSandboxAccess,
  needs_assistance: form.needsAssistance,
});

export const ERPOnboarding: React.FC<ERPOnboardingProps> = ({
  organizationId,
  onComplete,
  onSkip,
  isLoading = false,
  initialStepId,
}) => {
  const router = useRouter();
  const [serviceSelection, setServiceSelection] = useState<ServiceSelectionForm>(defaultServiceSelection);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfileForm>(defaultCompanyProfile);
  const [systemConnectivity, setSystemConnectivity] = useState<SystemConnectivityForm>(defaultConnectivity);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(() => {
    if (!initialStepId) return 0;
    const canonical = canonicalizeStep(initialStepId);
    return Math.max(ENTRY_STEP_IDS.indexOf(canonical), 0);
  });
  const [completedSteps, setCompletedSteps] = useState<Set<EntryStepId>>(new Set());
  const [serverMetadata, setServerMetadata] = useState<Record<string, any>>({});
  const [autosaveStatus, setAutosaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [autosaveMessage, setAutosaveMessage] = useState<string | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const autosaveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const hasRestoredStateRef = useRef(false);
  const serviceAutosaveReadyRef = useRef(false);
  const profileAutosaveReadyRef = useRef(false);

  const currentStep = ENTRY_STEPS[currentStepIndex];
  const storedUser = useMemo(() => authService.getStoredUser(), []);

  const updateSessionState = useCallback(
    (activeStep: EntryStepId, completed: Set<EntryStepId>) => {
      if (!storedUser?.id) {
        return;
      }
      if (!sessionPersistence.hasValidSession(storedUser.id)) {
        sessionPersistence.initializeSession(storedUser.id, storedUser.platform_role ?? 'system_integrator');
      }
      sessionPersistence.updateSession({
        currentStep: activeStep,
        completedSteps: Array.from(completed),
        userId: storedUser.id,
        userRole: storedUser.platform_role ?? 'system_integrator',
        metadata: {
          wizard: {
            service_focus: buildServicePayload(serviceSelection),
            company_profile: buildCompanyPayload(companyProfile),
            system_connectivity: buildConnectivityMetadata(systemConnectivity),
          },
        },
      });
    },
    [companyProfile, serviceSelection, systemConnectivity, storedUser],
  );

  const buildWizardMetadata = useCallback(() => {
    const base = { ...(serverMetadata || {}) };
    base.wizard = {
      ...(base.wizard ?? {}),
      service_focus: buildServicePayload(serviceSelection),
      company_profile: buildCompanyPayload(companyProfile),
      system_connectivity: buildConnectivityMetadata(systemConnectivity),
    };
    (base as Record<string, any>).forceSync = true;
    return base;
  }, [companyProfile, serviceSelection, systemConnectivity, serverMetadata]);

  const updateFromState = useCallback(
    (state: OnboardingState) => {
      if (!state) return;

      const metadata = (state.metadata ?? {}) as Record<string, any>;
      setServerMetadata(metadata);

      const wizard = (metadata.wizard ?? {}) as Record<string, any>;
      if (wizard.service_focus) {
        setServiceSelection(prev => ({
          ...prev,
          selectedPackage: wizard.service_focus.selected_package ?? prev.selectedPackage,
          integrationTargets: Array.isArray(wizard.service_focus.integration_targets)
            ? wizard.service_focus.integration_targets
            : prev.integrationTargets,
          primaryUseCases: Array.isArray(wizard.service_focus.primary_use_cases)
            ? wizard.service_focus.primary_use_cases
            : prev.primaryUseCases,
          goLiveTimeline: wizard.service_focus.go_live_timeline ?? prev.goLiveTimeline,
          notes: wizard.service_focus.notes ?? prev.notes,
        }));
      }
      if (wizard.company_profile) {
        setCompanyProfile(prev => ({
          ...prev,
          companyName: wizard.company_profile.company_name ?? prev.companyName,
          rcNumber: wizard.company_profile.rc_number ?? prev.rcNumber,
          tin: wizard.company_profile.tin ?? prev.tin,
          contactEmail: wizard.company_profile.contact_email ?? prev.contactEmail,
          contactPhone: wizard.company_profile.contact_phone ?? prev.contactPhone,
          address: wizard.company_profile.address ?? prev.address,
          industry: wizard.company_profile.industry ?? prev.industry,
          companySize: wizard.company_profile.company_size ?? prev.companySize,
          complianceContact: wizard.company_profile.compliance_contact ?? prev.complianceContact,
        }));
      }
      if (wizard.system_connectivity) {
        setSystemConnectivity(prev => ({
          ...prev,
          connectNow: typeof wizard.system_connectivity.connect_now === 'boolean'
            ? wizard.system_connectivity.connect_now
            : prev.connectNow,
          hasSandboxAccess: typeof wizard.system_connectivity.has_sandbox_access === 'boolean'
            ? wizard.system_connectivity.has_sandbox_access
            : prev.hasSandboxAccess,
          needsAssistance: typeof wizard.system_connectivity.needs_assistance === 'boolean'
            ? wizard.system_connectivity.needs_assistance
            : prev.needsAssistance,
        }));
      }

      const canonicalCompleted = new Set<EntryStepId>();
      const stepsFromState = Array.isArray(state.completed_steps) ? state.completed_steps : [];
      stepsFromState.forEach(step => {
        const canonical = canonicalizeStep(step);
        if (ENTRY_STEP_IDS.includes(canonical)) {
          canonicalCompleted.add(canonical);
        }
      });
      setCompletedSteps(canonicalCompleted);

      const activeStep = canonicalizeStep(state.current_step);
      const resolvedIndex = Math.max(ENTRY_STEP_IDS.indexOf(activeStep), 0);
      setCurrentStepIndex(resolvedIndex);

      updateSessionState(activeStep, canonicalCompleted);
    },
    [updateSessionState],
  );

  const handleAutosave = useCallback(
    async (stepId: EntryStepId) => {
      if (!authService.isAuthenticated()) {
        return;
      }
      try {
        setAutosaveStatus('saving');
        setAutosaveMessage(stepId === 'service-selection' ? 'Saving service focus…' : 'Saving company profile…');
        let state: OnboardingState | null = null;
        if (stepId === 'service-selection') {
          state = await onboardingApi.saveServiceSelection(buildServicePayload(serviceSelection));
        } else if (stepId === 'company-profile') {
          state = await onboardingApi.saveCompanyProfile(buildCompanyPayload(companyProfile));
        }
        if (state) {
          updateFromState(state);
        }
        setAutosaveStatus('saved');
        setAutosaveMessage('Saved');
        setLastSavedAt(new Date());
      } catch (error) {
        const message = extractErrorMessage(error, 'Autosave failed. We will retry soon.');
        setAutosaveStatus('error');
        setAutosaveMessage(message);
      }
    },
    [companyProfile, serviceSelection, updateFromState],
  );

  const scheduleAutosave = useCallback(
    (stepId: EntryStepId) => {
      if (autosaveTimerRef.current) {
        clearTimeout(autosaveTimerRef.current);
      }
      autosaveTimerRef.current = setTimeout(() => {
        void handleAutosave(stepId);
      }, 1200);
    },
    [handleAutosave],
  );

  useEffect(() => {
    const loadState = async () => {
      try {
        const state = await onboardingApi.getOnboardingState();
        if (state) {
          updateFromState(state);
        }
      } catch (error) {
        console.warn('Unable to load onboarding state:', error);
      } finally {
        hasRestoredStateRef.current = true;
      }
    };
    loadState();
    return () => {
      if (autosaveTimerRef.current) {
        clearTimeout(autosaveTimerRef.current);
      }
    };
  }, [updateFromState]);

  useEffect(() => {
    if (!hasRestoredStateRef.current) return;
    if (!serviceAutosaveReadyRef.current) {
      serviceAutosaveReadyRef.current = true;
      return;
    }
    scheduleAutosave('service-selection');
  }, [serviceSelection, scheduleAutosave]);

  useEffect(() => {
    if (!hasRestoredStateRef.current) return;
    if (!profileAutosaveReadyRef.current) {
      profileAutosaveReadyRef.current = true;
      return;
    }
    scheduleAutosave('company-profile');
  }, [companyProfile, scheduleAutosave]);

  const progressPercentage = useMemo(() => {
    const completedCount = completedSteps.size;
    return Math.round((completedCount / ENTRY_STEPS.length) * 100);
  }, [completedSteps.size]);

  const handleCompleteLater = useCallback(() => {
    const activeStep = currentStep?.id ?? 'service-selection';
    updateSessionState(activeStep, completedSteps);
    if (onSkip) {
      onSkip();
      return;
    }
    router.push('/si/dashboard');
  }, [completedSteps, currentStep?.id, onSkip, router, updateSessionState]);

  const handleBack = useCallback(() => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
    }
  }, [currentStepIndex]);

  const handleContinue = useCallback(async () => {
    if (!currentStep) return;
    setSubmissionError(null);

    if (currentStep.id === 'company-profile' && !companyProfile.companyName.trim()) {
      setSubmissionError('Company name is required.');
      return;
    }

    setIsSubmitting(true);
    try {
      let latestState: OnboardingState | null = null;
      const updatedCompleted = new Set(completedSteps);
      updatedCompleted.add(currentStep.id);

      await onboardingStateQueue.enqueue({
        step: currentStep.id,
        completed: true,
        completedSteps: Array.from(updatedCompleted),
        metadata: buildWizardMetadata(),
        userId: storedUser?.id,
        source: 'erp_onboarding.handleContinue',
      });

      try {
        latestState = await onboardingApi.getOnboardingState();
        if (latestState) {
          updateFromState(latestState);
        }
      } catch (refreshError) {
        console.warn('Failed to refresh onboarding state after queue dispatch:', refreshError);
      }

      const nextIndex =
        currentStepIndex < ENTRY_STEPS.length - 1 ? currentStepIndex + 1 : currentStepIndex;

      if (nextIndex === currentStepIndex && currentStep.id === 'system-connectivity') {
        sessionPersistence.completeSession();
        const resolvedOrgId =
          organizationId ||
          latestState?.metadata?.organization_id ||
          authService.getStoredUser()?.organization?.id ||
          'unknown';
        if (onComplete) {
          onComplete(String(resolvedOrgId));
        } else {
          router.push('/si/dashboard');
        }
        return;
      }

      if (nextIndex !== currentStepIndex) {
        setCurrentStepIndex(nextIndex);
      }

      updateSessionState(
        ENTRY_STEPS[Math.min(nextIndex, ENTRY_STEPS.length - 1)].id,
        updatedCompleted,
      );
    } catch (error) {
      setSubmissionError(extractErrorMessage(error, 'Unable to save progress. Please retry.'));
    } finally {
      setIsSubmitting(false);
    }
  }, [
    buildWizardMetadata,
    companyProfile.companyName,
    completedSteps,
    currentStep,
    currentStepIndex,
    onComplete,
    organizationId,
    router,
    storedUser?.id,
    updateFromState,
    updateSessionState,
  ]);

  const toggleIntegrationTarget = useCallback((target: string) => {
    setServiceSelection(prev => {
      const exists = prev.integrationTargets.includes(target);
      return {
        ...prev,
        integrationTargets: exists
          ? prev.integrationTargets.filter(item => item !== target)
          : [...prev.integrationTargets, target],
      };
    });
  }, []);

  const togglePrimaryUseCase = useCallback((useCase: string) => {
    setServiceSelection(prev => {
      const exists = prev.primaryUseCases.includes(useCase);
      return {
        ...prev,
        primaryUseCases: exists
          ? prev.primaryUseCases.filter(item => item !== useCase)
          : [...prev.primaryUseCases, useCase],
      };
    });
  }, []);

  const renderServiceSelection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900">Choose your primary focus</h3>
        <div className="mt-4 grid gap-3">
          {SERVICE_PACKAGES.map(option => (
            <label
              key={option.value}
              className={`rounded-lg border p-4 transition ${
                serviceSelection.selectedPackage === option.value
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-400'
              }`}
            >
              <input
                type="radio"
                name="service-package"
                value={option.value}
                className="mr-3"
                checked={serviceSelection.selectedPackage === option.value}
                onChange={() =>
                  setServiceSelection(prev => ({
                    ...prev,
                    selectedPackage: option.value,
                  }))
                }
              />
              <span className="font-medium text-gray-900">{option.label}</span>
              <p className="mt-1 text-sm text-gray-600">{option.description}</p>
            </label>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900">Which systems do you plan to connect?</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {INTEGRATION_OPTIONS.map(option => {
            const active = serviceSelection.integrationTargets.includes(option);
            return (
              <button
                key={option}
                type="button"
                className={`rounded-full border px-4 py-2 text-sm transition ${
                  active ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-300 text-gray-600 hover:border-blue-400'
                }`}
                onClick={() => toggleIntegrationTarget(option)}
              >
                {option}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900">Primary use cases</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {PRIMARY_USE_CASES.map(useCase => {
            const active = serviceSelection.primaryUseCases.includes(useCase);
            return (
              <button
                key={useCase}
                type="button"
                className={`rounded-full border px-4 py-2 text-sm transition ${
                  active ? 'border-emerald-600 bg-emerald-50 text-emerald-700' : 'border-gray-300 text-gray-600 hover:border-emerald-400'
                }`}
                onClick={() => togglePrimaryUseCase(useCase)}
              >
                {useCase}
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col text-sm font-medium text-gray-700">
          Target go-live timeline
          <input
            type="text"
            value={serviceSelection.goLiveTimeline}
            onChange={event =>
              setServiceSelection(prev => ({
                ...prev,
                goLiveTimeline: event.target.value,
              }))
            }
            placeholder="e.g. Within 30 days"
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </label>
        <label className="flex flex-col text-sm font-medium text-gray-700">
          Notes (optional)
          <input
            type="text"
            value={serviceSelection.notes}
            onChange={event =>
              setServiceSelection(prev => ({
                ...prev,
                notes: event.target.value,
              }))
            }
            placeholder="Anything we should know about this rollout?"
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </label>
      </div>
    </div>
  );

  const renderCompanyProfile = () => (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col text-sm font-medium text-gray-700">
          Company name <span className="text-red-500">*</span>
          <input
            type="text"
            value={companyProfile.companyName}
            onChange={event =>
              setCompanyProfile(prev => ({
                ...prev,
                companyName: event.target.value,
              }))
            }
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="e.g. Example Integrations Ltd"
          />
        </label>
        <label className="flex flex-col text-sm font-medium text-gray-700">
          RC / CAC number
          <input
            type="text"
            value={companyProfile.rcNumber}
            onChange={event =>
              setCompanyProfile(prev => ({
                ...prev,
                rcNumber: event.target.value,
              }))
            }
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Registration identifier"
          />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col text-sm font-medium text-gray-700">
          Tax Identification Number (TIN)
          <input
            type="text"
            value={companyProfile.tin}
            onChange={event =>
              setCompanyProfile(prev => ({
                ...prev,
                tin: event.target.value,
              }))
            }
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Optional"
          />
        </label>
        <label className="flex flex-col text-sm font-medium text-gray-700">
          Industry
          <input
            type="text"
            value={companyProfile.industry}
            onChange={event =>
              setCompanyProfile(prev => ({
                ...prev,
                industry: event.target.value,
              }))
            }
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="e.g. Technology consulting"
          />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col text-sm font-medium text-gray-700">
          Contact email
          <input
            type="email"
            value={companyProfile.contactEmail}
            onChange={event =>
              setCompanyProfile(prev => ({
                ...prev,
                contactEmail: event.target.value,
              }))
            }
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="contact@example.com"
          />
        </label>
        <label className="flex flex-col text-sm font-medium text-gray-700">
          Contact phone
          <input
            type="tel"
            value={companyProfile.contactPhone}
            onChange={event =>
              setCompanyProfile(prev => ({
                ...prev,
                contactPhone: event.target.value,
              }))
            }
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="+234 800 000 0000"
          />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col text-sm font-medium text-gray-700">
          Address
          <input
            type="text"
            value={companyProfile.address}
            onChange={event =>
              setCompanyProfile(prev => ({
                ...prev,
                address: event.target.value,
              }))
            }
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Head office address"
          />
        </label>
        <label className="flex flex-col text-sm font-medium text-gray-700">
          Compliance contact
          <input
            type="text"
            value={companyProfile.complianceContact}
            onChange={event =>
              setCompanyProfile(prev => ({
                ...prev,
                complianceContact: event.target.value,
              }))
            }
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Person responsible for compliance"
          />
        </label>
      </div>

      <label className="flex flex-col text-sm font-medium text-gray-700">
        Company size
        <input
          type="text"
          value={companyProfile.companySize}
          onChange={event =>
            setCompanyProfile(prev => ({
              ...prev,
              companySize: event.target.value,
            }))
          }
          className="mt-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          placeholder="e.g. 51-200 employees"
        />
      </label>
    </div>
  );

  const renderSystemConnectivity = () => (
    <div className="space-y-6">
      <p className="text-sm text-gray-600">
        Decide how you would like to connect your ERP or financial systems. You can continue to the dashboard and finish this later if you are not ready.
      </p>

      <div className="space-y-4">
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            checked={systemConnectivity.connectNow}
            onChange={event =>
              setSystemConnectivity(prev => ({
                ...prev,
                connectNow: event.target.checked,
              }))
            }
          />
          <span className="text-sm text-gray-700">
            I want to connect an ERP or financial system now.
          </span>
        </label>
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            checked={systemConnectivity.hasSandboxAccess}
            onChange={event =>
              setSystemConnectivity(prev => ({
                ...prev,
                hasSandboxAccess: event.target.checked,
              }))
            }
          />
          <span className="text-sm text-gray-700">
            I already have sandbox credentials ready for testing.
          </span>
        </label>
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            checked={systemConnectivity.needsAssistance}
            onChange={event =>
              setSystemConnectivity(prev => ({
                ...prev,
                needsAssistance: event.target.checked,
              }))
            }
          />
          <span className="text-sm text-gray-700">
            I would like a TaxPoynt specialist to guide this setup.
          </span>
        </label>
      </div>

      <div className="rounded-lg bg-blue-50 p-4 text-sm text-blue-900">
        <h4 className="font-semibold">What happens next?</h4>
        <ul className="mt-2 list-inside list-disc space-y-1">
          <li>We generate a tailored checklist on your dashboard.</li>
          <li>You can invite teammates and continue integrating systems.</li>
          <li>Support is available if you enabled the assistance option.</li>
        </ul>
      </div>
    </div>
  );

  const renderStepContent = () => {
    switch (currentStep.id) {
      case 'service-selection':
        return renderServiceSelection();
      case 'company-profile':
        return renderCompanyProfile();
      case 'system-connectivity':
        return renderSystemConnectivity();
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-2/3 rounded bg-gray-200" />
          <div className="h-4 w-full rounded bg-gray-100" />
          <div className="h-4 w-5/6 rounded bg-gray-100" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">
            Step {currentStepIndex + 1} of {ENTRY_STEPS.length}
          </p>
          <h2 className="mt-1 text-2xl font-bold text-gray-900">{currentStep.title}</h2>
          <p className="mt-1 text-sm text-gray-600">{currentStep.description}</p>
        </div>
        <div className="flex items-center gap-4">
          {autosaveStatus === 'saving' && <span className="text-xs text-blue-600">Saving…</span>}
          {autosaveStatus === 'error' && (
            <span className="text-xs text-red-500">
              {autosaveMessage ?? 'Autosave failed'}
            </span>
          )}
          {autosaveStatus === 'saved' && lastSavedAt && (
            <span className="text-xs text-emerald-600">
              Saved {lastSavedAt.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      <div className="mt-6">
        <div className="h-2 overflow-hidden rounded-full bg-gray-100">
          <div
            className="h-full rounded-full bg-blue-500 transition-all"
            style={{ width: `${Math.max(progressPercentage, 5)}%` }}
          />
        </div>
        <div className="mt-2 flex justify-between text-xs font-medium text-gray-500">
          {ENTRY_STEPS.map((step, index) => {
            const complete = completedSteps.has(step.id) || index < currentStepIndex;
            const active = index === currentStepIndex;
            return (
              <div key={step.id} className="flex flex-col items-start">
                <span
                  className={`rounded-full px-2 py-1 ${
                    active
                      ? 'bg-blue-100 text-blue-700'
                      : complete
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {step.title}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-8">{renderStepContent()}</div>

      {submissionError && (
        <div className="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {submissionError}
        </div>
      )}

      <div className="mt-8 flex flex-col gap-3 border-t border-gray-100 pt-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3 text-sm text-gray-600">
          <button
            type="button"
            className="text-sm font-medium text-blue-600 hover:text-blue-500"
            onClick={handleCompleteLater}
          >
            Complete later
          </button>
        </div>
        <div className="flex items-center gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={handleBack}
            disabled={currentStepIndex === 0 || isSubmitting}
          >
            Back
          </Button>
          <Button
            type="button"
            onClick={handleContinue}
            loading={isSubmitting}
          >
            {currentStep.id === 'system-connectivity' ? 'Finish Setup' : 'Save & Continue'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ERPOnboarding;
