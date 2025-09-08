'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Monitor, Key, CheckCircle, AlertCircle, Loader2, QrCode } from 'lucide-react';

export default function DeviceRegistrationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    device_name: '',
    organization_code: '',
    registration_key: '',
    aspect_ratio: '',
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/devices/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          device_name: formData.device_name,
          organization_code: formData.organization_code,
          registration_key: formData.registration_key,
          aspect_ratio: formData.aspect_ratio || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to register device');
      }

      const result = await response.json();
      setSuccess(true);

      // Store device info in localStorage for future use
      localStorage.setItem('device_id', result.device_id);
      localStorage.setItem('organization_code', result.organization_code);
      localStorage.setItem('company_name', result.company_name);

      // Redirect after success
      setTimeout(() => {
        router.push('/dashboard');
      }, 3000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to register device');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Device Registered!</h2>
              <p className="text-gray-600 mb-4">
                Your device has been successfully registered and is now ready to display content.
              </p>
              <Button onClick={() => router.push('/dashboard')}>
                Go to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <Monitor className="h-12 w-12 text-blue-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900">Device Registration</h1>
          <p className="text-gray-600 mt-2">
            Register your digital signage device to start displaying content
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Device Setup</CardTitle>
            <CardDescription>
              Enter your device information and registration key to connect to the platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Device Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Device Information</h3>

                <div>
                  <Label htmlFor="device_name">Device Name *</Label>
                  <Input
                    id="device_name"
                    value={formData.device_name}
                    onChange={(e) => handleInputChange('device_name', e.target.value)}
                    placeholder="e.g., Lobby Display, Store Screen 1"
                    required
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Choose a descriptive name for your device
                  </p>
                </div>

                <div>
                  <Label htmlFor="organization_code">Organization Code *</Label>
                  <Input
                    id="organization_code"
                    value={formData.organization_code}
                    onChange={(e) => handleInputChange('organization_code', e.target.value)}
                    placeholder="Enter your organization code"
                    required
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Provided by your organization administrator
                  </p>
                </div>

                <div>
                  <Label htmlFor="registration_key">Registration Key *</Label>
                  <div className="relative">
                    <Input
                      id="registration_key"
                      type="password"
                      value={formData.registration_key}
                      onChange={(e) => handleInputChange('registration_key', e.target.value)}
                      placeholder="Enter registration key"
                      required
                    />
                    <Key className="absolute right-3 top-3 h-4 w-4 text-gray-400" />
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Secure key provided by your organization
                  </p>
                </div>

                <div>
                  <Label htmlFor="aspect_ratio">Aspect Ratio (Optional)</Label>
                  <Input
                    id="aspect_ratio"
                    value={formData.aspect_ratio}
                    onChange={(e) => handleInputChange('aspect_ratio', e.target.value)}
                    placeholder="e.g., 16:9, 4:3"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Screen aspect ratio for optimal content display
                  </p>
                </div>
              </div>

              {/* QR Code Option */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Alternative Registration</h3>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <QrCode className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">
                    Scan QR code for quick registration
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      // TODO: Implement QR scanner
                      alert('QR scanner will be implemented');
                    }}
                  >
                    Scan QR Code
                  </Button>
                </div>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Registering Device...
                  </>
                ) : (
                  'Register Device'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600">
            Need help? Contact your organization administrator for registration details.
          </p>
        </div>
      </div>
    </div>
  );
}
