import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(
  request: NextRequest,
  { params }: { params: { contentId: string } }
) {
  try {
    // Forward the Authorization header from the frontend request
    const authHeader = request.headers.get('authorization');
    const headers: HeadersInit = {};
    
    if (authHeader) {
      headers.Authorization = authHeader;
    }

    const formData = await request.formData();

    const backendResponse = await fetch(`${BACKEND_URL}/api/content/admin/approve/${params.contentId}`, {
      method: 'POST',
      headers,
      body: formData,
    });

    const responseData = await backendResponse.json();

    return NextResponse.json(responseData, {
      status: backendResponse.status,
    });
  } catch (error) {
    console.error('Content approve proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}