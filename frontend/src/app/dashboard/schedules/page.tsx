'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface Schedule {
  id: string;
  campaign: string;
  startDate: string;
  endDate: string;
  frequency: string;
  status: string;
  screens: number;
}

export default function SchedulesPage() {
  const [schedules] = useState<Schedule[]>([]); // TODO: Replace with API call to fetch schedules

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
            <p className="text-2xl font-bold">0</p> {/* TODO: Replace with API data */}
            <p className="text-sm text-gray-600">Running now</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Scheduled</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">0</p> {/* TODO: Replace with API data */}
            <p className="text-sm text-gray-600">Upcoming</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Total Screens</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">0</p> {/* TODO: Replace with API data */}
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
