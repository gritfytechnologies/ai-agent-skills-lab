# Setup

Everything in this lab runs locally on one machine: Python for the agents,
Docker for the one database, and API keys for the outside world. Budget about
20 minutes for first-time setup.

## 1. Prerequisites

- **Python 3.11 or newer** — check with `python3 --version`.
- **Docker** (with the Compose plugin) — only needed for projects 02, 04, and
  06, which use Postgres. Check with `docker compose version`.
- A code editor and a terminal. Nothing else.

## 2. Create the environment and install dependencies

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

The root `requirements.txt` covers all six projects. Two projects need one
extra package for Google APIs — install it when you get there (the project
guides call it out):

```bash
# Projects 01 and 06 only (Google Calendar / Gmail client libraries)
pip install google-api-python-client google-auth google-auth-oauthlib
```

## 3. Configure environment variables

```bash
cp .env.example .env
```

Then open `.env` and fill in what you have. You do **not** need every key on
day one — each project guide lists exactly which keys it needs. `.env` is in
`.gitignore`; never commit it.

| Variable | Used by | Where to get it |
|----------|---------|-----------------|
| `ANTHROPIC_API_KEY` | All projects | Anthropic Console → Settings → API Keys (https://platform.claude.com/settings/keys) |
| `OPENWEATHER_API_KEY` | 01 | https://openweathermap.org/api — sign up, key arrives by email; free tier |
| `GOOGLE_MAPS_API_KEY` | 03 | Google Cloud Console → APIs & Services → Credentials (see below) |
| `TAVILY_API_KEY` | 05 | https://app.tavily.com — free tier, 1,000 credits/month |
| `DATABASE_URL` | 02, 04, 06 | Pre-filled for the local Docker Postgres; change only if you run your own |
| `GOOGLE_CREDENTIALS_FILE` | 01, 06 | Path to the OAuth client JSON you download from Google Cloud (see below) |

## 4. Where each key comes from

### Anthropic (Claude API) — all projects

1. Create an account at https://console.anthropic.com (the API Console is now
   also reachable as platform.claude.com).
2. Add a small amount of credit (US$5 is plenty for this whole lab).
3. Settings → API Keys → Create Key. Copy it into `ANTHROPIC_API_KEY`.

### OpenWeather — project 01

1. Sign up at https://openweathermap.org.
2. Your default key appears under your profile → API keys. Free tier allows
   1,000 calls/day — far more than this project needs.
3. New keys can take up to ~2 hours to activate; if you get a 401, wait and
   retry before debugging your code.

### Google Cloud — projects 01 (Calendar), 03 (Maps), 06 (Gmail)

One Google Cloud project can serve all three.

1. Go to https://console.cloud.google.com and create a project (e.g.
   `ai-agent-skills-lab`).
2. **For Maps (project 03):** enable the *Places API*, *Distance Matrix API*
   (or Routes API), and *Geocoding API* under APIs & Services → Library, then
   create an **API key** under Credentials and paste it into
   `GOOGLE_MAPS_API_KEY`. Restrict the key to those APIs once it works.
3. **For Calendar and Gmail (projects 01 and 06):** enable the *Google
   Calendar API* and/or *Gmail API*, then under Credentials create an
   **OAuth client ID** of type *Desktop app* and download the JSON. Save it as
   `credentials.json` in the project folder (it is git-ignored) and point
   `GOOGLE_CREDENTIALS_FILE` at it. On first run a browser opens for you to
   consent; the resulting `token.json` is also git-ignored. While your app is
   in "Testing" mode, add your own Google account as a test user on the OAuth
   consent screen — that is sufficient for personal use.

### Tavily — project 05

1. Sign up at https://app.tavily.com.
2. Copy the key (starts with `tvly-`) into `TAVILY_API_KEY`. The free tier's
   1,000 monthly credits cover this project many times over.

## 5. Start Postgres (projects 02, 04, 06)

From the repo root:

```bash
docker compose up -d
```

This starts one Postgres 16 container with the pgvector extension available
(image `pgvector/pgvector:pg16`), listening on `localhost:5432`, with a named
volume (`lab_pgdata`) so your data survives restarts. The default
`DATABASE_URL` in `.env.example` already matches it.

Verify it's up and the extension works:

```bash
docker compose exec db psql -U lab -d lab -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extname FROM pg_extension;"
```

You should see `vector` in the output. Useful commands:

```bash
docker compose ps          # status
docker compose logs db     # logs
docker compose down        # stop (data kept in the volume)
docker compose down -v     # stop AND delete all data — fresh start
```

## 6. Cost note

This lab is deliberately cheap:

- **Claude API:** the projects use a mid-tier model at learning pace. Expect a
  few US dollars *total* across all six projects if you build and test
  normally. Set a spend limit in the Anthropic Console if you want a hard cap.
- **OpenWeather:** free tier (1,000 calls/day).
- **Google Maps:** new accounts get free monthly usage allotments per API;
  this project's call volume sits well inside them. Enable billing only if
  Google requires it for your account, and set a budget alert.
- **Google Calendar / Gmail APIs:** free.
- **Tavily:** free tier, 1,000 credits/month.
- **Postgres:** local Docker, free.

If a guide ever tells you to loop an agent "until it's good," put a cap on the
iterations first (the guides do). Uncapped loops are the only realistic way to
spend real money here.

## 7. Sanity check

```bash
python3 -c "import anthropic, fastapi, langgraph, pydantic; print('imports ok')"
docker compose up -d && docker compose ps
```

Then open `01-tool-calling/GUIDE.md` and start building.
