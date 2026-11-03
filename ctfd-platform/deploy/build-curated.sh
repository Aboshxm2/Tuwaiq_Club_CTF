#!/usr/bin/env sh
# Build on every challenge node before importing the curated catalog.
set -eu
cd "$(dirname "$0")"
for mode in last-edit forgotten-route frontend-pass trial-login refund-desk caravan-ledger template-studio; do
  docker build --build-arg "CHALLENGE=$mode" -t "taibah-ctf/curated-$mode:v1" curated-web
done
