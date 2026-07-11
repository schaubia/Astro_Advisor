# Deploying AstroAdvisor to another host

The app is a standard Python/Streamlit process — the `Dockerfile` in this
folder packages it so it can run on essentially any host that accepts a
container: a VPS, Render, Railway, Fly.io, DigitalOcean App Platform, AWS/GCP/Azure, etc.

## Build & run locally (sanity check before deploying)

```bash
docker compose up --build
```

Visit `http://localhost:8501`.

## Option A — Managed container platforms (least ops work)

**Render, Railway, Fly.io, DigitalOcean App Platform** all work the same way:
point them at your GitHub repo, they detect the `Dockerfile`, build it, and
give you a public HTTPS URL. No server management, TLS certs, or reverse
proxy config needed. This is the closest equivalent to "another Streamlit
Cloud" but with more control over resources and scaling.

Typical steps (Render as an example):
1. Push this repo (including `Dockerfile`, `streamlit_app.py`,
   `dso_catalog.csv`, `requirements.txt`) to GitHub.
2. In Render: New → Web Service → connect the repo → it auto-detects the
   Dockerfile → deploy.
3. Set the health check path to `/_stcore/health`.

## Option B — Your own VPS (most control, most setup)

1. Install Docker on the VPS.
2. Copy the repo over (`git clone` or `scp`).
3. `docker compose up -d --build`.
4. Put a reverse proxy in front for HTTPS. **Caddy** is the simplest —
   it gets you automatic Let's Encrypt certificates with a two-line config:

   ```
   yourdomain.com {
       reverse_proxy localhost:8501
   }
   ```

   Run Caddy as a system service or its own container, then
   `caddy run --config Caddyfile`.

## Concurrency: what actually happens with many simultaneous users

Streamlit isn't a traditional stateless web app, so a few things are worth
knowing before pointing real traffic at this:

- **One process, many sessions.** A single `streamlit run` process can serve
  many browser sessions concurrently — each user gets their own session
  state (their sidebar selections, results, etc.) — but it's still one
  Python process. A slow, CPU-heavy computation for one user (e.g. scoring
  109+ objects with `ephem`, especially with the Simbad extension enabled)
  can momentarily slow down other users' requests, since Streamlit's script
  reruns aren't isolated across CPU cores by default.
- **`@st.cache_data` is per-process, not per-user.** This is good — the
  Open-Meteo seeing forecast and CSV catalog load once and are shared by
  everyone hitting that instance — but if you scale to *multiple* container
  instances behind a load balancer, each instance has its own separate
  cache and will hit Open-Meteo independently.
- **Sessions are sticky to one instance.** If you do scale horizontally
  (multiple containers behind a load balancer for more capacity), you need
  **session affinity / sticky sessions** at the load balancer — a user's
  browser tab must keep talking to the same container, or their session
  state resets. Most managed platforms (Render, Fly.io) support this; a
  bare nginx/Caddy setup needs it configured explicitly (e.g. cookie-based
  or IP-hash sticky sessions).
- **External API limits.** Open-Meteo's free tier and Simbad both have
  reasonable-use rate limits. The app's caching (30 min for weather, 1 hour
  for Simbad) already helps a lot; it gets more important the more
  concurrent users you have, especially across multiple instances.

### Practical recommendation

For "a handful to a few dozen people using it at once," a **single
container with 1–2 vCPUs / 1GB+ RAM** on any of the platforms above will be
plenty — no horizontal scaling needed. Only reach for multiple instances +
sticky sessions once you're seeing real slowdowns under load, since it adds
real operational complexity for a personal-scale tool.

## Files in this deployment bundle

| File | Purpose |
|---|---|
| `Dockerfile` | Builds the app image (includes build tools `ephem` needs) |
| `.dockerignore` | Keeps the image lean |
| `docker-compose.yml` | One-command local build/run, or simple VPS deploy |
| `DEPLOYMENT.md` | This guide |
