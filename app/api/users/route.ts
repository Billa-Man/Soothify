import { connectMongo } from "@/lib/db";
import { UserDataModel } from "@/models/UserData";
import { withErrorHandler, successResponse, API_ERRORS } from "@/lib/api-utils";

export const GET = withErrorHandler(async () => {
  try {
    await connectMongo();
    const users = await UserDataModel.distinct('user_id');

    if (!users || users.length === 0) {
      throw API_ERRORS.NOT_FOUND("No users found");
    }

    return successResponse(users, "Users retrieved successfully");
  } catch (error) {
    // Handle MongoDB connection errors
    if (error instanceof Error && error.message.includes("connection")) {
      throw API_ERRORS.INTERNAL_SERVER_ERROR("Database connection failed");
    }
    throw error;
  }
});
