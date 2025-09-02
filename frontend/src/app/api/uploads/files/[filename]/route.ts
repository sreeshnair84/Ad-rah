import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    const filename = params.filename;

    if (!filename) {
      return NextResponse.json(
        { error: 'Filename is required' },
        { status: 400 }
      );
    }

    // Forward the request to the backend download endpoint
    // We need to extract the content ID from the filename
    // The filename format is typically: {content_id}_{original_filename}
    const contentId = filename.split('_')[0];

    if (!contentId) {
      return NextResponse.json(
        { error: 'Invalid filename format' },
        { status: 400 }
      );
    }

    const backendResponse = await fetch(`${BACKEND_URL}/api/content/download/${contentId}`, {
      method: 'GET',
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({}));
      return NextResponse.json(
        errorData,
        { status: backendResponse.status }
      );
    }

    // Get the response as a blob/arraybuffer
    const fileData = await backendResponse.arrayBuffer();
    const contentType = backendResponse.headers.get('content-type') || 'application/octet-stream';
    const contentDisposition = backendResponse.headers.get('content-disposition') || `attachment; filename="${filename}"`;

    // Return the file with proper headers
    return new NextResponse(fileData, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': contentDisposition,
        'Cache-Control': 'public, max-age=31536000', // Cache for 1 year
      },
    });

  } catch (error) {
    console.error('File serving error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
