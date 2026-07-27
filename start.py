"""
start.py — one command to run the AFB backend.

    python start.py

Instead of starting uvicorn straight away, this runs a short pre-flight check
first. Every failure that cost us time during setup is checked here, and each
one prints what to do about it rather than a traceback.

Options:
    python start.py --port 8080     run on a different port
    python start.py --no-reload     don't restart on file changes
    python start.py --check         run the checks and stop, don't start
"""

import os
import sys
import argparse

# Colour codes. Windows Terminal and PowerShell 7 handle these; older consoles
# print them as noise, so we turn them off if the output isn't a real terminal.
if sys.stdout.isatty():
    OK, BAD, WARN, DIM, END = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m"
else:
    OK = BAD = WARN = DIM = END = ""

HERE = os.path.dirname(os.path.abspath(__file__))

# Anchor to this file's folder so the script works no matter where it's run
# from. uvicorn resolves "app.main:app" against the working directory, so
# without this, launching from another folder passes every check and then
# fails to import.
os.chdir(HERE)
sys.path.insert(0, HERE)
problems = []
warnings = []


def check(label, passed, fix=None, warn_only=False):
    """Print one check line. Collect failures so we can report them together."""
    if passed:
        print(f"  {OK}OK{END}    {label}")
    elif warn_only:
        print(f"  {WARN}WARN{END}  {label}")
        if fix:
            warnings.append(fix)
    else:
        print(f"  {BAD}FAIL{END}  {label}")
        if fix:
            problems.append(fix)
    return passed


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-reload", action="store_true")
    ap.add_argument("--check", action="store_true", help="run checks only")
    args = ap.parse_args()

    print(f"\n{DIM}American Food & Beverage — starting up{END}")
    print(f"{DIM}{'-' * 58}{END}")

    # ---------------------------------------------------------------- 1. venv
    # A virtual environment sets sys.prefix to its own folder while
    # sys.base_prefix stays pointed at the system Python. If they match, we are
    # NOT in a venv — which is why 'No module named fastapi' keeps happening.
    in_venv = sys.prefix != sys.base_prefix
    # Warning, not a failure: what actually matters is whether the packages are
    # importable. Missing venv is only the usual REASON they aren't.
    check(
        f"virtual environment active  {DIM}({os.path.basename(sys.prefix)}){END}",
        in_venv,
        "Not running inside the venv. It works if the packages happen to be\n"
        "    installed system-wide, but activate it to be sure you're using the\n"
        "    same Python and package versions every time:\n"
        "      .\\venv\\Scripts\\Activate.ps1",
        warn_only=True,
    )

    print(f"  {DIM}      python {sys.version.split()[0]} at {sys.executable}{END}")

    # ------------------------------------------------------- 2. right folder
    # 'app.main:app' means "the folder called app, the file main.py, the object
    # called app". That only resolves if we're standing in the folder that
    # CONTAINS app/, so check for the file rather than trusting the path.
    main_py = os.path.join(HERE, "app", "main.py")
    check(
        "app/main.py found",
        os.path.isfile(main_py),
        f"Expected {main_py}\n"
        "    Run this script from the afb_backend folder, where app/ lives.",
    )

    # ---------------------------------------------------------- 3. packages
    missing = []
    for mod in ("fastapi", "uvicorn", "sqlalchemy", "pydantic"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    venv_hint = ("\n    You are not in the venv — that is almost certainly why. Try:\n"
                 "      .\\venv\\Scripts\\Activate.ps1\n"
                 "    then run this again before installing anything."
                 if not in_venv else
                 "\n    Install them:\n      pip install -r requirements.txt")
    check(
        "required packages installed",
        not missing,
        f"Missing: {', '.join(missing)}" + venv_hint,
    )

    # ------------------------------------------------------ 4. static site
    # The site is mounted by main.py. If the folder is missing, FastAPI raises
    # RuntimeError at import time and the server never starts.
    site = os.path.join(HERE, "afb-site")
    if check(
        "afb-site folder found",
        os.path.isdir(site),
        f"Expected {site}\n"
        "    Extract afb-package.zip into this folder, or remove the\n"
        "    app.mount('/store', ...) line from app/main.py.",
    ):
        # assets/ holds the CSS and JS. Without it the pages load unstyled,
        # which looks broken but throws no error — worth catching early.
        assets = os.path.join(site, "assets")
        have = os.path.isdir(assets) and {
            "site.css", "app.js", "catalog.js"
        }.issubset(set(os.listdir(assets)))
        check(
            "afb-site/assets complete",
            have,
            "assets/ is missing or incomplete. The site will load with no styling\n"
            "    and no catalog. It needs site.css, app.js and catalog.js.",
            warn_only=True,
        )

    # ------------------------------------------------------ 5. SOP seed file
    seed = os.path.join(HERE, "app", "sops.json")
    has_seed = check(
        "app/sops.json found",
        os.path.isfile(seed),
        "The SOP library can't be seeded without it. Everything else still runs.",
        warn_only=True,
    )

    # --------------------------------------------------------- 6. database
    # Render sets DATABASE_URL. Locally it's usually unset, which means SQLite —
    # fine on your machine, data-losing on Render.
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        kind = "Postgres" if "postgres" in db_url else db_url.split(":")[0]
        check(f"DATABASE_URL set  {DIM}({kind}){END}", True)
    else:
        check(
            "DATABASE_URL not set — using local SQLite",
            True,
            "Fine locally. On Render this must be set to Postgres or every\n"
            "    deploy wipes your data. See docs/HOSTING.md.",
            warn_only=True,
        )

    # ------------------------------------------------------------ 7. email
    mail_on = os.getenv("MAIL_ENABLED") == "1"
    if mail_on:
        creds = bool(os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"))
        check("MAIL_ENABLED=1 and SMTP credentials present", creds,
              "MAIL_ENABLED is on but SMTP_USER or SMTP_PASSWORD is missing.\n"
              "    Applications will save, but no email will go out.",
              warn_only=True)
    else:
        print(f"  {DIM}INFO  email off (MAIL_ENABLED unset) — applications save, "
              f"nothing sends{END}")

    # ------------------------------------------------------------- report
    print(f"{DIM}{'-' * 58}{END}")

    if problems:
        print(f"\n{BAD}Can't start yet.{END} Fix these:\n")
        for i, p in enumerate(problems, 1):
            print(f"  {i}. {p}\n")
        sys.exit(1)

    for w in warnings:
        print(f"\n  {WARN}Note:{END} {w}")
    if warnings:
        print()

    # ------------------------------------------------- seed the SOP library
    # Safe to run every time — seed_from_json skips documents that already
    # exist, so this only does work on a fresh database.
    if has_seed:
        try:
            from app.routers.sops import seed_from_json
            added = seed_from_json(seed)
            if added:
                print(f"  {OK}seeded{END} SOP library: {', '.join(added)}")
            else:
                print(f"  {DIM}SOP library already seeded{END}")
        except Exception as e:
            print(f"  {WARN}couldn't seed the SOP library:{END} {e}")

    if args.check:
        print(f"\n{OK}All checks passed.{END} Run without --check to start.\n")
        return

    # ------------------------------------------------------------- go
    print(f"\n{OK}Starting.{END}  Press CTRL+C to stop.\n")
    print(f"  Site        http://{args.host}:{args.port}/store/")
    print(f"  Careers     http://{args.host}:{args.port}/store/careers.html")
    print(f"  SOP library http://{args.host}:{args.port}/store/sops.html")
    print(f"  Ops         http://{args.host}:{args.port}/ops")
    print(f"  API docs    http://{args.host}:{args.port}/docs")
    print()

    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        reload_dirs=[os.path.join(HERE, "app")],
    )


if __name__ == "__main__":
    main()
