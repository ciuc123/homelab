#!/usr/bin/env bash
# Set every Actions secret the provision workflow needs (see .env.example) in one sitting.
#
# For each key the script prints where to create it and which scopes it needs. The value comes from
# 1Password when an item named "homelab <KEY>" exists (field: credential) and the `op` CLI is signed in;
# otherwise you paste it hidden. It is sent to GitHub with `gh secret set` through stdin, so it never
# touches a command line, a file or the shell history. Only this repo needs the secrets: the client
# repos get their NPM_TOKEN from the provisioning run itself.
#
#   scripts/setup-secrets.sh                    walk through every key (empty paste = skip)
#   scripts/setup-secrets.sh VERCEL_TOKEN ...   only these keys
#   OP_VAULT=Private HOMELAB_REPO=ciuc123/homelab scripts/setup-secrets.sh
#   scripts/setup-secrets.sh --usage            only what the usage guard needs (2 secrets, then its variables)
#
# Variables (not secret, for the usage guard) are asked for in the open with a suggested default and set with
# `gh variable set`; they are only asked for with --usage or when one is named on the command line.
#
# Rotation later: update the 1Password item, re-run the script, done.
set -euo pipefail

REPO="${HOMELAB_REPO:-ciuc123/homelab}"
VAULT="${OP_VAULT:-Private}"
ALL_KEYS=(CF_API_TOKEN CF_ZONE_ID CF_ZONE_NAME VERCEL_TOKEN VERCEL_TEAM_ID NEON_API_KEY GH_PAT NPM_TOKEN CLERK_PLATFORM_API_KEY SENTRY_AUTH_TOKEN RESEND_API_KEY)
# The usage guard (.github/workflows/usage-guard.yml) also reads VERCEL_TOKEN, NEON_API_KEY and GH_PAT, set above.
USAGE_SECRETS=(SENTRY_AUTH_TOKEN RESEND_API_KEY)
USAGE_VARS=(USAGE_EMAIL_TO USAGE_EMAIL_FROM USAGE_STATE_REPO USAGE_GUARD_REF USAGE_APPLY)
KEYS=()
VARS=()
if [ "${1:-}" = "--usage" ]; then
  KEYS=("${USAGE_SECRETS[@]}")
  VARS=("${USAGE_VARS[@]}")
else
  for arg in "$@"; do
    case " ${USAGE_VARS[*]} " in *" $arg "*) VARS+=("$arg") ;; *) KEYS+=("$arg") ;; esac
  done
  if [ $# -eq 0 ]; then KEYS=("${ALL_KEYS[@]}"); fi
fi

guide() {
  case "$1" in
    CF_API_TOKEN) cat <<'EOF'
  Create:  https://dash.cloudflare.com/profile/api-tokens  ->  Create Token  ->  template "Edit zone DNS"
  Scope:   Zone / DNS / Edit, limited to the one zone the client subdomains live in
EOF
      ;;
    CF_ZONE_ID) cat <<'EOF'
  Find:    https://dash.cloudflare.com  ->  open the zone  ->  Overview, right column "Zone ID" (not a secret, but kept with the rest)
EOF
      ;;
    CF_ZONE_NAME) cat <<'EOF'
  Value:   the zone name itself, for example example.com (client sites are subdomains of it)
EOF
      ;;
    VERCEL_TOKEN) cat <<'EOF'
  Create:  https://vercel.com/account/settings/tokens  ->  Create  (scope: your account; expiry as you prefer)
EOF
      ;;
    VERCEL_TEAM_ID) cat <<'EOF'
  Optional (only when the projects live in a team): https://vercel.com/teams  ->  team Settings  ->  General  ->  Team ID
EOF
      ;;
    NEON_API_KEY) cat <<'EOF'
  Optional (only for neon_provider "neon"): https://console.neon.tech/app/settings/api-keys  ->  Create API key
EOF
      ;;
    GH_PAT) cat <<'EOF'
  Create:  https://github.com/settings/tokens/new  ->  classic token, scopes: repo + workflow
  Used to create the client repos and to read the private infra-template. The usage guard also uses it to set the
  USAGE_* variables on watched repos, keep its state in USAGE_STATE and read workflow runs (all covered by "repo").
