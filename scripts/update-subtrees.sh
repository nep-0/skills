#!/usr/bin/env bash
set -euo pipefail

CONFIG="${CONFIG:-subtrees.json}"
ONLY="${1:-}"

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to read $CONFIG." >&2
  exit 1
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Subtree config not found: $CONFIG" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Working tree has uncommitted changes. Commit or stash them before updating." >&2
  exit 1
fi

count="$(jq '.subtrees | length' "$CONFIG")"
if [[ "$count" -eq 0 ]]; then
  echo "No subtrees configured in $CONFIG." >&2
  exit 1
fi

updated=0

for index in $(seq 0 "$((count - 1))"); do
  subtree="$(jq -c ".subtrees[$index]" "$CONFIG")"

  name="$(jq -r '.name' <<<"$subtree")"
  remote="$(jq -r '.remote' <<<"$subtree")"
  remote_url="$(jq -r '.remote_url' <<<"$subtree")"
  branch="$(jq -r '.branch // "main"' <<<"$subtree")"
  upstream_prefix="$(jq -r '.upstream_prefix' <<<"$subtree")"
  local_prefix="$(jq -r '.local_prefix' <<<"$subtree")"

  if [[ -n "$ONLY" && "$ONLY" != "$name" ]]; then
    continue
  fi

  for field in name remote remote_url upstream_prefix local_prefix; do
    value="$(jq -r ".$field // empty" <<<"$subtree")"
    if [[ -z "$value" ]]; then
      echo "Missing required field '$field' in subtree entry $index." >&2
      exit 1
    fi
  done

  safe_name="$(printf '%s' "$name" | tr -c '[:alnum:]._-' '-')"
  split_branch="update-subtree-${safe_name}"

  echo "Updating $name..."

  if ! git remote get-url "$remote" >/dev/null 2>&1; then
    git remote add "$remote" "$remote_url"
  fi

  git fetch "$remote" "$branch"
  git branch -D "$split_branch" >/dev/null 2>&1 || true
  git subtree split \
    --prefix="$upstream_prefix" \
    "$remote/$branch" \
    -b "$split_branch"

  git subtree pull \
    --prefix="$local_prefix" \
    . "$split_branch" \
    --squash
  git branch -D "$split_branch" >/dev/null

  echo "Updated $local_prefix from $remote/$branch:$upstream_prefix"
  updated="$((updated + 1))"
done

if [[ -n "$ONLY" && "$updated" -eq 0 ]]; then
  echo "No subtree named '$ONLY' found in $CONFIG." >&2
  exit 1
fi

echo "Updated $updated subtree(s)."
