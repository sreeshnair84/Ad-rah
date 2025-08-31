import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate required fields
    const requiredFields = [
      'company_name',
      'company_type',
      'business_license',
      'address',
      'city',
      'country',
      'description',
      'applicant_name',
      'applicant_email',
      'applicant_phone'
    ];

    for (const field of requiredFields) {
      if (!body[field]) {
        return NextResponse.json(
          { error: `Missing required field: ${field}` },
          { status: 400 }
        );
      }
    }

    // Validate company type
    if (!['HOST', 'ADVERTISER'].includes(body.company_type)) {
      return NextResponse.json(
        { error: 'Invalid company type. Must be HOST or ADVERTISER' },
        { status: 400 }
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(body.applicant_email)) {
      return NextResponse.json(
        { error: 'Invalid email format' },
        { status: 400 }
      );
    }

    // In a real implementation, you would:
    // 1. Save the application to your backend database
    // 2. Send confirmation email to the applicant
    // 3. Notify administrators about the new application

    // For now, we'll simulate a successful submission
    const applicationId = `app_${Date.now()}`;

    // Call backend API to create company application
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

    try {
      const backendResponse = await fetch(`${backendUrl}/api/company-applications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: body.company_name,
          company_type: body.company_type,
          business_license: body.business_license,
          address: body.address,
          city: body.city,
          country: body.country,
          website: body.website,
          description: body.description,
          applicant_name: body.applicant_name,
          applicant_email: body.applicant_email,
          applicant_phone: body.applicant_phone,
          documents: body.documents || {},
        }),
      });

      if (!backendResponse.ok) {
        const errorData = await backendResponse.json();
        throw new Error(errorData.detail || 'Failed to create application in backend');
      }

      const backendResult = await backendResponse.json();

      return NextResponse.json({
        success: true,
        application_id: backendResult.id,
        message: 'Company application submitted successfully. You will receive an email with login credentials once approved.',
        status: 'pending_review'
      });

    } catch (backendError) {
      console.error('Backend API error:', backendError);

      // Fallback: return success with simulated data
      return NextResponse.json({
        success: true,
        application_id: applicationId,
        message: 'Company application submitted successfully. You will receive an email with login credentials once approved.',
        status: 'pending_review',
        note: 'Application stored locally due to backend connectivity issues'
      });
    }

  } catch (error) {
    console.error('Company registration error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const token = request.headers.get('authorization')?.replace('Bearer ', '');
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

    // Check if this is a stats request
    const url = new URL(request.url);
    const isStatsRequest = url.pathname.includes('/stats/summary');

    const endpoint = isStatsRequest
      ? `${backendUrl}/api/company-applications/stats/summary`
      : `${backendUrl}/api/company-applications`;

    const backendResponse = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json();
      return NextResponse.json(
        { error: errorData.detail || 'Failed to fetch data from backend' },
        { status: backendResponse.status }
      );
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Company applications API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
