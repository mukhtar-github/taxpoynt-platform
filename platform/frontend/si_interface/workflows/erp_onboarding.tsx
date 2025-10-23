'use client';

/**
 * ERP Onboarding Workflow
 * =======================
 * 
 * System Integrator workflow for onboarding new organizations with ERP system integration.
 * Complete end-to-end process from organization setup to production deployment.
 * 
 * Features:
 * - Organization registration and verification
 * - ERP system selection and configuration
 * - Data mapping and validation
 * - Nigerian compliance setup (FIRS, VAT, CBN)
 * - Testing and production deployment
 * - Progress tracking and status updates
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../../design_system/components/Button';
import apiClient from '../../shared_components/api/client';
import { useFormPersistence, CrossFormDataManager } from '../../shared_components/utils/formPersistence';
import { authService } from '../../shared_components/services/auth';
import { onboardingApi } from '../../shared_components/services/onboardingApi';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  required: boolean;
  completed: boolean;
  estimatedDuration: string;
  dependencies?: string[];
}

interface OrganizationProfile {
  basicInfo: {
    name: string;
    rcNumber: string;
    tinNumber: string;
    email: string;
    phone: string;
    address: string;
    industry: string;
    size: string;
  };
  compliance: {
    vatRegistered: boolean;
    vatNumber?: string;
    firsRegistered: boolean;
    firsId?: string;
    cbnCompliant: boolean;
  };
  businessSystems: {
    primaryErp?: string;
    secondaryErp?: string;
    currentSoftware: string[];
    invoiceVolume: string;
    integrationRequirements: string[];
  };
}

interface ERPConfiguration {
  systemType: string;
  version?: string;
  credentials: {
    server?: string;
    database?: string;
    username?: string;
    apiKey?: string;
    oauthToken?: string;
    password?: string;
    environment?: string;
  };
  dataSources: {
    customers: boolean;
    products: boolean;
    invoices: boolean;
    payments: boolean;
    inventory: boolean;
  };
  mappingRules: Array<{
    sourceField: string;
    targetField: string;
    transformation?: string;
  }>;
}

type MappingRule = ERPConfiguration['mappingRules'][number];

interface ErpConnectionRecord {
  connection_id: string;
  connection_name?: string;
  organization_id?: string;
  erp_system?: string;
  environment?: string;
  status?: string | null;
  status_reason?: string | null;
  last_status_at?: string | null;
}

type BulkConnectionTestResponse = {
  success?: boolean;
  message?: string;
  detail?: string;
  data?: {
    summary?: {
      total?: number;
      successful?: number;
      failed?: number;
      warnings?: number;
    };
    results?: Array<Record<string, unknown>>;
    connection_activity?: Record<string, unknown>;
  };
};

const INFORMATION_REDIRECT_KEY = 'taxpoynt_connection_manager_org';

const unwrapApiPayload = (raw: unknown): { payload: Record<string, any>; meta?: Record<string, any>; success?: boolean } => {
  if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
    const candidate = raw as Record<string, any>;
    const inner = candidate.data;
    if (inner && typeof inner === 'object' && !Array.isArray(inner)) {
      return { payload: inner as Record<string, any>, meta: candidate.meta, success: candidate.success };
    }
    return { payload: candidate, meta: candidate.meta, success: candidate.success };
  }
  return { payload: {} };
};

type ValidateMappingResponse = {
  success?: boolean;
  message?: string;
  detail?: string;
  errors?: Record<string, string[]>;
  preview_data?: {
    system_id?: string;
    validated_at?: string;
    validated_targets?: string[];
    missing_required?: string[];
    mapped_fields?: Record<string, unknown>;
  };
};

const pickString = (value: unknown): string | undefined =>
  typeof value === 'string' && value.trim().length > 0 ? value : undefined;

const normalizeUserFacingMessage = (value?: string): string | undefined => {
  if (!value) {
    return undefined;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }

  const lower = trimmed.toLowerCase();
  if (lower.includes('network error') || lower.includes('check your connection')) {
    return 'Service temporarily unavailable. Please retry shortly.';
  }

  return trimmed;
};

const extractErrorMessage = (error: unknown, fallback: string): string => {
  const sanitizedFallback = normalizeUserFacingMessage(fallback) ?? fallback;

  if (error instanceof Error) {
    const msg = normalizeUserFacingMessage(error.message);
    if (msg) return msg;
  }

  if (typeof error === 'string') {
    const msg = normalizeUserFacingMessage(error);
    if (msg) return msg;
  }

  if (error && typeof error === 'object') {
    const errObj = error as Record<string, unknown>;
    const detail = normalizeUserFacingMessage(pickString(errObj.detail));
    if (detail) return detail;
    const message = normalizeUserFacingMessage(pickString(errObj.message));
    if (message) return message;

    const response = errObj.response;
    if (response && typeof response === 'object') {
      const data = (response as Record<string, unknown>).data;
      if (data && typeof data === 'object') {
        const nestedDetail = normalizeUserFacingMessage(pickString((data as Record<string, unknown>).detail));
        if (nestedDetail) return nestedDetail;
        const nestedMessage = normalizeUserFacingMessage(pickString((data as Record<string, unknown>).message));
        if (nestedMessage) return nestedMessage;
      }
    }
  }

  return sanitizedFallback;
};

const isRecord = (value: unknown): value is Record<string, any> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const deepClone = <T>(value: T): T => {
  try {
    return JSON.parse(JSON.stringify(value ?? null));
  } catch {
    return value;
  }
};

const sanitizeErpConfiguration = (config: ERPConfiguration) => {
  const clone = deepClone(config) as Record<string, any>;
  if (clone && typeof clone === 'object' && 'credentials' in clone) {
    delete clone.credentials;
  }
  return clone;
};

const sanitizeStepPayload = (payload: Record<string, any>) => {
  const clone = deepClone(payload) as Record<string, any>;
  if (clone?.erp_configuration && typeof clone.erp_configuration === 'object') {
    delete clone.erp_configuration.credentials;
  }
  return clone;
};

interface ExtractedErpProgress {
  currentStep?: string;
  completedSteps: string[];
  raw: Record<string, any>;
}

const extractErpProgressMetadata = (metadata: Record<string, any> | null | undefined): ExtractedErpProgress => {
  if (!metadata || !isRecord(metadata.erp_onboarding)) {
    return { currentStep: undefined, completedSteps: [], raw: {} };
  }

  const erpMetadata = metadata.erp_onboarding as Record<string, any>;
  const completedSteps = Array.isArray(erpMetadata.completed_steps)
    ? erpMetadata.completed_steps.filter((step): step is string => typeof step === 'string')
    : [];

  const currentStep =
    typeof erpMetadata.current_step === 'string' ? erpMetadata.current_step : undefined;

  return {
    currentStep,
    completedSteps,
    raw: erpMetadata,
  };
};

const buildErpMetadataWithProgress = (
  baseMetadata: Record<string, any>,
  update: {
    currentStep: string;
    completedSteps: string[];
    stepPayload?: Record<string, any>;
    organizationProfile: OrganizationProfile;
    erpConfiguration: ERPConfiguration;
    complianceConfig: typeof DEFAULT_COMPLIANCE_CONFIG;
    productionChecklist: typeof DEFAULT_PRODUCTION_CHECKLIST;
    trainingChecklist: typeof DEFAULT_TRAINING_CHECKLIST;
    connectionId: string | null;
  }
) => {
  const metadataCopy: Record<string, any> = { ...baseMetadata };
  const existingErp = metadataCopy.erp_onboarding && isRecord(metadataCopy.erp_onboarding)
    ? { ...metadataCopy.erp_onboarding }
    : {};

  existingErp.current_step = update.currentStep;
  existingErp.completed_steps = update.completedSteps;
  existingErp.last_updated = new Date().toISOString();
  existingErp.organization_profile = deepClone(update.organizationProfile);
  existingErp.erp_configuration_snapshot = sanitizeErpConfiguration(update.erpConfiguration);
  existingErp.compliance_config = deepClone(update.complianceConfig);
  existingErp.production_checklist = deepClone(update.productionChecklist);
  existingErp.training_checklist = deepClone(update.trainingChecklist);
  existingErp.connection_id = update.connectionId ?? null;

  if (update.stepPayload) {
    existingErp.last_step_payload = sanitizeStepPayload(update.stepPayload);
  }

  metadataCopy.erp_onboarding = existingErp;
  return metadataCopy;
};

const normalizeStepKey = (value: string): string =>
  value.trim().toLowerCase().replace(/[\s-]+/g, '_');

const ERP_TO_CANONICAL_MAP: Record<string, string> = {
  organization_setup: 'service-selection',
  compliance_verification: 'company-profile',
  erp_selection: 'system-connectivity',
  erp_configuration: 'system-connectivity',
  data_mapping: 'system-connectivity',
  testing_validation: 'system-connectivity',
  compliance_setup: 'review',
  production_deployment: 'launch',
  training_handover: 'launch',
};

const CANONICAL_TO_ERP_MAP: Record<string, string> = {
  service_selection: 'organization_setup',
  company_profile: 'compliance_verification',
  system_connectivity: 'erp_configuration',
  review: 'compliance_setup',
  launch: 'production_deployment',
};

const getCanonicalStepId = (stepId: string): string => {
  const normalized = normalizeStepKey(stepId);
  return ERP_TO_CANONICAL_MAP[normalized] ?? stepId;
};

const getCanonicalStepIds = (stepIds: string[]): string[] => {
  const seen = new Set<string>();
  for (const step of stepIds) {
    const canonical = getCanonicalStepId(step);
    seen.add(canonical);
  }
  return Array.from(seen);
};

const getErpStepIdFromCanonical = (stepId: string): string => {
  const normalized = normalizeStepKey(stepId);
  return CANONICAL_TO_ERP_MAP[normalized] ?? stepId.replace(/-/g, '_');
};

const onboardingSteps: OnboardingStep[] = [
  {
    id: 'organization_setup',
    title: 'Organization Setup',
    description: 'Register organization and verify business credentials',
    required: true,
    completed: false,
    estimatedDuration: '30-45 minutes'
  },
  {
    id: 'compliance_verification',
    title: 'Compliance Verification',
    description: 'Verify FIRS registration, VAT status, and Nigerian compliance',
    required: true,
    completed: false,
    estimatedDuration: '20-30 minutes',
    dependencies: ['organization_setup']
  },
  {
    id: 'erp_selection',
    title: 'ERP System Selection',
    description: 'Choose and configure ERP system integration',
    required: true,
    completed: false,
    estimatedDuration: '15-30 minutes',
    dependencies: ['organization_setup']
  },
  {
    id: 'erp_configuration',
    title: 'ERP Configuration',
    description: 'Set up ERP credentials and connection parameters',
    required: true,
    completed: false,
    estimatedDuration: '45-60 minutes',
    dependencies: ['erp_selection']
  },
  {
    id: 'data_mapping',
    title: 'Data Mapping Setup',
    description: 'Configure data field mapping for FIRS compliance',
    required: true,
    completed: false,
    estimatedDuration: '60-90 minutes',
    dependencies: ['erp_configuration']
  },
  {
    id: 'testing_validation',
    title: 'Testing & Validation',
    description: 'Test integration and validate data flow',
    required: true,
    completed: false,
    estimatedDuration: '30-45 minutes',
    dependencies: ['data_mapping']
  },
  {
    id: 'compliance_setup',
    title: 'Compliance Configuration',
    description: 'Configure Nigerian tax compliance and FIRS integration',
    required: true,
    completed: false,
    estimatedDuration: '45-60 minutes',
    dependencies: ['testing_validation']
  },
  {
    id: 'production_deployment',
    title: 'Production Deployment',
    description: 'Deploy to production and activate live processing',
    required: true,
    completed: false,
    estimatedDuration: '15-30 minutes',
    dependencies: ['compliance_setup']
  },
  {
    id: 'training_handover',
    title: 'Training & Handover',
    description: 'Client training and system handover',
    required: false,
    completed: false,
    estimatedDuration: '60-90 minutes',
    dependencies: ['production_deployment']
  }
];

const KNOWN_ERP_STEPS = new Set(onboardingSteps.map(step => step.id));

const createDefaultSteps = (): OnboardingStep[] =>
  onboardingSteps.map(step => ({ ...step, completed: false }));

const createDefaultOrganizationProfile = (): OrganizationProfile => ({
  basicInfo: {
    name: '',
    rcNumber: '',
    tinNumber: '',
    email: '',
    phone: '',
    address: '',
    industry: '',
    size: ''
  },
  compliance: {
    vatRegistered: false,
    firsRegistered: false,
    cbnCompliant: false
  },
  businessSystems: {
    currentSoftware: [],
    invoiceVolume: '',
    integrationRequirements: []
  }
});

const createDefaultErpConfiguration = (): ERPConfiguration => ({
  systemType: '',
  credentials: {},
  dataSources: {
    customers: false,
    products: false,
    invoices: false,
    payments: false,
    inventory: false
  },
  mappingRules: []
});

const DEFAULT_COMPLIANCE_CONFIG = {
  firsApiKey: '',
  complianceEmail: '',
  vatMode: 'standard',
  vatRate: '7.5',
  enableRateLimiter: true,
  enableAuditTrail: true,
  requireSecureChannels: true,
  notes: '',
};

const DEFAULT_PRODUCTION_CHECKLIST = {
  promoteConnection: true,
  enableLiveSubmissions: false,
  notifyFinanceTeam: false,
  monitoringEnabled: false,
  rollbackPlanDocumented: true,
};

const DEFAULT_TRAINING_CHECKLIST = {
  trainingScheduled: false,
  supportDocsShared: false,
  successMetricsDefined: false,
  postGoLiveSupportAssigned: false,
  customerSignOffReceived: false,
};

const resolveStepIndexFromKey = (stepKey?: string): number | null => {
  if (!stepKey) {
    return null;
  }

  const normalized = stepKey.toLowerCase().replace(/[\s-]+/g, '_');
  const aliasMap: Record<string, string> = {
    organization: 'organization_setup',
    compliance: 'compliance_verification',
    erp: 'erp_selection',
    configuration: 'erp_configuration',
    mapping: 'data_mapping',
    testing: 'testing_validation',
    validation: 'testing_validation',
    deployment: 'production_deployment',
    production: 'production_deployment',
    training: 'training_handover',
    handover: 'training_handover'
  };
  const resolvedId = aliasMap[normalized] ?? normalized;
  const index = onboardingSteps.findIndex(step => step.id === resolvedId);
  return index >= 0 ? index : null;
};

interface ERPOnboardingProps {
  organizationId?: string;
  onComplete?: (organizationId: string) => void;
  onSkip?: () => void;
  isLoading?: boolean;
  initialStepId?: string;
}

export const ERPOnboarding: React.FC<ERPOnboardingProps> = ({
  organizationId,
  onComplete,
  onSkip,
  isLoading = false,
  initialStepId
}) => {
  const router = useRouter();
  const initialStepIndex = resolveStepIndexFromKey(initialStepId);
  const [currentStep, setCurrentStep] = useState<number>(() => initialStepIndex ?? 0);
  const initialPersistenceKey = useMemo(() => {
    if (organizationId) {
      return `taxpoynt_erp_onboarding_${organizationId}`;
    }
    if (typeof window !== 'undefined') {
      const stored = authService.getStoredUser();
      if (stored?.organization?.id) {
        return `taxpoynt_erp_onboarding_${stored.organization.id}`;
      }
      if (stored?.id) {
        return `taxpoynt_erp_onboarding_user_${stored.id}`;
      }
    }
    return 'taxpoynt_erp_onboarding_temp';
  }, [organizationId]);
  // Form persistence setup for ERP onboarding
  const erpFormPersistence = useFormPersistence({
    storageKey: initialPersistenceKey,
    persistent: true, // Use localStorage for longer persistence
    excludeFields: ['credentials'], // Don't store sensitive ERP credentials
    autoSaveInterval: 5000 // Save every 5 seconds
  });

  const [steps, setSteps] = useState<OnboardingStep[]>(() => createDefaultSteps());
  const [organizationProfile, setOrganizationProfile] = useState<OrganizationProfile>(() => createDefaultOrganizationProfile());
  const [erpConfiguration, setErpConfiguration] = useState<ERPConfiguration>(() => createDefaultErpConfiguration());
  const [remoteMetadata, setRemoteMetadata] = useState<Record<string, any>>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);
  const [resolvedOrganizationId, setResolvedOrganizationId] = useState<string | null>(organizationId ?? null);
  const [connections, setConnections] = useState<ErpConnectionRecord[]>([]);
  const [connectionsLoading, setConnectionsLoading] = useState(false);
  const [connectionsError, setConnectionsError] = useState<string | null>(null);
  const connectionsFetchRef = useRef(false);
  const [connectionTestStatus, setConnectionTestStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle');
  const [connectionTestMessage, setConnectionTestMessage] = useState<string>('');
  const [dataValidationStatus, setDataValidationStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle');
  const [dataValidationMessage, setDataValidationMessage] = useState<string>('');
  const [savedMapping, setSavedMapping] = useState<MappingRule[]>([]);
  const [savedMappingStatus, setSavedMappingStatus] = useState<'idle' | 'loading' | 'ready' | 'missing' | 'error'>('idle');
  const mappingFetchRef = useRef(false);
  const [createdConnectionId, setCreatedConnectionId] = useState<string | null>(null);
  const [connectionCreationStatus, setConnectionCreationStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [connectionCreationMessage, setConnectionCreationMessage] = useState<string>('');
  const [complianceConfig, setComplianceConfig] = useState(() => ({ ...DEFAULT_COMPLIANCE_CONFIG }));
  const [productionChecklist, setProductionChecklist] = useState(() => ({ ...DEFAULT_PRODUCTION_CHECKLIST }));
  const [trainingChecklist, setTrainingChecklist] = useState(() => ({ ...DEFAULT_TRAINING_CHECKLIST }));
  const [isResetting, setIsResetting] = useState(false);
  const [resetStatusMessage, setResetStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    connectionsFetchRef.current = false;
    mappingFetchRef.current = false;
  }, [resolvedOrganizationId, erpConfiguration.systemType]);

  const syncErpProgress = useCallback(
    async (stepId: string, completedIds: string[], stepPayload?: Record<string, any>) => {
      if (!authService.isAuthenticated()) {
        return undefined;
      }

      const baseMetadata = deepClone(remoteMetadata) as Record<string, any>;
      const canonicalCurrentStep = getCanonicalStepId(stepId);
      const canonicalCompletedSteps = getCanonicalStepIds(completedIds);
      const metadataToSend = buildErpMetadataWithProgress(baseMetadata, {
        currentStep: stepId,
        completedSteps: completedIds,
        stepPayload,
        organizationProfile,
        erpConfiguration,
        complianceConfig,
        productionChecklist,
        trainingChecklist,
        connectionId: createdConnectionId,
      });

      try {
        const updatedState = await onboardingApi.updateOnboardingState({
          current_step: canonicalCurrentStep,
          completed_steps: canonicalCompletedSteps,
          metadata: metadataToSend,
        });
        const updatedMetadata = isRecord(updatedState.metadata) ? updatedState.metadata : {};
        setRemoteMetadata(updatedMetadata);
        return metadataToSend;
      } catch (error) {
        console.warn(`Failed to synchronize ERP onboarding step "${stepId}":`, error);
        return undefined;
      }
    },
    [
      remoteMetadata,
      organizationProfile,
      erpConfiguration,
      complianceConfig,
      productionChecklist,
      trainingChecklist,
      createdConnectionId,
    ]
  );

  const markStepCompletedExternally = useCallback(
    (stepId: string | undefined, advanceToStep?: string) => {
      if (!stepId) {
        return;
      }

      const stepIndex = onboardingSteps.findIndex(step => step.id === stepId);
      if (stepIndex === -1) {
        return;
      }

      const advanceIndex = advanceToStep
        ? onboardingSteps.findIndex(step => step.id === advanceToStep)
        : -1;
      const nextIndexCandidate = Math.min(stepIndex + 1, onboardingSteps.length - 1);
      const nextIndex = advanceIndex >= 0 ? Math.max(nextIndexCandidate, advanceIndex) : nextIndexCandidate;

      const nextCurrentStep = currentStep <= stepIndex ? nextIndex : currentStep;
      if (currentStep <= stepIndex) {
        setCurrentStep(nextIndex);
      }

      setSteps(prev =>
        prev.map(step =>
          step.id === stepId ? { ...step, completed: true } : step
        )
      );

      const completedIdsSet = new Set(steps.filter(step => step.completed).map(step => step.id));
      completedIdsSet.add(stepId);
      const completedIds = Array.from(completedIdsSet);

      erpFormPersistence.saveFormData({
        organizationProfile,
        erpConfiguration,
        currentStep: nextCurrentStep,
        createdConnectionId,
        complianceConfig,
        productionChecklist,
        trainingChecklist,
        stepsCompleted: completedIds,
        timestamp: Date.now()
      });

      void syncErpProgress(stepId, completedIds);
    },
    [
      steps,
      currentStep,
      createdConnectionId,
      erpFormPersistence,
      organizationProfile,
      erpConfiguration,
      complianceConfig,
      productionChecklist,
      trainingChecklist,
      syncErpProgress
    ]
  );

  useEffect(() => {
    if (initialStepIndex !== null) {
      setCurrentStep(prev => (prev < initialStepIndex ? initialStepIndex : prev));
    }
  }, [initialStepIndex]);

  useEffect(() => {
    if (organizationId) {
      setResolvedOrganizationId(organizationId);
      return;
    }

    if (typeof window === 'undefined') {
      return;
    }

    const storedUser = authService.getStoredUser();
    if (storedUser?.organization?.id) {
      setResolvedOrganizationId(storedUser.organization.id);
    }
  }, [organizationId]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const readSessionFlag = () => {
      const stored = sessionStorage.getItem('taxpoynt_erp_onboarding_step_completed');
      if (!stored) {
        return;
      }

      sessionStorage.removeItem('taxpoynt_erp_onboarding_step_completed');
      try {
        const payload = JSON.parse(stored) as { step?: string; nextStep?: string } | null;
        if (payload?.step) {
          markStepCompletedExternally(payload.step, payload.nextStep);
        }
      } catch (error) {
        console.warn('Failed to parse onboarding completion payload:', error);
      }
    };

    const handleExternalCompletion = (event: Event) => {
      const detail = (event as CustomEvent<{ step?: string; nextStep?: string }>).detail;
      if (detail?.step) {
        markStepCompletedExternally(detail.step, detail.nextStep);
      }
    };

    const handleVisibilityChange = () => {
      if (!document.hidden) {
        readSessionFlag();
      }
    };

    const handleWindowFocus = () => {
      readSessionFlag();
    };

    readSessionFlag();

    window.addEventListener('taxpoynt:onboarding-step-completed', handleExternalCompletion);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleWindowFocus);

    return () => {
    window.removeEventListener('taxpoynt:onboarding-step-completed', handleExternalCompletion);
    document.removeEventListener('visibilitychange', handleVisibilityChange);
    window.removeEventListener('focus', handleWindowFocus);
  };
}, [markStepCompletedExternally]);

  const fetchErpConnections = useCallback(async (): Promise<ErpConnectionRecord[]> => {
    if (!resolvedOrganizationId) {
      setConnections([]);
      setConnectionsError('Organization context is required to load ERP connections.');
      return [];
    }

    setConnectionsLoading(true);
    setConnectionsError(null);
    try {
      const query = `?organization_id=${encodeURIComponent(resolvedOrganizationId)}`;
      const response = await apiClient.get<Record<string, any>>(`/si/business/erp/connections${query}`);
      const { payload: responseData } = unwrapApiPayload(response);
      const connectionsFromPayload =
        Array.isArray(responseData?.connections)
          ? responseData.connections
          : Array.isArray((responseData?.data as any)?.connections)
            ? (responseData.data as any).connections
            : [];
      const connectionList: ErpConnectionRecord[] = Array.isArray(connectionsFromPayload)
        ? connectionsFromPayload
        : [];

      setConnections(connectionList);
      if (!connectionList.length) {
        setConnectionsError('No ERP connections found yet. Configure a connection to enable automated testing.');
      } else {
        setConnectionsError(null);
      }

      return connectionList;
    } catch (error) {
      const message = extractErrorMessage(
        error,
        'Unable to load ERP connections. Please try again.'
      );
      setConnections([]);
      setConnectionsError(message);
      return [];
    } finally {
      setConnectionsLoading(false);
    }
  }, [resolvedOrganizationId]);

  const fetchSavedMapping = useCallback(async (): Promise<MappingRule[]> => {
    if (!erpConfiguration.systemType || !resolvedOrganizationId) {
      setSavedMapping([]);
      setSavedMappingStatus('missing');
      return [];
    }

    setSavedMappingStatus('loading');
    try {
      const response = await apiClient.get<{
        success?: boolean;
        mapping_rules?: MappingRule[];
        data?: { mapping_rules?: MappingRule[] };
      }>(`/si/business/erp/data-mapping/${resolvedOrganizationId}/${erpConfiguration.systemType}`);

      const rules =
        Array.isArray(response?.mapping_rules)
          ? response.mapping_rules
          : Array.isArray(response?.data?.mapping_rules)
            ? response.data.mapping_rules
            : [];

      if (rules.length) {
        setSavedMapping(rules);
        setSavedMappingStatus('ready');
      } else {
        setSavedMapping([]);
        setSavedMappingStatus('missing');
      }

      return rules;
    } catch (error) {
      setSavedMapping([]);
      setSavedMappingStatus('error');
      return [];
    }
  }, [erpConfiguration.systemType, resolvedOrganizationId]);

  useEffect(() => {
    const activeStepId = steps[currentStep]?.id;
    if (activeStepId !== 'testing_validation') {
      return;
    }

    if (!connectionsFetchRef.current) {
      connectionsFetchRef.current = true;
      void fetchErpConnections();
    }

    if (!mappingFetchRef.current) {
      mappingFetchRef.current = true;
      void fetchSavedMapping();
    }
  }, [currentStep, fetchErpConnections, fetchSavedMapping, steps]);

  // Load existing onboarding progress and initialize with shared data
  useEffect(() => {
    loadOnboardingProgress();

    // Load saved ERP form data and merge with shared registration data
    const savedErpData = erpFormPersistence.loadFormData();
    const sharedData = CrossFormDataManager.getSharedData();
    
    if (savedErpData) {
      // Restore ERP-specific saved data
      if (savedErpData.organizationProfile) {
        setOrganizationProfile(prev => ({
          ...prev,
          ...savedErpData.organizationProfile
        }));
      }
      if (savedErpData.erpConfiguration) {
        setErpConfiguration(prev => ({
          ...prev,
          ...savedErpData.erpConfiguration,
          credentials: {} // Never restore credentials
        }));
      }
      if (savedErpData.complianceConfig) {
        setComplianceConfig(prev => ({ ...prev, ...savedErpData.complianceConfig }));
      }
      if (savedErpData.productionChecklist) {
        setProductionChecklist(prev => ({ ...prev, ...savedErpData.productionChecklist }));
      }
      if (savedErpData.trainingChecklist) {
        setTrainingChecklist(prev => ({ ...prev, ...savedErpData.trainingChecklist }));
      }
      if (savedErpData.createdConnectionId) {
        setCreatedConnectionId(savedErpData.createdConnectionId);
        setConnectionCreationStatus('success');
        setConnectionCreationMessage('ERP connection ready for automated diagnostics.');
      }
      if (savedErpData.currentStep !== undefined) {
        const savedIndex = savedErpData.currentStep;
        setCurrentStep(prev => {
          if (initialStepIndex !== null && savedIndex < initialStepIndex) {
            return initialStepIndex;
          }
          return savedIndex;
        });
      } else if (initialStepIndex !== null) {
        setCurrentStep(prev => (prev < initialStepIndex ? initialStepIndex : prev));
      }
      console.log('📂 ERP onboarding form restored from saved data');
    }

    // Auto-populate basic info from registration if available
    if (Object.keys(sharedData).length > 0) {
      setOrganizationProfile(prev => ({
        ...prev,
        basicInfo: {
          ...prev.basicInfo,
          name: sharedData.business_name || prev.basicInfo.name,
          email: sharedData.email || prev.basicInfo.email,
          phone: sharedData.phone || prev.basicInfo.phone,
          address: sharedData.address || prev.basicInfo.address,
          rcNumber: sharedData.rc_number || prev.basicInfo.rcNumber,
          tinNumber: sharedData.tin || prev.basicInfo.tinNumber
        }
      }));
      console.log('🔗 ERP form auto-populated from registration data');
    }

    // Start auto-save for ERP data
    erpFormPersistence.startAutoSave(() => ({
      organizationProfile,
      erpConfiguration,
      currentStep,
      createdConnectionId,
      complianceConfig,
      productionChecklist,
      trainingChecklist,
      timestamp: Date.now()
    }));

    // Cleanup on unmount
    return () => {
      erpFormPersistence.stopAutoSave();
    };
  }, [organizationId, initialStepIndex, loadOnboardingProgress]);

  const loadOnboardingProgress = useCallback(async () => {
    if (!authService.isAuthenticated()) {
      return;
    }

    try {
      const state = await onboardingApi.getOnboardingState();
      if (!state) {
        return;
      }
      const metadata = isRecord(state.metadata) ? state.metadata : {};
      setRemoteMetadata(metadata);

      const progressMetadata = extractErpProgressMetadata(metadata);

      let completedSteps = progressMetadata.completedSteps.filter(step => KNOWN_ERP_STEPS.has(step));
      if ((!completedSteps || completedSteps.length === 0) && Array.isArray(state.completed_steps)) {
        completedSteps = state.completed_steps
          .filter((step): step is string => typeof step === 'string')
          .map(getErpStepIdFromCanonical)
          .filter(step => KNOWN_ERP_STEPS.has(step));
      }

      const completedSet = new Set(completedSteps);

      setSteps(prev =>
        prev.map(step => ({
          ...step,
          completed: completedSet.has(step.id)
        }))
      );

      let preferredStepId =
        progressMetadata.currentStep && KNOWN_ERP_STEPS.has(progressMetadata.currentStep)
          ? progressMetadata.currentStep
          : undefined;
      if (!preferredStepId && typeof state.current_step === 'string') {
        const mapped = getErpStepIdFromCanonical(state.current_step);
        if (KNOWN_ERP_STEPS.has(mapped)) {
          preferredStepId = mapped;
        }
      }

      if (preferredStepId) {
        const remoteIndex = onboardingSteps.findIndex(step => step.id === preferredStepId);
        if (remoteIndex >= 0) {
          const resolvedIndex =
            initialStepIndex !== null && remoteIndex < initialStepIndex
              ? initialStepIndex
              : remoteIndex;
          setCurrentStep(resolvedIndex);
        }
      }
    } catch (error) {
      console.error('Failed to load onboarding progress:', error);
    }
  }, [initialStepIndex]);

  const handleStepComplete = async () => {
    const stepId = steps[currentStep].id;
    
    try {
      setIsProcessing(true);

      if (stepId === 'erp_configuration') {
        try {
          await ensureConnectionPersisted();
        } catch (error) {
          const message = extractErrorMessage(
            error,
            'Unable to save ERP configuration. Please resolve the errors and try again.'
          );
          alert(`❌ ${message}`);
          return;
        }
      }

      if (stepId === 'compliance_setup') {
        if (!complianceConfig.firsApiKey.trim()) {
          alert('⚠️ Provide the FIRS API key before continuing.');
          return;
        }
        if (!complianceConfig.complianceEmail.trim()) {
          alert('⚠️ Enter the compliance contact email before continuing.');
          return;
        }
      }

      if (stepId === 'production_deployment') {
        if (!productionChecklist.promoteConnection || !productionChecklist.enableLiveSubmissions) {
          alert('⚠️ Confirm promotion and live submissions before marking deployment complete.');
          return;
        }
      }
      
      // Always update local state first for immediate UX feedback
      setSteps(prev =>
        prev.map((step, index) =>
          index === currentStep ? { ...step, completed: true } : step
        )
      );

      const completedIds = Array.from(
        new Set([
          ...steps.filter(step => step.completed).map(step => step.id),
          stepId
        ])
      );

      // Save to persistence immediately
      erpFormPersistence.saveFormData({
        organizationProfile,
        erpConfiguration,
        currentStep,
        createdConnectionId,
        complianceConfig,
        productionChecklist,
        trainingChecklist,
        stepsCompleted: completedIds,
        timestamp: Date.now()
      });

      // Attempt API save using onboarding client
      const syncResult = await syncErpProgress(stepId, completedIds, getCurrentStepData());
      if (syncResult) {
        console.log(`✅ ${steps[currentStep].title} progress synced successfully.`);
      } else {
        console.log(`💾 ${steps[currentStep].title} saved locally (offline mode).`);
      }

      // Always show success to user - local save succeeded
      alert(`✅ ${steps[currentStep].title} completed successfully!`);
      
    } catch (error) {
      console.error('Failed to save step progress:', error);
      // Even if API fails, we've saved locally, so don't block the user
      alert(`⚠️  ${steps[currentStep].title} saved locally. Will sync when online.`);
    } finally {
      setIsProcessing(false);
    }
  };

  const getCurrentStepData = () => {
    switch (steps[currentStep].id) {
      case 'organization_setup':
        return { organization_profile: organizationProfile.basicInfo };
      case 'compliance_verification':
        return { compliance: organizationProfile.compliance };
      case 'erp_selection':
      case 'erp_configuration':
        return {
          erp_configuration: erpConfiguration,
          connection_id: createdConnectionId,
        };
      case 'data_mapping':
        return { mapping_rules: erpConfiguration.mappingRules };
      case 'compliance_setup':
        return { compliance_configuration: complianceConfig };
      case 'testing_validation':
        return { test_results: testResults };
      case 'production_deployment':
        return {
          production_checklist: productionChecklist,
          connection_id: createdConnectionId,
        };
      case 'training_handover':
        return {
          training_checklist: trainingChecklist,
          optional: true,
        };
      default:
        return {};
    }
  };

  const INFORMATION_REDIRECT_KEY = 'taxpoynt_connection_manager_org';

  const unwrapApiPayload = (raw: unknown): { payload: Record<string, any>; meta?: Record<string, any>; success?: boolean } => {
    if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
      const candidate = raw as Record<string, any>;
      const inner = candidate.data;
      if (inner && typeof inner === 'object' && !Array.isArray(inner)) {
        return { payload: inner as Record<string, any>, meta: candidate.meta, success: candidate.success };
      }
      return { payload: candidate, meta: candidate.meta, success: candidate.success };
    }
    return { payload: {} };
  };

  const ensureConnectionPersisted = useCallback(async (): Promise<string | null> => {
    if (createdConnectionId) {
      return createdConnectionId;
    }

    const systemType = (erpConfiguration.systemType || '').trim();
    if (!systemType) {
      throw new Error('Select an ERP system before completing the configuration.');
    }

    if (!resolvedOrganizationId) {
      throw new Error('Organization context not detected. Please sign in again.');
    }

    const baseUrl = erpConfiguration.credentials.server?.trim();
    const database = erpConfiguration.credentials.database?.trim();
    const username = erpConfiguration.credentials.username?.trim();

    if (!baseUrl) {
      throw new Error('Provide the ERP server URL before continuing.');
    }
    if (!database) {
      throw new Error('Provide the ERP database or company identifier.');
    }
    if (!username) {
      throw new Error('Provide the integration username.');
    }

    const apiKey = erpConfiguration.credentials.apiKey?.trim();
    if (!apiKey) {
      throw new Error('Provide the ERP API key or integration token before continuing.');
    }

    const connectionName = `${systemType.toUpperCase()} ERP Connection`;

    const connectionConfig: Record<string, unknown> = {
      type: systemType,
      auth_method: 'api_key',
      url: baseUrl,
      database,
      username,
      api_key: apiKey,
      environment: 'sandbox',
      auto_sync: Boolean(erpConfiguration.dataSources?.invoices),
      data_sources: erpConfiguration.dataSources,
    };

    if (erpConfiguration.credentials.oauthToken) {
      connectionConfig.oauth_token = erpConfiguration.credentials.oauthToken;
    }

    if (erpConfiguration.version) {
      connectionConfig.version = erpConfiguration.version;
    }

    setConnectionCreationStatus('saving');
    setConnectionCreationMessage('Creating ERP connection…');

    try {
      const payload = {
        erp_system: systemType,
        organization_id: resolvedOrganizationId,
        connection_name: connectionName,
        environment: 'sandbox',
        connection_config: connectionConfig,
      };

      const response = await apiClient.post<Record<string, any>>('/si/business/erp/connections', payload);
      const { payload: responseData, meta: responseMeta } = unwrapApiPayload(response);
      const nestedConnection = (responseData?.connection ?? {}) as Record<string, any>;
      const metaFromResponse = (responseMeta ?? {}) as Record<string, any>;

      const newConnectionIdExplicit =
        pickString(responseData?.connection_id) ||
        pickString(responseData?.id) ||
        pickString(responseData?.connectionId) ||
        pickString(metaFromResponse?.connection_id);

      const newConnectionId =
        newConnectionIdExplicit ||
        pickString(nestedConnection?.connection_id) ||
        pickString((nestedConnection as any)?.connectionId) ||
        pickString(nestedConnection?.id) ||
        null;

      connectionsFetchRef.current = false;
      const updatedConnections = await fetchErpConnections();

      if (newConnectionId) {
        setCreatedConnectionId(newConnectionId);
        setConnectionCreationStatus('success');
        setConnectionCreationMessage('ERP connection saved. Diagnostics are ready when you reach Testing.');
        if (typeof window !== 'undefined') {
          window.sessionStorage.setItem(INFORMATION_REDIRECT_KEY, resolvedOrganizationId);
        }
        return newConnectionId;
      }

      const fallbackConnection = updatedConnections.find((connection) => {
        const configObj = connection.connection_config as Record<string, unknown> | undefined;
        const configUrl = pickString(configObj?.['url']);
        const configDatabase = pickString(configObj?.['database']);
        const compareSystem = (connection.erp_system || '').toLowerCase();
        return (
          compareSystem === systemType &&
          configUrl?.toLowerCase() === baseUrl.toLowerCase() &&
          configDatabase?.toLowerCase() === database.toLowerCase()
        );
      });

      if (fallbackConnection?.connection_id) {
        setCreatedConnectionId(fallbackConnection.connection_id);
        setConnectionCreationStatus('success');
        setConnectionCreationMessage('ERP connection saved. Diagnostics are ready when you reach Testing.');
        if (typeof window !== 'undefined') {
          window.sessionStorage.setItem(INFORMATION_REDIRECT_KEY, resolvedOrganizationId);
        }
        return fallbackConnection.connection_id;
      }

      setConnectionCreationStatus('success');
      setConnectionCreationMessage(
        'Connection saved. Refresh the list or open the connection manager to view the record.'
      );
      return null;
    } catch (error) {
      const message = extractErrorMessage(
        error,
        'Unable to create ERP connection. Please verify your configuration and try again.'
      );
      setConnectionCreationStatus('error');
      setConnectionCreationMessage(message);
      throw error instanceof Error ? error : new Error(message);
    }
  }, [
    createdConnectionId,
    erpConfiguration,
    fetchErpConnections,
    resolvedOrganizationId
  ]);

  const handleResetOnboarding = useCallback(async () => {
    if (isResetting) {
      return;
    }

    const confirmed = typeof window === 'undefined'
      ? true
      : window.confirm('Reset the SI onboarding wizard? All saved progress will be cleared.');

    if (!confirmed) {
      return;
    }

    setIsResetting(true);
    setResetStatusMessage('Resetting onboarding progress…');

    try {
      if (authService.isAuthenticated()) {
        await onboardingApi.resetOnboardingState();
        setRemoteMetadata({});
      }

      erpFormPersistence.clearFormData();
      CrossFormDataManager.clearSharedData();
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('taxpoynt_erp_onboarding_step_completed');
      }

      connectionsFetchRef.current = false;
      mappingFetchRef.current = false;

      setSteps(createDefaultSteps());
      setCurrentStep(initialStepIndex ?? 0);
      setResolvedOrganizationId(organizationId ?? null);
      setOrganizationProfile(createDefaultOrganizationProfile());
      setErpConfiguration(createDefaultErpConfiguration());
      setComplianceConfig({ ...DEFAULT_COMPLIANCE_CONFIG });
      setProductionChecklist({ ...DEFAULT_PRODUCTION_CHECKLIST });
      setTrainingChecklist({ ...DEFAULT_TRAINING_CHECKLIST });
      setConnections([]);
      setConnectionsError(null);
      setConnectionsLoading(false);
      setConnectionTestStatus('idle');
      setConnectionTestMessage('');
      setDataValidationStatus('idle');
      setDataValidationMessage('');
      setSavedMapping([]);
      setSavedMappingStatus('idle');
      setCreatedConnectionId(null);
      setConnectionCreationStatus('idle');
      setConnectionCreationMessage('');
      setTestResults(null);
      setResetStatusMessage('Onboarding progress reset. You can start again from the beginning.');
    } catch (error) {
      const message = extractErrorMessage(error, 'Unexpected error while resetting onboarding.');
      setResetStatusMessage(message);
    } finally {
      setIsResetting(false);
    }
  }, [
    erpFormPersistence,
    initialStepIndex,
    isResetting,
    organizationId
  ]);


  const handleRunConnectionTest = useCallback(async () => {
    setConnectionTestStatus('running');
    setConnectionTestMessage('Running connection diagnostics…');

    try {
      let activeConnections = connections;
      if (!activeConnections.length) {
        activeConnections = await fetchErpConnections();
      }

      if (!activeConnections.length) {
        throw new Error('No ERP connections found. Configure a connection before running tests.');
      }

      const connectionIds = activeConnections
        .map(connection => connection.connection_id)
        .filter((id): id is string => Boolean(id));

      if (!connectionIds.length) {
        throw new Error('Connections are missing identifiers. Refresh the integration list and try again.');
      }

      const response = await apiClient.post<BulkConnectionTestResponse>(
        '/si/business/erp/bulk/test-connections',
        { connection_ids: connectionIds }
      );

      const summary = response?.data?.summary ?? {};
      const total = typeof summary?.total === 'number' ? summary.total : connectionIds.length;
      const successful = typeof summary?.successful === 'number' ? summary.successful : 0;
      const failed = typeof summary?.failed === 'number' ? summary.failed : Math.max(total - successful, 0);
      const warnings = typeof summary?.warnings === 'number' ? summary.warnings : 0;

      setTestResults(prev => ({
        ...prev,
        connectionSummary: summary,
        connectionResults: response?.data?.results ?? [],
        connectionValidatedAt: new Date().toISOString(),
      }));

      if (response?.success !== false && failed === 0) {
        const message =
          response?.message ||
          `Tested ${total} connection${total === 1 ? '' : 's'} successfully.`;
        setConnectionTestStatus('success');
        setConnectionTestMessage(message);
      } else {
        const message =
          response?.detail ||
          response?.message ||
          `Tested ${total} connection${total === 1 ? '' : 's'} (${successful} passed${failed ? `, ${failed} failed` : ''}${warnings ? `, ${warnings} warning${warnings === 1 ? '' : 's'}` : ''}).`;
        setConnectionTestStatus(failed === 0 ? 'success' : 'error');
        setConnectionTestMessage(message);
      }

      await fetchErpConnections();
    } catch (error) {
      const message = extractErrorMessage(
        error,
        'Unable to run connection tests. Ensure at least one ERP connection exists.'
      );
      setConnectionTestStatus('error');
      setConnectionTestMessage(message);
    }
  }, [connections, fetchErpConnections]);

  const handleValidateSampleData = useCallback(async () => {
    if (!erpConfiguration.systemType) {
      setDataValidationStatus('error');
      setDataValidationMessage('Select an ERP system before running validation.');
      return;
    }

    setDataValidationStatus('running');
    setDataValidationMessage('Validating mapping rules against FIRS schema…');

    try {
      let mappingRules = savedMapping;
      if (!mappingRules.length && erpConfiguration.mappingRules.length) {
        mappingRules = erpConfiguration.mappingRules;
      }
      if (!mappingRules.length) {
        mappingRules = await fetchSavedMapping();
      }

      if (!mappingRules.length) {
        setDataValidationStatus('error');
        setDataValidationMessage('No saved mapping rules found. Complete the Data Mapping step first.');
        return;
      }

      const response = await apiClient.post<ValidateMappingResponse>(
        '/si/business/erp/data-mapping/validate',
        {
          system_id: erpConfiguration.systemType,
          organization_id: resolvedOrganizationId,
          mapping_rules: mappingRules,
        }
      );

      const preview = response?.preview_data;
      const missing = preview?.missing_required ?? [];
      const errors = response?.errors ?? {};

      setTestResults(prev => ({
        ...prev,
        mappingPreview: preview,
        mappingValidatedAt: preview?.validated_at ?? new Date().toISOString(),
        mappingErrors: errors,
      }));

      if (response?.success === false || missing.length > 0) {
        const errorMessage =
          Object.values(errors)
            .flat()
            .map(pickString)
            .find(Boolean) ||
          (missing.length
            ? `Validation completed with ${missing.length} missing required field${missing.length === 1 ? '' : 's'}: ${missing.join(', ')}.`
            : response?.message || response?.detail);
        setDataValidationStatus('error');
        setDataValidationMessage(
          errorMessage ||
            'Validation reported issues. Review your mapping configuration.'
        );
      } else {
        const message =
          response?.message ||
          'Validation successful. All required fields are mapped.';
        setDataValidationStatus('success');
        setDataValidationMessage(message);
      }
    } catch (error) {
      const message = extractErrorMessage(
        error,
        'Unable to validate mapping. Please retry after refreshing the page.'
      );
      setDataValidationStatus('error');
      setDataValidationMessage(message);
    }
  }, [
    erpConfiguration.mappingRules,
    erpConfiguration.systemType,
    fetchSavedMapping,
    resolvedOrganizationId,
    savedMapping
  ]);

  useEffect(() => {
    if (connectionTestStatus === 'success' && dataValidationStatus === 'success') {
      markStepCompletedExternally('testing_validation', 'compliance_setup');
    }
  }, [connectionTestStatus, dataValidationStatus, markStepCompletedExternally]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    try {
      setIsProcessing(true);

      const completedIds = onboardingSteps.map(step => step.id);
      const finalStepId = onboardingSteps[onboardingSteps.length - 1]?.id ?? completedIds[completedIds.length - 1];

      setSteps(prev =>
        prev.map(step => ({
          ...step,
          completed: true
        }))
      );

      erpFormPersistence.saveFormData({
        organizationProfile,
        erpConfiguration,
        currentStep,
        createdConnectionId,
        complianceConfig,
        productionChecklist,
        trainingChecklist,
        stepsCompleted: completedIds,
        timestamp: Date.now()
      });

      const metadataAfterSync =
        (await syncErpProgress(finalStepId, completedIds, {
          completion: true,
          completed_at: new Date().toISOString()
        })) || deepClone(remoteMetadata);

      const completionMetadata = {
        ...metadataAfterSync,
        erp_onboarding: {
          ...(metadataAfterSync?.erp_onboarding || {}),
          status: 'completed',
          completed_steps: completedIds,
          completed_at: new Date().toISOString()
        }
      };

      const finalState = await onboardingApi.completeOnboarding(completionMetadata);
      const updatedMetadata = isRecord(finalState.metadata) ? finalState.metadata : {};
      setRemoteMetadata(updatedMetadata);

      erpFormPersistence.clearFormData();
      console.log('✅ ERP onboarding completed - form data cleared');

      alert('🎉 ERP onboarding completed successfully!');
      if (onComplete && organizationId) {
        onComplete(organizationId);
      }
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      alert('❌ Failed to complete onboarding');
    } finally {
      setIsProcessing(false);
    }
  };

  const formatTimestamp = (iso?: string) => {
    if (!iso) {
      return '';
    }

    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) {
      return iso;
    }

    return date.toLocaleString();
  };

  const resolveConnectionStatusClass = (status?: string | null) => {
    if (!status) {
      return 'bg-gray-100 text-gray-600';
    }

    const normalized = status.toLowerCase();
    if (['active', 'connected', 'healthy', 'success', 'online'].includes(normalized)) {
      return 'bg-green-100 text-green-700';
    }

    if (['warning', 'degraded', 'pending'].includes(normalized)) {
      return 'bg-yellow-100 text-yellow-700';
    }

    if (['failed', 'error', 'inactive', 'disconnected', 'offline'].includes(normalized)) {
      return 'bg-red-100 text-red-600';
    }

    return 'bg-gray-100 text-gray-600';
  };

  const renderOrganizationSetup = () => (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-900 mb-2">🏢 Organization Registration</h3>
        <p className="text-blue-800 text-sm">
          Register the organization and verify business credentials for Nigerian compliance.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Company Name *
          </label>
          <input
            type="text"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.name}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, name: e.target.value }
            }))}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            RC Number (CAC) *
          </label>
          <input
            type="text"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.rcNumber}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, rcNumber: e.target.value }
            }))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            TIN Number *
          </label>
          <input
            type="text"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.tinNumber}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, tinNumber: e.target.value }
            }))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Business Email *
          </label>
          <input
            type="email"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.email}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, email: e.target.value }
            }))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Industry Sector *
          </label>
          <select
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.industry}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, industry: e.target.value }
            }))}
          >
            <option value="">Select industry</option>
            <option value="manufacturing">Manufacturing</option>
            <option value="retail">Retail & E-commerce</option>
            <option value="services">Professional Services</option>
            <option value="technology">Technology</option>
            <option value="healthcare">Healthcare</option>
            <option value="education">Education</option>
            <option value="hospitality">Hospitality</option>
            <option value="construction">Construction</option>
            <option value="agriculture">Agriculture</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Company Size *
          </label>
          <select
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.size}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, size: e.target.value }
            }))}
          >
            <option value="">Select company size</option>
            <option value="startup">Startup (1-10 employees)</option>
            <option value="small">Small (11-50 employees)</option>
            <option value="medium">Medium (51-200 employees)</option>
            <option value="large">Large (201-1000 employees)</option>
            <option value="enterprise">Enterprise (1000+ employees)</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Business Address *
        </label>
        <textarea
          required
          rows={3}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          value={organizationProfile.basicInfo.address}
          onChange={(e) => setOrganizationProfile(prev => ({
            ...prev,
            basicInfo: { ...prev.basicInfo, address: e.target.value }
          }))}
        />
      </div>
    </div>
  );

  const renderComplianceVerification = () => (
    <div className="space-y-6">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-green-900 mb-2">🇳🇬 Nigerian Compliance Verification</h3>
        <p className="text-green-800 text-sm">
          Verify FIRS registration, VAT status, and other Nigerian regulatory requirements.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="border rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">FIRS Registration</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={organizationProfile.compliance.firsRegistered}
                onChange={(e) => setOrganizationProfile(prev => ({
                  ...prev,
                  compliance: { ...prev.compliance, firsRegistered: e.target.checked }
                }))}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-gray-700">Organization is registered with FIRS</span>
            </label>
            
            {organizationProfile.compliance.firsRegistered && (
              <input
                type="text"
                placeholder="FIRS ID"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={organizationProfile.compliance.firsId || ''}
                onChange={(e) => setOrganizationProfile(prev => ({
                  ...prev,
                  compliance: { ...prev.compliance, firsId: e.target.value }
                }))}
              />
            )}
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">VAT Registration</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={organizationProfile.compliance.vatRegistered}
                onChange={(e) => setOrganizationProfile(prev => ({
                  ...prev,
                  compliance: { ...prev.compliance, vatRegistered: e.target.checked }
                }))}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-gray-700">Organization is VAT registered</span>
            </label>
            
            {organizationProfile.compliance.vatRegistered && (
              <input
                type="text"
                placeholder="VAT Number"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={organizationProfile.compliance.vatNumber || ''}
                onChange={(e) => setOrganizationProfile(prev => ({
                  ...prev,
                  compliance: { ...prev.compliance, vatNumber: e.target.value }
                }))}
              />
            )}
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">CBN Compliance</h4>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={organizationProfile.compliance.cbnCompliant}
              onChange={(e) => setOrganizationProfile(prev => ({
                ...prev,
                compliance: { ...prev.compliance, cbnCompliant: e.target.checked }
              }))}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="ml-2 text-gray-700">Compliant with CBN regulations</span>
          </label>
        </div>

        <div className="border rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Invoice Volume</h4>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.businessSystems.invoiceVolume}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              businessSystems: { ...prev.businessSystems, invoiceVolume: e.target.value }
            }))}
          >
            <option value="">Select monthly invoice volume</option>
            <option value="0-50">0-50 invoices/month</option>
            <option value="51-200">51-200 invoices/month</option>
            <option value="201-500">201-500 invoices/month</option>
            <option value="501-1000">501-1,000 invoices/month</option>
            <option value="1000+">1,000+ invoices/month</option>
          </select>
        </div>
      </div>
    </div>
  );

const renderERPSelection = () => (
  <div className="space-y-6">
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-purple-900 mb-2">🔧 ERP System Selection</h3>
        <p className="text-purple-800 text-sm">
          Choose the primary ERP system for integration with TaxPoynt e-invoicing.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { id: 'sap', name: 'SAP', icon: '🏢', description: 'SAP ERP, S/4HANA, Business One' },
          { id: 'oracle', name: 'Oracle ERP', icon: '🔴', description: 'Oracle ERP Cloud, E-Business Suite' },
          { id: 'dynamics', name: 'Microsoft Dynamics', icon: '🔷', description: 'Dynamics 365, NAV, GP' },
          { id: 'netsuite', name: 'NetSuite', icon: '🌐', description: 'Oracle NetSuite ERP' },
          { id: 'odoo', name: 'Odoo', icon: '🟣', description: 'Odoo Community & Enterprise' },
          { id: 'custom', name: 'Custom ERP', icon: '⚙️', description: 'Custom or proprietary ERP system' }
        ].map(erp => (
          <div
            key={erp.id}
            className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
              erpConfiguration.systemType === erp.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setErpConfiguration(prev => ({ ...prev, systemType: erp.id }))}
          >
            <div className="text-center">
              <div className="text-3xl mb-2">{erp.icon}</div>
              <h4 className="font-semibold text-gray-900">{erp.name}</h4>
              <p className="text-sm text-gray-600 mt-1">{erp.description}</p>
            </div>
          </div>
        ))}
      </div>

      {erpConfiguration.systemType && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Selected: {erpConfiguration.systemType.toUpperCase()}</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                System Version
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., S/4HANA 2021"
                value={erpConfiguration.version || ''}
                onChange={(e) => setErpConfiguration(prev => ({ ...prev, version: e.target.value }))}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Implementation Status
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                <option value="">Select status</option>
                <option value="live">Live/Production</option>
                <option value="testing">Testing Phase</option>
                <option value="implementation">Under Implementation</option>
                <option value="planning">Planning Phase</option>
              </select>
            </div>
          </div>
        </div>
      )}
  </div>
);

  const renderERPConfiguration = () => (
    <div className="space-y-6">
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-indigo-900 mb-2">⚙️ ERP Configuration</h3>
        <p className="text-indigo-800 text-sm">
          Provide connection details for your primary ERP system. These settings are stored securely and power the
          automated integration workflow once onboarding is complete.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            ERP Version / Edition
          </label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={erpConfiguration.version || ''}
            onChange={(e) =>
              setErpConfiguration((prev) => ({
                ...prev,
                version: e.target.value,
              }))
            }
            placeholder="e.g. Odoo 16 Enterprise"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Server URL / Endpoint
          </label>
          <input
            type="url"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={erpConfiguration.credentials.server || ''}
            onChange={(e) =>
              setErpConfiguration((prev) => ({
                ...prev,
                credentials: { ...prev.credentials, server: e.target.value },
              }))
            }
            placeholder="https://erp.company.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Database / Company ID
          </label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={erpConfiguration.credentials.database || ''}
            onChange={(e) =>
              setErpConfiguration((prev) => ({
                ...prev,
                credentials: { ...prev.credentials, database: e.target.value },
              }))
            }
            placeholder="Internal database or tenant identifier"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Integration Username
          </label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={erpConfiguration.credentials.username || ''}
            onChange={(e) =>
              setErpConfiguration((prev) => ({
                ...prev,
                credentials: { ...prev.credentials, username: e.target.value },
              }))
            }
            placeholder="svc_taxpoynt"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            API Key / Password
          </label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={erpConfiguration.credentials.apiKey || ''}
            onChange={(e) =>
              setErpConfiguration((prev) => ({
                ...prev,
                credentials: { ...prev.credentials, apiKey: e.target.value },
              }))
            }
            placeholder="Secure API key or password"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            OAuth Token (optional)
          </label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={erpConfiguration.credentials.oauthToken || ''}
            onChange={(e) =>
              setErpConfiguration((prev) => ({
                ...prev,
                credentials: { ...prev.credentials, oauthToken: e.target.value },
              }))
            }
            placeholder="Paste OAuth access token if required"
          />
        </div>
      </div>

      <div className="border rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3">Data Sources to Synchronize</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {Object.entries(erpConfiguration.dataSources).map(([key, value]) => (
            <label key={key} className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={value}
                onChange={(e) =>
                  setErpConfiguration((prev) => ({
                    ...prev,
                    dataSources: { ...prev.dataSources, [key]: e.target.checked },
                  }))
                }
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="capitalize text-gray-700">{key.replace(/_/g, ' ')}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
        <p className="mb-2">
          Need to reference connector specifics? Review the{' '}
          <a
            href="https://docs.taxpoynt.com/integrations/erp"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:underline"
          >
            ERP integration checklist
          </a>{' '}
          to confirm required scopes and field mappings.
        </p>
        <p>
          Credentials are encrypted before transmission. Only provide service accounts with the minimum permissions
          required for invoice synchronization.
        </p>
      </div>

      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
        <p>
          When you mark this step complete we will register your {erpConfiguration.systemType?.toUpperCase() || 'ERP'}
          {' '}connection in the integration gateway using the details above.
        </p>
        {connectionCreationStatus === 'saving' && (
          <p className="mt-2 text-indigo-600">{connectionCreationMessage || 'Creating ERP connection…'}</p>
        )}
        {connectionCreationStatus === 'success' && (
          <p className="mt-2 text-green-600">
            {connectionCreationMessage || 'ERP connection saved. Diagnostics will pick it up automatically.'}
            {createdConnectionId && (
              <span className="block text-xs text-green-700">Connection ID: {createdConnectionId}</span>
            )}
          </p>
        )}
        {connectionCreationStatus === 'error' && (
          <p className="mt-2 text-red-600">{connectionCreationMessage}</p>
        )}
        <div className="mt-3 flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
          if (typeof window !== 'undefined' && resolvedOrganizationId) {
            window.sessionStorage.setItem(INFORMATION_REDIRECT_KEY, resolvedOrganizationId);
          }
          const targetUrl = resolvedOrganizationId
            ? `/dashboard/si/business-systems?organization_id=${encodeURIComponent(resolvedOrganizationId)}`
            : '/dashboard/si/business-systems';
          router.push(targetUrl);
        }}
      >
        Open connection manager
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              connectionsFetchRef.current = false;
              void fetchErpConnections();
            }}
            loading={connectionsLoading}
            disabled={connectionsLoading}
          >
            Refresh list
          </Button>
        </div>
      </div>
    </div>
  );

  const renderComplianceSetup = () => (
    <div className="space-y-6">
      <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-4">
        <h3 className="text-lg font-semibold text-green-900">🛡️ Compliance Configuration</h3>
        <p className="mt-1 text-sm text-green-800">
          Finalize your FIRS credentials, VAT parameters, and security controls before moving live. These settings apply
          across every submission routed through TaxPoynt.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">FIRS API Key *</label>
          <input
            type="password"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-500"
            value={complianceConfig.firsApiKey}
            onChange={(event) =>
              setComplianceConfig((prev) => ({
                ...prev,
                firsApiKey: event.target.value,
              }))
            }
            placeholder="Secure token for FIRS gateway"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Compliance contact email *</label>
          <input
            type="email"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-500"
            value={complianceConfig.complianceEmail}
            onChange={(event) =>
              setComplianceConfig((prev) => ({
                ...prev,
                complianceEmail: event.target.value,
              }))
            }
            placeholder="compliance@client.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">VAT mode</label>
          <select
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-500"
            value={complianceConfig.vatMode}
            onChange={(event) =>
              setComplianceConfig((prev) => ({
                ...prev,
                vatMode: event.target.value,
              }))
            }
          >
            <option value="standard">Standard VAT (7.5%)</option>
            <option value="zero_rated">Zero-rated / Exempt</option>
            <option value="custom">Custom rate</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">VAT rate (%)</label>
          <input
            type="number"
            step="0.1"
            min="0"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-500"
            value={complianceConfig.vatRate}
            onChange={(event) =>
              setComplianceConfig((prev) => ({
                ...prev,
                vatRate: event.target.value,
              }))
            }
            disabled={complianceConfig.vatMode !== 'custom'}
          />
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 p-4">
        <h4 className="text-sm font-semibold text-gray-900">Security & rate limits</h4>
        <div className="mt-3 space-y-2 text-sm text-gray-700">
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 text-green-600"
              checked={complianceConfig.enableRateLimiter}
              onChange={(event) =>
                setComplianceConfig((prev) => ({
                  ...prev,
                  enableRateLimiter: event.target.checked,
                }))
              }
            />
            <span>Enable FIRS-specific rate limiter</span>
          </label>
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 text-green-600"
              checked={complianceConfig.enableAuditTrail}
              onChange={(event) =>
                setComplianceConfig((prev) => ({
                  ...prev,
                  enableAuditTrail: event.target.checked,
                }))
              }
            />
            <span>Log compliance audit trail for every submission</span>
          </label>
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 text-green-600"
              checked={complianceConfig.requireSecureChannels}
              onChange={(event) =>
                setComplianceConfig((prev) => ({
                  ...prev,
                  requireSecureChannels: event.target.checked,
                }))
              }
            />
            <span>Enforce secure channels (TLS ≥ 1.2, signed payloads)</span>
          </label>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Compliance notes</label>
        <textarea
          rows={4}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-500"
          value={complianceConfig.notes}
          onChange={(event) =>
            setComplianceConfig((prev) => ({
              ...prev,
              notes: event.target.value,
            }))
          }
          placeholder="Document any clarifications from FIRS or client-specific exemptions."
        />
      </div>

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            if (typeof window !== 'undefined') {
              window.open('https://docs.taxpoynt.com/compliance/firs', '_blank', 'noopener');
            }
          }}
        >
          Open FIRS checklist
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            if (typeof window !== 'undefined') {
              window.open('/dashboard/si/compliance', '_blank', 'noopener');
            }
          }}
        >
          Review compliance dashboard
        </Button>
      </div>
    </div>
  );

  const renderProductionDeployment = () => (
    <div className="space-y-6">
      <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-4">
        <h3 className="text-lg font-semibold text-blue-900">🚀 Activate production</h3>
        <p className="mt-1 text-sm text-blue-800">
          Confirm the final go-live actions. We’ll update onboarding state and remind you to monitor the first live
          submissions.
        </p>
      </div>

      <div className="rounded-lg border border-gray-200 p-4 text-sm">
        <div className="space-y-3 text-gray-700">
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 text-blue-600"
              checked={productionChecklist.promoteConnection}
              onChange={(event) =>
                setProductionChecklist((prev) => ({
                  ...prev,
                  promoteConnection: event.target.checked,
                }))
              }
            />
            <span>Promote sandbox connection to production gateway</span>
          </label>
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 text-blue-600"
              checked={productionChecklist.enableLiveSubmissions}
              onChange={(event) =>
                setProductionChecklist((prev) => ({
                  ...prev,
                  enableLiveSubmissions: event.target.checked,
                }))
              }
            />
            <span>Enable live submissions and confirm invoice numbering aligns with FIRS requirements</span>
          </label>
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 text-blue-600"
              checked={productionChecklist.notifyFinanceTeam}
              onChange={(event) =>
                setProductionChecklist((prev) => ({
                  ...prev,
                  notifyFinanceTeam: event.target.checked,
                }))
              }
            />
            <span>Notify client finance / tax operations about the cutover date</span>
          </label>
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 text-blue-600"
              checked={productionChecklist.monitoringEnabled}
              onChange={(event) =>
                setProductionChecklist((prev) => ({
                  ...prev,
                  monitoringEnabled: event.target.checked,
                }))
              }
            />
            <span>Enable monitoring & alerts for FIRS submission failures or latency</span>
          </label>
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 text-blue-600"
              checked={productionChecklist.rollbackPlanDocumented}
              onChange={(event) =>
                setProductionChecklist((prev) => ({
                  ...prev,
                  rollbackPlanDocumented: event.target.checked,
                }))
              }
            />
            <span>Document rollback plan and escalation path</span>
          </label>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            if (typeof window !== 'undefined') {
              window.open('/dashboard/si/monitoring', '_blank', 'noopener');
            }
          }}
        >
          Open monitoring dashboard
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            if (typeof window !== 'undefined') {
              window.open('/dashboard/si/webhooks', '_blank', 'noopener');
            }
          }}
        >
          Review webhook status
        </Button>
      </div>
    </div>
  );

  const renderTrainingHandover = () => (
    <div className="space-y-6">
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-4">
        <h3 className="text-lg font-semibold text-amber-900">🤝 Training & handover (optional)</h3>
        <p className="mt-1 text-sm text-amber-800">
          Capture the client-facing tasks so you can close the engagement smoothly. This step is optional—finish whenever
          your customer team is ready.
        </p>
      </div>

      <div className="space-y-3 rounded-lg border border-gray-200 p-4 text-sm text-gray-700">
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 text-amber-600"
            checked={trainingChecklist.trainingScheduled}
            onChange={(event) =>
              setTrainingChecklist((prev) => ({
                ...prev,
                trainingScheduled: event.target.checked,
              }))
            }
          />
          <span>Client training workshop scheduled</span>
        </label>
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 text-amber-600"
            checked={trainingChecklist.supportDocsShared}
            onChange={(event) =>
              setTrainingChecklist((prev) => ({
                ...prev,
                supportDocsShared: event.target.checked,
              }))
            }
          />
          <span>Support documents / runbooks shared with client teams</span>
        </label>
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 text-amber-600"
            checked={trainingChecklist.successMetricsDefined}
            onChange={(event) =>
              setTrainingChecklist((prev) => ({
                ...prev,
                successMetricsDefined: event.target.checked,
              }))
            }
          />
          <span>Success metrics / KPIs agreed with client</span>
        </label>
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 text-amber-600"
            checked={trainingChecklist.postGoLiveSupportAssigned}
            onChange={(event) =>
              setTrainingChecklist((prev) => ({
                ...prev,
                postGoLiveSupportAssigned: event.target.checked,
              }))
            }
          />
          <span>Post go-live support owner assigned</span>
        </label>
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 text-amber-600"
            checked={trainingChecklist.customerSignOffReceived}
            onChange={(event) =>
              setTrainingChecklist((prev) => ({
                ...prev,
                customerSignOffReceived: event.target.checked,
              }))
            }
          />
          <span>Customer sign-off / acceptance recorded</span>
        </label>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            if (typeof window !== 'undefined') {
              window.open('/dashboard/si/resources/training-pack', '_blank', 'noopener');
            }
          }}
        >
          Download training pack
        </Button>
        <span className="text-xs text-gray-500">
          Optional step – you can move forward once activation is complete.
        </span>
      </div>
    </div>
  );

  const renderStepContent = () => {
    switch (steps[currentStep].id) {
      case 'organization_setup':
        return renderOrganizationSetup();
      case 'compliance_verification':
        return renderComplianceVerification();
      case 'erp_selection':
        return renderERPSelection();
      case 'erp_configuration':
        return renderERPConfiguration();
      case 'data_mapping':
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🔄</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Data Mapping</h3>
            <p className="text-gray-600 mb-6">Configure data field mapping for FIRS compliance</p>
            <Button
              onClick={() => {
                const targetSystem = erpConfiguration.systemType;
                const mappingUrl = targetSystem
                  ? `/onboarding/si/data-mapping?system=${targetSystem}`
                  : '/onboarding/si/data-mapping';
                router.push(mappingUrl);
              }}
            >
              Open Data Mapping Tool
            </Button>
          </div>
        );
      case 'compliance_setup':
        return renderComplianceSetup();
      case 'testing_validation': {
        const connectionSummary = testResults?.connectionSummary ?? {};
        const connectionValidatedAt = (testResults?.connectionValidatedAt as string | undefined) ?? undefined;
        const mappingPreview = testResults?.mappingPreview as
          | {
              validated_targets?: string[];
              missing_required?: string[];
              mapped_fields?: Record<string, unknown>;
            }
          | undefined;
        const mappingValidatedAt = (testResults?.mappingValidatedAt as string | undefined) ?? undefined;
        const displayedConnections = connections.slice(0, 3);

        return (
          <div className="space-y-6">
            <div className="rounded-lg border border-purple-200 bg-purple-50 px-4 py-3 text-sm text-purple-900">
              <p className="font-medium">Run automated checks before moving to compliance configuration.</p>
              <p className="mt-1 text-purple-800">
                Use the tools below to verify your ERP connection is reachable and that your mapping produces a
                FIRS-ready payload.
              </p>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-lg border border-gray-200 p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">Connection diagnostics</h4>
                    <p className="text-sm text-gray-600">
                      We’ll ping your configured ERP connectors and report the gateway status.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        connectionsFetchRef.current = false;
                        void fetchErpConnections();
                      }}
                      loading={connectionsLoading}
                      disabled={connectionsLoading}
                    >
                      Refresh list
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        router.push('/dashboard/si/business-systems');
                      }}
                    >
                      Open connection manager
                    </Button>
                  </div>
                </div>

                {connectionsError ? (
                  <p
                    className={
                      connectionsError.startsWith('No ERP connections')
                        ? 'mt-4 text-sm text-gray-600'
                        : 'mt-4 text-sm text-red-600'
                    }
                  >
                    {connectionsError}
                  </p>
                ) : displayedConnections.length ? (
                  <ul className="mt-4 space-y-3">
                    {displayedConnections.map((connection) => (
                      <li key={connection.connection_id} className="rounded-md border border-gray-200 p-3">
                        <div className="flex items-center justify-between gap-2">
                          <div className="text-sm font-semibold text-gray-900">
                            {connection.connection_name || connection.erp_system?.toUpperCase() || 'ERP Connection'}
                          </div>
                          <span
                            className={`rounded-full px-2 py-1 text-xs font-semibold ${resolveConnectionStatusClass(
                              connection.status
                            )}`}
                          >
                            {(connection.status || 'unknown').toUpperCase()}
                          </span>
                        </div>
                        <p className="mt-2 text-xs text-gray-500">
                          {connection.erp_system ? `System: ${connection.erp_system.toUpperCase()}` : 'System not specified'}
                          {connection.environment ? ` • Environment: ${connection.environment}` : ''}
                          {connection.last_status_at ? ` • Last status: ${formatTimestamp(connection.last_status_at)}` : ''}
                        </p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-4 text-sm text-gray-600">
                    No ERP connections detected yet. Configure a connection in the previous steps to enable automated
                    testing.
                  </p>
                )}

                <div className="mt-4 space-y-2">
                  <Button
                    onClick={handleRunConnectionTest}
                    loading={connectionTestStatus === 'running'}
                    disabled={connectionsLoading || connectionTestStatus === 'running'}
                  >
                    Run Connection Test
                  </Button>
                  {connectionTestMessage && (
                    <p
                      className={`text-sm ${
                        connectionTestStatus === 'success'
                          ? 'text-green-600'
                          : connectionTestStatus === 'error'
                          ? 'text-red-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {connectionTestMessage}
                    </p>
                  )}
                </div>

                {createdConnectionId && (
                  <p className="mt-2 text-xs text-gray-500">
                    Primary connection ID: {createdConnectionId}
                  </p>
                )}

                {Object.keys(connectionSummary).length > 0 && (
                  <div className="mt-4 rounded-md bg-gray-50 p-3 text-sm text-gray-700">
                    <div className="font-medium text-gray-900">Last diagnostics</div>
                    <div className="mt-1 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
                      <div>Total: {connectionSummary.total ?? '-'}</div>
                      <div>Successful: {connectionSummary.successful ?? '-'}</div>
                      {connectionSummary.failed !== undefined && <div>Failed: {connectionSummary.failed}</div>}
                      {connectionSummary.warnings !== undefined && <div>Warnings: {connectionSummary.warnings}</div>}
                    </div>
                    {connectionValidatedAt && (
                      <div className="mt-2 text-xs text-gray-500">Run on {formatTimestamp(connectionValidatedAt)}</div>
                    )}
                  </div>
                )}
              </div>

              <div className="rounded-lg border border-gray-200 p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">Data validation</h4>
                    <p className="text-sm text-gray-600">
                      We reuse your saved mapping to produce a FIRS-compliant payload preview.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const targetSystem = erpConfiguration.systemType;
                        const mappingUrl = targetSystem
                          ? `/onboarding/si/data-mapping?system=${targetSystem}`
                          : '/onboarding/si/data-mapping';
                        if (typeof window !== 'undefined') {
                          window.open(mappingUrl, '_blank', 'noopener');
                        }
                      }}
                    >
                      Open mapping tool
                    </Button>
                  </div>
                </div>

                {savedMappingStatus === 'loading' && (
                  <div className="mt-3 h-5 w-5 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
                )}

                {savedMappingStatus === 'missing' && (
                  <p className="mt-4 text-sm text-amber-600">
                    We could not find saved mapping rules for this organization. Complete the Data Mapping step and save
                    your configuration first.
                  </p>
                )}

                {savedMappingStatus === 'error' && (
                  <p className="mt-4 text-sm text-red-600">
                    Unable to load saved mapping from the server. Refresh the page or revisit the Data Mapping tool.
                  </p>
                )}

                <div className="mt-4 space-y-2">
                  <Button
                    variant="outline"
                    onClick={handleValidateSampleData}
                    loading={dataValidationStatus === 'running'}
                    disabled={dataValidationStatus === 'running'}
                  >
                    Validate Sample Data
                  </Button>
                  {dataValidationMessage && (
                    <p
                      className={`text-sm ${
                        dataValidationStatus === 'success'
                          ? 'text-green-600'
                          : dataValidationStatus === 'error'
                          ? 'text-red-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {dataValidationMessage}
                    </p>
                  )}
                </div>

                {mappingPreview && (
                  <div className="mt-4 rounded-md bg-gray-50 p-3 text-sm text-gray-700">
                    <div className="font-medium text-gray-900">Latest validation</div>
                    <div className="mt-1 text-xs text-gray-600">
                      Validated targets: {mappingPreview.validated_targets?.length ?? 0}
                      {mappingPreview.missing_required?.length
                        ? ` • Missing: ${mappingPreview.missing_required.join(', ')}`
                        : ' • All required fields mapped'}
                    </div>
                    {mappingValidatedAt && (
                      <div className="mt-2 text-xs text-gray-500">Run on {formatTimestamp(mappingValidatedAt)}</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
        }
      case 'production_deployment':
        return renderProductionDeployment();
      case 'training_handover':
        return renderTrainingHandover();
      default:
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⚠️</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">{steps[currentStep].title}</h3>
            <p className="text-gray-600">{steps[currentStep].description}</p>
          </div>
        );
    }
  };

  const currentStepData = steps[currentStep];
  const canProceed = currentStepData ? (currentStepData.completed || !currentStepData.required) : false;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">ERP Onboarding Workflow</h1>
              <p className="text-gray-600 mt-2">Complete organization setup and ERP integration</p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <div className="text-sm text-gray-500">
                Step {currentStep + 1} of {steps.length}
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleResetOnboarding}
                loading={isResetting}
                disabled={isResetting}
              >
                Reset onboarding
              </Button>
            </div>
          </div>
        </div>
      </div>

      {resetStatusMessage && (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {resetStatusMessage}
          </div>
        </div>
      )}

      {/* Progress Steps */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center overflow-x-auto pb-2">
            {steps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className={`flex items-center ${index <= currentStep ? 'text-blue-600' : 'text-gray-400'} whitespace-nowrap`}>
                  <div className={`
                    flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium flex-shrink-0
                    ${index <= currentStep ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}
                  `}>
                    {step.completed ? '✓' : index + 1}
                  </div>
                  <div className="ml-2">
                    <div className="text-sm font-medium">{step.title}</div>
                    <div className="text-xs text-gray-500">{step.estimatedDuration}</div>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div className={`h-1 w-8 mx-4 flex-shrink-0 ${index < currentStep ? 'bg-blue-600' : 'bg-gray-200'}`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg border p-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">{currentStepData?.title}</h2>
            <p className="text-gray-600">{currentStepData?.description}</p>
            <div className="text-sm text-gray-500 mt-1">
              Estimated time: {currentStepData?.estimatedDuration}
            </div>
          </div>

          {renderStepContent()}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t">
            <Button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              variant="outline"
            >
              Previous
            </Button>

            <div className="flex items-center space-x-4">
              {!currentStepData?.completed && (
                <Button
                  onClick={handleStepComplete}
                  disabled={isProcessing}
                  variant="outline"
                  loading={isProcessing}
                >
                  {currentStepData?.required === false ? 'Mark Complete (optional)' : 'Mark Complete'}
                </Button>
              )}
              
              <Button
                onClick={handleNext}
                disabled={!canProceed || isProcessing}
                loading={currentStep === steps.length - 1 && isProcessing}
              >
                {currentStep === steps.length - 1 ? 'Complete Onboarding' : 'Continue'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ERPOnboarding;
