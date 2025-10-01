# Soothify

**Soothify** is a comprehensive mental health companion application built with Next.js and Node.js. It provides users with AI-powered chat support, mood tracking, assessment tools, and access to mental health resources, creating a supportive digital environment for emotional wellbeing. Designed for individuals seeking accessible mental health support and professionals looking to offer digital wellness tools.

## Prerequisites

- Node.js 18+
- MongoDB (local installation or MongoDB Atlas)

## Quick Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.local.example .env.local
   ```
   Fill in your API keys and database connection details in `.env.local`:
   ```env
   OPENAI_API_KEY=your_openai_key
   MONGODB_URI=mongodb://localhost:27017
   DB_NAME=soothify
   HUME_API_KEY=your_hume_key
   HUME_SECRET_KEY=your_hume_secret
   HUME_CONFIG_ID=your_config_id
   ```

3. **Seed demo data (optional):**
   ```bash
   npm run seed
   ```

## Usage

**Start the development server:**
```bash
npm run dev
```

**For full audio features, also start the WebSocket relay:**
```bash
npm run dev:ws
```

The application will be available at `http://localhost:3000` with the following key features:

## Key Features

- **🤖 AI Chat**: Real-time conversational AI with streaming responses and text-to-speech
- **📊 Assessment Tools**: Interactive mental health assessments with progress tracking
- **📈 Dashboard**: Personal mood tracking and analytics with MongoDB integration
- **🎙️ Voice Integration**: Speech-to-text transcription and audio processing via Hume AI
- **🗺️ Resource Locator**: Find nearby mental health facilities and resources
- **💪 Wellness Exercises**: Guided exercises and coping strategies
- **📚 Educational Content**: Mental health blogs and informational resources

## Project Structure

```
├── app/                 # Next.js app directory
│   ├── api/            # API routes (chat, audio, user data, etc.)
│   └── [pages]/        # React pages and components
├── lib/                # Shared utilities and configurations
│   ├── components/     # Reusable React components
│   ├── hooks/         # Custom React hooks
│   └── [utils]/       # Helper functions and schemas
├── models/             # MongoDB data models
├── public/             # Static assets
└── server/             # WebSocket server for audio features
```

## Testing

Run the test suite:
```bash
npm test
```

For test coverage:
```bash
npm run test:coverage
```
