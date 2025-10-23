'use client';

/**
 * Role Management Dev Tools
 * ========================
 * Developer-facing overlays for inspecting role, permission, and feature flag
 * state without polluting the main provider module. Loaded dynamically to avoid
 * circular evaluation during SSR bundling.
 */

import React, { useState } from 'react';
import { useRoleDetector } from './role_detector';
import { usePermissions } from './permission_provider';
import { useFeatureFlags } from './feature_flag_provider';

interface DevToolsProps {
  enabled: boolean;
}

export const DevTools: React.FC<DevToolsProps> = ({ enabled }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!enabled || process.env.NODE_ENV === 'production') {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-purple-600 text-white p-2 rounded-full shadow-lg hover:bg-purple-700 transition-colors"
        title="Role Management Dev Tools"
      >
        🛠️
      </button>

      {isOpen && (
        <div className="absolute bottom-12 right-0 bg-white border rounded-lg shadow-xl p-4 w-80 max-h-96 overflow-auto">
          <h4 className="font-medium text-gray-900 mb-3">Role Management Dev Tools</h4>

          <div className="space-y-3">
            <RoleDebugInfo />
            <PermissionDebugInfo />
            <FeatureFlagDebugInfo />
          </div>

          <button
            onClick={() => setIsOpen(false)}
            className="mt-3 text-sm text-gray-500 hover:text-gray-700"
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
};

const RoleDebugInfo: React.FC = () => {
  const { detectionResult } = useRoleDetector();

  return (
    <div className="border rounded p-2">
      <h5 className="text-sm font-medium text-gray-700 mb-1">Current Role</h5>
      <div className="text-xs text-gray-600">
        <div>Primary: {detectionResult?.primaryRole || 'None'}</div>
        <div>All: {detectionResult?.availableRoles.join(', ') || 'None'}</div>
        <div>Can Switch: {detectionResult?.canSwitchRoles ? 'Yes' : 'No'}</div>
      </div>
    </div>
  );
};

const PermissionDebugInfo: React.FC = () => {
  const { getUserPermissions } = usePermissions();
  const permissions = getUserPermissions();

  return (
    <div className="border rounded p-2">
      <h5 className="text-sm font-medium text-gray-700 mb-1">Permissions ({permissions.length})</h5>
      <div className="text-xs text-gray-600 max-h-20 overflow-auto">
        {permissions.length > 0 ? permissions.join(', ') : 'None'}
      </div>
    </div>
  );
};

const FeatureFlagDebugInfo: React.FC = () => {
  const { getEnabledFlags } = useFeatureFlags();
  const enabledFlags = getEnabledFlags();

  return (
    <div className="border rounded p-2">
      <h5 className="text-sm font-medium text-gray-700 mb-1">Feature Flags ({enabledFlags.length})</h5>
      <div className="text-xs text-gray-600 max-h-20 overflow-auto">
        {enabledFlags.length > 0 ? enabledFlags.join(', ') : 'None'}
      </div>
    </div>
  );
};

export default DevTools;
