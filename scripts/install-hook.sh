#!/bin/bash
# Install the post-commit hook for blog syndication reminders.
# Run once: bash scripts/install-hook.sh

set -e

HOOK_SRC="$(dirname "$0")/post-commit"
HOOK_DST="$(git rev-parse --git-dir)/hooks/post-commit"

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

echo "✅ post-commit hook installed at .git/hooks/post-commit"
