'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAuth } from '@/hooks/useAuth';

export default function SettingsPage() {
  const { user, hasRole, getDefaultRole } = useAuth();
  const [settings, setSettings] = useState({
    notifications: true,
    emailUpdates: false,
    autoApprove: false,
    theme: 'light',
    language: 'en'
  });

  const handleSave = () => {
    // Mock save settings
    alert('Settings saved successfully!');
  };

  if (!user) return <div>Loading...</div>;

  return (
    <div className="h-full p-6">
      <h2 className="text-3xl font-bold mb-8">Settings</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Profile Settings</CardTitle>
            <CardDescription>
              Manage your account information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                name="name"
                type="text"
                autoComplete="name"
                defaultValue={user.name || user.email}
                placeholder="Enter your name"
              />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                defaultValue={user.email}
                placeholder="Enter your email"
              />
            </div>
            <div>
              <Label htmlFor="role">Role</Label>
              <Input
                id="role"
                value={getDefaultRole()?.role_name || 'No Role'}
                disabled
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Preferences</CardTitle>
            <CardDescription>
              Customize your experience
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <Label>Email Notifications</Label>
                <p className="text-sm text-gray-600">Receive updates via email</p>
              </div>
              <Switch
                checked={settings.notifications}
                onCheckedChange={(checked: boolean) =>
                  setSettings({ ...settings, notifications: checked })
                }
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label>Campaign Updates</Label>
                <p className="text-sm text-gray-600">Get notified about campaign changes</p>
              </div>
              <Switch
                checked={settings.emailUpdates}
                onCheckedChange={(checked: boolean) =>
                  setSettings({ ...settings, emailUpdates: checked })
                }
              />
            </div>
            {hasRole('HOST') && (
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-approve Ads</Label>
                  <p className="text-sm text-gray-600">Automatically approve ads from trusted advertisers</p>
                </div>
                <Switch
                  checked={settings.autoApprove}
                  onCheckedChange={(checked: boolean) =>
                    setSettings({ ...settings, autoApprove: checked })
                  }
                />
              </div>
            )}
            <div>
              <Label htmlFor="theme">Theme</Label>
              <Select value={settings.theme} onValueChange={(value) =>
                setSettings({ ...settings, theme: value })
              } name="theme">
                <SelectTrigger id="theme">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="language">Language</Label>
              <Select value={settings.language} onValueChange={(value) =>
                setSettings({ ...settings, language: value })
              } name="language">
                <SelectTrigger id="language">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="ar">Arabic</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {hasRole('ADMIN') && (
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>System Settings</CardTitle>
              <CardDescription>
                Administrative system configuration
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label htmlFor="moderationThreshold">AI Moderation Threshold</Label>
                <Input
                  id="moderationThreshold"
                  type="number"
                  defaultValue="0.95"
                  step="0.01"
                  min="0"
                  max="1"
                />
                <p className="text-sm text-gray-600 mt-1">
                  Minimum confidence score for auto-approval (0.0 - 1.0)
                </p>
              </div>
              <div>
                <Label htmlFor="maxFileSize">Maximum File Size (MB)</Label>
                <Input
                  id="maxFileSize"
                  type="number"
                  defaultValue="50"
                />
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="mt-8 flex justify-end">
        <Button onClick={handleSave}>Save Settings</Button>
      </div>
    </div>
  );
}
