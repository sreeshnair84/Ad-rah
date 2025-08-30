'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAdsApproval } from '@/hooks/useAdsApproval';

export default function AdsApprovalPage() {
  const { pendingAds, loading, handleApprove, handleReject, metrics } = useAdsApproval();

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold">Ads for Approval</h2>
        <Badge variant="secondary">{metrics.pendingCount} pending</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Pending Review</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{metrics.pendingCount}</p>
            <p className="text-sm text-gray-600">Ads awaiting approval</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Approved Today</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{metrics.approvedToday}</p>
            <p className="text-sm text-gray-600">This week: 45</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Rejected</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{metrics.rejectedThisWeek}</p>
            <p className="text-sm text-gray-600">This week: 8</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pending Ads</CardTitle>
          <CardDescription>
            Review and approve advertisements for your screens
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ad ID</TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Advertiser</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Submitted</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pendingAds.map((ad) => (
                <TableRow key={ad.id}>
                  <TableCell className="font-medium">{ad.id}</TableCell>
                  <TableCell>{(ad.metadata?.title as string) || 'Untitled'}</TableCell>
                  <TableCell>{ad.advertiser}</TableCell>
                  <TableCell>{ad.type}</TableCell>
                  <TableCell>{ad.category_id}</TableCell>
                  <TableCell>{new Date(ad.submittedDate).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <div className="space-x-2">
                      <Button
                        size="sm"
                        onClick={() => handleApprove(ad.id)}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleReject(ad.id)}
                      >
                        Reject
                      </Button>
                      <Button variant="outline" size="sm">
                        Preview
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
