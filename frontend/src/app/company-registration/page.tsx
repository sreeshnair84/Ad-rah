'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Building2, Upload, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface CompanyApplicationData {
  company_name: string;
  company_type: 'HOST' | 'ADVERTISER';
  business_license: string;
  address: string;
  city: string;
  country: string;
  website?: string;
  description: string;
  applicant_name: string;
  applicant_email: string;
  applicant_phone: string;
  documents: Record<string, string>;
}

export default function CompanyRegistrationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState<CompanyApplicationData>({
    company_name: '',
    company_type: 'HOST',
    business_license: '',
    address: '',
    city: '',
    country: '',
    website: '',
    description: '',
    applicant_name: '',
    applicant_email: '',
    applicant_phone: '',
    documents: {},
  });

  const handleInputChange = (field: keyof CompanyApplicationData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDocumentUpload = (documentType: string, file: File) => {
    // In a real implementation, you would upload the file to a server
    // For now, we'll just store the filename
    setFormData(prev => ({
      ...prev,
      documents: {
        ...prev.documents,
        [documentType]: file.name
      }
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/company-applications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit application');
      }

      const result = await response.json();
      setSuccess(true);

      // Redirect to success page or show success message
      setTimeout(() => {
        router.push('/login');
      }, 3000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit application');
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
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Application Submitted!</h2>
              <p className="text-gray-600 mb-4">
                Your company registration application has been submitted successfully.
                You will receive an email with login credentials once your application is approved.
              </p>
              <Button onClick={() => router.push('/login')}>
                Go to Login
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
          <Building2 className="h-12 w-12 text-blue-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900">Company Registration</h1>
          <p className="text-gray-600 mt-2">
            Register your company to join the Adara Digital Signage platform
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Registration Form</CardTitle>
            <CardDescription>
              Please provide your company information and business details
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Company Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Company Information</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="company_name">Company Name *</Label>
                    <Input
                      id="company_name"
                      value={formData.company_name}
                      onChange={(e) => handleInputChange('company_name', e.target.value)}
                      placeholder="Enter company name"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="company_type">Company Type *</Label>
                    <Select
                      value={formData.company_type}
                      onValueChange={(value: 'HOST' | 'ADVERTISER') => handleInputChange('company_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select company type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="HOST">Host - Venue Owner</SelectItem>
                        <SelectItem value="ADVERTISER">Advertiser - Content Provider</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="business_license">Business License *</Label>
                  <Input
                    id="business_license"
                    value={formData.business_license}
                    onChange={(e) => handleInputChange('business_license', e.target.value)}
                    placeholder="Enter business license number"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="description">Business Description *</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Describe your business and services"
                    rows={4}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="address">Address *</Label>
                    <Input
                      id="address"
                      value={formData.address}
                      onChange={(e) => handleInputChange('address', e.target.value)}
                      placeholder="Street address"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="city">City *</Label>
                    <Input
                      id="city"
                      value={formData.city}
                      onChange={(e) => handleInputChange('city', e.target.value)}
                      placeholder="City"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="country">Country *</Label>
                    <Input
                      id="country"
                      value={formData.country}
                      onChange={(e) => handleInputChange('country', e.target.value)}
                      placeholder="Country"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="website">Website</Label>
                    <Input
                      id="website"
                      type="url"
                      value={formData.website}
                      onChange={(e) => handleInputChange('website', e.target.value)}
                      placeholder="https://www.example.com"
                    />
                  </div>
                </div>
              </div>

              {/* Applicant Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Applicant Information</h3>

                <div>
                  <Label htmlFor="applicant_name">Full Name *</Label>
                  <Input
                    id="applicant_name"
                    value={formData.applicant_name}
                    onChange={(e) => handleInputChange('applicant_name', e.target.value)}
                    placeholder="Enter your full name"
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="applicant_email">Email Address *</Label>
                    <Input
                      id="applicant_email"
                      type="email"
                      value={formData.applicant_email}
                      onChange={(e) => handleInputChange('applicant_email', e.target.value)}
                      placeholder="Enter email address"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="applicant_phone">Phone Number *</Label>
                    <Input
                      id="applicant_phone"
                      type="tel"
                      value={formData.applicant_phone}
                      onChange={(e) => handleInputChange('applicant_phone', e.target.value)}
                      placeholder="Enter phone number"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Document Upload */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Document Upload</h3>
                <p className="text-sm text-gray-600">
                  Please upload the following documents to complete your registration:
                </p>

                <div className="space-y-3">
                  {[
                    { key: 'business_license_doc', label: 'Business License Document' },
                    { key: 'tax_certificate', label: 'Tax Certificate' },
                    { key: 'company_registration', label: 'Company Registration Certificate' },
                    { key: 'identification', label: 'Applicant Identification' },
                  ].map((doc) => (
                    <div key={doc.key} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <Upload className="h-5 w-5 text-gray-400" />
                        <span className="text-sm">{doc.label}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {formData.documents[doc.key] && (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        )}
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            // Simulate file upload
                            const mockFile = new File([''], `${doc.label}.pdf`);
                            handleDocumentUpload(doc.key, mockFile);
                          }}
                        >
                          Upload
                        </Button>
                      </div>
                    </div>
                  ))}
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
                    Submitting Application...
                  </>
                ) : (
                  'Submit Application'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
