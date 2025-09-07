import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(
  request: NextRequest,
  { params }: { params: { contentId: string } }
) {
  try {
    // Forward the Authorization header from the frontend request
    const authHeader = request.headers.get('authorization');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (authHeader) {
      headers.Authorization = authHeader;
    }

    const body = await request.json();

    // Convert the body format to match backend expectations
    const formData = new FormData();
    if (body.device_ids && Array.isArray(body.device_ids)) {
      body.device_ids.forEach((deviceId: string) => {
        formData.append('target_devices', deviceId);
      });
    }

    const backendResponse = await fetch(`${BACKEND_URL}/api/content/distribute/${params.contentId}`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader || '',
      },
      body: formData,
    });

    const responseData = await backendResponse.json();

    return NextResponse.json(responseData, {
      status: backendResponse.status,
    });
  } catch (error) {
    console.error('Content distribute proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}