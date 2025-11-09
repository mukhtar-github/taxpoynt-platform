import apiClient from '../api/client';

interface V1Response<T> {
  success: boolean;
  action: string;
  data: T;
  meta?: Record<string, unknown>;
}

export interface OdooInvoiceTestResult {
  fetched_count?: number;
  invoices?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

const ERP_BASE_PATH = '/si/business/erp';

export const erpIntegrationApi = {
  async testFetchOdooInvoices(
    invoiceIds: string[],
    options?: {
      transform?: boolean;
      targetFormat?: string;
      odooConfig?: Record<string, unknown>;
    },
  ): Promise<V1Response<OdooInvoiceTestResult>> {
    const payload = {
      invoice_ids: invoiceIds,
      transform: options?.transform ?? true,
      target_format: options?.targetFormat ?? 'UBL_BIS_3.0',
      odoo_config: options?.odooConfig ?? {},
    };
    return apiClient.post<V1Response<OdooInvoiceTestResult>>(
      `${ERP_BASE_PATH}/odoo/test-fetch-invoices`,
      payload,
    );
  },

  async testFetchOdooInvoiceBatch(
    options?: {
      batchSize?: number;
      includeAttachments?: boolean;
      transform?: boolean;
      targetFormat?: string;
      odooConfig?: Record<string, unknown>;
    },
  ): Promise<V1Response<OdooInvoiceTestResult>> {
    const payload = {
      batch_size: options?.batchSize ?? 10,
      include_attachments: options?.includeAttachments ?? false,
      transform: options?.transform ?? true,
      target_format: options?.targetFormat ?? 'UBL_BIS_3.0',
      odoo_config: options?.odooConfig ?? {},
    };
    return apiClient.post<V1Response<OdooInvoiceTestResult>>(
      `${ERP_BASE_PATH}/odoo/test-fetch-invoice-batch`,
      payload,
    );
  },
};

export default erpIntegrationApi;
