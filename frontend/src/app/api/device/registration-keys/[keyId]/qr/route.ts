import { NextRequest, NextResponse } from 'next/server';
import QRCode from 'qrcode';

export async function GET(
  request: NextRequest,
  { params }: { params: { keyId: string } }
) {
  try {
    const { keyId } = params;
    
    if (!keyId) {
      return NextResponse.json(
        { detail: 'Key ID is required' },
        { status: 400 }
      );
    }

    // Get authorization header from the request
    const authHeader = request.headers.get('authorization');
    
    // First, fetch the registration key details from backend to verify it exists
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const keyResponse = await fetch(`${backendUrl}/api/device/keys/${keyId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    if (!keyResponse.ok) {
      const errorData = await keyResponse.json();
      return NextResponse.json(
        { detail: errorData.detail || 'Registration key not found' },
        { status: keyResponse.status }
      );
    }

    const keyData = await keyResponse.json();
    
    // Create QR code data - this will be used by the device to register
    const qrData = {
      type: 'device_registration',
      key: keyData.key,
      server_url: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000',
      company_id: keyData.company_id,
      expires_at: keyData.expires_at
    };

    // Generate QR code as data URL
    const qrCodeDataUrl = await QRCode.toDataURL(JSON.stringify(qrData), {
      width: 300,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#FFFFFF'
      }
    });

    return NextResponse.json({
      qr_code: qrCodeDataUrl,
      qr_data: qrData,
      key_info: keyData
    });
  } catch (error) {
    console.error('Generate QR code error:', error);
    return NextResponse.json(
      { detail: 'Failed to generate QR code' },
      { status: 500 }
    );
  }
}