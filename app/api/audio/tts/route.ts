import OpenAI from "openai";
import { env } from "@/lib/env";
import { withErrorHandler, API_ERRORS } from "@/lib/api-utils";
import { z } from "zod";
import { NextRequest } from "next/server";

const TTSRequestSchema = z.object({
  text: z.string()
    .min(1, "Text cannot be empty")
    .max(4000, "Text must be less than 4000 characters")
    .refine(text => text.trim().length > 0, "Text cannot be only whitespace"),
});

export const runtime = "nodejs";

export const POST = withErrorHandler(async (req: NextRequest) => {
  const body = await req.json();
  const { text } = TTSRequestSchema.parse(body);

  // Validate text length for TTS API limits
  if (text.length > 4000) {
    throw API_ERRORS.UNPROCESSABLE_ENTITY("Text exceeds maximum length of 4000 characters");
  }

  const client = new OpenAI({ apiKey: env.OPENAI_API_KEY });

  try {
    const speech = await client.audio.speech.create({
      model: 'tts-1',
      voice: 'nova',
      input: text.trim(),
      response_format: 'mp3',
      speed: 1.0, // Normal speed for clarity
    });

    return new Response(speech.body, {
      headers: {
        'content-type': 'audio/mpeg',
        'cache-control': 'public, max-age=3600', // Cache for 1 hour
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

    // Handle text processing errors
    if (error instanceof Error && error.message.includes("text")) {
      throw API_ERRORS.UNPROCESSABLE_ENTITY("Unable to process text. Please ensure it contains valid characters.");
    }

    throw error;
  }
});