EOF
      ;;
    NPM_TOKEN) cat <<'EOF'
  Create:  https://github.com/settings/tokens/new  ->  classic token, scope: read:packages
  Used by the client sites to install the private @ciuc123/app-core package.
EOF
      ;;
    CLERK_PLATFORM_API_KEY) cat <<'EOF'
  Optional (automates Clerk application creation): https://dashboard.clerk.com  ->  your platform settings  ->  Platform API keys (ak_...)
  Without it, the run prints a manual Clerk checklist instead.
EOF
      ;;
    SENTRY_AUTH_TOKEN) cat <<'EOF'
  Usage guard. Create:  https://sentry.io/settings/account/api/auth-tokens/  ->  Create New Token (a personal token;
  organization tokens only allow CI scopes). Scopes: org:read, project:read, project:write.
  Used to list the uptime monitors and to slow the uptime check down when Vercel usage runs over plan. Optional.
EOF
      ;;
    RESEND_API_KEY) cat <<'EOF'
  Usage guard. Create:  https://resend.com/api-keys  ->  Create API Key, permission "Sending access", domain: the one
  USAGE_EMAIL_FROM is on. Use a key of its own, not a site's. Without it there is no email (a level going up still
  fails the run, so GitHub's failed-run email is the fallback).
EOF
      ;;
  esac
}

# Variables: "suggested default|what it is".
var_help() {
  case "$1" in
    USAGE_EMAIL_TO) echo "|where the morning summary and alerts go" ;;
    USAGE_EMAIL_FROM) echo "|sender, an address on a domain verified in Resend" ;;
    USAGE_STATE_REPO) echo "ciuc123/infra-template|repo whose Actions variable USAGE_STATE holds the guard's state" ;;
    USAGE_GUARD_REF) echo "main|infra-template branch to run (feat/usage-guard while testing; main once merged)" ;;
    USAGE_APPLY) echo "false|true lets scheduled runs switch the levers; keep false until a few report-only runs look right" ;;
  esac
}

have_op=0
if command -v op >/dev/null 2>&1 && op whoami >/dev/null 2>&1; then
  have_op=1
else
  echo "1Password CLI not available or not signed in (op signin): values are pasted by hand." >&2
fi

for key in "${KEYS[@]}"; do
  echo
  echo "== $key =="
  guide "$key"
  value=""
  if [ "$have_op" = 1 ]; then
    value="$(op read "op://$VAULT/homelab $key/credential" 2>/dev/null || true)"
    [ -n "$value" ] && echo "  Using the value from 1Password ($VAULT / homelab $key)."
  fi
  if [ -z "$value" ]; then
    read -rs -p "  Paste $key (empty = skip): " value
    echo
    if [ -z "$value" ]; then
      echo "  Skipped."
      continue
    fi
    echo "  Tip: save it in 1Password as item \"homelab $key\" (field: credential); the next run then needs no pasting."
  fi
  printf '%s' "$value" | gh secret set "$key" -R "$REPO"
  echo "  Set on $REPO."
done

for var in "${VARS[@]}"; do
  help="$(var_help "$var")"
  default="${help%%|*}"
  what="${help#*|}"
  current="$(gh variable get "$var" -R "$REPO" 2>/dev/null || true)"
  echo
  echo "== $var (variable) =="
  echo "  $what"
  if [ -n "$current" ]; then echo "  Now: $current"; fi
  read -r -p "  Value [${current:-$default}] (- = delete): " value
  value="${value:-${current:-$default}}"
  if [ "$value" = "-" ]; then
    gh variable delete "$var" -R "$REPO" >/dev/null 2>&1 || true
    echo "  Deleted."
  elif [ -z "$value" ]; then
    echo "  Skipped."
  else
    gh variable set "$var" -R "$REPO" --body "$value"
    echo "  Set on $REPO."
  fi
done

echo
echo "Done. Check: gh secret list -R $REPO; gh variable list -R $REPO"
