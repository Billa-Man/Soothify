import mongoose, { Schema, InferSchemaType, Model } from "mongoose";

const MoodSchema = new Schema({
  timestamp: { type: Date, required: true },
  mood: { type: String, enum: ["Happy", "Neutral", "Anxious", "Sad", "Depressed"], required: true },
});

const ActivityImpactSchema = new Schema({
  positive: Number,
  neutral: Number,
  negative: Number,
});

const UserDataSchema = new Schema({
  user_id: { type: String, index: true, required: true },
  date: { type: Date, index: true, required: true },
  mood_history: [MoodSchema],
  panic_episodes: [Date],
  chat_durations: [Number],
  stressors: {
    work: Number,
    relationships: Number,
    health: Number,
    financial: Number,
  },
  activity_impact: {
    Exercise: ActivityImpactSchema,
    Meditation: ActivityImpactSchema,
    "Social Activities": ActivityImpactSchema,
  },
  device_type: String,
  location: String,
});

export type UserData = InferSchemaType<typeof UserDataSchema>;

export const UserDataModel: Model<UserData> =
  mongoose.models.UserData || mongoose.model<UserData>("UserData", UserDataSchema);
