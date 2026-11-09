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
#
# Rotation later: update the 1Password item, re-run the script, done.
set -euo pipefail

REPO="${HOMELAB_REPO:-ciuc123/homelab}"
VAULT="${OP_VAULT:-Private}"
ALL_KEYS=(CF_API_TOKEN CF_ZONE_ID CF_ZONE_NAME VERCEL_TOKEN VERCEL_TEAM_ID NEON_API_KEY GH_PAT NPM_TOKEN CLERK_PLATFORM_API_KEY)
KEYS=("$@")
if [ ${#KEYS[@]} -eq 0 ]; then KEYS=("${ALL_KEYS[@]}"); fi

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
  Used to create the client repos and to read the private infra-template.
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

echo
echo "Done. Check: gh secret list -R $REPO"
