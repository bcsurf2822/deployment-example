/**
 * Main types export file
 * Consolidates all TypeScript interfaces and types
 */

// Database types
export * from './database';

// UI/Component types
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface ToastNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}

// Theme types for Neon Dark aesthetic
export interface NeonTheme {
  colors: {
    primary: {
      deep: string; // #1a0b2e
      medium: string; // #16213e
      light: string; // #0f3460
    };
    accent: {
      yellow: string; // #ffff00
      gold: string; // #f1c40f
      red: string; // #e74c3c
    };
    background: {
      black: string;
      gradient: string;
    };
    text: {
      primary: string; // Light gray/white
      secondary: string; // Medium gray
      accent: string; // Yellow accent
    };
  };
  effects: {
    glow: string;
    glassMorphism: string;
  };
}

// Form types
export interface FormField {
  name: string;
  type: 'text' | 'email' | 'password' | 'textarea' | 'select' | 'file';
  label: string;
  placeholder?: string;
  required?: boolean;
  validation?: (value: any) => string | null;
}

export interface FormState {
  values: Record<string, any>;
  errors: Record<string, string>;
  isSubmitting: boolean;
  isValid: boolean;
}

// Navigation types
export interface NavItem {
  id: string;
  label: string;
  icon?: React.ComponentType;
  path: string;
  badge?: number;
}

export interface SidebarState {
  isCollapsed: boolean;
  activeItem: string | null;
}

// Chat-specific UI types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  isLoading?: boolean;
  metadata?: Record<string, any>;
}