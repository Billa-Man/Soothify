import { connectMongo } from "@/lib/db";
import { UserDataModel } from "@/models/UserData";

export async function GET() {
  await connectMongo();
  const users = await UserDataModel.distinct('user_id');
  return new Response(JSON.stringify(users), { headers: { 'content-type': 'application/json' } });
}
