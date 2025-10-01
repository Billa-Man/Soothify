import { NextRequest } from "next/server";
import { connectMongo } from "@/lib/db";
import { UserDataModel } from "@/models/UserData";

export async function GET(req: NextRequest, { params }: { params: Promise<{ userId: string }> }) {
  await connectMongo();
  const { userId } = await params;
  const url = new URL(req.url);
  const start = url.searchParams.get("start");
  const end = url.searchParams.get("end");
  const query: { user_id: string; date?: { $gte?: Date; $lte?: Date } } = { user_id: userId };
  if (start || end) {
    query.date = {};
    if (start) query.date.$gte = new Date(start);
    if (end) query.date.$lte = new Date(end);
  }
  const docs = await UserDataModel.find(query).sort({ date: 1 }).lean();
  return new Response(JSON.stringify(docs), { headers: { "content-type": "application/json" } });
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ userId: string }> }) {
  await connectMongo();
  const { userId } = await params;
  const body = await req.json();
  const { date, mood_entry } = body as { date: string; mood_entry: { timestamp: string; mood: string } };
  const day = new Date(new Date(date).setHours(0, 0, 0, 0));
  await UserDataModel.updateOne({ user_id: userId, date: day }, { $push: { mood_history: mood_entry } }, { upsert: true });
  return new Response(null, { status: 204 });
}
