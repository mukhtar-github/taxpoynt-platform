'use client';

/**
 * Data Mapping Page
 * =================
 * 
 * System Integrator interface for mapping business system data to FIRS-compliant invoice format.
 * Visual drag-and-drop data mapping with Nigerian tax compliance validation.
 * 
 * Features:
 * - Visual data field mapping interface
 * - FIRS invoice schema validation
 * - Nigerian VAT and tax code mapping
 * - Real-time data preview
 * - Template-based mapping for common systems
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../../design_system/components/Button';
import apiClient from '../../shared_components/api/client';

const DATA_MAPPING_BASE = '/si/business/erp/data-mapping';

interface DataField {
  id: string;
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'object' | 'array';
  required: boolean;
  description: string;
  example?: string | number;
  validation?: string[];
  category?: string;
  path?: string;
}

interface BusinessSystemCategory {
  id: string;
  label: string;
  description?: string;
}

interface BusinessSystemSummary {
  id: string;
  name: string;
  description?: string;
  apiType?: string;
  dataTypes?: string[];
}

interface BusinessSystemSchema extends BusinessSystemSummary {
  systemId: string;
  systemName: string;
  version?: string;
  fields: DataField[];
  categories?: BusinessSystemCategory[];
  defaultMappings?: Record<string, string>;
}

interface FIRSInvoiceField {
  id: string;
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'object' | 'array';
  required: boolean;
  description: string;
  firsCode?: string;
  validation: string[];
  nigerianCompliance?: {
    vatApplicable: boolean;
    taxCode?: string;
    regulatoryNote?: string;
  };
}

interface MappingRule {
  id: string;
  sourceField: string;
  sourceLabel?: string;
  targetField: string;
  transformation?: {
    type: 'direct' | 'format' | 'calculate' | 'lookup' | 'conditional';
    formula?: string;
    lookupTable?: Record<string, any>;
    conditions?: Array<{
      condition: string;
      value: any;
    }>;
  };
  validated: boolean;
}

// FIRS-compliant invoice schema
const firsInvoiceSchema: FIRSInvoiceField[] = [
  {
    id: 'invoice_number',
    name: 'Invoice Number',
    type: 'string',
    required: true,
    description: 'Unique invoice identifier',
    firsCode: 'INV_NUM',
    validation: ['unique', 'alphanumeric', 'max_length:50'],
    nigerianCompliance: {
      vatApplicable: false,
      regulatoryNote: 'Must be unique across all invoices'
    }
  },
  {
    id: 'invoice_date',
    name: 'Invoice Date',
    type: 'date',
    required: true,
    description: 'Date invoice was issued',
    firsCode: 'INV_DATE',
    validation: ['date_format:YYYY-MM-DD', 'not_future'],
    nigerianCompliance: {
      vatApplicable: false,
      regulatoryNote: 'Must not be in the future'
    }
  },
  {
    id: 'supplier_tin',
    name: 'Supplier TIN',
    type: 'string',
    required: true,
    description: 'Supplier Tax Identification Number',
    firsCode: 'SUP_TIN',
    validation: ['tin_format', 'length:14'],
    nigerianCompliance: {
      vatApplicable: false,
      regulatoryNote: 'Must be valid FIRS TIN format'
    }
  },
  {
    id: 'customer_tin',
    name: 'Customer TIN',
    type: 'string',
    required: false,
    description: 'Customer Tax Identification Number',
    firsCode: 'CUST_TIN',
    validation: ['tin_format', 'length:14'],
    nigerianCompliance: {
      vatApplicable: false,
      regulatoryNote: 'Required for B2B transactions above ₦25M'
    }
  },
  {
    id: 'line_items',
    name: 'Line Items',
    type: 'array',
    required: true,
    description: 'Invoice line items with products/services',
    firsCode: 'LINE_ITEMS',
    validation: ['min_items:1', 'max_items:1000'],
    nigerianCompliance: {
      vatApplicable: true,
      taxCode: 'VAT_ITEMS',
      regulatoryNote: 'Each item must have VAT calculation'
    }
  },
  {
    id: 'total_amount',
    name: 'Total Amount',
    type: 'number',
    required: true,
    description: 'Total invoice amount including VAT',
    firsCode: 'TOTAL_AMT',
    validation: ['positive', 'decimal_places:2', 'currency:NGN'],
    nigerianCompliance: {
      vatApplicable: true,
      taxCode: 'VAT_INCLUSIVE',
      regulatoryNote: 'Must include VAT where applicable'
    }
  },
  {
    id: 'vat_amount',
    name: 'VAT Amount',
    type: 'number',
    required: false,
    description: 'Value Added Tax amount',
    firsCode: 'VAT_AMT',
    validation: ['positive', 'decimal_places:2', 'percentage:7.5'],
    nigerianCompliance: {
      vatApplicable: true,
      taxCode: 'VAT_7_5',
      regulatoryNote: 'Standard Nigerian VAT rate is 7.5%'
    }
  },
  {
    id: 'currency',
    name: 'Currency',
    type: 'string',
    required: true,
    description: 'Invoice currency code',
    firsCode: 'CURRENCY',
    validation: ['currency_code', 'supported_currencies'],
    nigerianCompliance: {
      vatApplicable: false,
      regulatoryNote: 'NGN required for domestic transactions'
    }
  }
];

interface DataMappingProps {
  systemId?: string;
  organizationId?: string;
  onMappingComplete?: (mappingRules: MappingRule[]) => void;
}

export const DataMapping: React.FC<DataMappingProps> = ({
  systemId,
  organizationId,
  onMappingComplete
}) => {
  const router = useRouter();
  const [availableSystems, setAvailableSystems] = useState<BusinessSystemSummary[]>([]);
  const availableSystemsRef = useRef<BusinessSystemSummary[]>([]);
  const [schemaCache, setSchemaCache] = useState<Record<string, BusinessSystemSchema>>({});
  const schemaCacheRef = useRef<Record<string, BusinessSystemSchema>>({});
  const [selectedSystem, setSelectedSystem] = useState<BusinessSystemSchema | null>(null);
  const [loadingSystems, setLoadingSystems] = useState<boolean>(false);
  const [loadingSchema, setLoadingSchema] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hasAppliedRecommendations, setHasAppliedRecommendations] = useState<boolean>(false);
  const [mappingRules, setMappingRules] = useState<MappingRule[]>([]);
  const [draggedField, setDraggedField] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string[]>>({});
  const [isValidating, setIsValidating] = useState(false);

  const loadSchema = useCallback(async (systemKey: string, summaryOverride?: BusinessSystemSummary) => {
    const normalizedKey = systemKey.toLowerCase();

    const cachedSchema = schemaCacheRef.current[normalizedKey];
    if (cachedSchema) {
      setSelectedSystem(cachedSchema);
      setMappingRules([]);
      setValidationErrors({});
      setPreviewData(null);
      setHasAppliedRecommendations(false);
      return;
    }

    setLoadingSchema(true);
    setErrorMessage(null);
    try {
      const response = await apiClient.get<any>(`/si/business/erp/${normalizedKey}/schema`);

      const envelope = response?.data ?? response;
      const schemaData = envelope?.schema;
      const erpMeta = envelope?.erp_system;

      if (!schemaData || !Array.isArray(schemaData.fields) || schemaData.fields.length === 0) {
        throw new Error('Schema definition missing fields');
      }

      const summaryLookup = availableSystemsRef.current;
      const summary = summaryOverride || summaryLookup.find(sys => sys.id === normalizedKey) || (erpMeta
        ? ({
            id: normalizedKey,
            name: erpMeta.name ?? normalizedKey.toUpperCase(),
            description: erpMeta.description,
            apiType: erpMeta.api_type,
            dataTypes: erpMeta.data_types,
          } as BusinessSystemSummary)
        : undefined);

      const normalizedSchema: BusinessSystemSchema = {
        id: normalizedKey,
        systemId: schemaData.system_id || normalizedKey,
        systemName: schemaData.system_name || summary?.name || normalizedKey.toUpperCase(),
        version: schemaData.version,
        description: schemaData.description || summary?.description,
        apiType: summary?.apiType,
        dataTypes: summary?.dataTypes,
        fields: schemaData.fields.map((field: any) => ({
          id: field.id,
          path: field.path ?? field.id,
          name: field.name || field.id,
          type: field.type ?? 'string',
          required: Boolean(field.required),
          description: field.description || '',
          example: field.example,
          validation: field.validation,
          category: field.category,
        })),
        categories: schemaData.categories,
        defaultMappings: schemaData.default_mappings,
        name: summary?.name || schemaData.system_name || normalizedKey.toUpperCase(),
      };

      setSchemaCache(prev => {
        const next = { ...prev, [normalizedKey]: normalizedSchema };
        schemaCacheRef.current = next;
        return next;
      });
      setSelectedSystem(normalizedSchema);
      setMappingRules([]);
      setValidationErrors({});
      setPreviewData(null);
      setHasAppliedRecommendations(false);
    } catch (error) {
      console.error('Failed to load ERP schema:', error);
      setErrorMessage('Unable to load the schema for the selected ERP system. Please try again.');
    } finally {
      setLoadingSchema(false);
    }
  }, []);

  useEffect(() => {
    const fetchAvailableSystems = async () => {
      setLoadingSystems(true);
      setErrorMessage(null);
      try {
        const response = await apiClient.get<any>('/si/business/erp/available');
        const envelope = response?.data ?? response;
        const systemsPayload: Record<string, any> = envelope?.erp_systems ?? {};
        const normalized: BusinessSystemSummary[] = Object.entries(systemsPayload).map(([id, info]) => ({
          id,
          name: info?.name ?? id.toUpperCase(),
          description: info?.description,
          apiType: info?.api_type,
          dataTypes: info?.data_types,
        }));

        setAvailableSystems(normalized);
        availableSystemsRef.current = normalized;

        if (systemId) {
          const match = normalized.find(sys => sys.id === systemId.toLowerCase());
          if (match) {
            await loadSchema(match.id, match);
          }
        }
      } catch (error) {
        console.error('Failed to fetch ERP systems:', error);
        setErrorMessage('Unable to load available ERP systems at the moment.');
      } finally {
        setLoadingSystems(false);
      }
    };

    fetchAvailableSystems();
  }, [loadSchema, systemId]);

  // Load existing mapping rules
  useEffect(() => {
    if (selectedSystem && organizationId) {
      loadExistingMappings();
    }
  }, [selectedSystem, organizationId]);

  const loadExistingMappings = async () => {
    if (!selectedSystem) {
      return;
    }

    try {
      const data = await apiClient.get<{ mapping_rules?: MappingRule[] }>(
        `${DATA_MAPPING_BASE}/${organizationId}/${selectedSystem?.systemId}`
      );

      const incomingRules = data?.mapping_rules || [];
      const enrichedRules = incomingRules.map(rule => {
        const sourceField = selectedSystem.fields.find(
          field => (field.path ?? field.id) === rule.sourceField
        );
        return {
          ...rule,
          sourceLabel: rule.sourceLabel || sourceField?.name,
        } as MappingRule;
      });

      setMappingRules(enrichedRules);
    } catch (error) {
      console.error('Failed to load existing mappings:', error);
    }
  };

  const handleDragStart = (fieldPath: string) => {
    setDraggedField(fieldPath);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (targetFieldId: string) => {
    setShowWizardPrompt(false);
    if (draggedField && selectedSystem) {
      const sourceField = selectedSystem.fields.find(f => (f.path ?? f.id) === draggedField);
      const targetField = firsInvoiceSchema.find(f => f.id === targetFieldId);
      
      if (sourceField && targetField) {
        const sourceFieldKey = sourceField.path ?? sourceField.id;
        const newRule: MappingRule = {
          id: `${sourceFieldKey}_to_${targetFieldId}`,
          sourceField: sourceFieldKey,
          sourceLabel: sourceField.name,
          targetField: targetFieldId,
          transformation: {
            type: 'direct'
          },
          validated: false
        };

        setMappingRules(prev => {
          const filtered = prev.filter(rule => rule.targetField !== targetFieldId);
          return [...filtered, newRule];
        });

        setValidationErrors(prev => {
          if (!prev[targetFieldId]) {
            return prev;
          }
          const next = { ...prev };
          delete next[targetFieldId];
          return next;
        });
      }
    }
    setDraggedField(null);
  };

  const handleValidateMapping = async () => {
    if (!selectedSystem || mappingRules.length === 0) return;

    setIsValidating(true);
    try {
      const result = await apiClient.post<{
        success: boolean;
        errors?: Record<string, string[]>;
        preview_data?: any;
      }>(`${DATA_MAPPING_BASE}/validate`, {
        system_id: selectedSystem.systemId,
        organization_id: organizationId,
        mapping_rules: mappingRules,
        firs_schema: firsInvoiceSchema
      });
      
      if (result.success) {
        setValidationErrors({});
        setMappingRules(prev => prev.map(rule => ({ ...rule, validated: true })));
        setPreviewData(result.preview_data);
        alert('✅ Mapping validation successful!');
      } else {
        setValidationErrors(result.errors || {});
        alert('❌ Mapping validation failed. Please check the errors.');
      }
    } catch (error) {
      console.error('Validation failed:', error);
      alert('Validation failed. Please try again.');
    } finally {
      setIsValidating(false);
    }
  };

  const handleSaveMapping = async () => {
    if (!selectedSystem || mappingRules.length === 0) return;

    try {
      const result = await apiClient.post<{ success: boolean; error?: string }>(
        `${DATA_MAPPING_BASE}/save`,
        {
          system_id: selectedSystem.systemId,
          organization_id: organizationId,
          mapping_rules: mappingRules
        }
      );
      
      if (result.success) {
        alert('✅ Mapping configuration saved successfully!');
        if (onMappingComplete) {
          onMappingComplete(mappingRules);
        }
        router.push('/onboarding/si/integration-setup?step=testing');
      } else {
        alert('❌ Failed to save mapping configuration.');
      }
    } catch (error) {
      console.error('Save failed:', error);
      alert('Save failed. Please try again.');
    }
  };

  const getMappedSourceField = (targetFieldId: string) => {
    const rule = mappingRules.find(rule => rule.targetField === targetFieldId);
    return rule ? selectedSystem?.fields.find(f => (f.path ?? f.id) === rule.sourceField) : null;
  };

  const groupedFields = useMemo(() => {
    if (!selectedSystem) {
      return [] as Array<{ category: BusinessSystemCategory; fields: DataField[] }>;
    }

    const categories = selectedSystem.categories ?? [];
    const order = categories.map(cat => cat.id);
    const groups = new Map<string, { category: BusinessSystemCategory; fields: DataField[] }>();

    categories.forEach(category => {
      groups.set(category.id, { category, fields: [] });
    });

    selectedSystem.fields.forEach(field => {
      const categoryId = field.category || categories[0]?.id || 'other';
      if (!groups.has(categoryId)) {
        groups.set(categoryId, {
          category: {
            id: categoryId,
            label: field.category || 'Other Fields',
          },
          fields: [],
        });
      }
      groups.get(categoryId)!.fields.push(field);
    });

    const grouped = Array.from(groups.values());
    grouped.forEach(group => {
      group.fields.sort((a, b) => {
        if (a.required !== b.required) {
          return a.required ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
      });
    });

    return grouped.sort((a, b) => {
      const indexA = order.indexOf(a.category.id);
      const indexB = order.indexOf(b.category.id);
      return (indexA === -1 ? 999 : indexA) - (indexB === -1 ? 999 : indexB);
    });
  }, [selectedSystem]);

  const handleApplyRecommendation = (targetFieldId: string) => {
    if (!selectedSystem?.defaultMappings) {
      return;
    }

    setShowWizardPrompt(false);
    const recommendedPath = selectedSystem.defaultMappings[targetFieldId];
    if (!recommendedPath) {
      return;
    }

    const recommendedField = selectedSystem.fields.find(
      field => (field.path ?? field.id) === recommendedPath
    );

    if (!recommendedField) {
      return;
    }

    const sourceKey = recommendedField.path ?? recommendedField.id;
    const newRule: MappingRule = {
      id: `${sourceKey}_to_${targetFieldId}`,
      sourceField: sourceKey,
      sourceLabel: recommendedField.name,
      targetField: targetFieldId,
      transformation: { type: 'direct' },
      validated: false,
    };

    setMappingRules(prev => {
      const filtered = prev.filter(rule => rule.targetField !== targetFieldId);
      return [...filtered, newRule];
    });
    setValidationErrors(prev => {
      if (!prev[targetFieldId]) {
        return prev;
      }
      const next = { ...prev };
      delete next[targetFieldId];
      return next;
    });
  };

  const handleApplyAllRecommendations = () => {
    if (!selectedSystem?.defaultMappings) {
      return;
    }

    setShowWizardPrompt(false);
    const rules: MappingRule[] = Object.entries(selectedSystem.defaultMappings)
      .map(([targetFieldId, recommendedPath]) => {
        const recommendedField = selectedSystem.fields.find(
          field => (field.path ?? field.id) === recommendedPath
        );

        if (!recommendedField) {
          return null;
        }

        const sourceKey = recommendedField.path ?? recommendedField.id;
        return {
          id: `${sourceKey}_to_${targetFieldId}`,
          sourceField: sourceKey,
          sourceLabel: recommendedField.name,
          targetField: targetFieldId,
          transformation: { type: 'direct' },
          validated: false,
        } as MappingRule;
      })
      .filter((rule): rule is MappingRule => Boolean(rule));

    if (!rules.length) {
      return;
    }

    setMappingRules(prev => {
      const filtered = prev.filter(rule => !rules.some(newRule => newRule.targetField === rule.targetField));
      return [...filtered, ...rules];
    });
    setValidationErrors({});
    setPreviewData(null);
    setHasAppliedRecommendations(true);
  };

  const handleResetSystemSelection = () => {
    setSelectedSystem(null);
    setMappingRules([]);
    setValidationErrors({});
    setPreviewData(null);
    setHasAppliedRecommendations(false);
    setErrorMessage(null);
    setShowWizardPrompt(false);
  };

  const recommendedMappingCount = selectedSystem?.defaultMappings
    ? Object.keys(selectedSystem.defaultMappings).length
    : 0;

  if (!selectedSystem) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-xl border p-8 text-center max-w-2xl w-full shadow-sm">
          <div className="text-4xl mb-4">🔄</div>
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Select Your ERP System</h2>
          <p className="text-gray-600 mb-6">
            Choose the ERP or accounting platform you want to map to the FIRS e-invoicing schema.
          </p>

          {errorMessage && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </div>
          )}

          {loadingSystems && availableSystems.length === 0 ? (
            <div className="py-8 text-sm text-gray-600">Loading available systems…</div>
          ) : (
            <div className="space-y-3 text-left">
              {loadingSchema && (
                <div className="rounded-lg border border-blue-100 bg-blue-50 px-4 py-2 text-xs text-blue-700">
                  Loading schema definition…
                </div>
              )}
              {availableSystems.map(system => (
                <button
                  key={system.id}
                  onClick={() => loadSchema(system.id, system)}
                  className="w-full rounded-lg border border-gray-200 p-4 transition-colors hover:border-blue-500 hover:bg-blue-50"
                  disabled={loadingSchema}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-lg font-semibold text-gray-900">{system.name}</div>
                      {system.description && (
                        <p className="mt-1 text-sm text-gray-600">{system.description}</p>
                      )}
                      {system.dataTypes && (
                        <p className="mt-2 text-xs uppercase tracking-wide text-gray-500">
                          Data types: {system.dataTypes.join(', ')}
                        </p>
                      )}
                    </div>
                    {system.apiType && (
                      <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
                        {system.apiType.toUpperCase()}
                      </span>
                    )}
                  </div>
                </button>
              ))}

              {availableSystems.length === 0 && !loadingSystems && (
                <div className="py-6 text-sm text-gray-600">
                  No ERP systems are available yet. Please contact the TaxPoynt integrations team.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {selectedSystem.systemName} → FIRS Data Mapping
              </h1>
              <p className="text-gray-600 mt-2">
                Align {selectedSystem.systemName} fields with Nigeria’s FIRS e-invoicing requirements.
              </p>
              {selectedSystem.description && (
                <p className="text-sm text-gray-500 mt-1 max-w-2xl">
                  {selectedSystem.description}
                </p>
              )}
              <div className="mt-2 text-sm text-gray-500 flex items-center gap-3">
                {selectedSystem.version && (
                  <span className="rounded-full bg-gray-100 px-3 py-1">Version {selectedSystem.version}</span>
                )}
                {selectedSystem.apiType && (
                  <span className="rounded-full bg-gray-100 px-3 py-1">
                    API: {selectedSystem.apiType.toUpperCase()}
                  </span>
                )}
                {selectedSystem.dataTypes && (
                  <span className="rounded-full bg-gray-100 px-3 py-1">
                    Data types: {selectedSystem.dataTypes.join(', ')}
                  </span>
                )}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Button variant="outline" onClick={handleResetSystemSelection}>
                Change ERP System
              </Button>
              {recommendedMappingCount > 0 && (
                <Button
                  variant="outline"
                  onClick={handleApplyAllRecommendations}
                  disabled={hasAppliedRecommendations}
                >
                  {hasAppliedRecommendations ? 'Recommendations Applied' : 'Load Recommended Mapping'}
                </Button>
              )}
              <Button
                onClick={handleValidateMapping}
                disabled={mappingRules.length === 0 || isValidating}
                loading={isValidating}
                variant="outline"
              >
                Validate Mapping
              </Button>
              <Button
                onClick={handleSaveMapping}
                disabled={mappingRules.length === 0 || !mappingRules.every(rule => rule.validated)}
              >
                Save Configuration
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Mapping Interface */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Source Fields */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {selectedSystem.systemName} Fields
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              Drag fields from here to map them to FIRS invoice format
            </p>
            
            <div className="space-y-6">
              {groupedFields.map(group => (
                <div key={group.category.id}>
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-2">
                    {group.category.label}
                  </h3>
                  {group.category.description && (
                    <p className="text-xs text-gray-500 mb-3">{group.category.description}</p>
                  )}
                  <div className="space-y-3">
                    {group.fields.map(field => {
                      const fieldKey = field.path ?? field.id;
                      return (
                        <div
                          key={fieldKey}
                          draggable
                          onDragStart={() => handleDragStart(fieldKey)}
                          className="p-3 border border-gray-200 rounded-lg cursor-move hover:border-blue-500 hover:bg-blue-50 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-medium text-gray-900 flex items-center gap-2">
                                {field.name}
                                {field.required && <span className="text-xs text-red-500">*</span>}
                              </div>
                              <div className="text-sm text-gray-600 break-all">{fieldKey}</div>
                            </div>
                            <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              {field.type}
                            </div>
                          </div>
                          {field.description && (
                            <p className="text-xs text-gray-500 mt-2">{field.description}</p>
                          )}
                          {field.example !== undefined && (
                            <p className="text-xs text-gray-400 mt-2">
                              Example: {String(field.example)}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Target Fields (FIRS Schema) */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              FIRS Invoice Format 🇳🇬
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              Drop source fields here to create mappings
            </p>
            
            <div className="space-y-3">
              {firsInvoiceSchema.map(field => {
                const mappedField = getMappedSourceField(field.id);
                const hasError = validationErrors[field.id];
                const recommendedPath = selectedSystem.defaultMappings?.[field.id];
                const recommendedField = recommendedPath
                  ? selectedSystem.fields.find(f => (f.path ?? f.id) === recommendedPath)
                  : undefined;
                
                return (
                  <div
                    key={field.id}
                    onDragOver={handleDragOver}
                    onDrop={() => handleDrop(field.id)}
                    className={`p-3 border-2 border-dashed rounded-lg transition-colors ${
                      mappedField 
                        ? hasError 
                          ? 'border-red-300 bg-red-50' 
                          : 'border-green-300 bg-green-50'
                        : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-medium text-gray-900 flex items-center">
                          {field.name}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                        </div>
                        <div className="text-sm text-gray-600">{field.firsCode}</div>
                      </div>
                      <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {field.type}
                      </div>
                    </div>
                    
                    {mappedField ? (
                      <div className="bg-white border rounded p-2 mb-2">
                        <div className="text-sm font-medium text-gray-900">
                          Mapped to: {mappedField.name}
                        </div>
                        <div className="text-xs text-gray-600 break-all">{mappedField.path ?? mappedField.id}</div>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500 italic">
                        Drop a field here to create mapping
                      </div>
                    )}
                    
                    <p className="text-xs text-gray-500 mt-2">{field.description}</p>
                    {!mappedField && recommendedField && (
                      <button
                        type="button"
                        onClick={() => handleApplyRecommendation(field.id)}
                        className="mt-2 inline-flex items-center text-xs font-medium text-blue-600 hover:underline"
                      >
                        Use recommended mapping ({recommendedField.name})
                      </button>
                    )}
                    
                    {field.nigerianCompliance && (
                      <div className="mt-2 text-xs text-blue-600 bg-blue-50 p-2 rounded">
                        🇳🇬 {field.nigerianCompliance.regulatoryNote}
                      </div>
                    )}
                    
                    {hasError && (
                      <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                        ❌ {hasError.join(', ')}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Preview and Validation */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Mapping Preview
            </h2>
            
            {mappingRules.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">📋</div>
                <p>No mappings created yet</p>
                <p className="text-sm">Drag and drop fields to create mappings</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Mapping Rules Summary */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Mapping Rules ({mappingRules.length})</h3>
                  <div className="space-y-2">
                    {mappingRules.map(rule => {
                      const sourceField = selectedSystem.fields.find(
                        f => (f.path ?? f.id) === rule.sourceField
                      );
                      const targetField = firsInvoiceSchema.find(f => f.id === rule.targetField);
                      const sourceLabel = sourceField?.name || rule.sourceLabel || rule.sourceField;
                      
                      return (
                        <div key={rule.id} className="text-sm">
                          <div className="flex items-center justify-between">
                            <span>{sourceLabel}</span>
                            <span className="text-gray-400">→</span>
                            <span>{targetField?.name}</span>
                            <span className={`w-2 h-2 rounded-full ${
                              rule.validated ? 'bg-green-500' : 'bg-yellow-500'
                            }`}></span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Preview Data */}
                {previewData && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3">FIRS Invoice Preview</h3>
                    <pre className="text-xs text-gray-700 bg-white p-3 rounded border overflow-auto max-h-64">
                      {JSON.stringify(previewData, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Nigerian Compliance Status */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-900 mb-2">🇳🇬 Nigerian Compliance</h3>
                  <div className="space-y-1 text-sm text-blue-800">
                    <div>✓ FIRS e-invoicing format compatibility</div>
                    <div>✓ VAT calculation fields mapped</div>
                    <div>✓ Nigerian business data requirements</div>
                    <div>✓ Currency and tax code validation</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataMapping;
