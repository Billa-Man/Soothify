'use client';

import { useEffect, useState } from 'react';
import HumeClient from './Client';

export default function HumeRealtime() {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchToken = async () => {
      try {
        console.log("[hume] fetching access token with configId", process.env.HUME_CONFIG_ID || "<none>");
        const response = await fetch('/api/hume/token');
        const data = await response.json();

        if (!response.ok) {
          if (response.status === 400 && data.error === 'Placeholder API credentials detected') {
            throw new Error('Please update your .env.local file with real Hume AI credentials');
          } else if (response.status === 500 && data.error === 'Missing Hume API credentials') {
            throw new Error('Hume API credentials not found in environment variables');
          } else {
            throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
          }
        }

        const { accessToken } = data;
        console.log("[hume] access token fetched (length)", accessToken?.length || 0);
        setAccessToken(accessToken);
      } catch (e: unknown) {
        console.error("[hume] token fetch error", e);
        setError((e as Error)?.message || 'Failed to fetch Hume access token');
      } finally {
        setLoading(false);
      }
    };

    fetchToken();
  }, []);

  if (loading) {
    return (
      <main className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-2xl font-semibold text-center">Hume Voice Chat</h1>
        <div className="card p-4 text-center">
          <p className="muted">Loading Hume voice chat...</p>
        </div>
      </main>
    );
  }

  if (error || !accessToken) {
    return (
      <main className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-2xl font-semibold text-center">Hume Voice Chat</h1>
        <div className="card p-4">
          <p className="muted">❌ Failed to initialize Hume voice chat</p>
          <p className="text-sm mt-2" style={{ color: '#b91c1c' }}>{error}</p>

          {error?.includes('credentials') && (
            <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded">
              <p className="text-sm text-blue-800 mb-2">To fix this issue:</p>
              <ol className="list-decimal ml-5 text-xs text-blue-700 space-y-1">
                <li>Visit <a href="https://platform.hume.ai/" target="_blank" rel="noopener noreferrer" className="underline">Hume AI Platform</a></li>
                <li>Create an account and navigate to your dashboard</li>
                <li>Copy your API Key and Secret Key</li>
                <li>Update your <code className="bg-blue-100 px-1 rounded">.env.local</code> file</li>
                <li>Restart your development server</li>
              </ol>
            </div>
          )}

          <div className="mt-3 text-xs text-slate-500">
            Check your browser console for more details
          </div>
        </div>
      </main>
    );
  }

  return <HumeClient accessToken={accessToken} configId={process.env.HUME_CONFIG_ID} />;
}


