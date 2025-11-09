'use client';

/**
 * Unified Onboarding Wizard
 * =========================
 * Streamlines onboarding for SI, APP, and Hybrid users through a single
 * milestone-based experience. The wizard keeps state locally while
 * synchronising progress with the onboarding API.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ShieldCheckIcon } from '@heroicons/react/24/solid';
import { TaxPoyntButton, TaxPoyntInput } from '../../design_system';
import { onboardingApi, type CompanyProfilePayload } from '../services/onboardingApi';
import erpIntegrationApi from '../services/erpIntegrationApi';
import { authService } from '../services/auth';
import siBankingApi from '../services/siBankingApi';
import { CrossFormDataManager } from '../utils/formPersistence';
import {
  MonoConsentIntegration,
  type MonoConsentState,
  type MonoLinkRequest,
} from '../../si_interface/components/financial_systems/banking_integration/MonoConsentIntegration';

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

interface CompanyProfileDetails {
  source?: string;
  verifiedAt?: string;
  status?: string;
}

interface ServiceConfiguration {
  connectors: string[];
  firsEnvironment: 'sandbox' | 'production';
  enableAutoRetry: boolean;
  enableNotifications: boolean;
  shareHybridInsights: boolean;
}

type ConnectivityTestStatus = {
  state: 'idle' | 'loading' | 'success' | 'error';
  message?: string;
  fetchedCount?: number;
  sampleInvoice?: string;
};

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

const SERVICE_SUMMARY_COPY: Record<ServicePackage, string> = {
  si: 'Connect ERPs and banking data for your clients with full validation tooling.',
  app: 'Transmit compliant invoices directly to FIRS with built-in monitoring.',
  hybrid: 'Blend SI integrations with APP controls for shared analytics.',
};

const DEMO_ODOO_CONFIG = {
  url: process.env.NEXT_PUBLIC_ODOO_DEMO_URL ?? 'https://odoo-demo.taxpoynt.com',
  database: process.env.NEXT_PUBLIC_ODOO_DEMO_DB ?? 'taxpoynt_demo',
  username: process.env.NEXT_PUBLIC_ODOO_DEMO_USER ?? 'demo@taxpoynt.com',
  apiKey: process.env.NEXT_PUBLIC_ODOO_DEMO_API_KEY ?? 'demo-api-key',
  password: process.env.NEXT_PUBLIC_ODOO_DEMO_PASSWORD ?? '',
};

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

const sanitizeOptionalString = (value: unknown): string | undefined => {
  const sanitized = sanitizeString(value);
  return sanitized ? sanitized : undefined;
};

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

const sanitizeCompanyProfileDetails = (value: unknown): CompanyProfileDetails | null => {
  if (!isRecord(value)) {
    return null;
  }

  const details: CompanyProfileDetails = {};
  const source = sanitizeOptionalString(value.source ?? value.provider);
  if (source) {
    details.source = source;
  }

  const verifiedAt = sanitizeOptionalString(value.verified_at ?? value.verifiedAt);
  if (verifiedAt) {
    details.verifiedAt = verifiedAt;
  }

  const status = sanitizeOptionalString(value.status);
  if (status) {
    details.status = status;
  }

  return Object.keys(details).length > 0 ? details : null;
};

const buildCompanyProfilePayload = (profile: CompanyProfile): CompanyProfilePayload => ({
  company_name: profile.companyName.trim(),
  industry: profile.industry.trim() || undefined,
  company_size: profile.teamSize.trim() || undefined,
  current_step: 'company-profile',
});

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

type BankingConnectionStatus =
  | 'not_started'
  | 'link_created'
  | 'awaiting_consent'
  | 'connected'
  | 'error'
  | 'skipped';

interface BankingConnectionState {
  status: BankingConnectionStatus;
  bankName?: string;
  lastMessage?: string;
  lastUpdated?: string;
}

const sanitizeBankingConnection = (value: unknown): BankingConnectionState => {
  if (!isRecord(value)) {
    return { status: 'not_started' };
  }
  const status = typeof value.status === 'string' ? (value.status as BankingConnectionStatus) : 'not_started';
  return {
    status,
    bankName: sanitizeString(value.bankName ?? value.bank_name),
    lastMessage: sanitizeString(value.lastMessage ?? value.last_message),
    lastUpdated: sanitizeOptionalString(value.lastUpdated ?? value.last_updated),
  };
};

type ERPConnectionStatus = 'not_connected' | 'connecting' | 'connected' | 'error' | 'demo';

interface ERPConnectionState {
  status: ERPConnectionStatus;
  connectionName?: string;
  lastMessage?: string;
  lastTestAt?: string;
  sampleInvoice?: Record<string, unknown> | null;
}

const sanitizeErpConnection = (value: unknown): ERPConnectionState => {
  if (!isRecord(value)) {
    return { status: 'not_connected', sampleInvoice: null };
  }
  const status = typeof value.status === 'string' ? (value.status as ERPConnectionStatus) : 'not_connected';
  const sampleInvoice = isRecord(value.sampleInvoice ?? value.sample_invoice)
    ? ((value.sampleInvoice ?? value.sample_invoice) as Record<string, unknown>)
    : null;
  return {
    status,
    connectionName: sanitizeString(value.connectionName ?? value.connection_name),
    lastMessage: sanitizeString(value.lastMessage ?? value.last_message),
    lastTestAt: sanitizeOptionalString(value.lastTestAt ?? value.last_test_at),
    sampleInvoice,
  };
};

const extractInvoiceLabel = (invoice: Record<string, unknown> | undefined): string | undefined => {
  if (!invoice) {
    return undefined;
  }
  const candidateKeys = ['invoice_number', 'name', 'BillingDocument', 'DocNumber'];
  for (const key of candidateKeys) {
    const raw = invoice[key];
    if (typeof raw === 'string' && raw.trim()) {
      return raw;
    }
  }
  return undefined;
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
      .filter((item): item is Record<string, unknown> => isRecord(item))
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
      .filter((item): item is Record<string, unknown> => isRecord(item))
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
  const storedUserRef = useRef(authService.getStoredUser());
  const storedUser = storedUserRef.current;
  const storedOrganizationId = storedUser?.organization?.id;
  const [showServiceSelection, setShowServiceSelection] = useState<boolean>(() => !initialService);
  const [selectedService, setSelectedService] = useState<ServicePackage | null>(initialService);
  const [currentIndex, setCurrentIndex] = useState<number>(() => (showServiceSelection ? 0 : 0));
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile>(INITIAL_COMPANY_PROFILE);
  const [companyProfileDetails, setCompanyProfileDetails] = useState<CompanyProfileDetails | null>(null);
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
  const [showCompanyDetails, setShowCompanyDetails] = useState(false);
  const [expandedConnectivityLane, setExpandedConnectivityLane] = useState<'mono' | 'odoo' | null>('mono');
  const [monoConsentState, setMonoConsentState] = useState<MonoConsentState | null>(null);
  const [monoWidgetUrl, setMonoWidgetUrl] = useState<string | null>(null);
  const [monoStatusMessage, setMonoStatusMessage] = useState<string | null>(null);
  const [erpInvoiceIdsInput, setErpInvoiceIdsInput] = useState('INV/2024/0001,INV/2024/0002');
  const [erpTestStatus, setErpTestStatus] = useState<ConnectivityTestStatus>({ state: 'idle' });
  const [bankingConnectionState, setBankingConnectionState] = useState<BankingConnectionState>({
    status: 'not_started',
  });
  const [bankOwnerName, setBankOwnerName] = useState<string>(() => {
    if (!storedUser) return '';
    const candidate = `${storedUser.first_name ?? ''} ${storedUser.last_name ?? ''}`.trim();
    return candidate || storedUser.email || '';
  });
  const [bankOwnerEmail, setBankOwnerEmail] = useState<string>(() => storedUser?.email ?? '');
  const [bankCallbackUrl, setBankCallbackUrl] = useState<string>('');
  const [monoLinkError, setMonoLinkError] = useState<string | null>(null);
  const [erpConnectionState, setErpConnectionState] = useState<ERPConnectionState>({
    status: 'not_connected',
    sampleInvoice: null,
  });
  const [odooUrl, setOdooUrl] = useState('');
  const [odooDatabase, setOdooDatabase] = useState('');
  const [odooUsername, setOdooUsername] = useState('');
  const [odooApiKey, setOdooApiKey] = useState('');
  const [odooPassword, setOdooPassword] = useState('');
  const [odooUseDemo, setOdooUseDemo] = useState(false);
  const [odooError, setOdooError] = useState<string | null>(null);
  const [erpPreviewInvoice, setErpPreviewInvoice] = useState<Record<string, unknown> | null>(null);
  const [erpPreviewVisible, setErpPreviewVisible] = useState(false);

  const connectors = useMemo(
    () => [
      { id: 'odoo', label: 'Odoo ERP' },
      { id: 'sap', label: 'SAP S/4HANA' },
      { id: 'salesforce', label: 'Salesforce CRM' },
      { id: 'mono', label: 'Mono Banking API' },
    ],
    [],
  );
  const displayedService: ServicePackage = selectedService ?? 'si';
  const serviceSummaryText = SERVICE_SUMMARY_COPY[displayedService];
  const bankingStatusDescriptor = useMemo(() => {
    switch (bankingConnectionState.status) {
      case 'connected':
        return {
          label: bankingConnectionState.bankName
            ? `Connected to ${bankingConnectionState.bankName}`
            : 'Connected via Mono',
          className: 'bg-green-100 text-green-700',
        };
      case 'link_created':
        return { label: 'Link generated', className: 'bg-blue-100 text-blue-700' };
      case 'awaiting_consent':
        return { label: 'Waiting for bank confirmation', className: 'bg-yellow-100 text-yellow-700' };
      case 'error':
        return { label: 'Action required', className: 'bg-red-100 text-red-700' };
      case 'skipped':
        return { label: 'Skipped', className: 'bg-gray-200 text-gray-600' };
      default:
        return { label: 'Not connected', className: 'bg-gray-100 text-gray-600' };
    }
  }, [bankingConnectionState]);
  const buildMetadataPayload = useCallback(
    (options?: {
      bankingConnection?: BankingConnectionState;
      erpConnection?: ERPConnectionState;
    }) => ({
      service_package: selectedService,
      company_profile: companyProfile,
      service_configuration: serviceConfig,
      system_connectivity: serviceConfig,
      banking_connections: {
        mono: options?.bankingConnection ?? bankingConnectionState,
      },
      erp_connections: {
        odoo: options?.erpConnection ?? erpConnectionState,
      },
    }),
    [selectedService, companyProfile, serviceConfig, bankingConnectionState, erpConnectionState],
  );

  const computeIsLocked = useCallback(
    (stepId: string) => {
      if (stepId === 'service-selection') {
        return false;
      }

      if (stepId === 'company-profile') {
        return showServiceSelection && !selectedService;
      }

      if (['system-connectivity', 'review', 'launch'].includes(stepId)) {
        return !selectedService;
      }

      return false;
    },
    [selectedService, showServiceSelection],
  );

  const resolvedStepSequence = useMemo(() => {
    const baseSequence = serverStepSequence && serverStepSequence.length > 0
      ? serverStepSequence
      : Array.from(DEFAULT_STEP_SEQUENCE);

    if (showServiceSelection) {
      return baseSequence;
    }

    return baseSequence.filter((stepId) => stepId !== 'service-selection');
  }, [serverStepSequence, showServiceSelection]);

  const visibleSteps: WizardStep[] = resolvedStepSequence
    .map((stepId) => {
      const renderer = (() => {
        switch (stepId) {
          case 'service-selection':
            return renderServiceSelection;
          case 'company-profile':
            return renderCompanyProfile;
          case 'system-connectivity':
            return renderSystemConnectivity;
          case 'review':
            return renderReview;
          case 'launch':
            return renderLaunch;
          default:
            return undefined;
        }
      })();
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
    if (!['link_created', 'awaiting_consent'].includes(bankingConnectionState.status)) {
      return;
    }
    let isCancelled = false;
    const intervalId = setInterval(async () => {
      try {
        const refreshedState = await onboardingApi.getOnboardingState();
        if (!refreshedState || isCancelled) {
          return;
        }
        const metadata = isRecord(refreshedState.metadata) ? refreshedState.metadata : {};
        const bankingConnectionsRaw = isRecord(metadata.banking_connections) ? metadata.banking_connections : null;
        const monoConnectionRaw = bankingConnectionsRaw?.mono ?? metadata.mono_connection;
        if (monoConnectionRaw) {
          const sanitized = sanitizeBankingConnection(monoConnectionRaw);
          setBankingConnectionState((prev) => {
            if (
              prev.status === sanitized.status &&
              prev.bankName === sanitized.bankName &&
              prev.lastMessage === sanitized.lastMessage &&
              prev.lastUpdated === sanitized.lastUpdated
            ) {
              return prev;
            }
            return sanitized;
          });
        }
      } catch (error) {
        console.warn('Banking status poll failed:', error);
      }
    }, 10000);
    return () => {
      isCancelled = true;
      clearInterval(intervalId);
    };
  }, [bankingConnectionState.status]);

  useEffect(() => {
    if (bankingConnectionState.lastMessage) {
      setMonoStatusMessage(bankingConnectionState.lastMessage);
      return;
    }
    switch (bankingConnectionState.status) {
      case 'connected':
        setMonoStatusMessage(
          bankingConnectionState.bankName
            ? `Connected to ${bankingConnectionState.bankName} via Mono.`
            : 'Mono connection confirmed.',
        );
        break;
      case 'link_created':
        setMonoStatusMessage('Secure Mono widget generated. Complete the consent to finish setup.');
        break;
      case 'awaiting_consent':
        setMonoStatusMessage('Waiting for your bank to confirm consent via Mono.');
        break;
      case 'skipped':
        setMonoStatusMessage('Bank feeds skipped. Connect Mono later from the dashboard.');
        break;
      default:
        break;
    }
  }, [bankingConnectionState]);

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

  useEffect(() => {
    if (odooUseDemo) {
      setOdooUrl(DEMO_ODOO_CONFIG.url);
      setOdooDatabase(DEMO_ODOO_CONFIG.database);
      setOdooUsername(DEMO_ODOO_CONFIG.username);
      setOdooApiKey(DEMO_ODOO_CONFIG.apiKey);
      setOdooPassword(DEMO_ODOO_CONFIG.password);
    }
  }, [odooUseDemo]);

  const persistBankingState = useCallback(
    async (nextState: BankingConnectionState) => {
      setBankingConnectionState(nextState);
      if (!selectedService) {
        return;
      }
      try {
        await onboardingApi.updateOnboardingState({
          current_step: currentStep?.id ?? 'system-connectivity',
          completed_steps: completedSteps,
          metadata: buildMetadataPayload({ bankingConnection: nextState }),
        });
      } catch (error) {
        console.error('Failed to persist banking connection state', error);
      }
    },
    [selectedService, currentStep?.id, completedSteps, buildMetadataPayload],
  );

  const persistErpState = useCallback(
    async (nextState: ERPConnectionState) => {
      setErpConnectionState(nextState);
      if (!selectedService) {
        return;
      }
      try {
        await onboardingApi.updateOnboardingState({
          current_step: currentStep?.id ?? 'system-connectivity',
          completed_steps: completedSteps,
          metadata: buildMetadataPayload({ erpConnection: nextState }),
        });
      } catch (error) {
        console.error('Failed to persist ERP connection state', error);
      }
    },
    [selectedService, currentStep?.id, completedSteps, buildMetadataPayload],
  );

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
          if (showServiceSelection && !initialService) {
            setShowServiceSelection(false);
          }
        }

        if (metadata.company_profile || metadata.companyProfile) {
          setCompanyProfile(sanitizeCompanyProfile(metadata.company_profile ?? metadata.companyProfile));
        }

        const profileDetailsRaw = metadata.company_profile_details ?? metadata.companyProfileDetails;
        setCompanyProfileDetails(sanitizeCompanyProfileDetails(profileDetailsRaw));

        const bankingConnectionsRaw = isRecord(metadata.banking_connections) ? metadata.banking_connections : null;
        const monoConnectionRaw = bankingConnectionsRaw?.mono ?? metadata.mono_connection;
        setBankingConnectionState(sanitizeBankingConnection(monoConnectionRaw));

        const erpConnectionsRaw = isRecord(metadata.erp_connections) ? metadata.erp_connections : null;
        const odooConnectionRaw = erpConnectionsRaw?.odoo ?? metadata.odoo_connection;
        setErpConnectionState(sanitizeErpConnection(odooConnectionRaw));
        setErpPreviewInvoice(
          isRecord(odooConnectionRaw?.sampleInvoice ?? odooConnectionRaw?.sample_invoice)
            ? ((odooConnectionRaw?.sampleInvoice ?? odooConnectionRaw?.sample_invoice) as Record<string, unknown>)
            : null,
        );

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
          determineInitialStepId(remoteState.current_step, showServiceSelection || !inferredPackage)
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

  const syncCompanyProfile = useCallback(async (): Promise<CompanyProfile> => {
    const payload = buildCompanyProfilePayload(companyProfile);
    const state = await onboardingApi.saveCompanyProfile(payload);

    let resolvedProfile: CompanyProfile = {
      ...companyProfile,
      companyName: payload.company_name,
      industry: payload.industry ?? '',
      teamSize: payload.company_size ?? '',
    };

    if (state && isRecord(state.metadata)) {
      const profileRaw = state.metadata.company_profile ?? state.metadata.companyProfile;
      if (profileRaw) {
        resolvedProfile = sanitizeCompanyProfile(profileRaw);
      }

      const detailsRaw = state.metadata.company_profile_details ?? state.metadata.companyProfileDetails;
      setCompanyProfileDetails(sanitizeCompanyProfileDetails(detailsRaw));
    }

    setCompanyProfile(resolvedProfile);
    return resolvedProfile;
  }, [companyProfile]);

  const persistState = useCallback(
    async (
      stepId: string,
      completionList: string[],
      markComplete: boolean = false,
      options?: { preSync?: () => Promise<CompanyProfile> },
    ) => {
      if (!selectedService) {
        return;
      }

      try {
        setIsPersisting(true);
        setPersistError(null);

        let profileForMetadata = companyProfile;
        if (options?.preSync) {
          profileForMetadata = await options.preSync();
        }

        await onboardingApi.updateOnboardingState({
          current_step: stepId,
          completed_steps: completionList,
          metadata: {
            ...buildMetadataPayload(),
            company_profile: profileForMetadata,
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
    [buildMetadataPayload, companyProfile, selectedService],
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

    const preSync = currentStep.id === 'company-profile' ? syncCompanyProfile : undefined;

    if (selectedService) {
      await persistState(nextStep.id, updatedCompleted, false, preSync ? { preSync } : undefined);
    }

    if (currentStep.id === 'service-selection') {
      setShowServiceSelection(false);
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

  const handleChangeService = () => {
    setShowServiceSelection(true);
    setPendingStepId('service-selection');
    setCurrentIndex(0);
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

  const handleMonoConsentUpdate = useCallback((state: MonoConsentState) => {
    setMonoConsentState(state);
    if (state.unified) {
      setServiceConfig((prev) =>
        prev.connectors.includes('mono')
          ? prev
          : { ...prev, connectors: [...prev.connectors, 'mono'] },
      );
      setMonoLinkError(null);
      setMonoStatusMessage('All required Mono consents granted. Generate a secure link to finish banking setup.');
    } else {
      setMonoStatusMessage('Grant the required banking consents to unlock Mono-powered feeds.');
    }
  }, []);

  const handleMonoWidgetReady = useCallback(
    (url: string) => {
      setMonoWidgetUrl(url);
      setMonoStatusMessage('Secure Mono widget generated. Complete the consent to finish setup.');
    },
    [],
  );

  const handleMonoConsentComplete = useCallback(() => {
    setMonoStatusMessage('Waiting for your bank to confirm consent via Mono.');
    void persistBankingState({
      status: 'awaiting_consent',
      lastMessage: 'Waiting for bank confirmation',
      lastUpdated: new Date().toISOString(),
    });
  }, [persistBankingState]);

  const handleMonoGenerateLink = useCallback(
    async ({ grantedScopes, grantedConsentIds }: MonoLinkRequest) => {
      const trimmedName = bankOwnerName.trim();
      const trimmedEmail = bankOwnerEmail.trim();
      if (!trimmedName || !trimmedEmail) {
        const error = 'Provide the account holder name and email before generating the link.';
        setMonoLinkError(error);
        throw new Error(error);
      }
      setMonoLinkError(null);
      const redirectUrl =
        typeof window !== 'undefined'
          ? `${window.location.origin}/onboarding/si/banking-callback`
          : '/onboarding/si/banking-callback';
      try {
        const monoUrl = await siBankingApi.createMonoLink({
          customer: {
            name: trimmedName,
            email: trimmedEmail,
          },
          scope: grantedScopes.join(' '),
          redirect_url: redirectUrl,
          callback_url: bankCallbackUrl.trim() || undefined,
          meta: {
            ref: `taxpoynt_consent_${Date.now()}`,
            consents_granted: grantedConsentIds,
            consent_timestamp: new Date().toISOString(),
          },
        });
        await persistBankingState({
          status: 'link_created',
          lastMessage: 'Secure Mono link generated. Launch the widget to continue.',
          lastUpdated: new Date().toISOString(),
        });
        return monoUrl;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to generate Mono link';
        setMonoLinkError(message);
        await persistBankingState({
          status: 'error',
          lastMessage: message,
          lastUpdated: new Date().toISOString(),
        });
        throw error;
      }
    },
    [bankOwnerName, bankOwnerEmail, bankCallbackUrl, persistBankingState],
  );

  const handleSkipBanking = useCallback(() => {
    setMonoStatusMessage('Bank feeds skipped. You can connect Mono later from the dashboard.');
    setExpandedConnectivityLane('odoo');
    void persistBankingState({
      status: 'skipped',
      lastMessage: 'User skipped Mono connection during onboarding',
      lastUpdated: new Date().toISOString(),
    });
  }, [persistBankingState]);

  const handleOdooExtraction = useCallback(
    async (mode: 'specific' | 'batch') => {
      let invoiceIds: string[] = [];
      if (mode === 'specific') {
        invoiceIds = erpInvoiceIdsInput
          .split(',')
          .map((value) => value.trim())
          .filter(Boolean);
        if (invoiceIds.length === 0) {
          setErpTestStatus({
            state: 'error',
            message: 'Provide at least one invoice ID before running the test fetch.',
          });
          return;
        }
      }

      const loadingMessage =
        mode === 'specific'
          ? 'Requesting targeted invoice pull via erp_data_extractor...'
          : 'Requesting Odoo sandbox batch via erp_data_extractor...';
      setErpTestStatus({ state: 'loading', message: loadingMessage });

      try {
        const response =
          mode === 'specific'
            ? await erpIntegrationApi.testFetchOdooInvoices(invoiceIds)
            : await erpIntegrationApi.testFetchOdooInvoiceBatch({ batchSize: 5 });

        const fetched =
          response?.data?.fetched_count ??
          (Array.isArray(response?.data?.invoices) ? response.data.invoices.length : 0);
        const firstInvoice =
          Array.isArray(response?.data?.invoices) && response.data.invoices.length > 0
            ? (response.data.invoices[0] as Record<string, unknown>)
            : undefined;
        const sampleInvoice = extractInvoiceLabel(firstInvoice);
        setErpPreviewInvoice(firstInvoice ?? null);

        setErpTestStatus({
          state: 'success',
          message:
            fetched && fetched > 0
              ? `Pulled ${fetched} invoice${fetched === 1 ? '' : 's'} from Odoo via erp_data_extractor.`
              : 'Request completed but no invoices were returned.',
          fetchedCount: fetched,
          sampleInvoice,
        });

        setServiceConfig((prev) =>
          prev.connectors.includes('odoo')
            ? prev
            : { ...prev, connectors: [...prev.connectors, 'odoo'] },
        );
        await persistErpState({
          ...erpConnectionState,
          status: odooUseDemo ? 'demo' : 'connected',
          lastMessage:
            fetched && fetched > 0
              ? `Fetched ${fetched} invoice${fetched === 1 ? '' : 's'}`
              : 'No invoices returned',
          lastTestAt: new Date().toISOString(),
          sampleInvoice: firstInvoice ?? null,
        });
      } catch (error) {
        const message =
          error instanceof Error ? error.message : 'Failed to reach ERP data extractor.';
        setErpTestStatus({ state: 'error', message });
        setOdooError(message);
        await persistErpState({
          ...erpConnectionState,
          status: 'error',
          lastMessage: message,
        });
      }
    },
    [erpConnectionState, erpInvoiceIdsInput, odooUseDemo, persistErpState],
  );

  const handleOdooConnectionSubmit = useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();
      setOdooError(null);
      if (!odooUrl.trim()) {
        setOdooError('Provide your Odoo URL before connecting.');
        return;
      }
      if (!odooUsername.trim()) {
        setOdooError('Provide your Odoo username/email.');
        return;
      }
      if (!odooApiKey.trim() && !odooPassword.trim()) {
        setOdooError('Provide an API key or password.');
        return;
      }

      const connectionName = odooUseDemo ? 'Odoo Demo Workspace' : `Odoo @ ${odooUrl.trim()}`;
      const connectionPayload = {
        erp_system: 'odoo',
        organization_id: storedOrganizationId,
        connection_name: connectionName,
        connection_config: {
          url: odooUrl.trim(),
          database: odooDatabase.trim() || undefined,
          username: odooUsername.trim(),
          api_key: odooApiKey.trim() || undefined,
          password: odooPassword.trim() || undefined,
          use_api_key: Boolean(odooApiKey.trim()),
          demo: odooUseDemo,
        },
      };

      setErpConnectionState((prev) => ({
        ...prev,
        status: odooUseDemo ? 'demo' : 'connecting',
        connectionName,
        lastMessage: 'Creating connection…',
      }));

      try {
        await erpIntegrationApi.createOdooConnection(connectionPayload);
        await persistErpState({
          status: odooUseDemo ? 'demo' : 'connected',
          connectionName,
          lastMessage: 'Connection established. Running invoice pull…',
          sampleInvoice: null,
        });
        await handleOdooExtraction('batch');
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to save Odoo connection.';
        setOdooError(message);
        await persistErpState({
          status: 'error',
          connectionName,
          lastMessage: message,
          sampleInvoice: null,
        });
      }
    },
    [
      handleOdooExtraction,
      odooApiKey,
      odooDatabase,
      odooPassword,
      odooUrl,
      odooUseDemo,
      odooUsername,
      persistErpState,
      storedOrganizationId,
    ],
  );

  const toggleConnectivityLane = (lane: 'mono' | 'odoo') => {
    setExpandedConnectivityLane((prev) => (prev === lane ? null : lane));
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
    const isDojahVerified = companyProfileDetails?.source?.toLowerCase() === 'dojah';

    return (
      <div className="space-y-6">
        {isDojahVerified && (
          <div className="flex items-start gap-3 rounded-xl border border-green-200 bg-green-50 px-4 py-3">
            <ShieldCheckIcon className="h-5 w-5 flex-shrink-0 text-green-600" />
            <div>
              <p className="text-sm font-semibold text-green-800">Verified via Dojah</p>
              <p className="text-xs text-green-700">
                {companyProfileDetails?.verifiedAt
                  ? `Matched ${formatRuntimeTimestamp(companyProfileDetails.verifiedAt)}`
                  : 'We prefilled these fields from your Dojah company profile. You can still make edits.'}
              </p>
            </div>
          </div>
        )}
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

        <div className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-800">More details</p>
              <p className="text-xs text-gray-500">Optional info we use for onboarding recommendations.</p>
            </div>
            <button
              type="button"
              onClick={() => setShowCompanyDetails((prev) => !prev)}
              className="text-sm font-semibold text-blue-600 hover:text-blue-800"
            >
              {showCompanyDetails ? 'Hide' : 'Add details'}
            </button>
          </div>
          {showCompanyDetails && (
            <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
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
            </div>
          )}
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

    const isSystemIntegrator = selectedService === 'si' || selectedService === 'hybrid';

    if (!isSystemIntegrator) {
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

    const monoReady = Boolean(monoConsentState?.unified);
    const odooReady =
      erpTestStatus.state === 'success' || serviceConfig.connectors.includes('odoo');
    const laneCards: Array<{
      id: 'mono' | 'odoo';
      title: string;
      description: string;
      helper: string;
      ready: boolean;
    }> = [
      {
        id: 'mono',
        title: 'Bank feeds (Mono)',
        description: 'Use CBN-compliant consent to unlock transaction data.',
        helper: 'Best when invoices originate from banking activity or reconciliations.',
        ready: monoReady,
      },
      {
        id: 'odoo',
        title: 'ERP adapters (Odoo)',
        description: 'Connect your Odoo workspace and pull invoices instantly.',
        helper: 'Perfect for structured invoice data already living in an ERP.',
        ready: odooReady,
      },
    ];

    const erpConnectorOptions = connectors.filter((connector) => connector.id !== 'mono');

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">How do you want to feed invoices?</h3>
          <p className="text-sm text-gray-600">
            Choose at least one pathway to start syncing invoice-ready data into TaxPoynt.
          </p>
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            {laneCards.map((lane) => {
              const isExpanded = expandedConnectivityLane === lane.id;
              const statusClass = lane.ready
                ? 'bg-green-100 text-green-700'
                : isExpanded
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600';
              const statusLabel = lane.ready
                ? 'Configured'
                : isExpanded
                ? 'In setup'
                : 'Connect now';
              return (
                <button
                  key={lane.id}
                  type="button"
                  onClick={() => toggleConnectivityLane(lane.id)}
                  className={`text-left rounded-2xl border-2 p-5 transition ${
                    isExpanded ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-base font-semibold text-gray-900">{lane.title}</p>
                      <p className="text-sm text-gray-600">{lane.description}</p>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass}`}>
                      {statusLabel}
                    </span>
                  </div>
                  <p className="mt-3 text-xs text-gray-500">{lane.helper}</p>
                </button>
              );
            })}
          </div>
        </div>

        {expandedConnectivityLane === 'mono' && (
          <div className="space-y-4">
            <div className="rounded-2xl border border-indigo-100 bg-white p-5 space-y-4">
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                  <h4 className="text-base font-semibold text-gray-900">Connect bank feeds via Mono</h4>
                  <p className="text-sm text-gray-600">
                    Provide the authorised contact and we&apos;ll route them through Mono&apos;s consent flow.
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${bankingStatusDescriptor.className}`}
                >
                  {bankingStatusDescriptor.label}
                </span>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Account holder name</label>
                  <TaxPoyntInput
                    value={bankOwnerName}
                    onChange={(event) => setBankOwnerName(event.target.value)}
                    placeholder="e.g. Adaobi O."
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Account holder email</label>
                  <TaxPoyntInput
                    type="email"
                    value={bankOwnerEmail}
                    onChange={(event) => setBankOwnerEmail(event.target.value)}
                    placeholder="billing@example.com"
                  />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <label className="text-sm font-medium text-gray-700">
                    Callback URL <span className="text-xs font-normal text-gray-400">(optional)</span>
                  </label>
                  <TaxPoyntInput
                    value={bankCallbackUrl}
                    onChange={(event) => setBankCallbackUrl(event.target.value)}
                    placeholder="https://example.com/mono/callback"
                  />
                </div>
              </div>
              {monoLinkError && <p className="text-sm text-red-600">{monoLinkError}</p>}
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={handleSkipBanking}
                  className="text-sm font-semibold text-gray-600 hover:text-gray-900"
                >
                  Skip for now
                </button>
                <p className="text-xs text-gray-500">
                  Skipping means no automated reconciliations until you connect Mono later.
                </p>
              </div>
            </div>
            <div className="rounded-2xl border border-indigo-100 bg-white p-5 space-y-4">
              <MonoConsentIntegration
                compactMode
                showDetailed={false}
                onConsentUpdate={handleMonoConsentUpdate}
                onMonoWidgetReady={handleMonoWidgetReady}
                onComplete={handleMonoConsentComplete}
                onGenerateLink={handleMonoGenerateLink}
                onSkip={handleSkipBanking}
              />
              {monoStatusMessage && <p className="text-sm text-gray-600">{monoStatusMessage}</p>}
              {monoWidgetUrl && (
                <div className="flex flex-wrap gap-3">
                  <TaxPoyntButton
                    variant="outline"
                    onClick={() => {
                      if (typeof window !== 'undefined') {
                        window.open(monoWidgetUrl, '_blank', 'noopener,noreferrer');
                      }
                    }}
                  >
                    Launch Mono widget
                  </TaxPoyntButton>
                  <button
                    type="button"
                    className="text-sm font-medium text-blue-600 hover:text-blue-800"
                    onClick={() => {
                      if (typeof navigator !== 'undefined' && navigator.clipboard) {
                        navigator.clipboard.writeText(monoWidgetUrl).catch(() => {});
                      }
                    }}
                  >
                    Copy secure link
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {expandedConnectivityLane === 'odoo' && (
          <div className="space-y-6">
            <form
              className="rounded-2xl border border-indigo-100 bg-white p-5 space-y-4"
              onSubmit={handleOdooConnectionSubmit}
            >
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                  <h4 className="text-base font-semibold text-gray-900">Connect your Odoo workspace</h4>
                  <p className="text-sm text-gray-600">
                    Enter your Odoo credentials or try the shared demo instance to see invoice pulls in action.
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    erpConnectionState.status === 'connected' || erpConnectionState.status === 'demo'
                      ? 'bg-green-100 text-green-700'
                      : erpConnectionState.status === 'connecting'
                      ? 'bg-blue-100 text-blue-700'
                      : erpConnectionState.status === 'error'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {erpConnectionState.status === 'connected'
                    ? 'Connected'
                    : erpConnectionState.status === 'demo'
                    ? 'Demo connected'
                    : erpConnectionState.status === 'connecting'
                    ? 'Connecting…'
                    : erpConnectionState.status === 'error'
                    ? 'Action required'
                    : 'Not connected'}
                </span>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Odoo URL</label>
                  <TaxPoyntInput
                    value={odooUrl}
                    onChange={(event) => setOdooUrl(event.target.value)}
                    placeholder="https://company.odoo.com"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    Database <span className="text-xs font-normal text-gray-400">(optional)</span>
                  </label>
                  <TaxPoyntInput
                    value={odooDatabase}
                    onChange={(event) => setOdooDatabase(event.target.value)}
                    placeholder="company_db"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Username / Email</label>
                  <TaxPoyntInput
                    value={odooUsername}
                    onChange={(event) => setOdooUsername(event.target.value)}
                    placeholder="finance@example.com"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    API key <span className="text-xs font-normal text-gray-400">(preferred)</span>
                  </label>
                  <TaxPoyntInput
                    value={odooApiKey}
                    onChange={(event) => setOdooApiKey(event.target.value)}
                    placeholder="Copy from Odoo user settings"
                  />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <label className="text-sm font-medium text-gray-700">
                    Password <span className="text-xs font-normal text-gray-400">(optional fallback)</span>
                  </label>
                  <TaxPoyntInput
                    type="password"
                    value={odooPassword}
                    onChange={(event) => setOdooPassword(event.target.value)}
                    placeholder="Only if API key unavailable"
                  />
                </div>
              </div>
              <label className="flex items-center space-x-3 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={odooUseDemo}
                  onChange={(event) => setOdooUseDemo(event.target.checked)}
                />
                <span>Use TaxPoynt&apos;s demo Odoo workspace</span>
              </label>
              {odooError && <p className="text-sm text-red-600">{odooError}</p>}
              <div className="flex flex-wrap gap-3">
                <TaxPoyntButton type="submit" variant="primary">
                  {erpConnectionState.status === 'connecting' ? 'Connecting…' : 'Connect workspace'}
                </TaxPoyntButton>
                <p className="text-xs text-gray-500">
                  Your credentials are encrypted and stored securely. You can rotate them after onboarding.
                </p>
              </div>
            </form>

            <div className="rounded-2xl border border-indigo-100 bg-white p-5 space-y-4">
              <div>
                <h4 className="text-base font-semibold text-gray-900">Choose the systems you plan to connect</h4>
                <p className="text-sm text-gray-600">
                  Select the ERP adapters you expect to use. We&apos;ll preload mapping templates for each.
                </p>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {erpConnectorOptions.map((connector) => {
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

              <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                <h5 className="font-semibold text-gray-900">Validation preferences</h5>
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

            <div className="rounded-2xl border border-indigo-100 bg-white p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-base font-semibold text-gray-900">Test invoice pulls</h4>
                  <p className="text-sm text-gray-600">
                    Use live credentials or the shared demo workspace to see erp_data_extractor in action.
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    erpTestStatus.state === 'success' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {erpTestStatus.state === 'success' ? 'Tested' : 'Sandbox ready'}
                </span>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  Sample Odoo invoice IDs
                  <span className="ml-1 text-xs font-normal text-gray-400">(comma separated)</span>
                </label>
                <TaxPoyntInput
                  value={erpInvoiceIdsInput}
                  onChange={(event) => setErpInvoiceIdsInput(event.target.value)}
                  placeholder="INV/2024/0001,INV/2024/0002"
                />
                <p className="text-xs text-gray-500">
                  Provide real IDs from your sandbox or stick with the shared demo data to preview transformations.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <TaxPoyntButton
                  variant="primary"
                  onClick={() => {
                    void handleOdooExtraction('specific');
                  }}
                  disabled={erpTestStatus.state === 'loading'}
                >
                  {erpTestStatus.state === 'loading' ? 'Running…' : 'Test selected invoices'}
                </TaxPoyntButton>
                <TaxPoyntButton
                  variant="outline"
                  onClick={() => {
                    void handleOdooExtraction('batch');
                  }}
                  disabled={erpTestStatus.state === 'loading'}
                >
                  {erpTestStatus.state === 'loading' ? 'Running…' : 'Run sandbox batch'}
                </TaxPoyntButton>
              </div>
              {erpTestStatus.state !== 'idle' && (
                <div
                  className={`rounded-lg border px-4 py-3 text-sm ${
                    erpTestStatus.state === 'success'
                      ? 'border-green-200 bg-green-50 text-green-800'
                      : erpTestStatus.state === 'error'
                      ? 'border-red-200 bg-red-50 text-red-700'
                      : 'border-blue-200 bg-blue-50 text-blue-800'
                  }`}
                >
                  <p>{erpTestStatus.message}</p>
                  {typeof erpTestStatus.fetchedCount === 'number' && (
                    <p className="mt-1 text-xs">
                      Fetched count: {erpTestStatus.fetchedCount}
                      {erpTestStatus.sampleInvoice && ` · Sample invoice ${erpTestStatus.sampleInvoice}`}
                    </p>
                  )}
                </div>
              )}
              {erpPreviewInvoice && (
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-gray-900">Preview sample invoice</p>
                    <button
                      type="button"
                      className="text-sm font-semibold text-blue-600 hover:text-blue-800"
                      onClick={() => setErpPreviewVisible((prev) => !prev)}
                    >
                      {erpPreviewVisible ? 'Hide preview' : 'Show JSON'}
                    </button>
                  </div>
                  {erpPreviewVisible && (
                    <pre className="mt-3 max-h-64 overflow-auto rounded bg-white p-3 text-xs text-gray-800">
                      {JSON.stringify(erpPreviewInvoice, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
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
  const runtimeIrnProgress = runtimeInsights.irnProgress ?? null;
  const runtimeIrnItems = runtimeIrnProgress?.recent ?? [];
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

      <section className="rounded-2xl border border-gray-200 bg-white/90 p-5 shadow-sm backdrop-blur">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Service focus</p>
            <p className="text-lg font-semibold text-slate-900">{serviceTitle(displayedService)}</p>
            <p className="text-sm text-slate-600">{serviceSummaryText}</p>
          </div>
          {!showServiceSelection ? (
            <button
              type="button"
              onClick={handleChangeService}
              className="text-sm font-semibold text-blue-600 hover:text-blue-800"
            >
              Change service
            </button>
          ) : (
            <span className="text-sm text-slate-500">Choose your service above to continue</span>
          )}
        </div>
      </section>

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
