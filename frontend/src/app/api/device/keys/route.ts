import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Get authorization header from the request
    const authHeader = request.headers.get('authorization');
    
    // Forward the request to the backend
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    const fetchUrl = `${backendUrl}/api/device/keys`;
    console.log('Environment BACKEND_URL:', process.env.BACKEND_URL);
    console.log('Using backend URL:', backendUrl);
    console.log('Full fetch URL:', fetchUrl);
    console.log('Authorization header present:', !!authHeader);
    console.log('Authorization header value:', authHeader ? authHeader.substring(0, 20) + '...' : 'none');
    
    const requestHeaders = {
      'Content-Type': 'application/json',
      ...(authHeader && { 'Authorization': authHeader }),
    };
    console.log('Request headers:', requestHeaders);
    
    const response = await fetch(fetchUrl, {
      method: 'GET',
      headers: requestHeaders,
      timeout: 10000, // 10 second timeout
    });

    console.log('Backend response status:', response.status);
    
    // Try to get the response as text first to handle non-JSON responses
    const responseText = await response.text();
    console.log('Backend response:', responseText);

    let data;
    try {
      data = JSON.parse(responseText);
    } catch (parseError) {
      console.error('Failed to parse backend response as JSON:', parseError);
      return NextResponse.json(
        { 
          detail: 'Backend returned invalid JSON', 
          response: responseText.substring(0, 500) // Limit response size
        },
        { status: 500 }
      );
    }

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || 'Failed to fetch registration keys' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Fetch registration keys error:', error);
    return NextResponse.json(
      { 
        detail: 'Internal server error',
        error: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const authHeader = request.headers.get('authorization');

    // Forward the request to the backend
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    const response = await fetch(`${backendUrl}/api/device/keys`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || 'Failed to create registration key' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Create registration key error:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}