const DEFAULT_DENYLIST = [
  'gmail.com',
  'googlemail.com',
  'yahoo.com',
  'yahoo.co.uk',
  'ymail.com',
  'hotmail.com',
  'hotmail.co.uk',
  'outlook.com',
  'outlook.co.uk',
  'live.com',
  'live.co.uk',
  'msn.com',
  'icloud.com',
  'me.com',
  'mac.com',
  'aol.com',
  'protonmail.com',
  'proton.me',
  'pm.me',
  'zoho.com',
  'yandex.com',
  'mail.com',
  'gmx.com',
  'web.de',
  'hey.com',
  'fastmail.com',
  'tutanota.com',
  'tuta.com',
  'mail.ru',
  'qq.com',
  'naver.com',
  'daum.net',
  '126.com',
  '163.com',
];

type PolicyMode = 'strict' | 'disabled' | 'allowlist_only';

interface BusinessEmailPolicy {
  mode: PolicyMode;
  denylist: Set<string>;
  allowlist: Set<string>;
}

let cachedPolicy: BusinessEmailPolicy | null = null;

const normalizeToken = (token: string | null | undefined): string | null => {
  if (!token) {
    return null;
  }
  const trimmed = token.trim().toLowerCase();
  if (!trimmed || trimmed.startsWith('#')) {
    return null;
  }
  return trimmed;
};

const parseTokens = (raw: string | undefined): Set<string> => {
  if (!raw) {
    return new Set();
  }
  const tokens = raw
    .split(/[,\s]+/)
    .map((token) => normalizeToken(token))
    .filter((token): token is string => Boolean(token));
  return new Set(tokens);
};

const domainMatches = (domain: string, candidates: Set<string>): boolean => {
  if (!domain) {
    return false;
  }
  const lowerDomain = domain.toLowerCase();

  for (const candidate of candidates) {
    if (!candidate) {
      continue;
    }
    if (candidate.startsWith('*.')) {
      const suffix = candidate.slice(1);
      if (lowerDomain.endsWith(suffix)) {
        return true;
      }
    } else if (lowerDomain === candidate) {
      return true;
    } else if (lowerDomain.endsWith(`.${candidate}`)) {
      return true;
    }
  }

  return false;
};

const resolveMode = (value: string | undefined): PolicyMode => {
  if (!value) {
    return 'strict';
  }
  const trimmed = value.trim().toLowerCase();
  if (trimmed === 'disabled' || trimmed === 'off' || trimmed === 'skip') {
    return 'disabled';
  }
  if (trimmed === 'allowlist_only' || trimmed === 'allowlist') {
    return 'allowlist_only';
  }
  return 'strict';
};

const loadPolicy = (): BusinessEmailPolicy => {
  if (cachedPolicy) {
    return cachedPolicy;
  }

  const mode = resolveMode(process.env.NEXT_PUBLIC_BUSINESS_EMAIL_POLICY_MODE);

  const denylist = new Set(DEFAULT_DENYLIST);
  const envDenylist = parseTokens(process.env.NEXT_PUBLIC_BUSINESS_EMAIL_DENYLIST);
  envDenylist.forEach((domain) => denylist.add(domain));

  const allowlist = parseTokens(process.env.NEXT_PUBLIC_BUSINESS_EMAIL_ALLOWLIST);

  cachedPolicy = { mode, denylist, allowlist };
  return cachedPolicy;
};

export const resetBusinessEmailPolicyCache = (): void => {
  cachedPolicy = null;
};

export const isBusinessEmail = (email: string): boolean => {
  const policy = loadPolicy();
  if (policy.mode === 'disabled') {
    return true;
  }

  const atIndex = email.indexOf('@');
  if (atIndex === -1) {
    return false;
  }
  const domain = email.slice(atIndex + 1).toLowerCase();

  if (domainMatches(domain, policy.allowlist)) {
    return true;
  }

  if (policy.mode === 'allowlist_only') {
    return false;
  }

  if (domainMatches(domain, policy.denylist)) {
    return false;
  }

  return true;
};

export const getBusinessEmailValidationMessage = (email: string): string | undefined => {
  const policy = loadPolicy();
  if (policy.mode === 'disabled') {
    return undefined;
  }

  const atIndex = email.indexOf('@');
  if (atIndex === -1) {
    return undefined;
  }
  const domain = email.slice(atIndex + 1).toLowerCase();

  if (domainMatches(domain, policy.allowlist)) {
    return undefined;
  }

  if (policy.mode === 'allowlist_only') {
    return 'This workspace requires an approved business email domain.';
  }

  if (domainMatches(domain, policy.denylist)) {
    return 'Use your business email (for example, you@company.com) to continue.';
  }

  return undefined;
};
