import { NextRequest } from "next/server";
import { connectMongo } from "@/lib/db";
import mongoose from "mongoose";

const AssessmentSchema = new mongoose.Schema({
  user_id: { type: String, required: true, index: true },
  date: { type: Date, required: true },
  severity: String,
  score: Number,
  percentage: Number,
});

const AssessmentModel = mongoose.models.Assessment || mongoose.model("Assessment", AssessmentSchema);

export async function POST(req: NextRequest) {
  await connectMongo();
  const body = await req.json();
  await AssessmentModel.create(body);
  return new Response(null, { status: 201 });
}

export async function GET(req: NextRequest) {
  await connectMongo();
  const { searchParams } = new URL(req.url);
  const user_id = searchParams.get('user_id');
  if (!user_id) return new Response(JSON.stringify({ error: 'user_id required' }), { status: 400 });
  const last = await AssessmentModel.findOne({ user_id }).sort({ date: -1 }).lean();
  return new Response(JSON.stringify(last || null), { headers: { 'content-type': 'application/json' } });
}
