import { env } from "@/lib/env";
import OpenAI from "openai";

export const runtime = "edge"; // use edge for low-latency streaming

export async function POST(req: Request) {
  const { messages } = await req.json();
  const client = new OpenAI({ apiKey: env.OPENAI_API_KEY });
  const response = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages,
    stream: true,
  });

  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();
      for await (const chunk of response) {
        const text = chunk.choices?.[0]?.delta?.content ?? "";
        if (text) controller.enqueue(encoder.encode(text));
      }
      controller.close();
    },
  });

  return new Response(stream, { headers: { "content-type": "text/plain; charset=utf-8" } });
}
