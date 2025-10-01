import { z } from "zod";

// Chat API schemas
export const ChatMessageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string().min(1),
});

export const ChatRequestSchema = z.object({
  messages: z.array(ChatMessageSchema).min(1),
});

// User data API schemas
export const MoodEntrySchema = z.object({
  timestamp: z.string().datetime(),
  mood: z.enum(["Happy", "Neutral", "Anxious", "Sad", "Depressed"]),
});

export const UserDataUpdateSchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Date must be in YYYY-MM-DD format"),
  mood_entry: MoodEntrySchema,
});

// Audio API schemas
export const AudioTranscriptionSchema = z.object({
  file: z.instanceof(File).refine(
    (file) => file.size <= 25 * 1024 * 1024, // 25MB limit
    "File size must be less than 25MB"
  ).refine(
    (file) => file.type.startsWith("audio/"),
    "File must be an audio file"
  ),
});

// Assessment API schemas
export const AssessmentResponseSchema = z.object({
  questionId: z.string(),
  answer: z.number().min(0).max(3),
});

export const AssessmentSubmissionSchema = z.object({
  responses: z.array(AssessmentResponseSchema),
});

// Query parameter schemas for validation
export const DateRangeSchema = {
  start: { required: false, pattern: /^\d{4}-\d{2}-\d{2}$/ },
  end: { required: false, pattern: /^\d{4}-\d{2}-\d{2}$/ },
} as const;

export const PaginationSchema = {
  page: { required: false, pattern: /^\d+$/ },
  limit: { required: false, pattern: /^\d+$/ },
} as const;
