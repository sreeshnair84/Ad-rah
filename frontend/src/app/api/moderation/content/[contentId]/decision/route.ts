import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(
  request: NextRequest,
  { params }: { params: { contentId: string } }
) {
  try {
    const formData = await request.formData();
    const decision = formData.get('decision') as string;
    const reviewerId = formData.get('reviewer_id') as string;
    const notes = formData.get('notes') as string;

    if (!decision) {
      return NextResponse.json(
        { error: 'Decision is required' },
        { status: 400 }
      );
    }

    // Determine the backend endpoint based on decision
    let backendEndpoint: string;
    if (decision === 'approve') {
      backendEndpoint = `${BACKEND_URL}/api/content/admin/approve/${params.contentId}`;
    } else if (decision === 'reject') {
      backendEndpoint = `${BACKEND_URL}/api/content/admin/reject/${params.contentId}`;
    } else {
      return NextResponse.json(
        { error: 'Invalid decision. Must be "approve" or "reject"' },
        { status: 400 }
      );
    }

    // Prepare form data for backend
    const backendFormData = new FormData();
    if (reviewerId) backendFormData.append('reviewer_id', reviewerId);
    if (notes) backendFormData.append('notes', notes);

    const backendResponse = await fetch(backendEndpoint, {
      method: 'POST',
      body: backendFormData,
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.detail || `Failed to ${decision} content` },
        { status: backendResponse.status }
      );
    }

    const responseData = await backendResponse.json();
    return NextResponse.json(responseData);
  } catch (error) {
    console.error('Moderation decision proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
