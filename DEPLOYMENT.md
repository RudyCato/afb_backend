# Deploying AFB Ops (so no one needs Python/PowerShell ever again)

This turns the local-only setup into something everyone — you, staff, and the
client's team — can just open in a browser, from any device, with nothing
installed. Once deployed:

- **Desktop access** = a bookmark/shortcut to your URL
- **iPhone access** = "Add to Home Screen" — installs like a real app icon,
  opens full-screen, no App Store needed
- **Database** = real Postgres, safe for multiple people using it at once
  (not Google Drive — Drive can't handle simultaneous writes without
  corrupting the file, and has no live API a phone app can talk to)

## Steps (Render, free tier)

1. Push this project to a GitHub repo (Render deploys from GitHub).
   ```powershell
   cd afb_backend
   git init
   git add .
   git commit -m "Initial commit"
   ```
   Then create an empty repo on github.com and follow its "push an existing
   repository" instructions.

2. Go to https://render.com → sign up (free) → **New +** → **Blueprint**.
3. Connect your GitHub repo. Render will detect `render.yaml` in this project
   automatically and set up both:
   - a **web service** running the FastAPI app
   - a **free Postgres database**, wired up via the `DATABASE_URL` environment
     variable automatically — you don't need to configure anything by hand.
4. Click **Apply** / **Deploy**. First deploy takes a few minutes.
5. Once live, Render gives you a URL like `https://afb-backend.onrender.com`.
   - Order page: `https://afb-backend.onrender.com/order`
   - Dashboard: `https://afb-backend.onrender.com/dashboard`

6. **Seed the hosted database** (one-time, or whenever you want to reload
   the catalog): in the Render dashboard, open your web service → **Shell**
   tab, and run:
   ```
   python seed.py
   ```
   This runs against the live Postgres database, not your local machine.

## Adding it to your iPhone home screen

1. Open the `/order` link in **Safari** (must be Safari, not Chrome, for this
   to work on iOS).
2. Tap the **Share** icon → **Add to Home Screen**.
3. It now sits on your home screen with the AFB icon, opens full-screen with
   no browser address bar — feels like a real app.

Do the same for `/dashboard` if you want that as a separate icon too.

## Desktop access

No install needed — just bookmark the URL, or drag it to your desktop as a
shortcut. Anyone on the client's team can do the same with the link you
send them.

## Free tier notes

- Render's free web service "spins down" after 15 minutes of no traffic and
  takes ~30–60 seconds to wake back up on the next visit. Fine for a demo or
  light use; if that delay is annoying for daily use, their paid tier
  ($7/month) keeps it always-on.
- Render's free Postgres database expires after 90 days and needs to be
  recreated — fine for a pitch/demo phase; worth moving to a paid database
  ($7/month) once this becomes the client's actual production system.

## Local development still works exactly as before

Nothing about local development changed — `DATABASE_URL` simply isn't set
on your laptop, so it automatically falls back to the local SQLite file,
same as always:
```powershell
venv\Scripts\activate
python seed.py
uvicorn app.main:app --reload
```
