# MR REAN AI V3 FINAL

A Railway-ready Telegram AI coding assistant with a protected Admin Panel.

## Required Railway Variables

```text
TELEGRAM_BOT_TOKEN=...
GEMINI_API_KEY=...
OPENAI_API_KEY=...
MANUS_API_KEY=...
ADMIN_USERNAME=...
ADMIN_PASSWORD=...
```

Optional:

```text
AI_PROVIDER=auto
DAILY_CREDITS=20
DATA_DIR=/app/data
MAX_UPLOAD_MB=25
```

`AI_PROVIDER=auto` tries Gemini first, then OpenAI, then Manus.

## What it does

- Telegram `/start`, `/status`, `/new`, `/files`, `/export`
- Accepts ZIP project uploads
- Natural-language request such as `সব error fix করে zip দাও`
- AI proposes multi-file replacements
- Static verification for Python/JSON
- Retries once after a failed verification
- Returns a fixed ZIP
- Admin Panel at `/admin`
- Admin can block/unblock users and change daily credits
- Admin login is controlled only by `ADMIN_USERNAME` and `ADMIN_PASSWORD`
- Root page automatically shows the current Railway public domain and Admin link
- Uses Railway environment variables; no secrets are committed

## Deploy

1. Upload this repository to GitHub.
2. Railway -> New Project -> Deploy from GitHub.
3. Add the six required variables above.
4. Deploy.
5. Railway -> Service -> Settings -> Networking -> Generate Domain.
6. Open `https://YOUR-DOMAIN/admin`.

Railway provides `RAILWAY_PUBLIC_DOMAIN`, so the app can display its own public domain automatically.

## Important

This is a real working foundation, not a claim that it is identical to commercial products. Manus tasks are asynchronous and are polled through Manus API v2. Uploaded code is untrusted; the app intentionally does not execute arbitrary commands from a ZIP.
