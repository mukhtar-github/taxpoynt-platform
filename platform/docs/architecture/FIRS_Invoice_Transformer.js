# FIRS Invoice Transformer
// Converts various invoice formats to FIRS-compliant structure

class FIRSInvoiceTransformer {
  constructor() {
    this.vatRate = 0.075; // 7.5% standard VAT rate in Nigeria
    this.requiredFields = {
      document: ['invoiceNumber', 'invoiceDate', 'invoiceType'],
      supplier: ['tin', 'cacNumber', 'name', 'address', 'contact'],
      buyer: ['name', 'address'],
      lineItems: ['productDescription', 'quantity', 'unitPrice'],
      summary: ['subtotal', 'totalVAT', 'totalPayable']
    };
  }

  /**
   * Main transformation method
   * @param {Object} inputInvoice - Original invoice data
   * @param {String} sourceFormat - Format of input (e.g., 'custom', 'quickbooks', 'sap')
   * @returns {Object} FIRS-compliant invoice
   */
  transformInvoice(inputInvoice, sourceFormat = 'custom') {
    try {
      // Map source format to appropriate transformer
      const mappedData = this.mapSourceFormat(inputInvoice, sourceFormat);
      
      // Validate required fields
      this.validateRequiredFields(mappedData);
      
      // Build FIRS-compliant structure
      const firsInvoice = this.buildFIRSStructure(mappedData);
      
      // Calculate tax summaries
      this.calculateTaxes(firsInvoice);
      
      // Add metadata and audit trail
      this.addMetadata(firsInvoice);
      
      // Final validation
      this.validateFIRSCompliance(firsInvoice);
      
      return firsInvoice;
    } catch (error) {
      throw new Error(`Transformation failed: ${error.message}`);
    }
  }

  /**
   * Map various source formats to standard structure
   */
  mapSourceFormat(input, format) {
    const mappers = {
      'custom': this.mapCustomFormat.bind(this),
      'quickbooks': this.mapQuickbooksFormat.bind(this),
      'sap': this.mapSAPFormat.bind(this),
      'excel': this.mapExcelFormat.bind(this),
      'pdf': this.mapPDFFormat.bind(this)
    };
    
    const mapper = mappers[format] || mappers['custom'];
    return mapper(input);
  }

  /**
   * Map custom format invoice
   */
  mapCustomFormat(input) {
    return {
      invoiceNumber: input.invoice_no || input.invoiceNumber,
      invoiceDate: this.parseDate(input.date || input.invoiceDate),
      invoiceType: this.determineInvoiceType(input),
      currency: input.currency || 'NGN',
      
      supplier: {
        tin: input.supplier?.tin || input.sellerTIN,
        cacNumber: input.supplier?.cacNumber || input.sellerCAC,
        name: input.supplier?.name || input.sellerName,
        address: this.parseAddress(input.supplier?.address || input.sellerAddress),
        contact: this.parseContact(input.supplier?.contact || input.sellerContact)
      },
      
      buyer: {
        tin: input.buyer?.tin || input.buyerTIN,
        cacNumber: input.buyer?.cacNumber || input.buyerCAC,
        name: input.buyer?.name || input.buyerName || input.customerName,
        address: this.parseAddress(input.buyer?.address || input.buyerAddress),
        contact: this.parseContact(input.buyer?.contact || input.buyerContact),
        customerType: this.determineCustomerType(input)
      },
      
      items: this.parseLineItems(input.items || input.lineItems || input.products),
      
      payment: {
        terms: input.paymentTerms,
        method: input.paymentMethod,
        dueDate: this.parseDate(input.dueDate)
      },
      
      references: {
        purchaseOrder: input.poNumber,
        contract: input.contractRef,
        previousInvoice: input.originalInvoice
      }
    };
  }

