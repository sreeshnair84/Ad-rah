import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(
  request: NextRequest,
  { params }: { params: { deviceId: string } }
) {
  try {
    const { deviceId } = params;

    // Check for invalid device ID
    if (!deviceId || deviceId === 'null' || deviceId === 'undefined') {
      console.error('Invalid device ID received:', deviceId);
      return NextResponse.json(
        {
          error: 'Invalid device ID',
          message: 'Device ID cannot be null or undefined',
          received_device_id: deviceId,
          debug_info: {
            timestamp: new Date().toISOString(),
            user_agent: request.headers.get('user-agent'),
            referer: request.headers.get('referer'),
            origin: request.headers.get('origin')
          }
        },
        { status: 400 }
      );
    }

    // Forward the Authorization header from the frontend request
    const authHeader = request.headers.get('authorization');
    const headers: HeadersInit = {};

    if (authHeader) {
      headers.Authorization = authHeader;
    }

    // Check if authorization is present for device analytics
    if (!authHeader) {
      console.error('No authorization header for device analytics:', deviceId);
      return NextResponse.json(
        {
          error: 'Authentication required',
          message: 'Device analytics requires authentication',
          device_id: deviceId
        },
        { status: 401 }
      );
    }

    const body = await request.json();

    const backendResponse = await fetch(`${BACKEND_URL}/api/devices/analytics/${deviceId}`, {
      method: 'POST',
      headers: {
        ...headers,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const responseData = await backendResponse.json();

    return NextResponse.json(responseData, {
      status: backendResponse.status,
    });
  } catch (error) {
    console.error('Device analytics proxy error:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

export async function OPTIONS(request: NextRequest) {
  return NextResponse.json({}, { status: 200 });
}