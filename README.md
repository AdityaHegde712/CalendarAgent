# 📅 Calendar Agent

A smart local AI scheduling assistant that reads your Google Calendar and books work sessions from natural language requests.

> "Schedule 3 hours of work on Essay Draft before Friday"  
> → Agent checks free slots → proposes a plan → you confirm → events created ✓

---

## ✨ Features

- **Natural Language Scheduling** — Just describe your task, duration, and deadline.
- **Clarifying Questions** — The agent asks before acting; it never guesses your intent.
- **Respects Existing Events** — Perfectly avoids conflicts with your current schedule.
- **Split Sessions** — Intelligently breaks long tasks into multiple smaller blocks.
- **Privacy First** — Your calendar data stays on your machine during the agent's logic.
- **Multi-LLM Support** — Use Gemini (default), GPT-4, or Claude.

---

## 🚀 Getting Started

### 1. Prerequisites

- **Python 3.11+** & **Node.js 18+**
- **LLM API Key**: Gemini (default), OpenAI, or Anthropic.
- **Google Cloud Project** with Calendar API enabled (see below).

### 2. Google Cloud Setup (One-Time Setup)

Because this agent interacts with your personal calendar, you need to set up a private "App" in the Google Cloud Console. Follow these steps carefully:

#### A. Create the Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "My Calendar Agent").
3. Search for **"Google Calendar API"** and click **Enable**.

#### B. Configure OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**.
2. **User Type**: Select **External** and click **Create**.
3. **App Information**: Fill in the required fields (App name, support email, developer email).
4. **Permissions (Audience Control)**:
   - Ensure the **Publishing Status** stays at **Testing**. This is the safest way to use it privately.
5. **Test Users (Crucial)**:
   - Under the **Test users** section, click **ADD USERS**.
   - Add your own Google email address (the one with the calendar you want to use).
   - **Note**: Google will block any account that isn't on this list while the app is in Testing mode.

#### C. Create Credentials

1. Go to **APIs & Services → Credentials**.
2. Click **Create Credentials → OAuth 2.0 Client ID**.
3. **Application type**: Select **Desktop app**.
4. Download the JSON file, rename it to `credentials.json`, and place it in the **project root** folder.

### 3. First-Run Authentication

1. Launch the app (see the "Running" section below).
2. Open `http://localhost:3000` in your browser.
3. Click the **LOGIN** button in the top right.
4. Follow the Google link to authorize. You will be given an **Authorization Code**.
5. Copy the code, paste it into the app's modal and hit **SUBMIT**.

> Your `token.json` is now generated! It is stored locally and will be reused for future sessions.

---

## 🛠️ Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` to select your provider and add your API key:
   ```env
   LLM_PROVIDER=gemini          # gemini | openai | anthropic
   MODEL_NAME=gemini-2.5-flash
   GEMINI_API_KEY=your_key_here
   ```

---

## 🏃 Running the App

### Option A: Docker (Recommended)

Fast and isolated setup:

```bash
docker compose up --build
```

### Option B: Local Setup

Great for development or low-resource machines:

```bash
chmod +x run.sh
./run.sh
```

This script handles virtual environments, dependency installation, and server launches automatically.

---

## ⚙️ How the Agent Works

1. **Context Building**: The agent calls `get_current_datetime` to understand "today".
2. **Availability Check**: It uses `get_free_slots` to find open windows within your "work hours" before your deadline.
3. **Proposal**: It presents a clear plan (e.g., "I'd like to book Tuesday 10–11:30 AM and Wednesday 2–3:30 PM").
4. **User Confirmation**: It waits for you to say "yes" or "looks good" before touching your calendar.
5. **Execution**: Once confirmed, it uses `create_calendar_events` to book the slots.

---

## 💡 Pro-Tips

- **Be Specific**: Try "Schedule 4 hours for project X before EOD Thursday, morning preferred."
- **Preferences**: You can tell the agent "one long block if possible" or "don't schedule on Mondays."
- **Control**: Use the **CLEAR** button to reset the session if you want to start a fresh scheduling request.

---

## 🛡️ Security & Privacy

- **Local Storage**: `credentials.json` and `token.json` are stored ONLY on your machine and are git-ignored.
- **Scoped Access**: The agent only has access to your Google Calendar; no other Google data is retrieved.
- **Direct Connection**: All communication goes directly between your machine and Google/LLM APIs.

---

Made for those who want to reclaim their time. ⏱️