  /**
   * Build FIRS-compliant structure
   */
  buildFIRSStructure(mappedData) {
    return {
      FIRSInvoice: {
        version: "1.0",
        standard: "BIS_Billing_3.0_UBL",
        
        documentMetadata: {
          invoiceNumber: mappedData.invoiceNumber,
          invoiceDate: mappedData.invoiceDate,
          invoiceType: mappedData.invoiceType || "STANDARD",
          currencyCode: mappedData.currency || "NGN",
          exchangeRate: mappedData.exchangeRate || 1,
          documentStatus: "ISSUED",
          issueTime: new Date().toTimeString().split(' ')[0],
          dueDate: mappedData.payment?.dueDate || this.calculateDueDate(mappedData.invoiceDate),
          taxPointDate: mappedData.invoiceDate
        },
        
        supplierInformation: this.buildSupplierInfo(mappedData.supplier),
        buyerInformation: this.buildBuyerInfo(mappedData.buyer),
        lineItems: this.buildLineItems(mappedData.items),
        
        taxSummary: {
          subtotal: 0,
          totalDiscount: 0,
          totalVAT: 0,
          withholdingTax: mappedData.withholdingTax || {},
          otherTaxes: [],
          totalPayable: 0
        },
        
        paymentInformation: {
          paymentTerms: mappedData.payment?.terms || "Net 30",
          paymentMethod: mappedData.payment?.method || "TRANSFER",
          paymentReference: mappedData.payment?.reference
        },
        
        additionalDocumentReferences: {
          purchaseOrderNumber: mappedData.references?.purchaseOrder,
          contractReference: mappedData.references?.contract,
          previousInvoiceNumber: mappedData.references?.previousInvoice
        },
        
        deliveryInformation: mappedData.delivery || {},
        
        digitalSignature: {},
        auditTrail: {}
      }
    };
  }

  /**
   * Build supplier information
   */
  buildSupplierInfo(supplier) {
    return {
      tin: supplier.tin,
      cacNumber: supplier.cacNumber,
      name: supplier.name,
      tradeName: supplier.tradeName,
      address: {
        streetName: supplier.address?.street || supplier.address?.streetName,
        buildingNumber: supplier.address?.buildingNumber,
        cityName: supplier.address?.city || supplier.address?.cityName,
        postalZone: supplier.address?.postalCode,
        stateCode: supplier.address?.state || supplier.address?.stateCode,
        countryCode: supplier.address?.country || "NG"
      },
      contact: {
        telephone: supplier.contact?.phone || supplier.contact?.telephone,
        email: supplier.contact?.email,
        contactPerson: supplier.contact?.person
      },
      bankDetails: supplier.bankDetails || {}
    };
  }

  /**
   * Build buyer information
   */
  buildBuyerInfo(buyer) {
    return {
      tin: buyer.tin || "",
      cacNumber: buyer.cacNumber || "",
      name: buyer.name,
      tradeName: buyer.tradeName,
      address: {
        streetName: buyer.address?.street || buyer.address?.streetName || "",
        buildingNumber: buyer.address?.buildingNumber || "",
        cityName: buyer.address?.city || buyer.address?.cityName || "",
        postalZone: buyer.address?.postalCode || "",
        stateCode: buyer.address?.state || buyer.address?.stateCode || "",
        countryCode: buyer.address?.country || "NG"
      },
      contact: {
        telephone: buyer.contact?.phone || buyer.contact?.telephone || "",
        email: buyer.contact?.email || "",
        contactPerson: buyer.contact?.person || ""
      },
      customerType: buyer.customerType || this.determineCustomerTypeFromTIN(buyer.tin)
    };
  }

  /**
   * Build line items with VAT calculations
   */
  buildLineItems(items) {
    return items.map((item, index) => {
      const quantity = parseFloat(item.quantity || 1);
      const unitPrice = parseFloat(item.unitPrice || item.price || 0);
      const discountAmount = parseFloat(item.discount || 0);
      const grossAmount = quantity * unitPrice;
      const netAmount = grossAmount - discountAmount;
      const vatAmount = netAmount * this.vatRate;
      const totalAmount = netAmount + vatAmount;
      
      return {
        lineNumber: index + 1,
        productCode: item.code || item.sku || "",
        productDescription: item.description || item.name,
        hscode: item.hscode || "",
        quantity: quantity,
        unitOfMeasure: item.unit || "UNIT",
        unitPrice: unitPrice,
        grossAmount: grossAmount,
        discountAmount: discountAmount,
        discountRate: (discountAmount / grossAmount) * 100,
        netAmount: netAmount,
        vatCategory: item.vatCategory || "STANDARD",
        vatRate: this.vatRate * 100,
        vatAmount: vatAmount,
        totalAmount: totalAmount,
        otherCharges: item.charges || []
      };
    });
  }

