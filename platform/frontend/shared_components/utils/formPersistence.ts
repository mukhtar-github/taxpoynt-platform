/**
 * Form Persistence Utility
 * ========================
 * 
 * Handles automatic form data persistence across page refreshes and form navigation.
 * Uses sessionStorage for temporary data and localStorage for long-term persistence.
 * Includes cross-form data sharing and visual indicators for pre-filled fields.
 */

export interface FormPersistenceOptions {
  /** Unique key for storing form data */
  storageKey: string;
  /** Use localStorage (persistent) vs sessionStorage (session-only) */
  persistent?: boolean;
  /** Fields to exclude from persistence (e.g., passwords) */
  excludeFields?: string[];
  /** Auto-save interval in milliseconds */
  autoSaveInterval?: number;
  /** Enable cross-form data sharing */
  enableCrossFormSharing?: boolean;
}

export interface FormFieldState {
  value: any;
  isPreFilled: boolean;
  source: 'user_input' | 'persisted' | 'shared' | 'default';
  timestamp: number;
}

export class FormPersistenceManager {
  private options: FormPersistenceOptions;
  private autoSaveTimer: NodeJS.Timeout | null = null;

  constructor(options: FormPersistenceOptions) {
    this.options = {
      persistent: false,
      excludeFields: ['password', 'confirmPassword', 'token'],
      autoSaveInterval: 2000, // 2 seconds
      enableCrossFormSharing: true,
      ...options
    };
  }

  /**
   * Get storage instance based on persistence setting
   */
  private getStorage(): Storage {
    if (typeof window === 'undefined') {
      // SSR fallback - return a mock storage object
      return {
        getItem: () => null,
        setItem: () => {},
        removeItem: () => {},
        clear: () => {},
        length: 0,
        key: () => null
      };
    }
    
    if (this.options.persistent) {
      return window.localStorage;
    }
    return window.sessionStorage;
  }

  /**
   * Save form data to storage
   */
  saveFormData(formData: Record<string, any>): void {
    try {
      const storage = this.getStorage();
      const filteredData = this.filterExcludedFields(formData);
      
      const dataToStore = {
        data: filteredData,
        timestamp: Date.now(),
        formId: this.options.storageKey
      };
      
      storage.setItem(this.options.storageKey, JSON.stringify(dataToStore));
      
      // If cross-form sharing is enabled, also save to shared storage
      if (this.options.enableCrossFormSharing) {
        this.saveToSharedStorage(filteredData);
      }
      
      console.log(`💾 Form data saved to ${this.options.persistent ? 'localStorage' : 'sessionStorage'}:`, this.options.storageKey);
    } catch (error) {
      console.warn('Failed to save form data:', error);
    }
  }

  /**
   * Load form data from storage
   */
  loadFormData(): Record<string, any> | null {
    try {
      const storage = this.getStorage();
      const stored = storage.getItem(this.options.storageKey);
      
      if (!stored) return null;
      
      const parsed = JSON.parse(stored);
      
      // Check if data is not too old (24 hours for sessionStorage, 7 days for localStorage)
      const maxAge = this.options.persistent ? 7 * 24 * 60 * 60 * 1000 : 24 * 60 * 60 * 1000;
      if (Date.now() - parsed.timestamp > maxAge) {
        this.clearFormData();
        return null;
      }
      
      console.log(`📂 Form data loaded from ${this.options.persistent ? 'localStorage' : 'sessionStorage'}:`, this.options.storageKey);
      return parsed.data;
    } catch (error) {
      console.warn('Failed to load form data:', error);
      return null;
    }
  }

  /**
   * Clear form data from storage
   */
  clearFormData(): void {
    try {
      const storage = this.getStorage();
      storage.removeItem(this.options.storageKey);
      console.log('🗑️ Form data cleared:', this.options.storageKey);
    } catch (error) {
      console.warn('Failed to clear form data:', error);
    }
  }

  /**
   * Start auto-save timer
   */
  startAutoSave(getFormData: () => Record<string, any>): void {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
    }
    
