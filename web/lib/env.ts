import { z } from "zod";

const envSchema = z.object({
  OPENAI_API_KEY: z.string().min(1, "OPENAI_API_KEY is required"),
  MONGODB_URI: z.string().min(1),
  DB_NAME: z.string().min(1),
  HUME_API_KEY: z.string().min(1),
  HUME_SECRET_KEY: z.string().min(1),
  HUME_CONFIG_ID: z.string().optional().default(""),
});

const parsed = envSchema.safeParse({
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  MONGODB_URI: process.env.MONGODB_URI,
  DB_NAME: process.env.DB_NAME,
  HUME_API_KEY: process.env.HUME_API_KEY,
  HUME_SECRET_KEY: process.env.HUME_SECRET_KEY,
  HUME_CONFIG_ID: process.env.HUME_CONFIG_ID,
});

if (!parsed.success) {
  console.error("Invalid environment variables:", parsed.error.flatten().fieldErrors);
  throw new Error("Invalid environment variables");
}

export const env = parsed.data;
