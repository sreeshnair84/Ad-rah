import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    console.log('Login API route called');
    
    const body = await request.json();
    console.log('Login request body:', { email: body.email, password: '***' });

    // Forward the request to the backend
    const backendUrl = `${BACKEND_URL}/api/auth/login`;
    console.log('Forwarding to backend URL:', backendUrl);
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    console.log('Backend response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('Backend error response:', errorText);
      
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { detail: 'Authentication failed' };
      }
      
      return NextResponse.json(
        { detail: errorData.detail || 'Authentication failed' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Backend login response received');

    return NextResponse.json(data);
  } catch (error) {
    console.error('Login proxy error:', error);
    return NextResponse.json(
      { 
        detail: 'Internal server error',
        error: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}
