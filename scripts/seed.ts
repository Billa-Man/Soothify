import { faker } from '@faker-js/faker';
import * as dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });
import { connectMongo } from '../lib/db';
import { UserDataModel } from '../models/UserData';

async function main() {
  await connectMongo();
  const base = new Date('2025-01-01T00:00:00Z');
  const users: Array<{
    user_id: string;
    date: Date;
    mood_history: Array<{timestamp: Date; mood: string}>;
    panic_episodes: Date[];
    chat_durations: number[];
    stressors: { work: number; relationships: number; health: number; financial: number };
    activity_impact: {
      Exercise: { positive: number; neutral: number; negative: number };
      Meditation: { positive: number; neutral: number; negative: number };
      "Social Activities": { positive: number; neutral: number; negative: number };
    };
    device_type: string;
    location: string;
  }> = [];
  for (let u = 0; u < 5; u++) {
    const user_id = faker.string.uuid();
    for (let d = 0; d < 30; d++) {
      const date = new Date(base.getTime() + d * 24 * 60 * 60 * 1000);
      const moodCount = faker.number.int({ min: 1, max: 3 });
      const moods = Array.from({ length: moodCount }).map(() => ({
        timestamp: new Date(date.getTime() + faker.number.int({ min: 8, max: 20 }) * 60 * 60 * 1000),
        mood: faker.helpers.arrayElement(['Happy','Neutral','Anxious','Sad','Depressed']),
      }));
      const panic_episodes = Math.random() < 0.3 ? Array.from({ length: faker.number.int({ min: 1, max: 2 }) }).map(() => new Date(date.getTime() + faker.number.int({ min: 0, max: 23 }) * 60 * 60 * 1000)) : [];
      const chat_durations = Math.random() < 0.4 ? Array.from({ length: faker.number.int({ min: 1, max: 2 }) }).map(() => faker.number.int({ min: 5, max: 45 })) : [];
      const doc = {
        user_id,
        date,
        mood_history: moods,
        panic_episodes,
        chat_durations,
        stressors: { work: faker.number.int({ min:0, max:10 }), relationships: faker.number.int({ min:0, max:8 }), health: faker.number.int({ min:0, max:6 }), financial: faker.number.int({ min:0, max:5 }) },
        activity_impact: {
          Exercise: { positive: faker.number.int({ min:60, max:85 }), neutral: faker.number.int({ min:10, max:30 }), negative: faker.number.int({ min:0, max:10 }) },
          Meditation: { positive: faker.number.int({ min:50, max:75 }), neutral: faker.number.int({ min:15, max:35 }), negative: faker.number.int({ min:0, max:15 }) },
          'Social Activities': { positive: faker.number.int({ min:55, max:80 }), neutral: faker.number.int({ min:10, max:30 }), negative: faker.number.int({ min:0, max:15 }) },
        },
        device_type: faker.helpers.arrayElement(['mobile','desktop','tablet']),
        location: faker.location.countryCode(),
      };
      users.push(doc);
    }
  }
  await UserDataModel.insertMany(users);
  console.log('Seeded', users.length, 'documents');
  process.exit(0);
}

main().catch((e) => { console.error(e); process.exit(1); });
