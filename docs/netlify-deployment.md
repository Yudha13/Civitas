# Netlify Deployment

CIVITAS is split into a static React frontend and a FastAPI backend with PostgreSQL.
Netlify hosts the frontend only. The API, WebSocket service, and database must remain
available on a separate backend host.

## Netlify site setup

1. Open https://app.netlify.com/start and choose GitHub.
2. Authorize Netlify to access `Yudha13/Civitas`.
3. Select branch `beta/isolation-and-session-hardening` for a Closed Beta preview.
4. Netlify reads the root `netlify.toml`. Expected settings:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `dist`
   - Node.js: `22`
5. Deploy the site. Do not select `main` as the production branch until the beta PR is reviewed and merged.

## Required environment variables

Set these in Netlify under Site configuration → Environment variables.
Use values for the deployed backend, not localhost.

| Variable | Value |
| --- | --- |
| `VITE_API_URL` | HTTPS base URL of the FastAPI API, for example `https://api.example.com` |
| `VITE_WS_URL` | WebSocket base URL for the same API, using `wss://`, for example `wss://api.example.com` |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth Web client ID |

These values are embedded into the frontend at build time. Trigger a new deploy after changing them.
Do not put backend secrets, database credentials, or `CIVITAS_SESSION_SECRET` in any `VITE_*` variable.

## Backend requirements before the frontend can log in

- Deploy the FastAPI backend and PostgreSQL database separately.
- Configure the backend's allowed CORS origin to the exact Netlify site URL.
- Configure Google OAuth's authorized JavaScript origin to the Netlify site URL.
- Configure the Google OAuth redirect URI to the backend callback URL required by the backend implementation.
- Set backend runtime variables documented in `docs/closed-beta.md`, including `CIVITAS_ENV=beta`, a private `CIVITAS_SESSION_SECRET` of at least 32 characters, and `DATABASE_URL`.
- Serve the API over HTTPS and WebSocket over WSS. Beta cookies must be secure.

## Expected result and limitation

A successful Netlify deploy confirms that the frontend compiles and static assets are published.
It does not confirm that login, REST requests, WebSocket updates, or simulation persistence work.
Those require the separately deployed backend and database, followed by end-to-end testing.
