# 📅 Calendar Agent

A local AI scheduling assistant that reads your Google Calendar and books work sessions from natural language requests.

> "Schedule 3 hours of work on Essay Draft before Friday"  
> → Agent checks free slots → proposes a plan → you confirm → events created ✓

---

## Features

- **Natural language scheduling** — describe your task, duration, and deadline
- **Clarifying questions** — the agent asks before acting, never guesses
- **Respects existing events** — only schedules in truly free time
- **Split sessions** — can break a 3-hour block into multiple smaller sessions
- **Configurable LLM** — defaults to Gemini 2.5 Flash; swap to OpenAI or Anthropic via `.env`

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Cloud project with Calendar API enabled
- An LLM API key (Gemini / OpenAI / Anthropic)

---

## Google Calendar Setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable **Google Calendar API**
4. Go to **APIs & Services → Credentials**
5. Create **OAuth 2.0 Client ID** → Application type: **Desktop app**
6. Download the JSON file and rename it to `credentials.json`
7. Place `credentials.json` in the **project root** (same folder as `run.sh`)

## First Run & Authentication

On the first run (or if your token expires):

1. Start the app (via `run.sh` or Docker).
2. Open `http://localhost:3000`.
3. Click the **LOGIN** button in the top right.
4. Follow the link to sign in with Google.
5. Google will provide an **Authorization Code** — copy it.
6. Paste the code into the app's modal and click **SUBMIT**.

> Your `token.json` is auto-generated after auth and reused on subsequent runs.

---

## Configuration

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Choose your LLM provider
LLM_PROVIDER=gemini          # gemini | openai | anthropic
MODEL_NAME=gemini-2.5-flash  # Model name for the chosen provider

# Set the key for your chosen provider:
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

**Model name examples by provider:**
| Provider | Example models |
|-----------|-----------------------------------------|
| gemini | `gemini-2.5-flash`, `gemini-1.5-pro` |
| openai | `gpt-4o`, `gpt-4o-mini` |
| anthropic | `claude-opus-4-5`, `claude-sonnet-4-5` |

---

## Running (without Docker)

```bash
chmod +x run.sh
./run.sh
```

The script will:

1. Create a Python virtual environment (first run only)
2. Install all backend dependencies
3. Run `npm install` for the frontend (first run only)
4. Launch both servers
5. Open `http://localhost:3000` in your browser

---

## Running with Docker

```bash
docker compose up --build
```

Then open `http://localhost:3000`.

> Make sure `credentials.json` is in the project root before starting Docker.  
> The `token.json` will be created inside the `backend/` directory and persisted via the backend volume mount.

---

## Project Structure

```
calendar-agent/
├── backend/
│   ├── main.py            # FastAPI app + session management
│   ├── agent.py           # LangGraph ReAct agent
│   ├── calendar_tools.py  # Google Calendar API tools
│   ├── config.py          # LLM provider config
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/ChatWindow.jsx
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── run.sh                 # Non-Docker launcher
├── .env.example
└── README.md
```

---

## How the Agent Works

1. You type a scheduling request
2. Agent calls `get_current_datetime` to know today's date
3. Agent calls `get_free_slots` to find available windows before your deadline
4. Agent **proposes** a schedule (e.g., "I'd like to book Tuesday 10–11:30 AM and Wednesday 2–3:30 PM")
5. You confirm → agent calls `create_calendar_events`
6. Agent reports back with confirmation and calendar links

---

## Tips

- Be specific about deadlines: "before Friday", "by end of day Thursday", "this week"
- You can specify preferences: "mornings only", "not Wednesday", "one long block if possible"
- The agent will ask if anything is unclear before booking
- Say "yes", "go ahead", "looks good" to confirm a proposed schedule
- Say "clear" or use the CLEAR button to start a fresh conversation

---

## Security Notes

- `credentials.json` and `token.json` are **never** committed to version control (see `.gitignore`)
- All data stays local — no external servers beyond Google Calendar API and your LLM provider
- The token grants Calendar access only to the authorized account
