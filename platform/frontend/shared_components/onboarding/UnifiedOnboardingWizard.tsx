/**
 * Unified Onboarding Wizard
 * =========================
 * Streamlines onboarding for SI, APP, and Hybrid users through a single
 * milestone-based experience. The wizard keeps state locally while
 * synchronising progress with the onboarding API.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { TaxPoyntButton, TaxPoyntInput } from '../../design_system';
import { onboardingApi } from '../services/onboardingApi';
import { authService } from '../services/auth';
import { CrossFormDataManager } from '../utils/formPersistence';

export type ServicePackage = 'si' | 'app' | 'hybrid';

interface UnifiedOnboardingWizardProps {
  initialService?: ServicePackage | null;
  defaultStep?: string;
  onComplete?: (service: ServicePackage) => void;
}

interface WizardStep {
  id: string;
  label: string;
  description: string;
  render: () => React.ReactNode;
  isLocked?: boolean;
}

interface StepDefinition {
  title: string;
  description: string;
  success_criteria?: string;
}

interface CompanyProfile {
  companyName: string;
  industry: string;
  teamSize: string;
  country: string;
}

interface ServiceConfiguration {
  connectors: string[];
  firsEnvironment: 'sandbox' | 'production';
  enableAutoRetry: boolean;
  enableNotifications: boolean;
  shareHybridInsights: boolean;
}

const SERVICE_OPTIONS: Array<{ id: ServicePackage; title: string; summary: string; points: string[]; badge?: string }> = [
  {
    id: 'si',
    title: 'System Integrator',
    summary: 'Connect ERPs, CRMs, and data sources to TaxPoynt.',
    points: ['Integration hub', 'Workflow automation', 'Realtime validation'],
  },
  {
    id: 'app',
    title: 'Access Point Provider',
    summary: 'Transmit compliant invoices directly to FIRS.',
    points: ['FIRS transmission', 'Validation pipeline', 'Sandbox + production modes'],
    badge: 'Recommended',
  },
  {
    id: 'hybrid',
    title: 'Hybrid Suite',
    summary: 'Blend SI integrations with APP transmission controls.',
    points: ['Unified analytics', 'Shared workflows', 'Enterprise SLAs'],
  },
];

const INITIAL_COMPANY_PROFILE: CompanyProfile = {
  companyName: '',
  industry: '',
  teamSize: '',
  country: 'Nigeria',
};

const INITIAL_SERVICE_CONFIGURATION: ServiceConfiguration = {
  connectors: [],
  firsEnvironment: 'sandbox',
  enableAutoRetry: true,
  enableNotifications: true,
  shareHybridInsights: true,
};

const DEFAULT_STEP_SEQUENCE = [
  'service-selection',
  'company-profile',
  'system-connectivity',
  'review',
  'launch',
] as const;

const FALLBACK_STEP_DEFINITIONS: Record<string, StepDefinition> = {
  'service-selection': {
    title: 'Select Your Service Focus',
    description: 'Choose the workspace configuration that matches how you plan to use TaxPoynt.',
  },
  'company-profile': {
    title: 'Company Profile',
    description: 'Confirm the organisation details we will use across compliance and billing.',
  },
  'system-connectivity': {
    title: 'Connect Systems',
    description: 'Link any ERPs, CRMs, or banking systems needed for automation.',
  },
  review: {
    title: 'Review & Confirm',
    description: 'Double-check your selections before launch.',
  },
  launch: {
    title: 'Launch Workspace',
    description: 'Activate and head to your dashboard.',
  },
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const normalizeServicePackage = (value: unknown): ServicePackage | null => {
  if (typeof value !== 'string') {
    return null;
  }
  const normalized = value.toLowerCase();
  if (['si', 'system_integrator', 'system-integrator'].includes(normalized)) {
    return 'si';
  }
  if (['app', 'access_point_provider', 'access-point-provider'].includes(normalized)) {
    return 'app';
  }
  if (['hybrid', 'hybrid_user', 'hybrid-user'].includes(normalized)) {
    return 'hybrid';
  }
  return null;
};

const sanitizeString = (value: unknown): string => (typeof value === 'string' ? value : '');

const sanitizeCompanyProfile = (value: unknown): CompanyProfile => {
  if (!isRecord(value)) {
    return INITIAL_COMPANY_PROFILE;
  }
  return {
    companyName: sanitizeString(value.companyName ?? value.company_name),
    industry: sanitizeString(value.industry),
    teamSize: sanitizeString(value.teamSize ?? value.team_size),
    country: sanitizeString(value.country) || INITIAL_COMPANY_PROFILE.country,
  };
};

const sanitizeServiceConfiguration = (
  value: unknown,
  current: ServiceConfiguration
): ServiceConfiguration => {
  if (!isRecord(value)) {
    return current;
  }

  const source = isRecord(value.system_connectivity) ? value.system_connectivity : value;

  const connectorsRaw = Array.isArray(source.connectors) ? source.connectors : [];
  const connectors = connectorsRaw.filter((item): item is string => typeof item === 'string');

  const firsEnvironment =
    source.firsEnvironment === 'production'
      ? 'production'
      : source.firsEnvironment === 'sandbox'
      ? 'sandbox'
      : current.firsEnvironment;

  return {
    connectors,
    firsEnvironment,
    enableAutoRetry:
      typeof source.enableAutoRetry === 'boolean' ? source.enableAutoRetry : current.enableAutoRetry,
    enableNotifications:
      typeof source.enableNotifications === 'boolean'
        ? source.enableNotifications
        : current.enableNotifications,
    shareHybridInsights:
      typeof source.shareHybridInsights === 'boolean'
        ? source.shareHybridInsights
        : current.shareHybridInsights,
  };
};

interface RuntimeConnectionItem {
  id: string;
  name: string;
  status: string;
  lastSync?: string | null;
  error?: string | null;
  needsAttention?: boolean;
}

interface RuntimeConnectionsSnapshot {
  total: number;
  active: number;
  failing: number;
  needsAttention: number;
  items: RuntimeConnectionItem[];
}

interface RuntimeIrnSnapshot {
  totalGenerated: number;
  pending: number;
  recent: Array<{
    irn?: string | null;
    status?: string;
    createdAt?: string | null;
  }>;
}

interface RuntimeInsights {
  loginCount: number;
  connections: RuntimeConnectionsSnapshot | null;
  irnProgress: RuntimeIrnSnapshot | null;
}

const EMPTY_RUNTIME_INSIGHTS: RuntimeInsights = {
  loginCount: 0,
  connections: null,
  irnProgress: null,
};

const toNumber = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) ? value : 0;

const parseRuntimeInsights = (value: unknown): RuntimeInsights => {
  if (!isRecord(value)) {
    return EMPTY_RUNTIME_INSIGHTS;
  }

  const loginCount = toNumber(value.login_count ?? value.loginCount);

  let connections: RuntimeConnectionsSnapshot | null = null;
  if (isRecord(value.connections)) {
    const itemsRaw = Array.isArray(value.connections.items) ? value.connections.items : [];
    const items = itemsRaw
      .filter((item): item is Record<string, any> => isRecord(item))
      .map((item, index) => ({
        id:
          typeof item.id === 'string'
            ? item.id
            : typeof item.name === 'string'
            ? `${item.name}-${index}`
            : `connection-${index}`,
        name: typeof item.name === 'string' ? item.name : 'Integration',
        status: typeof item.status === 'string' ? item.status : 'unknown',
        lastSync:
          typeof item.lastSync === 'string'
            ? item.lastSync
            : typeof item.last_sync === 'string'
            ? item.last_sync
            : undefined,
        error: typeof item.error === 'string' ? item.error : undefined,
        needsAttention: Boolean(item.needsAttention ?? item.needs_attention),
      }));

    const needsAttention =
      typeof value.connections.needsAttention === 'number'
        ? value.connections.needsAttention
        : items.filter((item) => item.needsAttention).length;

    connections = {
      total: toNumber(value.connections.total ?? items.length),
      active: toNumber(value.connections.active),
      failing: toNumber(value.connections.failing),
      needsAttention,
      items,
    };
  }

  let irnProgress: RuntimeIrnSnapshot | null = null;
  const irnRaw = value.irn_progress ?? value.irnProgress;
  if (isRecord(irnRaw)) {
    const recentRaw = Array.isArray(irnRaw.recent) ? irnRaw.recent : [];
    const recent = recentRaw
      .filter((item): item is Record<string, any> => isRecord(item))
      .map((item) => ({
        irn: typeof item.irn === 'string' ? item.irn : undefined,
        status: typeof item.status === 'string' ? item.status : undefined,
        createdAt:
          typeof item.createdAt === 'string'
            ? item.createdAt
            : typeof item.created_at === 'string'
            ? item.created_at
            : undefined,
      }));

    irnProgress = {
      totalGenerated: toNumber(irnRaw.total_generated ?? irnRaw.totalGenerated),
      pending: toNumber(irnRaw.pending),
      recent,
    };
  }

  return {
    loginCount,
    connections,
    irnProgress,
  };
};

const formatRuntimeTimestamp = (value?: string | null): string => {
  if (!value) {
    return 'N/A';
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('en-NG', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(parsed);
};

const determineInitialStepId = (
  stepId: string | undefined,
  hasServiceSelectionStep: boolean
): string => {
  const fallback = hasServiceSelectionStep ? 'service-selection' : 'company-profile';
  if (!stepId) {
    return fallback;
  }

  const normalized = stepId.toLowerCase();

  if (
    [
      'service_introduction',
      'integration_choice',
      'service_selection',
      'select_service',
    ].includes(normalized)
  ) {
    return 'service-selection';
  }

  if (
    [
      'company_profile',
      'company-details',
      'company_details',
      'business_systems_setup',
      'business_verification',
    ].includes(normalized)
  ) {
    return 'company-profile';
  }

  if (
    [
      'service_configuration',
      'financial_systems_setup',
      'combined_setup',
      'firs_integration_setup',
      'banking_connected',
      'reconciliation_setup',
    ].includes(normalized)
  ) {
    return 'system-connectivity';
  }

  if (
    ['review', 'complete_integration_setup', 'onboarding_complete', 'launch_ready', 'launch'].includes(
      normalized
    )
  ) {
    return normalized === 'review' ? 'review' : 'launch';
  }

  return fallback;
};

export const UnifiedOnboardingWizard: React.FC<UnifiedOnboardingWizardProps> = ({
  initialService = null,
  defaultStep,
  onComplete,
}) => {
  const showServiceStep = !initialService;
  const [selectedService, setSelectedService] = useState<ServicePackage | null>(initialService);
  const [currentIndex, setCurrentIndex] = useState<number>(() => (showServiceStep ? 0 : 0));
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile>(INITIAL_COMPANY_PROFILE);
  const [serviceConfig, setServiceConfig] = useState<ServiceConfiguration>(INITIAL_SERVICE_CONFIGURATION);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [isPersisting, setIsPersisting] = useState(false);
  const [persistError, setPersistError] = useState<string | null>(null);
  const [isFinishing, setIsFinishing] = useState(false);
  const [isLoadingState, setIsLoadingState] = useState(true);
  const [pendingStepId, setPendingStepId] = useState<string | null>(defaultStep ?? null);
  const [stepDefinitions, setStepDefinitions] = useState<Record<string, StepDefinition>>(FALLBACK_STEP_DEFINITIONS);
  const [serverStepSequence, setServerStepSequence] = useState<string[] | null>(null);
  const hasPrefilledCompanyProfile = useRef(false);
  const [runtimeInsights, setRuntimeInsights] = useState<RuntimeInsights>(EMPTY_RUNTIME_INSIGHTS);

  const connectors = useMemo(
    () => [
      { id: 'odoo', label: 'Odoo ERP' },
      { id: 'sap', label: 'SAP S/4HANA' },
      { id: 'salesforce', label: 'Salesforce CRM' },
      { id: 'mono', label: 'Mono Banking API' },
    ],
    [],
  );

  const computeIsLocked = useCallback(
    (stepId: string) => {
      if (stepId === 'service-selection') {
        return false;
      }

      if (stepId === 'company-profile') {
        return showServiceStep && !selectedService;
      }

      if (['system-connectivity', 'review', 'launch'].includes(stepId)) {
        return !selectedService;
      }

      return false;
    },
    [selectedService, showServiceStep],
  );

  const stepRenderers: Record<string, () => React.ReactNode> = {
    'service-selection': renderServiceSelection,
    'company-profile': renderCompanyProfile,
    'system-connectivity': renderSystemConnectivity,
    review: renderReview,
    launch: renderLaunch,
  };

  const resolvedStepSequence = useMemo(() => {
    const baseSequence = serverStepSequence && serverStepSequence.length > 0
      ? serverStepSequence
      : Array.from(DEFAULT_STEP_SEQUENCE);

    if (showServiceStep) {
      return baseSequence;
    }

    return baseSequence.filter((stepId) => stepId !== 'service-selection');
  }, [serverStepSequence, showServiceStep]);

  const visibleSteps: WizardStep[] = useMemo(() => {
    return resolvedStepSequence
      .map((stepId) => {
        const renderer = stepRenderers[stepId];
        if (!renderer) {
          return null;
        }

        const definition = stepDefinitions[stepId] ?? FALLBACK_STEP_DEFINITIONS[stepId] ?? {
          title: stepId,
          description: '',
        };

        return {
          id: stepId,
          label: definition.title,
          description: definition.description,
          render: renderer,
          isLocked: computeIsLocked(stepId),
        };
      })
      .filter((step): step is WizardStep => Boolean(step));
  }, [computeIsLocked, resolvedStepSequence, stepDefinitions, stepRenderers]);

  useEffect(() => {
    if (!pendingStepId) {
      return;
    }
    const targetIndex = visibleSteps.findIndex((step) => step.id === pendingStepId);
    if (targetIndex >= 0) {
      setCurrentIndex(targetIndex);
      setPendingStepId(null);
    }
  }, [pendingStepId, visibleSteps]);

  useEffect(() => {
    if (hasPrefilledCompanyProfile.current) {
      return;
    }

    if (companyProfile.companyName.trim()) {
      hasPrefilledCompanyProfile.current = true;
      return;
    }

    const storedUser = authService.getStoredUser();
    const sharedBusinessName = CrossFormDataManager.getSharedField('business_name');
    const candidateName =
      storedUser?.organization?.name?.trim() ||
      storedUser?.business_name?.trim() ||
      (typeof sharedBusinessName === 'string' ? sharedBusinessName.trim() : '');

    if (candidateName) {
      setCompanyProfile((prev) => ({ ...prev, companyName: candidateName }));
      hasPrefilledCompanyProfile.current = true;
    }
  }, [companyProfile.companyName]);

  const currentStep = visibleSteps[currentIndex];
  const progress = Math.round(((currentIndex + 1) / visibleSteps.length) * 100);

  const canProceed = useMemo(() => {
    if (isLoadingState) return false;
    if (!currentStep) return false;
    if (currentStep.isLocked) return false;

    switch (currentStep.id) {
      case 'service-selection':
        return !!selectedService;
      case 'company-profile':
        return Boolean(companyProfile.companyName.trim());
      case 'system-connectivity':
        if (!selectedService) return false;
        if (selectedService === 'si') {
          return serviceConfig.connectors.length > 0;
        }
        return true;
      case 'launch':
        return true;
      default:
        return true;
    }
  }, [companyProfile.companyName, currentStep, selectedService, serviceConfig.connectors.length, isLoadingState]);

  useEffect(() => {
    let isCancelled = false;

    const hydrateFromBackend = async () => {
      try {
        setIsLoadingState(true);
        const remoteState = await onboardingApi.getOnboardingState();
        if (!remoteState || isCancelled) {
          return;
        }

        const metadata = isRecord(remoteState.metadata) ? remoteState.metadata : {};
        const expectedStepsRaw = Array.isArray(metadata.expected_steps)
          ? metadata.expected_steps.filter((step): step is string => typeof step === 'string')
          : null;
        if (expectedStepsRaw && expectedStepsRaw.length > 0) {
          setServerStepSequence(expectedStepsRaw);
        }

        if (isRecord(metadata.step_definitions)) {
          const sanitized: Record<string, StepDefinition> = {};
          Object.entries(metadata.step_definitions).forEach(([stepId, value]) => {
            if (!isRecord(value)) {
              return;
            }
            sanitized[stepId] = {
              title: sanitizeString(value.title) || FALLBACK_STEP_DEFINITIONS[stepId]?.title || stepId,
              description:
                sanitizeString(value.description) ||
                FALLBACK_STEP_DEFINITIONS[stepId]?.description ||
                '',
              success_criteria: sanitizeString(value.success_criteria ?? value.successCriteria),
            };
          });
          setStepDefinitions((prev) => ({
            ...prev,
            ...sanitized,
          }));
        }

        const inferredPackage =
          normalizeServicePackage(metadata.service_package ?? metadata.servicePackage ?? remoteState.metadata?.service_package) ??
          selectedService;

        if (inferredPackage) {
          setSelectedService(inferredPackage);
        }

        if (metadata.company_profile || metadata.companyProfile) {
          setCompanyProfile(sanitizeCompanyProfile(metadata.company_profile ?? metadata.companyProfile));
        }

        if (metadata.service_configuration || metadata.serviceConfiguration) {
          setServiceConfig((prev) =>
            sanitizeServiceConfiguration(metadata.service_configuration ?? metadata.serviceConfiguration, prev)
          );
        }

        if (isRecord(metadata.runtime)) {
          setRuntimeInsights(parseRuntimeInsights(metadata.runtime));
        } else {
          setRuntimeInsights(EMPTY_RUNTIME_INSIGHTS);
        }

        if (Array.isArray(remoteState.completed_steps)) {
          const normalizedSteps = remoteState.completed_steps
            .filter((step): step is string => typeof step === 'string')
            .map((step) => step);

          const withServiceSelection = inferredPackage
            ? [...normalizedSteps, 'service-selection']
            : normalizedSteps;
          const uniqueSteps = Array.from(new Set(withServiceSelection));
          setCompletedSteps(uniqueSteps);
        } else if (inferredPackage) {
          setCompletedSteps(['service-selection']);
        } else {
          setCompletedSteps([]);
        }

        setPendingStepId(
          determineInitialStepId(remoteState.current_step, showServiceStep || !inferredPackage)
        );
      } catch (error) {
        console.error('Failed to load onboarding state', error);
        // If backend unavailable, allow wizard to proceed with defaults
      } finally {
        if (!isCancelled) {
          setIsLoadingState(false);
        }
      }
    };

    hydrateFromBackend();

    return () => {
      isCancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const persistState = useCallback(
    async (stepId: string, completionList: string[], markComplete: boolean = false) => {
      if (!selectedService) {
        return;
      }

      try {
        setIsPersisting(true);
        setPersistError(null);

        await onboardingApi.updateOnboardingState({
          current_step: stepId,
          completed_steps: completionList,
          metadata: {
            service_package: selectedService,
            company_profile: companyProfile,
            service_configuration: serviceConfig,
            system_connectivity: serviceConfig,
            milestone_complete: markComplete,
          },
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to save onboarding progress';
        console.error('Onboarding persist failed:', error);
        setPersistError(message);
      } finally {
        setIsPersisting(false);
      }
    },
    [companyProfile, selectedService, serviceConfig],
  );

  const handleNext = async () => {
    if (!currentStep || currentIndex >= visibleSteps.length - 1) {
      return;
    }

    const nextStep = visibleSteps[currentIndex + 1];
    const updatedCompleted = completedSteps.includes(currentStep.id)
      ? completedSteps
      : [...completedSteps, currentStep.id];

    setCompletedSteps(updatedCompleted);

    if (selectedService) {
      await persistState(nextStep.id, updatedCompleted);
    }

    setCurrentIndex((index) => Math.min(index + 1, visibleSteps.length - 1));
  };

  const handleBack = () => {
    setCurrentIndex((index) => Math.max(index - 1, 0));
  };

  const handleFinish = async () => {
    if (!selectedService) return;

    setIsFinishing(true);
    const completionList = Array.from(new Set([...completedSteps, currentStep.id, 'launch']));

    await persistState('launch', completionList, true);
    setCompletedSteps(completionList);
    setIsFinishing(false);

    onComplete?.(selectedService);
  };

  const handleCompanyProfileChange = useCallback(
    (field: keyof CompanyProfile) => (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      setCompanyProfile((prev) => ({ ...prev, [field]: value }));

      if (field === 'companyName') {
        const trimmed = value.trim();
        if (trimmed) {
          CrossFormDataManager.saveSharedData({ business_name: trimmed });
        }
      }
    },
    [],
  );

  const toggleConnector = (connectorId: string) => {
    setServiceConfig((prev) => ({
      ...prev,
      connectors: prev.connectors.includes(connectorId)
        ? prev.connectors.filter((id) => id !== connectorId)
        : [...prev.connectors, connectorId],
    }));
  };

  function renderServiceSelection() {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {SERVICE_OPTIONS.map((option) => {
          const isActive = selectedService === option.id;
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => setSelectedService(option.id)}
              className={`relative rounded-2xl border-2 p-6 text-left transition-all ${
                isActive ? 'border-blue-500 bg-blue-50 shadow-lg' : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              {option.badge && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-green-500 px-3 py-1 text-xs font-semibold text-white">
                  {option.badge}
                </span>
              )}
              <div className="text-lg font-semibold text-gray-900">{option.title}</div>
              <p className="mt-2 text-sm text-gray-600">{option.summary}</p>
              <ul className="mt-4 space-y-1 text-sm text-gray-500">
                {option.points.map((point) => (
                  <li key={point} className="flex items-center">
                    <span className="mr-2">✓</span>
                    {point}
                  </li>
                ))}
              </ul>
            </button>
          );
        })}
      </div>
    );
  }

  function renderCompanyProfile() {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="space-y-2">
            <label className="flex items-center justify-between text-sm font-medium text-gray-700">
              <span>Company Name</span>
              <span className="text-red-500">*</span>
            </label>
            <TaxPoyntInput
              value={companyProfile.companyName}
              onChange={handleCompanyProfileChange('companyName')}
              placeholder="e.g. Horizon Payments"
            />
          </div>
          <div className="space-y-2">
            <label className="flex items-center justify-between text-sm font-medium text-gray-700">
              <span>Industry</span>
              <span className="text-xs font-normal italic text-gray-400">Optional</span>
            </label>
            <TaxPoyntInput
              value={companyProfile.industry}
              onChange={handleCompanyProfileChange('industry')}
              placeholder="e.g. Financial Services"
            />
          </div>
        </div>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="space-y-2">
            <label className="flex items-center justify-between text-sm font-medium text-gray-700">
              <span>Team Size</span>
              <span className="text-xs font-normal italic text-gray-400">Optional</span>
            </label>
            <TaxPoyntInput
              value={companyProfile.teamSize}
              onChange={handleCompanyProfileChange('teamSize')}
              placeholder="e.g. 25"
            />
          </div>
          <div className="space-y-2">
            <label className="flex items-center justify-between text-sm font-medium text-gray-700">
              <span>Country</span>
              <span className="text-red-500">*</span>
            </label>
            <TaxPoyntInput
              value={companyProfile.country}
              onChange={handleCompanyProfileChange('country')}
              placeholder="Nigeria"
            />
          </div>
        </div>
        <p className="text-sm text-gray-500">
          We use this information to preconfigure regional settings, currency defaults, and recommended
          integrations. You can update these later from your organisation settings.
        </p>
      </div>
    );
  }

  function renderSystemConnectivity() {
    if (!selectedService) {
      return <p className="text-gray-500">Select a service above to continue.</p>;
    }

    if (selectedService === 'si' || selectedService === 'hybrid') {
      return (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Choose the systems you plan to connect</h3>
            <p className="text-sm text-gray-600">We will prepare starter playbooks for each connector.</p>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
              {connectors.map((connector) => {
                const isChecked = serviceConfig.connectors.includes(connector.id);
                return (
                  <label
                    key={connector.id}
                    className={`flex cursor-pointer items-center justify-between rounded-xl border-2 px-4 py-3 transition ${
                      isChecked ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <span className="text-sm font-medium text-gray-900">{connector.label}</span>
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleConnector(connector.id)}
                      className="h-4 w-4"
                    />
                  </label>
                );
              })}
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-4">
            <h4 className="font-semibold text-gray-900">Validation preferences</h4>
            <div className="mt-3 space-y-2 text-sm text-gray-600">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={serviceConfig.enableAutoRetry}
                  onChange={(event) =>
                    setServiceConfig((prev) => ({ ...prev, enableAutoRetry: event.target.checked }))
                  }
                />
                <span>Auto-retry failed validations with exponential backoff</span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={serviceConfig.enableNotifications}
                  onChange={(event) =>
                    setServiceConfig((prev) => ({ ...prev, enableNotifications: event.target.checked }))
                  }
                />
                <span>Send email notifications for critical incidents</span>
              </label>
            </div>
          </div>

          {selectedService === 'hybrid' && (
            <label className="flex items-center space-x-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={serviceConfig.shareHybridInsights}
                onChange={(event) =>
                  setServiceConfig((prev) => ({ ...prev, shareHybridInsights: event.target.checked }))
                }
              />
              <span>Share validation and transmission summaries across SI and APP workspaces.</span>
            </label>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="text-lg font-semibold text-gray-900">Transmission environment</h3>
          <p className="text-sm text-gray-600">Pick where your first batches should run.</p>
          <div className="mt-4 flex gap-4">
            {(['sandbox', 'production'] as const).map((environment) => (
              <button
                key={environment}
                type="button"
                onClick={() => setServiceConfig((prev) => ({ ...prev, firsEnvironment: environment }))}
                className={`flex-1 rounded-xl border-2 px-4 py-3 text-left transition ${
                  serviceConfig.firsEnvironment === environment
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-sm font-semibold text-gray-900 capitalize">{environment}</div>
                <p className="mt-1 text-xs text-gray-600">
                  {environment === 'sandbox'
                    ? 'Safe for testing. Fully isolated with sample data.'
                    : 'Goes straight to FIRS production once credentials are confirmed.'}
                </p>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="text-lg font-semibold text-gray-900">Operational preferences</h3>
          <div className="mt-3 space-y-2 text-sm text-gray-600">
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={serviceConfig.enableAutoRetry}
                onChange={(event) =>
                  setServiceConfig((prev) => ({ ...prev, enableAutoRetry: event.target.checked }))
                }
              />
              <span>Enable automatic retransmission when FIRS responds with transient errors.</span>
            </label>
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={serviceConfig.enableNotifications}
                onChange={(event) =>
                  setServiceConfig((prev) => ({ ...prev, enableNotifications: event.target.checked }))
                }
              />
              <span>Notify finance teams via email when batches complete or fail.</span>
            </label>
          </div>
        </div>
      </div>
    );
  }

  function renderReview() {
    if (!selectedService) {
      return <p className="text-gray-600">Service selection is required before review.</p>;
    }

    const summaryItems = [
      { label: 'Service Package', value: serviceTitle(selectedService) },
      { label: 'Company', value: companyProfile.companyName || 'Not provided' },
      { label: 'Country', value: companyProfile.country || 'Not provided' },
      {
        label: 'Integrations',
        value:
          selectedService === 'app'
            ? 'Direct FIRS transmission'
            : serviceConfig.connectors.length > 0
            ? serviceConfig.connectors.join(', ')
            : 'No connectors selected yet',
      },
      {
        label: 'Environment',
        value: selectedService === 'si' ? 'Integration workspace' : serviceConfig.firsEnvironment,
      },
    ];

    if (runtimeInsights.loginCount > 0) {
      summaryItems.push({
        label: 'Recent sign-ins',
        value: runtimeInsights.loginCount.toLocaleString(),
      });
    }

    if (runtimeInsights.connections) {
      summaryItems.push({
        label: 'Connections',
        value: `${runtimeInsights.connections.active}/${runtimeInsights.connections.total} active (${runtimeInsights.connections.needsAttention} attention)`,
      });
    }

    if (runtimeInsights.irnProgress) {
      summaryItems.push({
        label: 'IRN progress',
        value: `${runtimeInsights.irnProgress.totalGenerated} generated · ${runtimeInsights.irnProgress.pending} pending`,
      });
    }

    return (
      <div className="space-y-4">
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900">Launch summary</h3>
          <ul className="mt-4 space-y-3">
            {summaryItems.map((item) => (
              <li key={item.label} className="flex items-start justify-between text-sm text-gray-700">
                <span className="font-medium text-gray-900">{item.label}</span>
                <span className="ml-4 max-w-sm text-right text-gray-600">{item.value}</span>
              </li>
            ))}
          </ul>
        </div>
        <p className="text-sm text-gray-500">
          Completing onboarding will unlock the full dashboard experience. You can revisit these settings from
          the workspace preferences panel at any time.
        </p>
      </div>
    );
  }

  function renderLaunch() {
    return (
      <div className="space-y-4">
        <div className="rounded-2xl border border-blue-200 bg-blue-50 p-6 text-sm text-blue-900">
          <h3 className="text-lg font-semibold text-blue-900">Ready for launch</h3>
          <p className="mt-2">
            We will apply your configuration, enable workspace analytics, and unlock the SI dashboard. You can revisit these
            settings from the workspace preferences panel after launch.
          </p>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h4 className="text-sm font-semibold text-gray-900">Launch checklist</h4>
          <ul className="mt-3 space-y-2 text-sm text-gray-600">
            <li className="flex items-start">
              <span className="mr-2 text-green-500">✓</span>
              Service package and company profile confirmed
            </li>
            <li className="flex items-start">
              <span className="mr-2 text-green-500">✓</span>
              Connectivity preferences saved for {selectedService ? serviceTitle(selectedService) : 'your workspace'}
            </li>
            <li className="flex items-start">
              <span className="mr-2 text-green-500">✓</span>
              Review complete and launch summary archived
            </li>
          </ul>
        </div>
        <p className="text-xs text-gray-500">
          Tip: After launch you can invite collaborators from the workspace menu and manage integrations from the connectivity panel.
        </p>
      </div>
    );
  }

  const runtimeConnectionItems = runtimeInsights.connections?.items ?? [];
  const runtimeIrnItems = runtimeInsights.irnProgress?.recent ?? [];
  const runtimeHasSignals =
    runtimeInsights.loginCount > 0 ||
    Boolean(runtimeInsights.connections) ||
    Boolean(runtimeInsights.irnProgress);

  return (
    <div className="space-y-6">
      <header className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Getting Started with TaxPoynt</h1>
            <p className="text-sm text-gray-600">
              Follow the milestones to configure your workspace. Progress is saved automatically.
            </p>
          </div>
          <span className="rounded-full bg-blue-50 px-4 py-2 text-sm font-medium text-blue-600">
            {progress}% complete
          </span>
        </div>
        <div className="h-2 w-full rounded-full bg-gray-200">
          <div
            className="h-2 rounded-full bg-blue-500 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </header>

      {runtimeHasSignals && (
        <section className="rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-blue-900">Live workspace signals</h2>
              <p className="text-sm text-slate-600">
                Real-time insight into logins, connections, and IRN activity tied to your onboarding progress.
              </p>
            </div>
            <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-600">
              {runtimeInsights.loginCount.toLocaleString()} sign-ins
            </span>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-3 text-sm md:grid-cols-3">
            <div className="rounded-lg border border-blue-100 bg-blue-50 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">Connections</p>
              <p className="mt-1 text-lg font-semibold text-blue-900">
                {runtimeInsights.connections
                  ? `${runtimeInsights.connections.active}/${runtimeInsights.connections.total}`
                  : '0/0'}
              </p>
              <p className="text-xs text-blue-600">
                {runtimeInsights.connections
                  ? `${runtimeInsights.connections.needsAttention} need attention`
                  : 'Connect your first system to unlock metrics'}
              </p>
            </div>
            <div className="rounded-lg border border-blue-100 bg-blue-50 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">IRN progress</p>
              <p className="mt-1 text-lg font-semibold text-blue-900">
                {runtimeIrnProgress
                  ? `${runtimeIrnProgress.totalGenerated} generated`
                  : '0 generated'}
              </p>
              <p className="text-xs text-blue-600">
                Pending: {runtimeIrnProgress ? runtimeIrnProgress.pending : 0}
              </p>
            </div>
            <div className="rounded-lg border border-blue-100 bg-blue-50 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">Next milestone</p>
              <p className="mt-1 text-lg font-semibold text-blue-900">
                {currentStep?.label ?? 'Awaiting kickoff'}
              </p>
              <p className="text-xs text-blue-600">{progress}% complete</p>
            </div>
          </div>

          {runtimeConnectionItems.length > 0 && (
            <div className="mt-4 rounded-lg border border-blue-100 bg-white px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">Recent connections</p>
              <ul className="mt-2 space-y-2 text-xs text-blue-700">
                {runtimeConnectionItems.slice(0, 3).map((item) => (
                  <li key={item.id} className="flex items-center justify-between">
                    <span className="font-semibold text-blue-800">{item.name}</span>
                    <span>{formatRuntimeTimestamp(item.lastSync)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {runtimeIrnItems.length > 0 && (
            <div className="mt-4 rounded-lg border border-blue-100 bg-white px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">Latest IRNs</p>
              <ul className="mt-2 space-y-2 text-xs text-blue-700">
                {runtimeIrnItems.slice(0, 3).map((entry, index) => (
                  <li key={entry.irn ?? `irn-${index}`} className="flex items-center justify-between">
                    <span className="font-semibold text-blue-800">
                      {entry.irn ? `IRN ${entry.irn}` : 'IRN submission'}
                    </span>
                    <span>{formatRuntimeTimestamp(entry.createdAt)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      <nav className="flex flex-wrap gap-3">
        {visibleSteps.map((step, index) => {
          const isActive = index === currentIndex;
          const isComplete = completedSteps.includes(step.id);
          return (
            <div
              key={step.id}
              className={`flex items-center space-x-2 rounded-full px-4 py-2 text-sm ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : isComplete
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              <span className="font-semibold">{String(index + 1).padStart(2, '0')}</span>
              <span>{step.label}</span>
            </div>
          );
        })}
      </nav>

      <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-gray-900">{currentStep?.label}</h2>
          <p className="text-sm text-gray-600">{currentStep?.description}</p>
        </div>
        {persistError && (
          <p className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
            {persistError}
          </p>
        )}
        <div className="space-y-4">{currentStep?.render()}</div>
      </section>

      <footer className="flex items-center justify-between">
        <TaxPoyntButton
          variant="outline"
          onClick={handleBack}
          disabled={currentIndex === 0 || isPersisting || isLoadingState}
        >
          Back
        </TaxPoyntButton>
        <div className="flex items-center space-x-3">
          {currentStep?.id !== 'launch' ? (
            <TaxPoyntButton
              variant="primary"
              onClick={handleNext}
              disabled={!canProceed || isPersisting || isLoadingState}
            >
              Continue
            </TaxPoyntButton>
          ) : (
            <TaxPoyntButton
              variant="primary"
              onClick={handleFinish}
              disabled={isFinishing || !selectedService || isLoadingState}
            >
              {isFinishing ? 'Completing…' : 'Launch Dashboard'}
            </TaxPoyntButton>
          )}
        </div>
      </footer>
    </div>
  );
};

function serviceTitle(service: ServicePackage): string {
  switch (service) {
    case 'si':
      return 'System Integrator';
    case 'app':
      return 'Access Point Provider';
    case 'hybrid':
      return 'Hybrid Suite';
    default:
      return service.toUpperCase();
  }
}

export default UnifiedOnboardingWizard;
