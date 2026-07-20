#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# GHAM headlines updater — local (devbox cron) replacement for the GitHub
# "pythonapp" workflow.
#
# What it does:
#   1. Fully rebases the local GHAM checkout onto origin/main (autostash), so
#      concurrent changes to the repo are never clobbered.
#   2. Runs ./test.py to regenerate the ETF headline JS + cache files.
#   3. Commits the changed artifacts and pushes to main, retrying with a fresh
#      rebase if another actor pushed in the meantime.
#   4. Notifies a Google Chat webhook on success / no-op / failure.
#
# Secrets (API_USERNAME, API_PASSWORD, GCHAT_WEBHOOK) are read from ENV_FILE,
# which lives OUTSIDE the repo and is never committed.
# ---------------------------------------------------------------------------
set -uo pipefail

REPO_DIR="${GHAM_REPO_DIR:-$HOME/GHAM}"
ENV_FILE="${GHAM_ENV_FILE:-$HOME/GHAM/.env}"   # holds GCHAT_WEBHOOK
NETRC_MACHINE="public.etfg.com"                 # holds etfg API login/password
BRANCH="main"
TAG="gham-headlines"

# --- GCHAT_WEBHOOK from the (gitignored) .env -----------------------------
if [[ -f "$ENV_FILE" ]]; then
  set -a; # shellcheck disable=SC1090
  source "$ENV_FILE"; set +a
fi

# --- etfg API creds from ~/.netrc (unless already provided in env) --------
if [[ -z "${API_USERNAME:-}" || -z "${API_PASSWORD:-}" ]]; then
  API_USERNAME="$(python3 -c "import netrc;print(netrc.netrc().authenticators('$NETRC_MACHINE')[0])" 2>/dev/null)"
  API_PASSWORD="$(python3 -c "import netrc;print(netrc.netrc().authenticators('$NETRC_MACHINE')[2])" 2>/dev/null)"
fi
export API_USERNAME API_PASSWORD

json_escape() { python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"; }

notify() {
  # $1 = message text; no-op if webhook not configured
  [[ -n "${GCHAT_WEBHOOK:-}" ]] || return 0
  curl -sS -X POST "$GCHAT_WEBHOOK" \
    -H "Content-Type: application/json" \
    -d "$(printf '{"text": %s}' "$(json_escape "$1")")" >/dev/null 2>&1 || true
}

fail() {
  echo "[$TAG] FAILED: $1" >&2
  notify "❌ *GHAM headlines* (devbox cron) failed.
Host: $(hostname)
Step: $1
Time: $(date)"
  exit 1
}

echo "[$TAG] === run started $(date) ==="

[[ -n "${API_USERNAME:-}" && -n "${API_PASSWORD:-}" ]] \
  || fail "etfg API creds missing (checked ~/.netrc machine $NETRC_MACHINE)"

cd "$REPO_DIR" || fail "cannot cd to $REPO_DIR"

# --- 1. full rebase onto latest origin/main -------------------------------
git fetch origin "$BRANCH"                       || fail "git fetch"
git checkout "$BRANCH"                            || fail "git checkout $BRANCH"
git pull --rebase --autostash origin "$BRANCH"   || fail "git pull --rebase"

# --- 2. run the generator --------------------------------------------------
python3 ./test.py || fail "python3 ./test.py"

# --- 3. stage the artifacts the workflow tracked --------------------------
git add assets/js/* assets/old_cache.txt

if git diff --cached --quiet; then
  echo "[$TAG] No new data from API, nothing to commit."
  notify "ℹ️ *GHAM headlines* (devbox cron): no new data, nothing to commit.
Host: $(hostname)
Time: $(date)"
  exit 0
fi

git -c user.name="devbox-cron" -c user.email="cron@devbox" \
    commit -m "CRON Headlines $(date)" || fail "git commit"

# --- 4. push, re-rebasing on rejection ------------------------------------
for attempt in 1 2 3; do
  if git push origin "$BRANCH"; then
    notify "✅ *GHAM headlines* (devbox cron) succeeded.
Host: $(hostname)
Commit: $(git rev-parse --short HEAD) — $(git log -1 --pretty=%s)
Time: $(date)"
    echo "[$TAG] pushed on attempt $attempt"
    exit 0
  fi
  echo "[$TAG] push rejected (attempt $attempt) — rebasing and retrying…"
  git pull --rebase --autostash origin "$BRANCH" || fail "git pull --rebase (retry $attempt)"
done

fail "git push rejected after 3 attempts"
