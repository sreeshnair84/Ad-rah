import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Get authorization header from the request
    const authHeader = request.headers.get('authorization');
    
    if (!authHeader) {
      return NextResponse.json(
        { detail: 'Authorization header missing' },
        { status: 401 }
      );
    }

    // Forward the request to the backend
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    const fetchUrl = `${backendUrl}/api/auth/me`;
    
    console.log('Environment BACKEND_URL:', process.env.BACKEND_URL);
    console.log('Using backend URL:', backendUrl);
    console.log('Full fetch URL:', fetchUrl);
    console.log('Authorization header present:', !!authHeader);
    
    const requestHeaders = {
      'Content-Type': 'application/json',
      'Authorization': authHeader,
    };
    console.log('Request headers:', requestHeaders);
    
    const response = await fetch(fetchUrl, {
      method: 'GET',
      headers: requestHeaders,
    });

    console.log('Backend response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('Backend error response:', errorText);
      
      return NextResponse.json(
        { detail: 'Authentication failed' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Backend user data received:', data);

    return NextResponse.json(data);
  } catch (error) {
    console.error('Get current user error:', error);
    return NextResponse.json(
      { 
        detail: 'Internal server error',
        error: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}
