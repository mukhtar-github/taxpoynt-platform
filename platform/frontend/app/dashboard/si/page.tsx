'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { authService, type User } from '../../../shared_components/services/auth';
import { onboardingApi } from '../../../shared_components/services/onboardingApi';
import { EnhancedSIInterface } from '../../../si_interface/EnhancedSIInterface';
import { DashboardLayout } from '../../../shared_components/layouts/DashboardLayout';
import {
  SIDashboardHero,
  type HeroStatusChipConfig,
  type ManualPullConfig,
  type ManualPullStatus,
} from '../../../si_interface/components/SIDashboardHero';
import { SIDashboardSummary } from '../../../si_interface/components/SIDashboardSummary';
import { onboardingChecklistApi } from '../../../shared_components/services/onboardingChecklistApi';
import { TaxPoyntButton } from '../../../design_system';
import { useOnboardingAnalytics } from '../../../shared_components/analytics/OnboardingAnalytics';
import { useIdleTelemetry } from '../../../shared_components/hooks/useIdleTelemetry';
import {
  sanitizeBankingConnection,
  sanitizeErpConnection,
  type BankingConnectionState,
  type ERPConnectionState,
} from '../../../shared_components/onboarding/connectionState';
import { erpIntegrationApi } from '../../../shared_components/services/erpIntegrationApi';
import siBankingApi from '../../../shared_components/services/siBankingApi';

const HERO_STORAGE_KEY = 'si_dashboard_intro_dismissed_v1';

const defaultBankingChip: HeroStatusChipConfig = {
  label: 'Bank feeds',
  helper: 'Connect Mono to unlock automations',
  tone: 'muted',
};

const defaultErpChip: HeroStatusChipConfig = {
  label: 'ERP adapters',
  helper: 'Connect Odoo or another ERP to start pulling invoices',
  tone: 'muted',
};

const describeBankingChip = (state: BankingConnectionState): HeroStatusChipConfig => {
  switch (state.status) {
    case 'connected':
      return {
        label: 'Bank feeds',
        helper: state.bankName ? `Connected to ${state.bankName}` : 'Connected via Mono',
        tone: 'success',
      };
    case 'demo':
      return {
        label: 'Bank feeds',
        helper: 'Demo feed active',
        tone: 'demo',
      };
    case 'link_created':
      return {
        label: 'Bank feeds',
        helper: 'Link generated – launch the Mono widget',
        tone: 'info',
      };
    case 'awaiting_consent':
      return {
        label: 'Bank feeds',
        helper: 'Awaiting bank confirmation',
        tone: 'warning',
      };
    case 'error':
      return {
        label: 'Bank feeds',
        helper: state.lastMessage ?? 'Action required before syncing',
        tone: 'danger',
      };
    case 'skipped':
      return {
        label: 'Bank feeds',
        helper: 'Skipped during onboarding',
        tone: 'muted',
      };
    default:
      return defaultBankingChip;
  }
};

