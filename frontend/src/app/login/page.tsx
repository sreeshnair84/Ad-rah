'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import { Building2, Shield, User, Lock, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [selectedRole, setSelectedRole] = useState<{ companyId: string; roleId: string } | null>(null);
  const [currentStep, setCurrentStep] = useState<'login' | 'role-selection' | 'redirecting'>('login');
  const [loginError, setLoginError] = useState<string | null>(null);
  const [authenticatedUser, setAuthenticatedUser] = useState<any>(null);
  const router = useRouter();
  const { login, user, switchRole, loading, isInitialized } = useAuth();

  // Redirect if already authenticated
  useEffect(() => {
    if (isInitialized && user) {
      console.log('User already authenticated, redirecting to dashboard');
      router.replace('/dashboard');
    }
  }, [isInitialized, user, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    
    if (!email || !password) {
      setLoginError('Please enter both email and password');
      return;
    }

    try {
      console.log('Attempting login for:', email);
      const loggedInUser = await login({ username: email, password });
      
      if (loggedInUser) {
        console.log('Login successful, user roles:', loggedInUser.roles);
        setAuthenticatedUser(loggedInUser);
        
        if (loggedInUser.roles && loggedInUser.roles.length > 1) {
          // Multiple roles - show role selection
          setCurrentStep('role-selection');
        } else if (loggedInUser.roles && loggedInUser.roles.length === 1) {
          // Single role - auto-select and redirect
          setCurrentStep('redirecting');
          const role = loggedInUser.roles[0];
          await switchRole(role.company_id, role.role_id);
          console.log('Single role selected, redirecting to dashboard');
          router.replace('/dashboard');
        } else {
          setLoginError('No roles assigned to this user. Please contact your administrator.');
        }
      } else {
        setLoginError('Login failed. Please check your credentials and try again.');
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoginError(error instanceof Error ? error.message : 'Login failed. Please try again.');
    }
  };

  const handleRoleSelect = async () => {
    if (!selectedRole) {
      setLoginError('Please select a role to continue');
      return;
    }

    try {
      setCurrentStep('redirecting');
      console.log('Switching to role:', selectedRole);
      await switchRole(selectedRole.companyId, selectedRole.roleId);
      console.log('Role switched successfully, redirecting to dashboard');
      router.replace('/dashboard');
    } catch (error) {
      console.error('Role switch error:', error);
      setLoginError(error instanceof Error ? error.message : 'Failed to switch role. Please try again.');
      setCurrentStep('role-selection');
    }
  };

  const getRoleDisplayName = (role: string, roleName?: string) => {
    if (roleName) {
      return roleName;
    }
    switch (role) {
      case 'ADMIN':
        return 'Administrator';
      case 'HOST':
        return 'Host Company User';
      case 'ADVERTISER':
        return 'Advertiser Company User';
      default:
        return role;
    }
  };

  const getCompanyDisplayName = (companyId: string) => {
    // This function is kept for compatibility but should be removed
    // Company names should come from the API
    switch (companyId) {
      case 'global':
      case 'system':
        return 'System';
      default:
        return companyId ? `Company ${companyId.slice(-3)}` : 'No Company';
    }
  };

  // Show loading screen during initial authentication check
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <Card className="w-full max-w-md">
          <CardContent className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-2 text-sm text-muted-foreground">Loading...</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Role selection step
  if (currentStep === 'role-selection' && authenticatedUser?.roles) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <Card className="w-full max-w-md shadow-xl">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
            <CardTitle className="text-xl">Select Your Role</CardTitle>
            <CardDescription>
              Welcome back, {authenticatedUser.name || authenticatedUser.email}! 
              <br />Please choose your role to continue.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loginError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{loginError}</AlertDescription>
              </Alert>
            )}
            <div>
              <Label>Select Role & Company</Label>
              <Select onValueChange={(value) => {
                const [companyId, roleId] = value.split('|');
                setSelectedRole({ companyId, roleId });
                setLoginError(null);
              }}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose your role and company" />
                </SelectTrigger>
                <SelectContent>
                  {authenticatedUser.roles.map((role: any, index: number) => (
                    <SelectItem key={index} value={`${role.company_id}|${role.role_id}`}>
                      <div className="flex items-center gap-3 py-2">
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                        <div className="flex flex-col">
                          <span className="font-medium">
                            {getRoleDisplayName(role.role, role.role_name)}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            Company: {getCompanyDisplayName(role.company_id)}
                          </span>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setCurrentStep('login');
                  setAuthenticatedUser(null);
                  setSelectedRole(null);
                }}
                className="w-full"
              >
                Back
              </Button>
              <Button
                onClick={handleRoleSelect}
                className="w-full"
                disabled={!selectedRole || loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Continue
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Redirecting step
  if (currentStep === 'redirecting') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <Card className="w-full max-w-md shadow-xl">
          <CardContent className="flex flex-col items-center justify-center py-8 text-center">
            <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Successfully Logged In!</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Redirecting you to your dashboard...
            </p>
            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main login form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-white rounded-xl flex items-center justify-center mb-4 shadow-lg">
            <img
              src="/images/logo.png"
              alt="Adara Logo"
              className="w-12 h-12 object-contain"
              onError={(e) => {
                // Fallback to icon if logo fails to load
                const target = e.currentTarget as HTMLImageElement;
                target.style.display = 'none';
                const fallback = target.nextElementSibling as HTMLElement;
                if (fallback) fallback.classList.remove('hidden');
              }}
            />
            <div className="hidden w-12 h-12 flex items-center justify-center text-blue-600">
              <User className="w-8 h-8" />
            </div>
          </div>
          <CardTitle className="text-2xl">
            Welcome to{' '}
            <span className="text-blue-600">Adara</span>
            <span className="text-xs text-muted-foreground block mt-1">from Hebron™</span>
          </CardTitle>
          <CardDescription>
            Sign in to access your digital kiosk dashboard
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            {loginError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{loginError}</AlertDescription>
              </Alert>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="pl-10"
                  required
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="pl-10"
                  required
                />
              </div>
            </div>
            <Button 
              type="submit" 
              className="w-full" 
              disabled={loading || !email || !password}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Signing In...
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4 mr-2" />
                  Sign In
                </>
              )}
            </Button>
          </form>
          
          <div className="mt-6 text-center space-y-2">
            <p className="text-sm text-muted-foreground">
              <a href="/reset-password" className="text-blue-600 hover:underline font-medium">
                Forgot your password?
              </a>
            </p>
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-muted-foreground">or</span>
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              Don't have an account?{' '}
              <a href="/signup" className="text-blue-600 hover:underline font-medium">
                Sign up
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
