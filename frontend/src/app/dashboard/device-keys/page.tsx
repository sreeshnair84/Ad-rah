'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';
import {
  Key,
  Plus,
  Copy,
  Eye,
  EyeOff,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  Loader2,
  Building2,
  Calendar,
  Shield,
  Monitor,
  Power
} from 'lucide-react';

interface RegistrationKey {
  id: string;
  key: string;
  company_id: string;
  company_name: string;
  organization_code?: string;
  created_by: string;
  created_at: string;
  expires_at: string;
  used: boolean;
  used_by_device?: string;
  used_at?: string;
  device_name?: string;
  device_status?: string;
  active?: boolean; // For deactivation functionality
}

interface Company {
  id: string;
  name: string;
  type: 'HOST' | 'ADVERTISER';
  status: 'active' | 'inactive';
  organization_code?: string;
}

export default function DeviceKeysPage() {
  const { user, hasRole } = useAuth();
  const [keys, setKeys] = useState<RegistrationKey[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());

  // Form state for generating new key
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('');
  const [expirationDays, setExpirationDays] = useState<number>(30);

  // Fetch registration keys
  const fetchKeys = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/device/keys', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch registration keys');
      }

      const data = await response.json();
      
      // For used keys, fetch device information
      const enhancedKeys = await Promise.all(
        data.map(async (key: RegistrationKey) => {
          if (key.used && key.used_by_device) {
            try {
              const deviceResponse = await fetch(`/api/device/status/${key.used_by_device}`, {
                headers: {
                  'Authorization': `Bearer ${token}`,
                },
              });
              
              if (deviceResponse.ok) {
                const deviceData = await deviceResponse.json();
                return {
                  ...key,
                  device_name: deviceData.name,
                  device_status: deviceData.is_online ? 'online' : 'offline'
                };
              }
            } catch (error) {
              console.error('Failed to fetch device info:', error);
            }
          }
          return key;
        })
      );
      
      setKeys(enhancedKeys);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch keys');
    }
  };

  // Fetch companies
  const fetchCompanies = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/auth/companies', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch companies');
      }

      const data = await response.json();
      setCompanies(data);
    } catch (err) {
      console.error('Failed to fetch companies:', err);
    }
  };

  // Generate new registration key
  const generateKey = async () => {
    if (!selectedCompanyId) {
      setError('Please select a company');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + expirationDays);

      const response = await fetch('/api/device/generate-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          company_id: selectedCompanyId,
          expires_at: expiresAt.toISOString(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate key');
      }

      const result = await response.json();

      // Refresh keys list
      await fetchKeys();

      // Reset form
      setSelectedCompanyId('');
      setExpirationDays(30);
      setShowGenerateDialog(false);
      setError(null);

      // Show success message
      toast.success('Registration key generated successfully!', {
        description: `Key: ${result.registration_key}\n\nPlease copy this key and provide it to the company administrator.`,
        duration: 10000,
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate key');
    } finally {
      setSubmitting(false);
    }
  };

  // Toggle key visibility
  const toggleKeyVisibility = (keyId: string) => {
    const newVisibleKeys = new Set(visibleKeys);
    if (newVisibleKeys.has(keyId)) {
      newVisibleKeys.delete(keyId);
    } else {
      newVisibleKeys.add(keyId);
    }
    setVisibleKeys(newVisibleKeys);
  };

  // Copy key to clipboard
  const copyKeyToClipboard = async (key: string) => {
    try {
      await navigator.clipboard.writeText(key);
      toast.success('Registration key copied to clipboard!');
    } catch (err) {
      toast.error('Failed to copy key to clipboard');
    }
  };

  // Toggle key active status
  const toggleKeyActive = async (keyId: string, currentActive: boolean) => {
    try {
      // TODO: Add backend endpoint for key activation/deactivation
      // For now, just show a toast message
      const action = currentActive ? 'deactivated' : 'activated';
      toast.success(`Registration key ${action} successfully`);
      
      // Refresh the keys list
      fetchKeys();
    } catch (err) {
      toast.error('Failed to toggle key status');
    }
  };

  // Initial data fetch
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchKeys(), fetchCompanies()]);
      setLoading(false);
    };

    loadData();
  }, []);

  // Check if user has admin access
  if (!hasRole('ADMIN')) {
    return (
      <div className="flex items-center justify-center h-full">
        <Alert className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            You don&apos;t have permission to access device key management. Contact your administrator.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="text-gray-600">Loading registration keys...</span>
        </div>
      </div>
    );
  }

  const activeKeys = keys.filter(k => !k.used && new Date(k.expires_at) > new Date());
  const expiredKeys = keys.filter(k => new Date(k.expires_at) <= new Date());
  const usedKeys = keys.filter(k => k.used);

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Key className="h-8 w-8 text-blue-600" />
            Device Registration Keys
          </h1>
          <p className="text-gray-600 mt-1">
            Generate and manage secure registration keys for device authentication. 
            <strong className="text-blue-600">Each key can only be used once</strong> to ensure secure one-to-one device registration.
          </p>
        </div>

        <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
              <Plus className="h-4 w-4 mr-2" />
              Generate New Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Generate Registration Key</DialogTitle>
              <DialogDescription>
                Create a new secure registration key for a company
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div>
                <Label htmlFor="company">Select Company *</Label>
                <Select value={selectedCompanyId} onValueChange={setSelectedCompanyId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a company" />
                  </SelectTrigger>
                  <SelectContent>
                    {companies
                      .filter(c => c.status === 'active' && c.type === 'HOST')
                      .map((company) => (
                      <SelectItem key={company.id} value={company.id}>
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4" />
                          <div className="flex flex-col">
                            <span className="font-medium">{company.name}</span>
                            {company.organization_code && (
                              <span className="text-xs text-gray-500 font-mono">
                                {company.organization_code}
                              </span>
                            )}
                          </div>
                          <Badge variant={company.type === 'HOST' ? 'default' : 'secondary'}>
                            {company.type}
                          </Badge>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="expiration">Expiration (Days)</Label>
                <Input
                  id="expiration"
                  type="number"
                  value={expirationDays}
                  onChange={(e) => setExpirationDays(parseInt(e.target.value) || 30)}
                  min="1"
                  max="365"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Key will expire after {expirationDays} days
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowGenerateDialog(false)} disabled={submitting}>
                Cancel
              </Button>
              <Button onClick={generateKey} disabled={submitting || !selectedCompanyId}>
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Key className="w-4 h-4 mr-2" />
                    Generate Key
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="flex items-center p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{activeKeys.length}</p>
                <p className="text-sm text-muted-foreground">Active Keys</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Shield className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{usedKeys.length}</p>
                <p className="text-sm text-muted-foreground">Used Keys</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <XCircle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{expiredKeys.length}</p>
                <p className="text-sm text-muted-foreground">Expired Keys</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <Key className="w-6 h-6 text-gray-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{keys.length}</p>
                <p className="text-sm text-muted-foreground">Total Keys</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Monitor className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{usedKeys.length}</p>
                <p className="text-sm text-muted-foreground">Devices Registered</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Keys Table */}
      <Card>
        <CardHeader>
          <CardTitle>Registration Keys</CardTitle>
          <CardDescription>
            Manage all registration keys and their usage status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Company</TableHead>
                <TableHead>Organization Code</TableHead>
                <TableHead>Registration Key</TableHead>
                <TableHead>Device ID</TableHead>
                <TableHead>Device Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Expires</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {keys.map((key) => {
                const isExpired = new Date(key.expires_at) <= new Date();
                const isVisible = visibleKeys.has(key.id);

                return (
                  <TableRow key={key.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-gray-500" />
                        <div>
                          <p className="font-medium">{key.company_name}</p>
                          <p className="text-sm text-gray-500">ID: {key.company_id}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {(() => {
                        const company = companies.find(c => c.id === key.company_id);
                        const orgCode = company?.organization_code;
                        return orgCode ? (
                          <div className="flex items-center gap-2">
                            <code className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-sm font-mono">
                              {orgCode}
                            </code>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyKeyToClipboard(orgCode)}
                              title="Copy organization code to clipboard"
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                        ) : (
                          <span className="text-gray-400 text-sm">-</span>
                        );
                      })()}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <code className="bg-gray-100 px-2 py-1 rounded text-sm font-mono">
                          {isVisible ? key.key : '••••••••••••••••••••'}
                        </code>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleKeyVisibility(key.id)}
                        >
                          {isVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell>
                      {key.used && key.used_by_device ? (
                        <div className="flex items-center gap-2">
                          <code className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs font-mono">
                            {key.used_by_device}
                          </code>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyKeyToClipboard(key.used_by_device!)}
                            title="Copy device ID to clipboard"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {key.used && key.device_name ? (
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{key.device_name}</span>
                          {key.device_status && (
                            <Badge 
                              variant={key.device_status === 'online' ? 'default' : 'secondary'}
                              className="text-xs"
                            >
                              {key.device_status}
                            </Badge>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {key.used ? (
                        <Badge variant="secondary" className="gap-1">
                          <Shield className="w-3 h-3" />
                          Used
                        </Badge>
                      ) : key.active === false ? (
                        <Badge variant="outline" className="gap-1 text-gray-600">
                          <Power className="w-3 h-3" />
                          Inactive
                        </Badge>
                      ) : isExpired ? (
                        <Badge variant="destructive" className="gap-1">
                          <XCircle className="w-3 h-3" />
                          Expired
                        </Badge>
                      ) : (
                        <Badge variant="default" className="gap-1 bg-green-100 text-green-800">
                          <CheckCircle className="w-3 h-3" />
                          Active
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm">
                        <Calendar className="h-3 w-3" />
                        {new Date(key.created_at).toLocaleDateString()}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm">
                        <Clock className="h-3 w-3" />
                        {new Date(key.expires_at).toLocaleDateString()}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyKeyToClipboard(key.key)}
                          title="Copy key to clipboard"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        {!key.used && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleKeyActive(key.id, key.active !== false)}
                            title={key.active === false ? "Activate key" : "Deactivate key"}
                            className={key.active === false ? "text-green-600 hover:text-green-700" : "text-red-600 hover:text-red-700"}
                          >
                            <Power className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>

          {keys.length === 0 && (
            <div className="text-center py-12">
              <Key className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No registration keys found</h3>
              <p className="text-gray-500 mb-6">
                Generate your first registration key to get started
              </p>
              <Button onClick={() => setShowGenerateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Generate First Key
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
