import OpenAI from "openai";
import { env } from "@/lib/env";
import { withErrorHandler, successResponse, API_ERRORS } from "@/lib/api-utils";
import { NextRequest } from "next/server";

export const runtime = "nodejs";

export const POST = withErrorHandler(async (req: NextRequest) => {
  const form = await req.formData();
  const file = form.get("file");

  if (!file || !(file instanceof File)) {
    throw API_ERRORS.BAD_REQUEST("file is required");
  }

  // Additional file validation for audio files
  if (!file.type.startsWith("audio/")) {
    throw API_ERRORS.UNPROCESSABLE_ENTITY("File must be an audio file");
  }

  if (file.size > 25 * 1024 * 1024) { // 25MB limit
    throw API_ERRORS.UNPROCESSABLE_ENTITY("File size must be less than 25MB");
  }

  const client = new OpenAI({ apiKey: env.OPENAI_API_KEY });

  try {
    const transcription = await client.audio.transcriptions.create({
      model: "whisper-1",
      file,
      response_format: "text",
      language: "en", // Specify language for better accuracy
    });

    return successResponse(transcription, "Audio transcribed successfully");
  } catch (error) {
    // Handle OpenAI API errors specifically
    if (error instanceof Error && 'status' in error) {
      const openaiError = error as { status: number; message: string };
      if (openaiError.status === 429) {
        throw API_ERRORS.UNPROCESSABLE_ENTITY("Rate limit exceeded. Please try again later.");
      } else if (openaiError.status === 401) {
        throw API_ERRORS.UNAUTHORIZED("Invalid API key configuration.");
      } else if (openaiError.status === 413) {
        throw API_ERRORS.UNPROCESSABLE_ENTITY("Audio file is too large.");
      }
    }

    // Handle audio processing errors
    if (error instanceof Error && error.message.includes("audio")) {
      throw API_ERRORS.UNPROCESSABLE_ENTITY("Unable to process audio file. Please ensure it's a valid audio format.");
    }

    throw error;
  }
});


