#!/usr/bin/env node
/**
 * URL Validation Script
 * ====================
 * 
 * Validates all configured URLs for consistency and accessibility.
 * Ensures redirect URLs match across components and environments.
 */

import { urlConfig, UrlValidator, UrlBuilder, EnvironmentUtils } from '../shared_components/config/urlConfig';

async function validateUrls() {
  console.log('🔍 URL Validation Script');
  console.log('========================');
  console.log();

  // Environment Information
  console.log(`Environment: ${EnvironmentUtils.getApiEnvironment()}`);
  console.log(`Frontend URL: ${urlConfig.base.frontend}`);
  console.log(`API URL: ${urlConfig.base.api}`);
  console.log();

  // Validate Configuration
  console.log('🧪 Validating URL Configuration...');
  const configValidation = await UrlValidator.validateConfiguration();
  
  if (configValidation.valid) {
    console.log('✅ URL configuration is valid');
  } else {
    console.log('❌ URL configuration has errors:');
    configValidation.errors.forEach(error => console.log(`  • ${error}`));
  }

  if (configValidation.warnings.length > 0) {
    console.log('⚠️ URL configuration warnings:');
    configValidation.warnings.forEach(warning => console.log(`  • ${warning}`));
  }
  console.log();

  // Check Consistency
  console.log('🔄 Checking URL Consistency...');
  const consistencyCheck = UrlValidator.checkConsistency();
  
  if (consistencyCheck.consistent) {
    console.log('✅ URLs are consistent across components');
  } else {
    console.log('❌ URL consistency issues found:');
    consistencyCheck.issues.forEach(issue => console.log(`  • ${issue}`));
  }
  console.log();

  // Test URL Builder Functions
  console.log('🔧 Testing URL Builder Functions...');
  
  console.log('Banking Callback URLs:');
  console.log(`  Mono: ${UrlBuilder.bankingCallbackUrl('mono')}`);
  console.log(`  Generic: ${UrlBuilder.bankingCallbackUrl('generic')}`);
  
  console.log('Dashboard URLs:');
  console.log(`  SI: ${UrlBuilder.dashboardUrl('si')}`);
  console.log(`  APP: ${UrlBuilder.dashboardUrl('app')}`);
  console.log(`  Hybrid: ${UrlBuilder.dashboardUrl('hybrid')}`);
  console.log(`  Generic: ${UrlBuilder.dashboardUrl(null)}`);
  
  console.log('Onboarding Step URLs:');
  console.log(`  SI Business Setup: ${UrlBuilder.onboardingStepUrl('si', 'business-systems-setup')}`);
  console.log(`  APP Business Verification: ${UrlBuilder.onboardingStepUrl('app', 'business-verification')}`);
  console.log();

  // Check for Common Issues
  console.log('🚨 Checking for Common Issues...');
  
  const issues: string[] = [];
  
  // Check if banking callback is consistent
  const expectedBankingCallback = '/onboarding/si/banking-callback';
  if (urlConfig.onboarding.si.bankingCallback !== expectedBankingCallback) {
    issues.push(`Banking callback URL mismatch: expected ${expectedBankingCallback}, got ${urlConfig.onboarding.si.bankingCallback}`);
  }
  
  // Check if all dashboard URLs start with /dashboard
  Object.entries(urlConfig.dashboard).forEach(([role, url]) => {
    if (!url.startsWith('/dashboard')) {
      issues.push(`Dashboard URL for ${role} should start with /dashboard: ${url}`);
    }
  });
  
  // Check if all onboarding URLs start with /onboarding
  const allOnboardingUrls = [
    ...Object.values(urlConfig.onboarding.si),
    ...Object.values(urlConfig.onboarding.app),
    ...Object.values(urlConfig.onboarding.hybrid)
  ];
  
  allOnboardingUrls.forEach(url => {
    if (!url.startsWith('/onboarding')) {
      issues.push(`Onboarding URL should start with /onboarding: ${url}`);
    }
  });
  
  if (issues.length === 0) {
    console.log('✅ No common issues detected');
  } else {
    console.log('❌ Common issues found:');
    issues.forEach(issue => console.log(`  • ${issue}`));
  }
  console.log();

  // Generate Test Report
  console.log('📊 URL Test Report');
  console.log('==================');
  
  const totalUrls = [
    ...Object.values(urlConfig.dashboard),
    ...Object.values(urlConfig.onboarding.si),
    ...Object.values(urlConfig.onboarding.app),
    ...Object.values(urlConfig.onboarding.hybrid),
    ...Object.values(urlConfig.api.v1.auth),
    ...Object.values(urlConfig.api.v1.si.onboarding),
    ...Object.values(urlConfig.api.v1.si.banking),
    ...Object.values(urlConfig.api.v1.app.onboarding),
    urlConfig.api.v1.si.organizations,
    urlConfig.api.v1.si.financial,
    urlConfig.api.v1.si.transactions,
    urlConfig.api.v1.app.taxpayers,
    urlConfig.api.v1.app.invoices,
    urlConfig.api.v1.app.compliance
  ].filter(url => typeof url === 'string');
  
  console.log(`Total URLs configured: ${totalUrls.length}`);
  console.log(`Configuration valid: ${configValidation.valid ? 'Yes' : 'No'}`);
  console.log(`URLs consistent: ${consistencyCheck.consistent ? 'Yes' : 'No'}`);
  console.log(`Issues found: ${configValidation.errors.length + consistencyCheck.issues.length + issues.length}`);
  console.log();

  // Final Summary
  const overallValid = configValidation.valid && consistencyCheck.consistent && issues.length === 0;
  
  if (overallValid) {
    console.log('🎉 All URL validations passed! Configuration is ready for production.');
  } else {
    console.log('⚠️ URL validation issues detected. Please review and fix before deployment.');
  }
  
  return overallValid;
}

// Run validation if script is executed directly
if (require.main === module) {
  validateUrls()
    .then(success => {
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      console.error('❌ URL validation failed:', error);
      process.exit(1);
    });
}

export { validateUrls };
