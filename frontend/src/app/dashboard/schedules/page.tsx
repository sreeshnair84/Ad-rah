'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function SchedulesPage() {
  const [schedules] = useState([
    {
      id: 'SCH-001',
      campaign: 'Summer Pizza Deal',
      startDate: '2025-08-20',
      endDate: '2025-08-31',
      frequency: 'Daily',
      status: 'active',
      screens: 5
    },
    {
      id: 'SCH-002',
      campaign: 'Fashion Sale',
      startDate: '2025-08-15',
      endDate: '2025-08-25',
      frequency: 'Weekly',
      status: 'scheduled',
      screens: 3
    },
    {
      id: 'SCH-003',
      campaign: 'Restaurant Special',
      startDate: '2025-08-01',
      endDate: '2025-08-10',
      frequency: 'Daily',
      status: 'completed',
      screens: 8
    }
  ]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default">Active</Badge>;
      case 'scheduled':
        return <Badge variant="secondary">Scheduled</Badge>;
      case 'completed':
        return <Badge variant="outline">Completed</Badge>;
      case 'paused':
        return <Badge variant="destructive">Paused</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold">Ad Scheduling</h2>
        <Button>Create New Schedule</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Active Campaigns</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">3</p>
            <p className="text-sm text-gray-600">Running now</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Scheduled</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">5</p>
            <p className="text-sm text-gray-600">Upcoming</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Total Screens</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">16</p>
            <p className="text-sm text-gray-600">Available</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Campaign Schedules</CardTitle>
          <CardDescription>
            Manage your ad campaign schedules and timing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Schedule ID</TableHead>
                <TableHead>Campaign</TableHead>
                <TableHead>Start Date</TableHead>
                <TableHead>End Date</TableHead>
                <TableHead>Frequency</TableHead>
                <TableHead>Screens</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {schedules.map((schedule) => (
                <TableRow key={schedule.id}>
                  <TableCell className="font-medium">{schedule.id}</TableCell>
                  <TableCell>{schedule.campaign}</TableCell>
                  <TableCell>{new Date(schedule.startDate).toLocaleDateString()}</TableCell>
                  <TableCell>{new Date(schedule.endDate).toLocaleDateString()}</TableCell>
                  <TableCell>{schedule.frequency}</TableCell>
                  <TableCell>{schedule.screens}</TableCell>
                  <TableCell>{getStatusBadge(schedule.status)}</TableCell>
                  <TableCell>
                    <div className="space-x-2">
                      <Button variant="outline" size="sm">
                        Edit
                      </Button>
                      <Button variant="outline" size="sm">
                        Pause
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
