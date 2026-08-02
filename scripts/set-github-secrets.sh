#!/bin/bash
# Set all GitHub Actions secrets expected by .github/workflows/*.yml
# using the GitHub CLI.
#
# Usage:
#   1. gh auth login                     # authenticate once
#   2. export VERCEL_TOKEN=<token>       # required (vercel.com/account/tokens)
#   3. ./scripts/set-github-secrets.sh   # Vercel secrets only
#      ./scripts/set-github-secrets.sh --all   # include Docker/SSH/Slack secrets
#
# Env vars read (for --all): DOCKER_USERNAME, DOCKER_PASSWORD, SSH_PRIVATE_KEY,
#   STAGING_SSH_HOST, STAGING_SSH_USER, PROD_SSH_HOST, PROD_SSH_USER,
#   SLACK_WEBHOOK_URL.

set -e

REPO="${GITHUB_REPOSITORY:-ShikkhaHub/ShikkhaHub}"
MODE="${1:-vercel}"

# Vercel team + project identifiers (not secrets, safe to hardcode)
VERCEL_ORG_ID="${VERCEL_ORG_ID:-team_81FQPbgLVb40hc48pk9y3Zz3}"
VERCEL_PROJECT_ID_FRONTEND="${VERCEL_PROJECT_ID_FRONTEND:-prj_iDknPDAJVk2y8qXFpokrZl9l1UuN}"
VERCEL_PROJECT_ID_BACKEND="${VERCEL_PROJECT_ID_BACKEND:-prj_hBcPTwvMdqMAJvyu9iOmeYIVQyUd}"

echo "==> Setting secrets on $REPO"

if [ -z "$VERCEL_TOKEN" ]; then
  echo "ERROR: VERCEL_TOKEN is not set."
  echo "Create one at https://vercel.com/account/tokens then: export VERCEL_TOKEN=..."
  exit 1
fi

gh secret set VERCEL_TOKEN -R "$REPO" -b "$VERCEL_TOKEN"
gh secret set VERCEL_ORG_ID -R "$REPO" -b "$VERCEL_ORG_ID"
gh secret set VERCEL_PROJECT_ID_FRONTEND -R "$REPO" -b "$VERCEL_PROJECT_ID_FRONTEND"
gh secret set VERCEL_PROJECT_ID_BACKEND -R "$REPO" -b "$VERCEL_PROJECT_ID_BACKEND"
echo "==> Vercel secrets set (4/12)"

if [ "$MODE" != "--all" ]; then
  echo "Done. Run '$0 --all' to also set the Docker/SSH/Slack secrets."
  exit 0
fi

set_secret() {
  local name="$1"
  local value="${!name}"
  if [ -z "$value" ]; then
    echo "!! Skipping $name (env var not set)"
  else
    gh secret set "$name" -R "$REPO" -b "$value"
  fi
}

set_secret DOCKER_USERNAME
set_secret DOCKER_PASSWORD
set_secret SSH_PRIVATE_KEY
set_secret STAGING_SSH_HOST
set_secret STAGING_SSH_USER
set_secret PROD_SSH_HOST
set_secret PROD_SSH_USER
set_secret SLACK_WEBHOOK_URL

echo "==> All secrets set."
echo "Verify: gh secret list -R $REPO"
