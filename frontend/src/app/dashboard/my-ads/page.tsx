'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useAds } from '@/hooks/useAds';
import { Upload, Filter, MapPin, PlaySquare, XCircle } from 'lucide-react';

export default function MyAdsPage() {
  const { ads, loading } = useAds();

  if (loading) return <div>Loading...</div>;

  return (
    <div className="grid gap-3 p-3 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Upload / Manage Ads</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Button variant="secondary" className="rounded-xl">
                <Upload className="mr-2 h-4 w-4" />
                Upload
              </Button>
              <Button variant="outline" className="rounded-xl">
                <Filter className="mr-2 h-4 w-4" />
                Filters
              </Button>
            </div>
            <Input 
              name="search-ads"
              type="search"
              autoComplete="off"
              placeholder="Search ads…" 
              className="max-w-xs rounded-full" 
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {ads.map((ad) => (
              <div key={ad.id} className="rounded-2xl border p-3">
                <div className="aspect-video rounded-xl border bg-muted" />
                <div className="mt-3 flex items-center gap-2">
                  <Badge variant="secondary">{ad.type}</Badge>
                  <Badge>{ad.category_id}</Badge>
                  <Badge variant="outline">EN/AR</Badge>
                </div>
                <div className="mt-2 flex items-center gap-2 text-sm">
                  <MapPin className="h-4 w-4" />
                  Dubai Mall, DIFC
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <Button size="sm" className="rounded-full">Schedule</Button>
                  <Button size="sm" variant="outline" className="rounded-full">Preview</Button>
                  <Button size="sm" variant="ghost" className="rounded-full">More</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>AI Pre-Check (Wire)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="rounded-xl border p-3">
            <p className="text-sm font-medium">Safety Flags</p>
            <ul className="mt-2 space-y-1 text-sm">
              <li className="flex items-center gap-2">
                <PlaySquare className="h-4 w-4 text-green-600" />
                Language OK
              </li>
              <li className="flex items-center gap-2">
                <PlaySquare className="h-4 w-4 text-green-600" />
                Brand-safe imagery
              </li>
              <li className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-600" />
                Missing Arabic subtitle
              </li>
            </ul>
          </div>
          <div className="rounded-xl border p-3">
            <Label className="text-sm">Notes to Reviewer</Label>
            <Textarea placeholder="Add context for moderators…" className="mt-2" />
            <div className="mt-2 flex gap-2">
              <Button className="rounded-full">Submit for Review</Button>
              <Button variant="outline" className="rounded-full">Save Draft</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
