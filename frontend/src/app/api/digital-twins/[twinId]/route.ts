import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { twinId: string } }
) {
  try {
    // Forward the Authorization header from the frontend request
    const authHeader = request.headers.get('authorization');
    const headers: HeadersInit = {};
    
    if (authHeader) {
      headers.Authorization = authHeader;
    }

    const backendResponse = await fetch(`${BACKEND_URL}/api/digital-twins/${params.twinId}`, {
      headers,
    });

    const responseData = await backendResponse.json();

    return NextResponse.json(responseData, {
      status: backendResponse.status,
    });
  } catch (error) {
    console.error('Digital twin get proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { twinId: string } }
) {
  try {
    const body = await request.json();
    
    // Forward the Authorization header from the frontend request
    const authHeader = request.headers.get('authorization');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (authHeader) {
      headers.Authorization = authHeader;
    }

    const backendResponse = await fetch(`${BACKEND_URL}/api/digital-twins/${params.twinId}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body),
    });

    const responseData = await backendResponse.json();

    return NextResponse.json(responseData, {
      status: backendResponse.status,
    });
  } catch (error) {
    console.error('Digital twin update proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { twinId: string } }
) {
  try {
    // Forward the Authorization header from the frontend request
    const authHeader = request.headers.get('authorization');
    const headers: HeadersInit = {};
    
    if (authHeader) {
      headers.Authorization = authHeader;
    }

    const backendResponse = await fetch(`${BACKEND_URL}/api/digital-twins/${params.twinId}`, {
      method: 'DELETE',
      headers,
    });

    const responseData = await backendResponse.json();

    return NextResponse.json(responseData, {
      status: backendResponse.status,
    });
  } catch (error) {
    console.error('Digital twin delete proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
