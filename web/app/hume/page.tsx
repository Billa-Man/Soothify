import HumeClient from './Client';
import { fetchAccessToken } from 'hume';

export default async function HumeRealtime() {
  const missing: string[] = [];
  if (!process.env.HUME_API_KEY) missing.push('HUME_API_KEY');
  if (!process.env.HUME_SECRET_KEY) missing.push('HUME_SECRET_KEY');

  if (missing.length) {
    console.error("[hume] missing env vars", missing);
    return (
      <main className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-2xl font-semibold text-center">Hume Voice Chat</h1>
        <div className="card p-4">
          <p className="muted">Missing environment variables:</p>
          <ul className="list-disc ml-5 text-sm">
            {missing.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
          <p className="muted mt-2">Add these to your .env.local and restart the dev server.</p>
        </div>
      </main>
    );
  }

  try {
    console.log("[hume] fetching access token with configId", process.env.HUME_CONFIG_ID || "<none>");
    const accessToken = await fetchAccessToken({
      apiKey: String(process.env.HUME_API_KEY),
      secretKey: String(process.env.HUME_SECRET_KEY),
    });
    console.log("[hume] access token fetched (length)", accessToken?.length || 0);
    return <HumeClient accessToken={accessToken} configId={process.env.HUME_CONFIG_ID} />;
  } catch (e: any) {
    console.error("[hume] token fetch error", e);
    return (
      <main className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-2xl font-semibold text-center">Hume Voice Chat</h1>
        <div className="card p-4">
          <p className="muted">Failed to fetch Hume access token.</p>
          <p className="text-sm" style={{ color: '#b91c1c' }}>{e?.message || 'Unknown error'}</p>
          <p className="muted mt-2">Double‑check your Hume API and Secret keys.</p>
        </div>
      </main>
    );
  }
}