    this.autoSaveTimer = setInterval(() => {
      const currentData = getFormData();
      if (Object.keys(currentData).length > 0) {
        this.saveFormData(currentData);
      }
    }, this.options.autoSaveInterval);
  }

  /**
   * Stop auto-save timer
   */
  stopAutoSave(): void {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
      this.autoSaveTimer = null;
    }
  }

  /**
   * Filter out excluded fields from data
   */
  private filterExcludedFields(data: Record<string, any>): Record<string, any> {
    const filtered = { ...data };
    
    this.options.excludeFields?.forEach(field => {
      delete filtered[field];
    });
    
    return filtered;
  }

  /**
   * Save data to shared storage for cross-form access
   */
  private saveToSharedStorage(data: Record<string, any>): void {
    try {
      const sharedKey = 'taxpoynt_shared_form_data';
      const currentShared = this.getFromSharedStorage();
      const merged = { ...currentShared, ...data };
      
      sessionStorage.setItem(sharedKey, JSON.stringify({
        data: merged,
        timestamp: Date.now(),
        lastUpdatedBy: this.options.storageKey
      }));
      
      console.log('🔗 Data saved to shared storage for cross-form access');
    } catch (error) {
      console.warn('Failed to save to shared storage:', error);
    }
  }

  /**
   * Get data from shared storage
   */
  private getFromSharedStorage(): Record<string, any> {
    try {
      const sharedKey = 'taxpoynt_shared_form_data';
      const stored = sessionStorage.getItem(sharedKey);
      
      if (!stored) return {};
      
      const parsed = JSON.parse(stored);
      
      // Clear if older than 24 hours
      if (Date.now() - parsed.timestamp > 24 * 60 * 60 * 1000) {
        sessionStorage.removeItem(sharedKey);
        return {};
      }
      
      return parsed.data || {};
    } catch (error) {
      console.warn('Failed to load from shared storage:', error);
      return {};
    }
  }

  /**
   * Merge saved data with current form data, preserving current values
   */
  mergeWithSavedData(currentData: Record<string, any>): Record<string, any> {
    const savedData = this.loadFormData();
    const sharedData = this.getFromSharedStorage();
    
    if (!savedData && Object.keys(sharedData).length === 0) {
      return currentData;
    }

    // Merge priority: current data > saved data > shared data
    const merged = { ...currentData };
    
    // First, fill from shared data (lowest priority)
    Object.keys(sharedData).forEach(key => {
      if (!merged[key] || merged[key] === '') {
        merged[key] = sharedData[key];
      }
    });
    
    // Then, fill from saved data (higher priority)
    if (savedData) {
      Object.keys(savedData).forEach(key => {
        if (!merged[key] || merged[key] === '') {
          merged[key] = savedData[key];
        }
      });
    }

    return merged;
  }

  /**
   * Get field state information for visual indicators
   */
  getFieldState(fieldName: string, currentValue: any): FormFieldState {
    const savedData = this.loadFormData();
    const sharedData = this.getFromSharedStorage();
    
    if (savedData && savedData[fieldName] && savedData[fieldName] === currentValue) {
      return {
        value: currentValue,
        isPreFilled: true,
        source: 'persisted',
        timestamp: Date.now()
      };
    }
    
    if (sharedData && sharedData[fieldName] && sharedData[fieldName] === currentValue) {
      return {
        value: currentValue,
        isPreFilled: true,
        source: 'shared',
        timestamp: Date.now()
      };
    }
    
    return {
      value: currentValue,
      isPreFilled: false,
      source: 'user_input',
      timestamp: Date.now()
    };
  }
}

/**
 * React Hook for Form Persistence
 */
export function useFormPersistence(options: FormPersistenceOptions) {
  const manager = new FormPersistenceManager(options);

  return {
    saveFormData: (data: Record<string, any>) => manager.saveFormData(data),
    loadFormData: () => manager.loadFormData(),
    clearFormData: () => manager.clearFormData(),
    mergeWithSavedData: (currentData: Record<string, any>) => manager.mergeWithSavedData(currentData),
    getFieldState: (fieldName: string, currentValue: any) => manager.getFieldState(fieldName, currentValue),
    startAutoSave: (getFormData: () => Record<string, any>) => manager.startAutoSave(getFormData),
    stopAutoSave: () => manager.stopAutoSave()
  };
}

/**
 * Cross-Form Data Sharing Utilities
 */
export class CrossFormDataManager {
  private static SHARED_DATA_KEY = 'taxpoynt_shared_form_data';

  /**
   * Save commonly used form fields for sharing across forms
   */
  static saveSharedData(data: {
    email?: string;
    first_name?: string;
    last_name?: string;
    phone?: string;
    business_name?: string;
    business_type?: string;
    companyType?: string;
    companySize?: string;
    rc_number?: string;
    tin?: string;
    address?: string;
    state?: string;
    lga?: string;
    industry?: string;
  }): void {
    try {
      if (typeof window === 'undefined') return;
      
      const currentShared = this.getSharedData();
      const merged = { ...currentShared, ...data };
      
      sessionStorage.setItem(this.SHARED_DATA_KEY, JSON.stringify({
        data: merged,
        timestamp: Date.now()
      }));
      
      console.log('🔗 Shared form data updated:', Object.keys(data));
    } catch (error) {
      console.warn('Failed to save shared form data:', error);
    }
  }

  /**
   * Get shared form data
   */
  static getSharedData(): Record<string, any> {
    try {
      if (typeof window === 'undefined') return {};
      
      const stored = sessionStorage.getItem(this.SHARED_DATA_KEY);
      if (!stored) return {};
      
      const parsed = JSON.parse(stored);
      
      // Clear if older than 24 hours
      if (Date.now() - parsed.timestamp > 24 * 60 * 60 * 1000) {
        this.clearSharedData();
        return {};
      }
      
      return parsed.data || {};
    } catch (error) {
      console.warn('Failed to load shared form data:', error);
      return {};
    }
  }

  /**
   * Clear shared form data
   */
  static clearSharedData(): void {
    try {
      if (typeof window === 'undefined') return;
      
      sessionStorage.removeItem(this.SHARED_DATA_KEY);
      console.log('🗑️ Shared form data cleared');
    } catch (error) {
      console.warn('Failed to clear shared form data:', error);
    }
  }

  /**
   * Check if a field has shared data
   */
  static hasSharedData(fieldName: string): boolean {
    const sharedData = this.getSharedData();
    return sharedData[fieldName] && sharedData[fieldName] !== '';
  }

  /**
   * Get shared data for a specific field
   */
  static getSharedField(fieldName: string): any {
    const sharedData = this.getSharedData();
    return sharedData[fieldName] || '';
  }
}

/**
 * Utility to get visual styling for pre-filled fields
 */
export function getPreFilledFieldStyles(isPreFilled: boolean, source: string): string {
  if (!isPreFilled) return '';
  
  const baseStyles = 'bg-gray-50 border-gray-300 text-gray-600';
  
  switch (source) {
    case 'persisted':
      return `${baseStyles} border-l-4 border-l-blue-400`;
    case 'shared':
      return `${baseStyles} border-l-4 border-l-green-400`;
    default:
      return baseStyles;
  }
}

/**
 * Utility to get helper text for pre-filled fields
 */
export function getPreFilledHelperText(source: string): string {
  switch (source) {
    case 'persisted':
      return 'Previously entered data';
    case 'shared':
      return 'Data from other forms';
    default:
      return '';
  }
}
