'use client';

import { authService } from './auth';

export interface QueuePayload {
  step: string;
  completed?: boolean;
  completedSteps?: string[];
  metadata?: Record<string, any>;
  userId?: string;
  source?: string;
}

interface QueueEntry {
  payload: QueuePayload;
  fallback?: () => Promise<void>;
}

interface OnboardingStateUpdateRequest {
  current_step: string;
  completed_steps?: string[];
  metadata?: Record<string, any>;
}

type DispatchHandler = (request: OnboardingStateUpdateRequest) => Promise<unknown>;

let dispatcher: DispatchHandler | null = null;

export const configureOnboardingStateDispatcher = (handler: DispatchHandler) => {
  dispatcher = handler;
};

const VOLATILE_KEYS = new Set([
  'step_updated_at',
  'lastUpdate',
  'last_update',
  'lastUpdated',
  'last_updated',
  'lastActiveDate',
  'last_active_date',
  'lastTestAt',
  'last_test_at',
  'timestamp',
]);

const normalizeMetadata = (value: any): any => {
  if (value === null || value === undefined) {
    return null;
  }
  if (Array.isArray(value)) {
    return value.map(normalizeMetadata);
  }
  if (typeof value === 'object') {
    return Object.entries(value)
      .filter(([key]) => !VOLATILE_KEYS.has(key))
      .sort(([a], [b]) => a.localeCompare(b))
      .reduce<Record<string, any>>((acc, [key, val]) => {
        acc[key] = normalizeMetadata(val);
        return acc;
      }, {});
  }
  return value;
};

const buildSignature = (payload: QueuePayload): string => {
  const steps = [...new Set(payload.completedSteps || [])].sort().join('|');
  const metadata = payload.metadata ? JSON.stringify(normalizeMetadata(payload.metadata)) : '';
  return `${payload.step}|${steps}|${metadata}`;
};

class OnboardingStateQueue {
  private pending = new Map<string, QueueEntry>();
  private processing = new Set<string>();
  private lastDispatched = new Map<string, string>();
  private lastDispatchAt = new Map<string, number>();
  private lastCommittedState = new Map<string, { step: string; completedSignature: string }>();
  private readonly MIN_DISPATCH_INTERVAL_MS = 1500;

  private resolveUserId(explicit?: string): string {
    if (explicit) {
      return explicit;
    }
    const user = authService.getStoredUser();
    return user?.id ?? 'anonymous';
  }

  private mergeEntries(current: QueueEntry | undefined, next: QueueEntry): QueueEntry {
    if (!current) {
      return next;
    }

    return {
      payload: {
        step: next.payload.step,
        completed: next.payload.completed ?? current.payload.completed,
        completedSteps: next.payload.completedSteps ?? current.payload.completedSteps,
        metadata: {
          ...(current.payload.metadata || {}),
          ...(next.payload.metadata || {}),
        },
        userId: next.payload.userId ?? current.payload.userId,
        source: next.payload.source || current.payload.source,
      },
      fallback: next.fallback ?? current.fallback,
    };
  }

  private async processQueue(userKey: string): Promise<void> {
    if (this.processing.has(userKey)) {
      return;
    }

    this.processing.add(userKey);
    try {
      while (this.pending.has(userKey)) {
        const entry = this.pending.get(userKey);
        if (!entry) {
          break;
        }

        const lastAt = this.lastDispatchAt.get(userKey) ?? 0;
        const elapsed = Date.now() - lastAt;
        if (elapsed < this.MIN_DISPATCH_INTERVAL_MS) {
          const wait = this.MIN_DISPATCH_INTERVAL_MS - elapsed;
          await new Promise((resolve) => setTimeout(resolve, wait));
          continue;
        }

        this.pending.delete(userKey);

        const signature = buildSignature(entry.payload);
        if (this.lastDispatched.get(userKey) === signature) {
          this.lastDispatchAt.set(userKey, Date.now());
          continue;
        }

        const completedSignature = [...new Set(entry.payload.completedSteps || [])]
          .sort()
          .join('|');
        const forceSync =
          Boolean(entry.payload.metadata?.forceSync) ||
          Boolean(entry.payload.metadata?.force_resync);
        const lastState = this.lastCommittedState.get(userKey);
        if (
          !forceSync &&
          lastState &&
          lastState.step === entry.payload.step &&
          lastState.completedSignature === completedSignature
        ) {
          this.lastDispatchAt.set(userKey, Date.now());
          continue;
        }

        const sanitizedMetadata = entry.payload.metadata
          ? Object.fromEntries(
              Object.entries(entry.payload.metadata).filter(
                ([key]) => key !== 'forceSync' && key !== 'force_resync'
              )
            )
          : undefined;

        const request = {
          current_step: entry.payload.step,
          completed_steps: entry.payload.completedSteps,
          metadata: sanitizedMetadata,
        };

        try {
          if (!dispatcher) {
            throw new Error('Onboarding state dispatcher not configured');
          }
          await dispatcher(request);
          this.lastDispatched.set(userKey, signature);
          this.lastDispatchAt.set(userKey, Date.now());
          this.lastCommittedState.set(userKey, {
            step: entry.payload.step,
            completedSignature,
          });
        } catch (error) {
          console.error('[OnboardingStateQueue] Failed to persist onboarding state:', error);
          if (entry.fallback) {
            try {
              await entry.fallback();
              this.lastDispatched.set(userKey, signature);
              this.lastDispatchAt.set(userKey, Date.now());
              this.lastCommittedState.set(userKey, {
                step: entry.payload.step,
                completedSignature,
              });
              continue;
            } catch (fallbackError) {
              console.error('[OnboardingStateQueue] Fallback also failed:', fallbackError);
            }
          }
          const existing = this.pending.get(userKey);
          this.pending.set(userKey, this.mergeEntries(existing, entry));
          break;
        }
      }
    } finally {
      this.processing.delete(userKey);
    }
  }

  public async enqueue(payload: QueuePayload, options?: { fallback?: () => Promise<void> }): Promise<void> {
    if (!authService.isAuthenticated()) {
      console.info('[OnboardingStateQueue] Skip enqueue: user not authenticated.');
      return;
    }

    const userKey = this.resolveUserId(payload.userId);
    const entry: QueueEntry = { payload, fallback: options?.fallback };
    const merged = this.mergeEntries(this.pending.get(userKey), entry);
    this.pending.set(userKey, merged);
    await this.processQueue(userKey);
  }

  public clear(userId?: string): void {
    const key = this.resolveUserId(userId);
    this.pending.delete(key);
    this.processing.delete(key);
    this.lastDispatched.delete(key);
    this.lastDispatchAt.delete(key);
    this.lastCommittedState.delete(key);
  }
}

export const onboardingStateQueue = new OnboardingStateQueue();
