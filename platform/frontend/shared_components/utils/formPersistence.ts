/**
 * Form Persistence Utility
 * ========================
 * 
 * Handles automatic form data persistence across page refreshes and form navigation.
 * Uses sessionStorage for temporary data and localStorage for long-term persistence.
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
}

export class FormPersistenceManager {
  private options: FormPersistenceOptions;
  private autoSaveTimer: NodeJS.Timeout | null = null;

  constructor(options: FormPersistenceOptions) {
    this.options = {
      persistent: false,
      excludeFields: ['password', 'confirmPassword', 'token'],
      autoSaveInterval: 2000, // 2 seconds
      ...options
    };
  }

  /**
   * Get storage instance based on persistence setting
   */
  private getStorage(): Storage {
    if (typeof window === 'undefined') {
      // SSR fallback
      return {
        getItem: () => null,
        setItem: () => {},
        removeItem: () => {},
        clear: () => {},
        length: 0,
        key: () => null
      };
    }
    
    return this.options.persistent ? localStorage : sessionStorage;
  }

  /**
   * Save form data to storage
   */
  saveFormData(formData: Record<string, any>): void {
    try {
      const storage = this.getStorage();
      const filteredData = this.filterExcludedFields(formData);
      
      storage.setItem(this.options.storageKey, JSON.stringify({
        data: filteredData,
        timestamp: Date.now(),
        version: '1.0'
      }));
      
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
      console.log(`🗑️  Form data cleared from storage:`, this.options.storageKey);
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
      const formData = getFormData();
      if (formData && Object.keys(formData).length > 0) {
        this.saveFormData(formData);
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
   * Filter out excluded fields
   */
  private filterExcludedFields(data: Record<string, any>): Record<string, any> {
    const filtered = { ...data };
    
    this.options.excludeFields?.forEach(field => {
      delete filtered[field];
    });
    
    return filtered;
  }

  /**
   * Merge saved data with current form data, preserving current values
   */
  mergeWithSavedData(currentData: Record<string, any>): Record<string, any> {
    const savedData = this.loadFormData();
    if (!savedData) return currentData;

    // Only fill empty fields from saved data
    const merged = { ...currentData };
    
    Object.keys(savedData).forEach(key => {
      if (!merged[key] || merged[key] === '') {
        merged[key] = savedData[key];
      }
    });

    return merged;
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
    rc_number?: string;
    tin?: string;
    address?: string;
    state?: string;
    lga?: string;
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
    } catch (error) {
      console.warn('Failed to clear shared form data:', error);
    }
  }

  /**
   * Auto-populate form with shared data (only empty fields)
   */
  static populateForm(currentFormData: Record<string, any>): Record<string, any> {
    const sharedData = this.getSharedData();
    const populated = { ...currentFormData };

    // Only populate empty fields
    Object.keys(sharedData).forEach(key => {
      if (!populated[key] || populated[key] === '') {
        populated[key] = sharedData[key];
      }
    });

    return populated;
  }
}
