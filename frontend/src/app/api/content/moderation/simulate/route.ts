import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const contentId = formData.get('content_id') as string;

    if (!contentId) {
      return NextResponse.json(
        { error: 'content_id is required' },
        { status: 400 }
      );
    }

    const backendFormData = new FormData();
    backendFormData.append('content_id', contentId);

    const backendResponse = await fetch(`${BACKEND_URL}/api/content/moderation/simulate`, {
      method: 'POST',
      body: backendFormData,
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.detail || 'Failed to simulate moderation' },
        { status: backendResponse.status }
      );
    }

    const responseData = await backendResponse.json();
    return NextResponse.json(responseData);
  } catch (error) {
    console.error('Content moderation simulate proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
