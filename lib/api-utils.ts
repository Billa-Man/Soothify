import { NextRequest } from "next/server";
import { ZodError, ZodSchema } from "zod";

// Standard API response types
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Error types for better error handling
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public code?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Common API errors
export const API_ERRORS = {
  BAD_REQUEST: (message = "Bad request") => new ApiError(400, message, "BAD_REQUEST"),
  UNAUTHORIZED: (message = "Unauthorized") => new ApiError(401, message, "UNAUTHORIZED"),
  FORBIDDEN: (message = "Forbidden") => new ApiError(403, message, "FORBIDDEN"),
  NOT_FOUND: (message = "Not found") => new ApiError(404, message, "NOT_FOUND"),
  METHOD_NOT_ALLOWED: (message = "Method not allowed") => new ApiError(405, message, "METHOD_NOT_ALLOWED"),
  CONFLICT: (message = "Conflict") => new ApiError(409, message, "CONFLICT"),
  UNPROCESSABLE_ENTITY: (message = "Unprocessable entity") => new ApiError(422, message, "UNPROCESSABLE_ENTITY"),
  INTERNAL_SERVER_ERROR: (message = "Internal server error") => new ApiError(500, message, "INTERNAL_SERVER_ERROR"),
} as const;

// Response helpers
export function successResponse<T>(data: T, message?: string): Response {
  const response: ApiResponse<T> = {
    success: true,
    data,
    ...(message && { message }),
  };

  return new Response(JSON.stringify(response), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

export function errorResponse(error: ApiError | Error | unknown): Response {
  const statusCode = error instanceof ApiError ? error.statusCode : 500;
  const message = error instanceof Error ? error.message : "Unknown error";

  const response: ApiResponse = {
    success: false,
    error: message,
  };

  return new Response(JSON.stringify(response), {
    status: statusCode,
    headers: { "content-type": "application/json" },
  });
}

// Input validation helper
export async function validateRequest<T>(
  req: NextRequest,
  schema: ZodSchema<T>
): Promise<T> {
  try {
    const body = await req.json();
    return schema.parse(body);
  } catch (error) {
    if (error instanceof ZodError) {
      throw API_ERRORS.UNPROCESSABLE_ENTITY(
        `Validation failed: ${error.errors.map(e => `${e.path.join('.')}: ${e.message}`).join(', ')}`
      );
    }
    throw API_ERRORS.BAD_REQUEST("Invalid request body");
  }
}

// Query parameter validation helper
export function validateQueryParams<T extends Record<string, string | undefined>>(
  searchParams: URLSearchParams,
  schema: Record<keyof T, { required?: boolean; pattern?: RegExp }>
): T {
  const result = {} as T;
  const errors: string[] = [];

  for (const [key, config] of Object.entries(schema)) {
    const value = searchParams.get(key);

    if (config.required && !value) {
      errors.push(`${key} is required`);
      continue;
    }

    if (value && config.pattern && !config.pattern.test(value)) {
      errors.push(`${key} format is invalid`);
      continue;
    }

    (result as Record<string, string | undefined>)[key] = value ?? undefined;
  }

  if (errors.length > 0) {
    throw API_ERRORS.BAD_REQUEST(errors.join(', '));
  }

  return result;
}

// File upload validation helper
export function validateFileUpload(formData: FormData, fieldName: string): File {
  const file = formData.get(fieldName);

  if (!file || !(file instanceof File)) {
    throw API_ERRORS.BAD_REQUEST(`${fieldName} is required`);
  }

  return file;
}

// Async error wrapper for API routes
export function withErrorHandler<T extends unknown[]>(
  handler: (...args: T) => Promise<Response>
) {
  return async (...args: T): Promise<Response> => {
    try {
      return await handler(...args);
    } catch (error) {
      console.error("API Error:", error);

      if (error instanceof ApiError) {
        return errorResponse(error);
      }

      return errorResponse(API_ERRORS.INTERNAL_SERVER_ERROR());
    }
  };
}
