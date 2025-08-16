import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Try Railway backend first
    try {
      const response = await fetch('https://taxpoynt-platform-production.up.railway.app/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(10000), // 10 second timeout
      });

      const data = await response.json();

      // Return the response with proper status
      return NextResponse.json(data, { 
        status: response.status,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    } catch (railwayError) {
      console.warn('Railway backend unavailable, using mock response:', railwayError);
      
      // Mock successful registration for testing
      const mockUser = {
        id: Math.random().toString(36).substr(2, 9),
        email: body.email,
        role: body.role,
        first_name: body.first_name,
        last_name: body.last_name,
        created_at: new Date().toISOString(),
      };

      const mockResponse = {
        access_token: 'mock_jwt_token_' + Math.random().toString(36),
        token_type: 'bearer',
        user: mockUser,
        message: 'Registration successful (mock mode - Railway backend unavailable)'
      };

      return NextResponse.json(mockResponse, { 
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    }

  } catch (error) {
    console.error('Auth proxy error:', error);
    return NextResponse.json(
      { error: 'Authentication service temporarily unavailable' },
      { status: 503 }
    );
  }
}

export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}