import { test, expect } from '@playwright/test';

const baseUrl = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3001';
const runSuite = process.env.RUN_ONBOARDING_E2E === 'true';

const uniqueEmail = () => {
  const seed = Date.now();
  const domain = process.env.PLAYWRIGHT_E2E_EMAIL_DOMAIN || 'taxpoynt.dev';
  return `qa-si-${seed}@${domain}`;
};

test.describe('SI onboarding happy path', () => {
  test.skip(!runSuite, 'Set RUN_ONBOARDING_E2E=true with a live backend before running this suite.');

  test('register, verify, connect Mono + Odoo demo', async ({ page }) => {
    const email = process.env.PLAYWRIGHT_E2E_EMAIL ?? uniqueEmail();
    const password = process.env.PLAYWRIGHT_E2E_PASSWORD ?? 'StrongPass!234';

    await test.step('Start streamlined registration', async () => {
      await page.goto(`${baseUrl}/auth/signup`);
      await page.getByLabel('Email').fill(email);
      await page.getByLabel(/first name/i).fill('QA');
      await page.getByLabel(/last name/i).fill('Automation');
      await page.getByLabel(/^password$/i).fill(password);
      await page.getByLabel(/confirm password/i).fill(password);
      await page.getByLabel(/business name/i).fill('QA Systems Ltd');
      await page.getByRole('checkbox', { name: /terms/i }).check();
      await page.getByRole('checkbox', { name: /privacy/i }).check();
      await page.getByRole('button', { name: /start free trial/i }).click();
    });

    await test.step('Verify email (Dojah autoprefill)', async () => {
      await page.goto(`${baseUrl}/auth/verify-email`);
      await page.getByLabel(/email/i).fill(email);
      const otp = process.env.PLAYWRIGHT_E2E_VERIFICATION_CODE ?? '000000';
      await page.getByLabel(/verification code/i).fill(otp);
      await page.getByRole('button', { name: /verify/i }).click();
      await expect(page.getByText(/Company Profile/i)).toBeVisible();
      await expect(page.getByText(/Verified via Dojah/i)).toBeVisible();
    });

    await test.step('Navigate to system connectivity', async () => {
      await page.goto(`${baseUrl}/onboarding`);
      await page.getByText(/How do you want to feed invoices/i).waitFor();
    });

    await test.step('Connect Mono via contact form (skipped when env missing)', async () => {
      if (!process.env.MONO_PUBLIC_KEY) {
        test.info().annotations.push({ type: 'info', description: 'Mono credentials missing; skipping consent launch.' });
        return;
      }
      await page.getByRole('button', { name: /Bank feeds/i }).click();
      await page.getByLabel(/Account holder name/i).fill('QA Automation');
      await page.getByLabel(/Account holder email/i).fill(email);
      await page.getByRole('button', { name: /Connect workspace/i }).click();
      await expect(page.getByText(/Link generated/i)).toBeVisible();
    });

    await test.step('Use demo Odoo workspace and run test pull', async () => {
      await page.getByRole('button', { name: /ERP adapters/i }).click();
      await page.getByLabel(/Use TaxPoynt's demo Odoo workspace/i).check();
      await page.getByRole('button', { name: /Connect workspace/i }).click();
      await expect(page.getByText(/Connection established/i)).toBeVisible({ timeout: 120000 });
      await expect(page.getByText(/Test selected invoices/i)).toBeVisible();
      await page.getByRole('button', { name: /Test selected invoices/i }).click();
      await expect(page.getByText(/Pulled/i)).toBeVisible({ timeout: 120000 });
      await expect(page.getByText(/Preview sample invoice/i)).toBeVisible();
    });
  });
});
