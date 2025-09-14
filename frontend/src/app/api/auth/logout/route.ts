import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    console.log('Logout API route called');
    
    // Get authorization header from the request
    const authHeader = request.headers.get('authorization');
    
    // Forward the request to the backend
    const backendUrl = `${BACKEND_URL}/api/auth/logout`;
    console.log('Forwarding logout to backend URL:', backendUrl);
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    console.log('Backend logout response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('Backend logout error response:', errorText);
      
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { detail: 'Logout failed' };
      }
      
      return NextResponse.json(
        { detail: errorData.detail || 'Logout failed' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Backend logout successful');

    return NextResponse.json(data);
  } catch (error) {
    console.error('Logout proxy error:', error);
    return NextResponse.json(
      { 
        detail: 'Internal server error',
        error: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}
