import { WebSocketServer } from "ws";
import WebSocket from "isomorphic-ws";
import * as dotenv from "dotenv";

// WebSocket client type for Node.js ws library with ping support

// Load environment variables
dotenv.config({ path: '.env.local' });

const fetch = (global as typeof global & { fetch?: typeof global.fetch }).fetch as typeof global.fetch;

// Environment variables with validation
const env = {
  HUME_API_KEY: process.env.HUME_API_KEY,
  HUME_SECRET_KEY: process.env.HUME_SECRET_KEY,
  HUME_CONFIG_ID: process.env.HUME_CONFIG_ID || "",
};

// Validate required environment variables
if (!env.HUME_API_KEY || !env.HUME_SECRET_KEY) {
  console.error("❌ Missing required environment variables:");
  if (!env.HUME_API_KEY) console.error("  - HUME_API_KEY is required");
  if (!env.HUME_SECRET_KEY) console.error("  - HUME_SECRET_KEY is required");
  console.error("\n📝 Please add these to your .env.local file:");
  console.error("HUME_API_KEY=your_api_key_here");
  console.error("HUME_SECRET_KEY=your_secret_key_here");
  console.error("HUME_CONFIG_ID=your_config_id_here (optional)");
  process.exit(1);
}

export function startWsRelay(port = 8787) {
  const wss = new WebSocketServer({ port, perMessageDeflate: false });
  console.log(`[ws] relay listening on :${port}`);

  wss.on("connection", async (client) => {
    let upstream: WebSocket | null = null;
    let pingTimer: NodeJS.Timeout | null = null;
    const startHeartbeat = () => {
      stopHeartbeat();
      pingTimer = setInterval(() => {
        try {
          // Ping downstream client
          if (client.readyState === 1 && typeof (client as WebSocket & { ping?: () => void }).ping === 'function') (client as WebSocket & { ping?: () => void }).ping();
        } catch {}
        try {
          // Ping upstream server
          if (upstream && upstream.readyState === 1 && typeof upstream.send === 'function') upstream.send(JSON.stringify({ type: "ping", ts: Date.now() }));
        } catch {}
      }, 25000);
    };
    const stopHeartbeat = () => {
      if (pingTimer) clearInterval(pingTimer);
      pingTimer = null;
    };
    try {
      console.log("[ws] client connected, requesting access token...");
      const tokenResp = await fetch(`https://api.hume.ai/oauth2-cc/token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          Authorization: "Basic " + Buffer.from(`${env.HUME_API_KEY}:${env.HUME_SECRET_KEY}`).toString("base64"),
        },
        body: new URLSearchParams({ grant_type: "client_credentials" }),
      });
      
      if (!tokenResp.ok) {
        throw new Error(`Token request failed: ${tokenResp.status} ${tokenResp.statusText}`);
      }
      
      const tokenJson = (await tokenResp.json()) as { access_token: string; [key: string]: unknown };
      console.log("[ws] token response received:", tokenJson.access_token ? "SUCCESS" : "FAILED", tokenJson);
      const token = tokenJson.access_token as string;
      
      if (!token) {
        throw new Error("No access token received from Hume AI");
      }

      const qs = new URLSearchParams({ access_token: token, verbose_transcription: "true" });
      if (env.HUME_CONFIG_ID) qs.set("config_id", env.HUME_CONFIG_ID);
      const upstreamUrl = `wss://api.hume.ai/v0/evi/chat?${qs.toString()}`;
      console.log("[ws] connecting upstream", upstreamUrl.replace(/access_token=[^&]+/, "access_token=***"));
      upstream = new WebSocket(upstreamUrl);

      upstream.onopen = () => { console.log("[ws] upstream connected"); startHeartbeat(); };
      upstream.onmessage = (evt) => client.readyState === 1 && client.send(evt.data);
      upstream.onerror = (err) => console.error("[ws] upstream error", err);
      upstream.onclose = (evt) => {
        const code = (evt && evt.code) ?? 'unknown';
        const reason = (evt && evt.reason) ?? '';
        console.warn("[ws] upstream closed", code, reason);
        
        // Check for credit exhaustion
        if (reason && String(reason).includes('credit balance')) {
          console.error('[ws] ❌ Credit exhaustion detected. Connection will not be retried.');
          console.error('[ws] 💳 Please visit https://platform.hume.ai/billing to add credits.');
        }
        
        stopHeartbeat();
        try { client.close(); } catch {}
      };

      client.on("message", (data) => {
        if (upstream && upstream.readyState === 1) {
          upstream.send(data);
        }
      });
      client.on("close", (code) => {
        console.warn("[ws] client closed", code);
        stopHeartbeat();
        if (upstream) upstream.close();
      });
      client.on("error", (e) => { console.error("[ws] client error", e); stopHeartbeat(); });
    } catch (e) {
      console.error("[ws] setup error", e);
      client.close();
      if (upstream && upstream.readyState === 1) upstream.close();
    }
  });
}

// Start the server if this file is run directly
if (process.argv[1] === new URL(import.meta.url).pathname) {
  startWsRelay(parseInt(process.env.WS_PORT || "8787", 10));
}
