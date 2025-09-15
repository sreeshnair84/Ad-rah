import { useState, useCallback } from 'react';

export interface LoginFormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

export interface LoginFormErrors {
  email?: string;
  password?: string;
  general?: string;
}

export interface UseLoginFormReturn {
  formData: LoginFormData;
  errors: LoginFormErrors;
  showPassword: boolean;
  isFormValid: boolean;
  updateField: (field: keyof LoginFormData, value: string) => void;
  togglePasswordVisibility: () => void;
  validateForm: () => boolean;
  setError: (field: keyof LoginFormErrors, message: string | null) => void;
  clearErrors: () => void;
  resetForm: () => void;
}

export function useLoginForm(): UseLoginFormReturn {
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
    rememberMe: false,
  });

  const [errors, setErrors] = useState<LoginFormErrors>({});
  const [showPassword, setShowPassword] = useState(false);

  const validateEmail = (email: string): string | null => {
    if (!email) return 'Email is required';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) return 'Please enter a valid email address';
    return null;
  };

  const validatePassword = (password: string): string | null => {
    if (!password) return 'Password is required';
    if (password.length < 6) return 'Password must be at least 6 characters';
    return null;
  };

  const updateField = useCallback((field: keyof LoginFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));

    // Clear field-specific error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }

    // Real-time validation for individual fields
    if (field === 'email') {
      const emailError = validateEmail(value);
      if (emailError) {
        setErrors(prev => ({ ...prev, email: emailError }));
      }
    }

    if (field === 'password') {
      const passwordError = validatePassword(value);
      if (passwordError) {
        setErrors(prev => ({ ...prev, password: passwordError }));
      }
    }
  }, [errors]);

  const togglePasswordVisibility = useCallback(() => {
    setShowPassword(prev => !prev);
  }, []);

  const validateForm = useCallback((): boolean => {
    const emailError = validateEmail(formData.email);
    const passwordError = validatePassword(formData.password);

    const newErrors: LoginFormErrors = {};
    if (emailError) newErrors.email = emailError;
    if (passwordError) newErrors.password = passwordError;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  const setError = useCallback((field: keyof LoginFormErrors, message: string | null) => {
    setErrors(prev => ({ ...prev, [field]: message || undefined }));
  }, []);

  const clearErrors = useCallback(() => {
    setErrors({});
  }, []);

  const resetForm = useCallback(() => {
    setFormData({ email: '', password: '', rememberMe: false });
    setErrors({});
    setShowPassword(false);
  }, []);

  const isFormValid = !errors.email && !errors.password && formData.email.trim() !== '' && formData.password.trim() !== '';

  return {
    formData,
    errors,
    showPassword,
    isFormValid,
    updateField,
    togglePasswordVisibility,
    validateForm,
    setError,
    clearErrors,
    resetForm,
  };
}