import mongoose from "mongoose";
import { env } from "./env";

const globalWithMongoose = global as typeof global & {
  _mongooseConn?: typeof mongoose;
};

export async function connectMongo(): Promise<typeof mongoose> {
  if (globalWithMongoose._mongooseConn) return globalWithMongoose._mongooseConn;
  const conn = await mongoose.connect(env.MONGODB_URI, { dbName: env.DB_NAME });
  globalWithMongoose._mongooseConn = conn;
  return conn;
}