const describeErpChip = (state: ERPConnectionState): HeroStatusChipConfig => {
  switch (state.status) {
    case 'connected':
      return {
        label: 'ERP adapters',
        helper: state.connectionName ? `Connected to ${state.connectionName}` : 'ERP connected',
        tone: 'success',
      };
    case 'demo':
      return {
        label: 'ERP adapters',
        helper: 'Demo workspace configured',
        tone: 'demo',
      };
    case 'connecting':
      return {
        label: 'ERP adapters',
        helper: 'Connecting…',
        tone: 'info',
      };
    case 'error':
      return {
        label: 'ERP adapters',
        helper: state.lastMessage ?? 'Resolve connection issues',
        tone: 'danger',
      };
    default:
      return defaultErpChip;
  }
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

type ManualPullUiState = {
  status: ManualPullStatus;
  helper: string;
  disabledReason?: string;
};

type BankingSyncTarget = {
  accountDbId?: string;
  connectionId?: string;
  monoAccountId?: string;
  lastSyncedAt?: string | null;
};

const formatLastSyncHelper = (iso?: string): string => {
  if (!iso) {
    return '';
  }
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) {
    return '';
  }
  return ` · Last sync ${parsed.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })} ${parsed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
};

const describeBankingManualHelper = (
  state: BankingConnectionState,
  lastSyncedOverride?: string | null,
): { helper: string; disabledReason?: string } => {
  const lastSyncSuffix = formatLastSyncHelper(lastSyncedOverride ?? state.lastUpdated);
  switch (state.status) {
    case 'connected':
      return {
        helper: state.bankName ? `Linked to ${state.bankName}${lastSyncSuffix}` : `Connected via Mono${lastSyncSuffix}`,
      };
    case 'demo':
      return {
        helper: `Demo feed active${lastSyncSuffix}`,
      };
    case 'link_created':
      return {
        helper: 'Link generated—launch the Mono widget before running a pull.',
        disabledReason: 'Launch the Mono widget to finish setup.',
      };
    case 'awaiting_consent':
      return {
        helper: 'Consent required before pulling transactions.',
        disabledReason: 'Awaiting consent from the banking user.',
      };
    case 'error':
      return {
        helper: state.lastMessage ?? 'Resolve Mono errors before pulling.',
        disabledReason: 'Resolve Mono connection issues first.',
      };
    case 'skipped':
      return {
        helper: 'Connect Mono later to enable manual pulls.',
        disabledReason: 'Mono was skipped during onboarding.',
      };
    default:
      return {
        helper: 'Mono link required before syncing.',
        disabledReason: 'Mono connection not ready.',
      };
  }
};

export default function SIDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const analytics = useOnboardingAnalytics();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showHero, setShowHero] = useState(false);
  const [heroEvaluated, setHeroEvaluated] = useState(false);
  const [connectionChips, setConnectionChips] = useState({
    banking: defaultBankingChip,
    erp: defaultErpChip,
  });
  const [bankingConnectionState, setBankingConnectionState] = useState<BankingConnectionState | null>(null);
  const [checklistSummary, setChecklistSummary] = useState({
    remainingPhases: 0,
    nextPhaseTitle: undefined as string | undefined,
    lastUpdated: undefined as string | undefined,
  });
  const [checklistStatus, setChecklistStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [erpManualPullState, setErpManualPullState] = useState<ManualPullUiState>({
    status: 'idle',
    helper: 'Ready to trigger a sample batch pull.',
  });
  const [bankingManualPullState, setBankingManualPullState] = useState<ManualPullUiState>({
    status: 'idle',
    helper: 'Manual pull available once Mono is connected.',
    disabledReason: undefined,
  });
  const [bankingSyncTarget, setBankingSyncTarget] = useState<BankingSyncTarget>({});
  const heroFirstImpressionLogged = React.useRef(false);

  useEffect(() => {
    const currentUser = authService.getStoredUser();
    
    if (!currentUser || !authService.isAuthenticated()) {
      router.push('/auth/signin');
      return;
    }

    // Verify user has SI role
    if (currentUser.role !== 'system_integrator') {
      router.push('/dashboard'); // Redirect to appropriate dashboard
      return;
    }

    setUser(currentUser);
    setIsLoading(false);
  }, [router]);

  useEffect(() => {
    if (!user) {
      return;
    }
    if (typeof window === 'undefined') {
      setShowHero(false);
      setHeroEvaluated(true);
      return;
    }
    const introParam = searchParams.get('intro');
    const dismissed = window.localStorage.getItem(HERO_STORAGE_KEY) === 'true';
    const shouldShow = introParam === '1' || !dismissed;
    setShowHero(shouldShow);
    setHeroEvaluated(true);
    if (introParam === '1') {
      const params = new URLSearchParams(searchParams.toString());
      params.delete('intro');
      const nextQuery = params.toString();
      router.replace(`/dashboard/si${nextQuery ? `?${nextQuery}` : ''}`, { scroll: false });
    }
  }, [router, searchParams, user]);

  useEffect(() => {
    if (!analytics.isInitialized || !user?.id) {
      return;
    }
    if (showHero && heroEvaluated && !heroFirstImpressionLogged.current) {
      heroFirstImpressionLogged.current = true;
      analytics.trackCustomEvent('dashboard_first_impression', 'dashboard', user.id, 'si', {
        bankingStatus: connectionChips.banking.label,
        erpStatus: connectionChips.erp.label,
      });
    }
  }, [analytics, connectionChips.banking.label, connectionChips.erp.label, heroEvaluated, showHero, user?.id]);

  useEffect(() => {
    if (!user) {
      return;
    }
    let cancelled = false;

    const fetchConnectionMetadata = async () => {
      try {
        const state = await onboardingApi.getOnboardingState();
        if (cancelled || !state) {
          return;
        }
        const metadata = isRecord(state.metadata) ? state.metadata : {};
        const bankingConnectionsRaw = isRecord(metadata.banking_connections) ? metadata.banking_connections : null;
        const monoConnectionRaw = bankingConnectionsRaw?.mono ?? metadata.mono_connection;
        const erpConnectionsRaw = isRecord(metadata.erp_connections) ? metadata.erp_connections : null;
        const odooConnectionRaw = erpConnectionsRaw?.odoo ?? metadata.odoo_connection;

        const bankingState = sanitizeBankingConnection(monoConnectionRaw);
        const erpState = sanitizeErpConnection(odooConnectionRaw);

        setConnectionChips({
          banking: describeBankingChip(bankingState),
          erp: describeErpChip(erpState),
        });
        setBankingConnectionState(bankingState);
      } catch (error) {
        console.warn('Failed to load onboarding metadata for dashboard hero:', error);
        setConnectionChips({ banking: defaultBankingChip, erp: defaultErpChip });
        setBankingConnectionState(null);
      }
    };

    fetchConnectionMetadata();
    return () => {
      cancelled = true;
    };
  }, [user]);

  useEffect(() => {
    if (!bankingConnectionState) {
      setBankingManualPullState((prev) => ({
        status: prev.status === 'running' ? prev.status : 'idle',
        helper: 'Mono link required before syncing.',
        disabledReason: 'Mono connection not ready.',
      }));
      return;
    }
    const manualMeta = describeBankingManualHelper(
      bankingConnectionState,
      bankingSyncTarget.lastSyncedAt ?? bankingConnectionState.lastUpdated,
    );
    setBankingManualPullState((prev) => {
      const nextStatus = prev.status === 'running' ? 'running' : prev.status;
      const helper = nextStatus === 'idle' ? manualMeta.helper : prev.helper;
      return {
        status: nextStatus,
        helper,
        disabledReason: manualMeta.disabledReason,
      };
    });
  }, [bankingConnectionState, bankingSyncTarget.lastSyncedAt]);

  const refreshBankingAccountTarget = React.useCallback(async () => {
    if (!user) {
      setBankingSyncTarget({});
      return;
    }
    try {
      const response = await siBankingApi.listAccounts({ provider: 'mono' });
      const account = response?.data?.items?.find((item) => item.provider === 'mono') ?? response?.data?.items?.[0];
      setBankingSyncTarget(
        account
          ? {
              accountDbId: account.id,
              connectionId: account.connection_id,
              monoAccountId: account.provider_account_id,
              lastSyncedAt: account.last_sync_at ?? null,
            }
          : {},
      );
    } catch (error) {
      console.warn('Failed to load Mono banking account metadata', error);
      setBankingSyncTarget({});
    }
  }, [user]);

  useEffect(() => {
    void refreshBankingAccountTarget();
  }, [refreshBankingAccountTarget]);

  const handleManualErpPull = React.useCallback(async () => {
    setErpManualPullState({
      status: 'running',
      helper: 'Requesting Odoo sandbox batch...',
    });
    try {
      const response = await erpIntegrationApi.testFetchOdooInvoiceBatch({ batchSize: 5 });
      const fetched =
        response?.data?.fetched_count ??
        (Array.isArray(response?.data?.invoices) ? response.data.invoices.length : 0);
      const timeText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setErpManualPullState({
        status: 'success',
        helper:
          fetched && fetched > 0
            ? `Fetched ${fetched} invoice${fetched === 1 ? '' : 's'} at ${timeText}.`
            : `Pull completed at ${timeText}, no invoices returned.`,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to reach ERP data extractor.';
      setErpManualPullState({
        status: 'error',
        helper: `Manual pull failed: ${message}`,
      });
    }
  }, []);

  const handleManualBankingPull = React.useCallback(async () => {
    if (!bankingSyncTarget.accountDbId) {
      setBankingManualPullState({
        status: 'error',
        helper: 'No Mono account metadata available yet. Complete consent or retry after syncing.',
        disabledReason: 'Mono account metadata unavailable.',
      });
      return;
    }
    setBankingManualPullState({
      status: 'running',
      helper: 'Requesting Mono transaction sync...',
      disabledReason: undefined,
    });
    try {
      const response = await siBankingApi.syncTransactions({
        accountDbId: bankingSyncTarget.accountDbId,
        monoAccountId: bankingSyncTarget.monoAccountId,
        connectionId: bankingSyncTarget.connectionId,
      });
      const fetched =
        response?.data?.fetched_count ??
        (typeof response?.data?.fetched_count === 'number' ? response.data.fetched_count : 0);
      const syncTime = response?.data?.last_synced_at
        ? new Date(response.data.last_synced_at)
        : new Date();
      const timeText = syncTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setBankingManualPullState({
        status: 'success',
        helper:
          fetched && fetched > 0
            ? `Fetched ${fetched} transaction${fetched === 1 ? '' : 's'} at ${timeText}.`
            : `Sync completed at ${timeText}, no new transactions.`,
        disabledReason: undefined,
      });
      setBankingSyncTarget((prev) => ({
        ...prev,
        lastSyncedAt: response?.data?.last_synced_at ?? prev.lastSyncedAt ?? syncTime.toISOString(),
      }));
      void refreshBankingAccountTarget();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to reach Mono feed.';
      setBankingManualPullState({
        status: 'error',
        helper: `Manual pull failed: ${message}`,
        disabledReason: undefined,
      });
    }
  }, [bankingSyncTarget, refreshBankingAccountTarget]);

  const erpManualPullConfig = React.useMemo<ManualPullConfig>(
    () => ({
      modeLabel: 'Manual',
      helper: erpManualPullState.helper,
      status: erpManualPullState.status,
      ariaLabel: 'Trigger manual ERP pull for Odoo adapters',
      onRun: () => {
        if (erpManualPullState.status === 'running') {
          return;
        }
        void handleManualErpPull();
      },
    }),
    [erpManualPullState, handleManualErpPull],
  );

  const bankingManualPullConfig = React.useMemo<ManualPullConfig>(() => {
    const missingAccountReason = bankingSyncTarget.accountDbId
      ? undefined
      : 'Mono account metadata unavailable.';
    const effectiveDisabledReason = bankingManualPullState.disabledReason ?? missingAccountReason;
    const disabled = Boolean(effectiveDisabledReason);
    return {
      modeLabel: 'Manual',
      helper: bankingManualPullState.helper,
      status: bankingManualPullState.status,
      ariaLabel: 'Trigger manual Mono transaction sync',
      isDisabled: disabled,
      onRun: () => {
        if (bankingManualPullState.status === 'running' || disabled) {
          return;
        }
        void handleManualBankingPull();
      },
    };
  }, [bankingManualPullState, bankingSyncTarget.accountDbId, handleManualBankingPull]);

  const heroIdleHandler = React.useCallback(() => {
    if (!analytics.isInitialized || !user?.id) {
      return;
    }
    analytics.trackCustomEvent('dashboard_intro_idle', 'dashboard', user.id, 'si', {
      bankingStatus: connectionChips.banking.label,
      erpStatus: connectionChips.erp.label,
    });
  }, [analytics, connectionChips.banking.label, connectionChips.erp.label, user?.id]);

  const heroIdleEnabled = analytics.isInitialized && !!user?.id && showHero;

  useIdleTelemetry({
    enabled: heroIdleEnabled,
    timeoutMs: 5 * 60 * 1000,
    onIdle: heroIdleHandler,
  });

  useEffect(() => {
    if (!user) {
      return;
    }
    let cancelled = false;
    const fetchChecklist = async () => {
      try {
        setChecklistStatus('loading');
        const data = await onboardingChecklistApi.fetchChecklist();
        if (cancelled || !data) {
          return;
        }
        const remaining = data.summary?.remaining_phases?.length ?? 0;
        setChecklistSummary({
          remainingPhases: remaining,
          nextPhaseTitle: data.summary?.remaining_phases?.[0]?.title,
          lastUpdated: data.summary?.last_updated,
        });
        setChecklistStatus('ready');
      } catch (error) {
        console.warn('Failed to fetch onboarding checklist for summary:', error);
        if (!cancelled) {
          setChecklistStatus('error');
        }
      }
    };

    fetchChecklist();
    return () => {
      cancelled = true;
    };
  }, [user]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const handleHeroDismiss = () => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(HERO_STORAGE_KEY, 'true');
    }
    setShowHero(false);
  };

  const handleHeroPrimary = () => {
    router.push('/dashboard/si/firs-invoice-generator');
  };

  const handleHeroSecondary = () => {
    router.push('/dashboard/si/setup');
  };

  if (showHero || !heroEvaluated) {
    return (
      <DashboardLayout
        role="si"
        userName={`${user.first_name} ${user.last_name}`.trim() || 'System Integrator'}
        userEmail={user.email}
        activeTab="dashboard"
      >
        <SIDashboardHero
          userName={user.first_name || 'System Integrator'}
          bankingStatus={connectionChips.banking}
          bankingManualPull={bankingManualPullConfig}
          erpStatus={connectionChips.erp}
          erpManualPull={erpManualPullConfig}
          onPrimaryAction={handleHeroPrimary}
          onSecondaryAction={handleHeroSecondary}
          onDismiss={handleHeroDismiss}
        />
      </DashboardLayout>
    );
  }

  if (!showAdvanced) {
    return (
      <DashboardLayout
        role="si"
        userName={`${user.first_name} ${user.last_name}`.trim() || 'System Integrator'}
        userEmail={user.email}
        activeTab="dashboard"
      >
        <SIDashboardSummary
          userName={user.first_name || 'System Integrator'}
          bankingStatus={connectionChips.banking}
          bankingManualPull={bankingManualPullConfig}
          erpStatus={connectionChips.erp}
          erpManualPull={erpManualPullConfig}
          checklist={checklistSummary}
          onResumeOnboarding={() => router.push('/onboarding')}
          onPrimaryAction={() => router.push('/dashboard/si/firs-invoice-generator')}
          onSecondaryAction={() => router.push('/dashboard/si/setup')}
          onOpenAdvanced={() => setShowAdvanced(true)}
        />
        {checklistStatus === 'error' && (
          <p className="mt-4 text-sm text-amber-600" data-testid="checklist-warning">
            Unable to load the latest checklist status. You can still resume onboarding from the checklist panel.
          </p>
        )}
      </DashboardLayout>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end px-6 pt-4">
        <TaxPoyntButton variant="outline" size="sm" onClick={() => setShowAdvanced(false)}>
          Back to summary
        </TaxPoyntButton>
      </div>
      <EnhancedSIInterface userName={`${user.first_name} ${user.last_name}`} userEmail={user.email} />
    </div>
  );
}
