import { NextResponse } from 'next/server';
import { fetchAccessToken } from 'hume';

export async function GET() {
  try {
    // Check if required environment variables are present and not placeholder values
    if (!process.env.HUME_API_KEY || !process.env.HUME_SECRET_KEY) {
      return NextResponse.json(
        {
          error: 'Missing Hume API credentials',
          message: 'Please configure HUME_API_KEY and HUME_SECRET_KEY in your .env.local file'
        },
        { status: 500 }
      );
    }

    // Check if the API keys are still placeholder values
    if (process.env.HUME_API_KEY === 'your_hume_api_key_here' ||
        process.env.HUME_SECRET_KEY === 'your_hume_secret_key_here') {
      return NextResponse.json(
        {
          error: 'Placeholder API credentials detected',
          message: 'Please replace the placeholder values in .env.local with your actual Hume AI credentials'
        },
        { status: 400 }
      );
    }

    console.log("[hume] fetching access token with configId", process.env.HUME_CONFIG_ID || "<none>");

    const accessToken = await fetchAccessToken({
      apiKey: String(process.env.HUME_API_KEY),
      secretKey: String(process.env.HUME_SECRET_KEY),
    });

    console.log("[hume] access token fetched (length)", accessToken?.length || 0);

    return NextResponse.json({ accessToken });
  } catch (error) {
    console.error("[hume] token fetch error", error);
    return NextResponse.json(
      {
        error: 'Failed to fetch Hume access token',
        details: (error as Error)?.message,
        message: 'Please check your Hume API credentials and try again'
      },
      { status: 500 }
    );
  }
}
