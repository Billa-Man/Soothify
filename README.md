# Soothify (Next.js + Node)

## Prerequisites
- Node 18+
- MongoDB running (local or Atlas)

## Setup
1. Copy `.env.local` and fill values:
```
OPENAI_API_KEY=...
MONGODB_URI=mongodb://localhost:27017
DB_NAME=soothify
HUME_API_KEY=...
HUME_SECRET_KEY=...
HUME_CONFIG_ID=
```
2. Install deps:
```
npm install
```
3. Seed demo data (optional):
```
npm run seed
```

## Run
- UI (Next.js dev server):
```
npm run dev
```
- Audio WS relay (Hume proxy):
```
npm run dev:ws
```

## Pages
- `/` Home
- `/assessment` Assessment
- `/chat` AI Chat (text streaming)
- `/dashboard` Dashboard (Mongo)
- `/facilities` Geocode stub
- `/exercises`, `/blogs` Static resources

## Notes
- Media assets are under `public/media`.
- API routes under `app/api/*`.
- Mongo models are in `models/`; connection in `lib/db.ts`.
