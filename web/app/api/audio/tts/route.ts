import OpenAI from "openai";
import { env } from "@/lib/env";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const { text } = await req.json();
  if (!text) return new Response(JSON.stringify({ error: 'text required' }), { status: 400 });
  const client = new OpenAI({ apiKey: env.OPENAI_API_KEY });
  const speech = await client.audio.speech.create({
    model: 'tts-1',
    voice: 'nova',
    input: text,
    response_format: 'mp3',
  });
  return new Response(speech.body, { headers: { 'content-type': 'audio/mpeg' } });
}


