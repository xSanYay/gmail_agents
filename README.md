# gmail_agents
A collection of gmail ai assistant/ agents.

Make a simple fastapi backend.

Button -> authenticate -> goes through oauth process and gets the access token in the sqlite. 

model:

gmail_account
Access_token
refresh token
scopes (deafualt it to read for now)
created at



Now using this token, we make a gmail fetch call to read the mails.

Use tools with optional parameters:
from email
date
context ( like subject etc)


## Local dev

### 1) Create env

- Copy `backend/.env.example` to `backend/.env` and fill:
	- `GOOGLE_CLIENT_ID`
	- `GOOGLE_CLIENT_SECRET`
	- `GOOGLE_REDIRECT_URI` (defaults to your ngrok callback)

### 2) Install + run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- http://localhost:8000/

## API

- `GET /auth/start` -> redirects to Google OAuth
- `GET /api/callback` -> OAuth callback, stores tokens in SQLite
- `GET /gmail/messages?from=...&date=YYYY-MM-DD&context=...&context_field=subject|any&max_results=10`

Notes:

- Tokens are stored in `app.db` (SQLite) by default.
- Never commit your `.env`.

