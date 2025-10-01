import { env } from "@/lib/env";
import OpenAI from "openai";
import { withErrorHandler, API_ERRORS } from "@/lib/api-utils";
import { ChatRequestSchema } from "@/lib/api-schemas";
import { NextRequest } from "next/server";

export const runtime = "edge";

export const POST = withErrorHandler(async (req: NextRequest) => {
  const body = await req.json();
  const { messages } = ChatRequestSchema.parse(body);

  const client = new OpenAI({ apiKey: env.OPENAI_API_KEY });

  try {
    const response = await client.chat.completions.create({
      model: "gpt-4o-mini",
      messages,
      stream: true,
      max_tokens: 1000, // Reasonable limit for chat responses
      temperature: 0.7, // Balanced creativity vs consistency
    });

    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();
        try {
          for await (const chunk of response) {
            const text = chunk.choices?.[0]?.delta?.content ?? "";
            if (text) controller.enqueue(encoder.encode(text));
          }
        } catch (error) {
          console.error("Streaming error:", error);
          controller.error(error);
          return;
        }
        controller.close();
      },
    });

    return new Response(stream, {
      headers: {
        "content-type": "text/plain; charset=utf-8",
        "cache-control": "no-cache",
      }
    });
  } catch (error) {
    // Handle OpenAI API errors specifically
    if (error instanceof Error && 'status' in error) {
      const openaiError = error as { status: number; message: string };
      if (openaiError.status === 429) {
        throw API_ERRORS.UNPROCESSABLE_ENTITY("Rate limit exceeded. Please try again later.");
      } else if (openaiError.status === 401) {
        throw API_ERRORS.UNAUTHORIZED("Invalid API key configuration.");
      }
    }
    throw error;
  }
});
