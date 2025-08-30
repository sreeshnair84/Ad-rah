'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { useModerationQueue } from '@/hooks/useModerationQueue';

export default function ModerationPage() {
  const { pendingAds, loading, approveAd, getAIScoreBadge } = useModerationQueue();

  if (loading) return <div>Loading...</div>;

  return (
    <div className="grid gap-6 p-6 lg:grid-cols-3 h-full">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Moderation Queue</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {pendingAds.map((ad) => (
            <div key={ad.id} className="flex items-center gap-4 rounded-2xl border p-4">
              <div className="aspect-video w-40 rounded-xl border bg-muted" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">Ad #{ad.id} — {(ad.metadata?.title as string) || 'Untitled'}</p>
                <p className="text-xs text-muted-foreground">Requested by: {ad.business_id} • Dubai Mall</p>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                  <Badge variant="outline">AI: {getAIScoreBadge(ad.review.ai_score) === 'default' ? 'Safe' : 'Review'}</Badge>
                  <Badge variant="destructive">Missing Consent</Badge>
                  <Badge variant="secondary">Arabic OK</Badge>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" className="rounded-full">Request Fix</Button>
                <Button size="sm" className="rounded-full" onClick={() => approveAd(ad.id)}>Approve</Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Policy Quick-Toggle</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-xl border p-4">
            <div>
              <p className="text-sm font-medium">Political Ads</p>
              <p className="text-xs text-muted-foreground">Disable by default</p>
            </div>
            <Switch />
          </div>
          <div className="flex items-center justify-between rounded-xl border p-4">
            <div>
              <p className="text-sm font-medium">Gambling</p>
              <p className="text-xs text-muted-foreground">Require explicit host opt-in</p>
            </div>
            <Switch />
          </div>
          <div className="flex items-center justify-between rounded-xl border p-4">
            <div>
              <p className="text-sm font-medium">Adult Content</p>
              <p className="text-xs text-muted-foreground">Block on all screens</p>
            </div>
            <Switch />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
