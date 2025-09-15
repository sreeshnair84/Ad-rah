'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useAuth } from '@/hooks/useAuth';
import { useLoginForm } from '@/hooks/useLoginForm';
import { mapAuthError, getBrandConfig, secureLog } from '@/lib/utils';
import { Building2, Shield, User, Lock, AlertCircle, CheckCircle, Loader2, Crown, Eye, EyeOff, Info, Mail, Chrome, Unlock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';
import { Checkbox } from '@/components/ui/checkbox';

export default function LoginPage() {
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginFailed, setLoginFailed] = useState(false);
  const router = useRouter();
  const { login, user, loading, isInitialized, getDisplayName, getRoleDisplay } = useAuth();
  const {
    formData,
    errors,
    showPassword,
    isFormValid,
    updateField,
    togglePasswordVisibility,
    validateForm,
    setError,
    clearErrors,
  } = useLoginForm();

  const brandConfig = getBrandConfig();

  // Redirect if already authenticated
  useEffect(() => {
    if (isInitialized && user) {
      secureLog('info', 'User already authenticated, redirecting to dashboard');
      router.replace('/dashboard');
    }
  }, [isInitialized, user, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    setLoginFailed(false);

    if (!validateForm()) {
      return;
    }

    try {
      secureLog('info', 'Attempting login for:', { email: formData.email });
      const loggedInUser = await login({ email: formData.email, password: formData.password });

      if (loggedInUser) {
        secureLog('info', 'Login successful, user type:', loggedInUser.user_type);

        // Show success message briefly then redirect
        setTimeout(() => {
          secureLog('info', 'Redirecting to dashboard');
          router.replace('/dashboard');
        }, 1000);
      } else {
        setLoginFailed(true);
        setLoginError('Login failed. Please check your credentials and try again.');
      }
    } catch (error) {
      secureLog('error', 'Login error:', error);
      setLoginFailed(true);
      setLoginError(mapAuthError(error));
    }
  };

  const getUserTypeIcon = (userType: string) => {
    switch (userType) {
      case 'SUPER_USER':
        return <Crown className="w-5 h-5 text-purple-600" />;
      case 'COMPANY_USER':
        return <Building2 className="w-5 h-5 text-blue-600" />;
      case 'DEVICE_USER':
        return <Shield className="w-5 h-5 text-green-600" />;
      default:
        return <User className="w-5 h-5 text-gray-600" />;
    }
  };

  const getUserTypeLabel = (userType: string) => {
    switch (userType) {
      case 'SUPER_USER':
        return 'Platform Administrator';
      case 'COMPANY_USER':
        return 'Company User';
      case 'DEVICE_USER':
        return 'Device User';
      default:
        return 'User';
    }
  };

  // Show loading screen during initial authentication check
  if (!isInitialized) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100"
      >
        <Card className="w-full max-w-md">
          <CardContent className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-2 text-sm text-muted-foreground">Initializing...</span>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  // Show success message if user is logged in (before redirect)
  if (user) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100"
      >
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="w-full max-w-md shadow-xl">
            <CardContent className="flex flex-col items-center justify-center py-8 text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.4, type: "spring", stiffness: 200 }}
                className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4"
              >
                <CheckCircle className="w-6 h-6 text-green-600" />
              </motion.div>
              <motion.h3
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.6 }}
                className="text-lg font-semibold mb-2"
              >
                Welcome back!
              </motion.h3>
              <motion.div
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.7 }}
                className="space-y-2 mb-4"
              >
                <div className="flex items-center justify-center gap-2">
                  {getUserTypeIcon(user.user_type)}
                  <span className="text-sm font-medium">{getDisplayName()}</span>
                </div>
                <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                  <span>{getRoleDisplay()}</span>
                  {user.company?.name && <span>• {user.company.name}</span>}
                </div>
              </motion.div>
              <motion.p
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="text-sm text-muted-foreground mb-4"
              >
                Redirecting you to your dashboard...
              </motion.p>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.9 }}
              >
                <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
              </motion.div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    );
  }

  // Main login form
  return (
    <TooltipProvider>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="min-h-screen flex items-center justify-center relative overflow-hidden p-4"
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }} />
        </div>

        <motion.div
          animate={loginFailed ? {
            x: [-10, 10, -10, 10, 0],
            transition: { duration: 0.5 }
          } : {}}
          className="relative z-10"
        >
          <Card className="w-full max-w-lg shadow-2xl border-0 bg-white/95 backdrop-blur-md">
            <CardHeader className="pb-4">
              {/* Logo positioned at top-left of card */}
              <div className="flex items-start justify-between mb-6">
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  transition={{ type: "spring", stiffness: 300 }}
                  className="flex items-center gap-3"
                >
                  <Image
                    src="/images/logo.png"
                    alt="Adara Screen Logo"
                    width={200}
                    height={60}
                    className="h-12 w-auto object-contain"
                    priority
                    onError={(e) => {
                      console.log('Logo failed to load, showing fallback');
                      const target = e.currentTarget as HTMLImageElement;
                      target.style.display = 'none';
                      const fallback = target.nextElementSibling as HTMLElement;
                      if (fallback) fallback.classList.remove('hidden');
                    }}
                  />
                  <div className="hidden flex items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
                      <User className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-lg font-bold text-gray-900">Adara Screen</span>
                      <span className="text-xs text-blue-600 font-medium">Digital Signage Platform</span>
                    </div>
                  </div>
                </motion.div>
              </div>

              <motion.div
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="text-center"
              >
                <CardTitle className="text-2xl font-bold mb-2 text-gray-900">
                  Welcome Back
                </CardTitle>
                <CardDescription className="text-gray-600">
                  Your all-in-one digital signage platform
                </CardDescription>
              </motion.div>
            </CardHeader>
            <CardContent className="px-8 pb-8">
              <motion.form
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 }}
                onSubmit={handleLogin}
                className="space-y-6"
              >
                <AnimatePresence>
                  {loginError && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <Alert variant="destructive" aria-live="polite" role="alert" className="border-red-200 bg-red-50">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{loginError}</AlertDescription>
                      </Alert>
                    </motion.div>
                  )}
                </AnimatePresence>

                <motion.div
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.4 }}
                  className="space-y-2"
                >
                  <Label htmlFor="email" className="text-sm font-medium text-gray-700">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      value={formData.email}
                      onChange={(e) => updateField('email', e.target.value)}
                      placeholder="Enter your email"
                      className={`pl-12 h-12 border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all ${errors.email || (loginFailed && !formData.email) ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : ''}`}
                      required
                      aria-label="Email address"
                      aria-describedby={errors.email ? "email-error" : undefined}
                      aria-invalid={!!errors.email}
                    />
                  </div>
                  <AnimatePresence>
                    {errors.email && (
                      <motion.p
                        id="email-error"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="text-sm text-red-600"
                        role="alert"
                      >
                        {errors.email}
                      </motion.p>
                    )}
                  </AnimatePresence>
                </motion.div>

                <motion.div
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  className="space-y-2"
                >
                  <Label htmlFor="password" className="text-sm font-medium text-gray-700">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                    <Input
                      id="password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="current-password"
                      value={formData.password}
                      onChange={(e) => updateField('password', e.target.value)}
                      placeholder="Enter your password"
                      className={`pl-12 pr-12 h-12 border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all ${errors.password || (loginFailed && !formData.password) ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : ''}`}
                      required
                      aria-label="Password"
                      aria-describedby={errors.password ? "password-error" : undefined}
                      aria-invalid={!!errors.password}
                    />
                    <button
                      type="button"
                      onClick={togglePasswordVisibility}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                  <AnimatePresence>
                    {errors.password && (
                      <motion.p
                        id="password-error"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="text-sm text-red-600"
                        role="alert"
                      >
                        {errors.password}
                      </motion.p>
                    )}
                  </AnimatePresence>
                </motion.div>

                {/* Remember Me Checkbox */}
                <motion.div
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.55 }}
                  className="flex items-center space-x-2"
                >
                  <Checkbox
                    id="rememberMe"
                    checked={formData.rememberMe}
                    onCheckedChange={(checked) => updateField('rememberMe', !!checked)}
                    className="border-gray-300 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                  />
                  <Label
                    htmlFor="rememberMe"
                    className="text-sm font-medium text-gray-700 cursor-pointer"
                  >
                    Remember me for 30 days
                  </Label>
                </motion.div>

                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.6 }}
                  className="space-y-4"
                >
                  <Button
                    type="submit"
                    className="w-full h-12 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold text-base shadow-lg hover:shadow-xl transition-all duration-200"
                    disabled={loading || !isFormValid}
                    aria-label="Sign in to your account"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Authenticating...
                      </>
                    ) : (
                      <>
                        <Unlock className="w-5 h-5 mr-2" />
                        Sign In
                      </>
                    )}
                  </Button>

                  {/* Social Login Options */}
                  <div className="space-y-3">
                    <div className="relative">
                      <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t border-gray-200" />
                      </div>
                      <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-white px-3 text-gray-500 font-medium">or continue with</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <Button
                        type="button"
                        variant="outline"
                        className="h-11 border-gray-200 hover:bg-gray-50 transition-colors"
                        disabled={loading}
                      >
                        <Chrome className="w-5 h-5 mr-2 text-red-500" />
                        Google
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        className="h-11 border-gray-200 hover:bg-gray-50 transition-colors"
                        disabled={loading}
                      >
                        <Building2 className="w-5 h-5 mr-2 text-blue-600" />
                        Microsoft
                      </Button>
                    </div>
                  </div>
                </motion.div>
              </motion.form>

              {/* Footer Links */}
              <motion.div
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.7 }}
                className="mt-6 flex items-center justify-center gap-6 text-sm"
              >
                <a href="/reset-password" className="text-blue-600 hover:text-blue-700 font-medium transition-colors">
                  Forgot Password?
                </a>
                <span className="text-gray-300">•</span>
                <a href="/company-registration" className="text-blue-600 hover:text-blue-700 font-medium transition-colors">
                  Register Company
                </a>
              </motion.div>

              {/* Enhanced Security Features - Professional Badges */}
              <motion.div
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="mt-8 pt-6 border-t border-gray-100"
              >
                <div className="text-center mb-4">
                  <h4 className="text-xs font-bold text-gray-600 mb-3 uppercase tracking-wider">
                    Enterprise Security
                  </h4>
                </div>
                <div className="flex justify-center gap-4">
                  <div className="flex flex-col items-center group">
                    <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mb-2 group-hover:bg-blue-100 transition-colors">
                      <Shield className="w-6 h-6 text-blue-500" />
                    </div>
                    <span className="text-xs font-medium text-gray-600">RBAC</span>
                    <span className="text-xs text-gray-400">Access Control</span>
                  </div>
                  <div className="flex flex-col items-center group">
                    <div className="w-12 h-12 bg-green-50 rounded-full flex items-center justify-center mb-2 group-hover:bg-green-100 transition-colors">
                      <Building2 className="w-6 h-6 text-green-500" />
                    </div>
                    <span className="text-xs font-medium text-gray-600">Multi-Tenant</span>
                    <span className="text-xs text-gray-400">Data Isolation</span>
                  </div>
                  <div className="flex flex-col items-center group">
                    <div className="w-12 h-12 bg-purple-50 rounded-full flex items-center justify-center mb-2 group-hover:bg-purple-100 transition-colors">
                      <Crown className="w-6 h-6 text-purple-500" />
                    </div>
                    <span className="text-xs font-medium text-gray-600">Granular</span>
                    <span className="text-xs text-gray-400">Permissions</span>
                  </div>
                </div>
                <div className="text-center mt-4">
                  <p className="text-xs text-gray-500">
                    Enterprise-grade security for your digital signage platform
                  </p>
                </div>
              </motion.div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </TooltipProvider>
  );
}
