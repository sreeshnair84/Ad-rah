'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import { Building2, Shield, User, Lock, AlertCircle, CheckCircle, Loader2, Crown } from 'lucide-react';
import Image from 'next/image';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState<string | null>(null);
  const router = useRouter();
  const { login, user, loading, isInitialized, getDisplayName, getRoleDisplay } = useAuth();

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
      const loggedInUser = await login({ email, password });
      
      if (loggedInUser) {
        console.log('Login successful, user type:', loggedInUser.user_type);
        
        // Show success message briefly then redirect
        setTimeout(() => {
          console.log('Redirecting to dashboard');
          router.replace('/dashboard');
        }, 1000);
      } else {
        setLoginError('Login failed. Please check your credentials and try again.');
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoginError(error instanceof Error ? error.message : 'Login failed. Please try again.');
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <Card className="w-full max-w-md">
          <CardContent className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-2 text-sm text-muted-foreground">Initializing...</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show success message if user is logged in (before redirect)
  if (user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <Card className="w-full max-w-md shadow-xl">
          <CardContent className="flex flex-col items-center justify-center py-8 text-center">
            <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Welcome back!</h3>
            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-center gap-2">
                {getUserTypeIcon(user.user_type)}
                <span className="text-sm font-medium">{getDisplayName()}</span>
              </div>
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <span>{getRoleDisplay()}</span>
                {user.company?.name && <span>• {user.company.name}</span>}
              </div>
            </div>
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
          <div className="mx-auto w-16 h-16 bg-white rounded-xl flex items-center justify-center mb-4 shadow-lg border border-gray-100">
            <Image
              src="/images/logo.png"
              alt="Adara Logo"
              width={56}
              height={56}
              className="w-14 h-14 object-contain"
              priority
              onError={(e) => {
                // Fallback to icon if logo fails to load
                const target = e.currentTarget as HTMLImageElement;
                target.style.display = 'none';
                const fallback = target.nextElementSibling as HTMLElement;
                if (fallback) fallback.classList.remove('hidden');
              }}
            />
            <div className="hidden w-14 h-14 flex items-center justify-center text-blue-600">
              <User className="w-8 h-8" />
            </div>
          </div>
          <CardTitle className="text-2xl">
            Welcome to{' '}
            <span className="text-blue-600">Adara</span>
            <span className="text-xs text-muted-foreground block mt-1">Digital Signage Platform™</span>
          </CardTitle>
          <CardDescription>
            Sign in to access your digital signage dashboard
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
              Don&apos;t have an account?{' '}
              <a href="/company-registration" className="text-blue-600 hover:underline font-medium">
                Register Company
              </a>
            </p>
          </div>

          {/* Enhanced RBAC Features Info */}
          <div className="mt-6 border-t pt-4">
            <h4 className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
              Enhanced Security Features
            </h4>
            <div className="grid grid-cols-1 gap-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-2">
                <Shield className="w-3 h-3 text-blue-500" />
                <span>Role-based access control</span>
              </div>
              <div className="flex items-center gap-2">
                <Building2 className="w-3 h-3 text-green-500" />
                <span>Company data isolation</span>
              </div>
              <div className="flex items-center gap-2">
                <Crown className="w-3 h-3 text-purple-500" />
                <span>Granular permissions</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
