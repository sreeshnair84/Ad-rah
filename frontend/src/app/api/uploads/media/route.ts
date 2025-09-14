import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Forward the Authorization header from the frontend request
    const authHeader = request.headers.get('authorization');
    const headers: HeadersInit = {};

    if (authHeader) {
      headers.Authorization = authHeader;
    }

    const formData = await request.formData();

    // Get owner_id from form data, if not provided, get user info
    let ownerId = formData.get('owner_id') as string;

    // If owner_id is not provided, get it from the user's profile
    if (!ownerId && authHeader) {
      try {
        const profileResponse = await fetch(`${BACKEND_URL}/api/auth/me`, {
          headers: {
            Authorization: authHeader,
          },
        });

        if (profileResponse.ok) {
          const userProfile = await profileResponse.json();
          // Use user id for media uploads
          ownerId = userProfile.id;
        }
      } catch (error) {
        console.warn('Could not get user profile for owner_id:', error);
      }
    }

    // If we still don't have owner_id, return error
    if (!ownerId) {
      return NextResponse.json(
        { detail: 'Could not determine owner_id. Please ensure you are logged in.' },
        { status: 400 }
      );
    }

    // Create URL with owner_id as query parameter for the multi-file endpoint
    const backendUrl = new URL(`${BACKEND_URL}/api/content/upload`);
    backendUrl.searchParams.set('owner_id', ownerId);

    const backendResponse = await fetch(backendUrl.toString(), {
      method: 'POST',
      headers,
      body: formData,
    });

    const responseData = await backendResponse.json();

    return NextResponse.json(responseData, {
      status: backendResponse.status,
    });
  } catch (error) {
    console.error('Upload media proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}