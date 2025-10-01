import { NextRequest } from "next/server";
import { connectMongo } from "@/lib/db";
import { UserDataModel } from "@/models/UserData";
import { withErrorHandler, successResponse, validateRequest, validateQueryParams, API_ERRORS } from "@/lib/api-utils";
import { UserDataUpdateSchema, DateRangeSchema } from "@/lib/api-schemas";

export const GET = withErrorHandler(async (req: NextRequest, { params }: { params: Promise<{ userId: string }> }) => {
  const { userId } = await params;

  // Validate userId format
  if (!userId || typeof userId !== 'string' || userId.trim().length === 0) {
    throw API_ERRORS.BAD_REQUEST("Invalid user ID");
  }

  await connectMongo();
  const url = new URL(req.url);
  const { start, end } = validateQueryParams(url.searchParams, DateRangeSchema);

  const query: { user_id: string; date?: { $gte?: Date; $lte?: Date } } = { user_id: userId };

  if (start || end) {
    query.date = {};
    if (start) {
      const startDate = new Date(start);
      if (isNaN(startDate.getTime())) {
        throw API_ERRORS.BAD_REQUEST("Invalid start date format");
      }
      query.date.$gte = startDate;
    }
    if (end) {
      const endDate = new Date(end);
      if (isNaN(endDate.getTime())) {
        throw API_ERRORS.BAD_REQUEST("Invalid end date format");
      }
      query.date.$lte = endDate;
    }
  }

  try {
    const docs = await UserDataModel.find(query).sort({ date: 1 }).lean();

    if (!docs || docs.length === 0) {
      throw API_ERRORS.NOT_FOUND(`No data found for user ${userId}`);
    }

    return successResponse(docs, `Retrieved ${docs.length} records for user ${userId}`);
  } catch (error) {
    // Handle MongoDB query errors
    if (error instanceof Error && error.message.includes("Cast to ObjectId failed")) {
      throw API_ERRORS.BAD_REQUEST("Invalid user ID format");
    }
    throw error;
  }
});

export const POST = withErrorHandler(async (req: NextRequest, { params }: { params: Promise<{ userId: string }> }) => {
  const { userId } = await params;

  // Validate userId format
  if (!userId || typeof userId !== 'string' || userId.trim().length === 0) {
    throw API_ERRORS.BAD_REQUEST("Invalid user ID");
  }

  const { date, mood_entry } = await validateRequest(req, UserDataUpdateSchema);

  await connectMongo();

  try {
    const day = new Date(new Date(date).setHours(0, 0, 0, 0));

    // Validate that the mood_entry timestamp is within the same day
    const entryDate = new Date(mood_entry.timestamp);
    if (entryDate.toDateString() !== day.toDateString()) {
      throw API_ERRORS.BAD_REQUEST("Mood entry timestamp must be within the specified date");
    }

    await UserDataModel.updateOne(
      { user_id: userId, date: day },
      { $push: { mood_history: mood_entry } },
      { upsert: true }
    );

    return successResponse(null, "Mood entry added successfully");
  } catch (error) {
    // Handle MongoDB operation errors
    if (error instanceof Error && error.message.includes("duplicate key")) {
      throw API_ERRORS.CONFLICT("Mood entry already exists for this timestamp");
    }
    throw error;
  }
});