  /**
   * Calculate tax summaries
   */
  calculateTaxes(invoice) {
    const items = invoice.FIRSInvoice.lineItems;
    
    const subtotal = items.reduce((sum, item) => sum + item.netAmount, 0);
    const totalDiscount = items.reduce((sum, item) => sum + item.discountAmount, 0);
    const totalVAT = items.reduce((sum, item) => sum + item.vatAmount, 0);
    const totalPayable = items.reduce((sum, item) => sum + item.totalAmount, 0);
    
    invoice.FIRSInvoice.taxSummary = {
      ...invoice.FIRSInvoice.taxSummary,
      subtotal: parseFloat(subtotal.toFixed(2)),
      totalDiscount: parseFloat(totalDiscount.toFixed(2)),
      totalVAT: parseFloat(totalVAT.toFixed(2)),
      totalPayable: parseFloat(totalPayable.toFixed(2))
    };
    
    // Add withholding tax if applicable
    if (invoice.FIRSInvoice.buyerInformation.customerType === 'GOVERNMENT') {
      const whtRate = 0.05; // 5% WHT for government contracts
      invoice.FIRSInvoice.taxSummary.withholdingTax = {
        rate: whtRate * 100,
        amount: subtotal * whtRate,
        type: "WHT"
      };
    }
  }

  /**
   * Add metadata and audit trail
   */
  addMetadata(invoice) {
    const timestamp = new Date().toISOString();
    
    invoice.FIRSInvoice.digitalSignature = {
      signatureMethod: "SHA256",
      signatureValue: this.generateHash(invoice),
      timestamp: timestamp
    };
    
    invoice.FIRSInvoice.auditTrail = {
      createdBy: "System",
      createdDate: timestamp,
      modifiedBy: "System",
      modifiedDate: timestamp
    };
  }

  /**
   * Validate FIRS compliance
   */
  validateFIRSCompliance(invoice) {
    const errors = [];
    const inv = invoice.FIRSInvoice;
    
    // Check mandatory fields
    if (!inv.documentMetadata.invoiceNumber) errors.push("Invoice number is required");
    if (!inv.documentMetadata.invoiceDate) errors.push("Invoice date is required");
    if (!inv.supplierInformation.tin) errors.push("Supplier TIN is required");
    if (!inv.supplierInformation.cacNumber) errors.push("Supplier CAC number is required");
    if (!inv.buyerInformation.name) errors.push("Buyer name is required");
    
    // B2B specific validation
    if (inv.buyerInformation.customerType === 'B2B' && !inv.buyerInformation.tin) {
      errors.push("Buyer TIN is required for B2B transactions");
    }
    
    // Line items validation
    if (!inv.lineItems || inv.lineItems.length === 0) {
      errors.push("At least one line item is required");
    }
    
    inv.lineItems.forEach((item, index) => {
      if (!item.productDescription) {
        errors.push(`Line ${index + 1}: Product description is required`);
      }
      if (item.quantity <= 0) {
        errors.push(`Line ${index + 1}: Quantity must be greater than 0`);
      }
    });
    
    // VAT validation
    const calculatedVAT = inv.lineItems.reduce((sum, item) => sum + item.vatAmount, 0);
    if (Math.abs(calculatedVAT - inv.taxSummary.totalVAT) > 0.01) {
      errors.push("VAT calculation mismatch");
    }
    
    if (errors.length > 0) {
      throw new Error(`Validation errors: ${errors.join(', ')}`);
    }
    
    return true;
  }

  // Helper methods
  parseDate(dateString) {
    if (!dateString) return null;
    const date = new Date(dateString);
    return date.toISOString().split('T')[0];
  }

  parseAddress(address) {
    if (typeof address === 'string') {
      const parts = address.split(',').map(s => s.trim());
      return {
        street: parts[0] || '',
        city: parts[1] || '',
        state: parts[2] || '',
        country: 'NG'
      };
    }
    return address || {};
  }

