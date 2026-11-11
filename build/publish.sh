#!/bin/bash
# Commit + push the site as Gyaanoxa. The GitHub job also commits (video updates), so a rebase may conflict on
# generated files: take GitHub's version of them, rebuild every page, and never push a file with conflict markers.
# Usage: bash build/publish.sh "commit message"
set -u
cd "$(dirname "$0")/.." || exit 1
G=(git -c user.name=Gyaanoxa -c user.email=351388292+gyaanoxa@users.noreply.github.com)
"${G[@]}" add -A
"${G[@]}" diff --cached --quiet || "${G[@]}" commit -q -m "$1"
for try in 1 2 3; do
  if ! "${G[@]}" pull -q --rebase 2>/dev/null; then
    while [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; do
      for f in $(git diff --name-only --diff-filter=U); do
        git checkout --ours -- "$f" 2>/dev/null || git checkout --theirs -- "$f"
      done
      py build/build.py >/dev/null 2>&1 || python build/build.py >/dev/null
      "${G[@]}" add -A
      GIT_EDITOR=true "${G[@]}" rebase --continue >/dev/null 2>&1 || break
    done
  fi
  if git grep -q -E "^(<<<<<<< |>>>>>>> )" -- '*.html' '*.css' '*.json' '*.py'; then
    echo "conflict markers left - not pushing:"; git grep -l -E "^(<<<<<<< |>>>>>>> )" -- '*.html' '*.css' '*.json' '*.py'
    exit 1
  fi
  git -c http.postBuffer=157286400 push -q && { git status -sb | head -1; exit 0; }
  sleep 5
done
exit 1
