# Prompt for Claude Code (revised)

Your working tree isn't clean, and one of the untracked files
(`app/routers/applications.py`) turns out to be a real, more complete
implementation of the same feature as one of my patches — not a naming
coincidence. Don't apply the patches mechanically. Use the staged plan below
instead.

---

## Step 1 — Safety first: commit and push what's already here

```
Before touching any of the four patch files, I want you to commit and push
everything currently sitting uncommitted in this repo — the modified files
(app/database.py, app/main.py, app/models.py, app/schemas.py, seed.py,
web/dashboard.html, web/order.html, web/production.html, afb.db) and the
untracked new work (app/routers/applications.py, app/routers/mixes.py,
app/routers/order_tasks.py, app/routers/sops.py, app/sops.json, afb-site/,
docs/, sop-library/, CLAUDE.md, and anything else currently untracked except
the four .patch files and PROMPT_FOR_CLAUDE_CODE.md — leave those out of
this commit).

Do NOT touch the "New folder/afb_backend/..." deletions yet — just leave
those staged or unstaged as they are, I'll look at those separately.

Show me `git status` and a `git diff --stat` summary before committing, so
I can see exactly what's about to be committed. Use a commit message like
"Snapshot: local work in progress (mixes, order tasks, SOPs, careers
applications with email+resume) before merging in patch series." Then push
to origin main.

Stop after this push and wait for me before going any further.
```

Once that's pushed, the actual risk (this work only existing on one laptop)
is gone no matter what happens next.

## Step 2 — Reconcile careers/applications by hand, not by patch

```
Patch 1 (0001-Add-careers-site-staff-login.patch) adds a competing
implementation of job applications — a `job_applications` table and
`/careers/apply` router, versus the `applications` table and
`/api/applications` router already in this repo. Do NOT apply patch 1.

Instead, look at both app/routers/applications.py (existing) and the
careers-related content inside patch 1 (you can inspect it with
`git show` against a scratch branch, or by reading the .patch file directly
without applying it) and help me merge them:

1. Keep app/routers/applications.py as the foundation — it already does
   real SMTP email (applicant confirmation + resume forwarded to the
   hiring inbox) and resume upload validation, which patch 1 doesn't have
   at all.
2. Add authentication to it. Right now `list_applications` and
   `update_status` in applications.py have no auth check at all — anyone
   who finds the URL can read every applicant's name, email, phone, and
   pull resumes. Patch 1 has a working staff-session auth system
   (app/auth.py, get_current_staff, require_role) — wire that same
   dependency into applications.py's GET and PATCH endpoints, restricted
   to admin/manager roles.
3. Decide with me whether to also add patch 1's job-posting management
   (create/edit/close postings via an admin UI) on top of the existing
   `role` free-text field, or leave `role` as free text for now. Ask me
   before building that part — it's a real scope decision, not a
   mechanical merge.
4. Do NOT apply patch 1's public careers.html/login.html/careers-admin.html
   if equivalent pages already exist under afb-site/ or elsewhere in the
   untracked work — check first and show me what's already there before
   creating anything that might duplicate it.

Show me your plan before writing any code.
```

## Step 3 — Patches 2-4, one at a time, checking for the same overlap

```
Patches 2 (security/backups), 3 (inventory locations), and 4 (direct
link/share) don't touch applications.py, but they do modify
app/main.py, app/models.py, app/schemas.py, seed.py, web/dashboard.html,
and web/production.html — the same files modified in the work we just
committed in Step 1. Before applying each one:

1. Try `git am` for that patch alone.
2. If it applies cleanly, good — show me a summary of what it added and
   move to the next patch.
3. If it fails, stop and show me the actual conflicting lines — don't
   guess at a resolution. In particular check whether the other session's
   work already added something equivalent (e.g. if seed.py already seeds
   staff logins or similar, we don't want two competing versions).

Do them in order: patch 2, then patch 3, then patch 4. Stop after each one
and wait for my confirmation before moving to the next.
```

## Step 4 — Final smoke test, then push

```
Once everything is merged and applied, reseed the local database and start
the server. Confirm /login, /careers (or wherever the real careers page
ends up living), /stock, /dashboard, and /api/applications all respond
correctly, and that submitting a test application still triggers the
email flow (with MAIL_ENABLED unset/off, so it just logs instead of
actually sending). Show me a full summary of the final state before
pushing to origin main. Don't push until I say so.
```

---

## Why this is slower than the original plan, on purpose

The original four-patch plan assumed GitHub had everything and your laptop
just had a few uncommitted tweaks on top. That's not what's actually true —
your laptop has a materially better careers/applications implementation
that was never pushed. Applying my patch on top of that mechanically would
have either silently created two competing systems or thrown a conflict
Claude Code would've had to guess its way through. Better to reconcile it
deliberately, in the open, than to force it.