  parseContact(contact) {
    if (typeof contact === 'string') {
      return { phone: contact };
    }
    return contact || {};
  }

  parseLineItems(items) {
    if (!Array.isArray(items)) return [];
    return items.map(item => ({
      description: item.description || item.name || item.product,
      quantity: item.quantity || item.qty || 1,
      unitPrice: item.unitPrice || item.price || item.amount || 0,
      unit: item.unit || item.uom || 'UNIT',
      discount: item.discount || 0,
      code: item.code || item.sku,
      hscode: item.hscode,
      vatCategory: item.vatCategory || 'STANDARD'
    }));
  }

  determineInvoiceType(input) {
    if (input.invoiceType) return input.invoiceType.toUpperCase();
    if (input.type?.toLowerCase().includes('credit')) return 'CREDIT';
    if (input.type?.toLowerCase().includes('debit')) return 'DEBIT';
    return 'STANDARD';
  }

  determineCustomerType(input) {
    if (input.customerType) return input.customerType;
    if (input.buyer?.tin || input.buyerTIN) return 'B2B';
    return 'B2C';
  }

  determineCustomerTypeFromTIN(tin) {
    if (!tin) return 'B2C';
    if (tin.startsWith('GOV')) return 'GOVERNMENT';
    return 'B2B';
  }

  calculateDueDate(invoiceDate, terms = 30) {
    const date = new Date(invoiceDate);
    date.setDate(date.getDate() + terms);
    return date.toISOString().split('T')[0];
  }

  generateHash(data) {
    // Simple hash for demonstration - use proper crypto in production
    return Buffer.from(JSON.stringify(data)).toString('base64').substring(0, 64);
  }

  // Format-specific mappers
  mapQuickbooksFormat(input) {
    // Quickbooks-specific mapping logic
    return this.mapCustomFormat(input);
  }

  mapSAPFormat(input) {
    // SAP-specific mapping logic
    return this.mapCustomFormat(input);
  }

  mapExcelFormat(input) {
    // Excel-specific mapping logic
    return this.mapCustomFormat(input);
  }

  mapPDFFormat(input) {
    // PDF extraction and mapping logic
    return this.mapCustomFormat(input);
  }

  validateRequiredFields(data) {
    const missing = [];
    
    if (!data.invoiceNumber) missing.push('invoiceNumber');
    if (!data.invoiceDate) missing.push('invoiceDate');
    if (!data.supplier?.tin) missing.push('supplier.tin');
    if (!data.supplier?.name) missing.push('supplier.name');
    if (!data.buyer?.name) missing.push('buyer.name');
    if (!data.items || data.items.length === 0) missing.push('items');
    
    if (missing.length > 0) {
      throw new Error(`Missing required fields: ${missing.join(', ')}`);
    }
  }
}

// Example usage
const transformer = new FIRSInvoiceTransformer();

// Sample input invoice (your existing format)
const inputInvoice = {
  invoice_no: "INV-2025-001",
  date: "2025-09-27",
  sellerTIN: "1234567890",
  sellerCAC: "RC123456",
  sellerName: "ABC Company Limited",
  sellerAddress: "123 Victoria Island, Lagos, Lagos State",
  sellerContact: { phone: "+234-1-2345678", email: "info@abccompany.ng" },
  
  customerName: "XYZ Corporation",
  buyerTIN: "0987654321",
  buyerAddress: "456 Wuse II, Abuja, FCT",
  buyerContact: { email: "procurement@xyzcorp.ng" },
  
  items: [
    {
      name: "Professional Services",
      quantity: 10,
      price: 50000,
      unit: "HOUR"
    },
    {
      name: "Software License",
      quantity: 5,
      price: 100000,
      unit: "LICENSE"
    }
  ],
  
  paymentTerms: "Net 30 days",
  paymentMethod: "TRANSFER"
};

// Transform the invoice
try {
  const firsInvoice = transformer.transformInvoice(inputInvoice, 'custom');
  console.log("Transformation successful!");
  console.log(JSON.stringify(firsInvoice, null, 2));
  
  // The transformed invoice is now ready for submission to FIRS API
} catch (error) {
  console.error("Transformation failed:", error.message);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FIRSInvoiceTransformer;
}
