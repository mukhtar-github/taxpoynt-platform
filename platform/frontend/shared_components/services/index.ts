/**
 * Shared Services
 * ===============
 * Export all shared services for use across the application
 */

export { authService } from './auth';
export type { 
  AuthResponse, 
  RegisterRequest, 
  LoginRequest, 
  User, 
  Organization 
} from './auth';