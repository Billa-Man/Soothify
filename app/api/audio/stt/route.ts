import OpenAI from "openai";
import { env } from "@/lib/env";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const form = await req.formData();
  const file = form.get("file");
  if (!file || !(file instanceof File)) {
    return new Response(JSON.stringify({ error: "file required" }), { status: 400 });
  }
  const client = new OpenAI({ apiKey: env.OPENAI_API_KEY });
  const transcription = await client.audio.transcriptions.create({
    model: "whisper-1",
    file,
    response_format: "text",
  });
  return new Response(transcription, { headers: { "content-type": "text/plain; charset=utf-8" } });
}


