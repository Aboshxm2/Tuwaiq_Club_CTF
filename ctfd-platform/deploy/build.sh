#!/usr/bin/env sh
# Build every deployable challenge image.
#
# Each subdirectory that contains a Dockerfile becomes the image
# "taibah-ctf/<dirname>:latest" — the same name used in catalog.DEPLOYABLE.
#
# Run this on every swarm node labelled for challenges (whale's "Swarm Nodes"),
# so the images are present locally. Those nodes never pull from a registry;
# see PRODUCTION.md, step 5.
set -eu

cd "$(dirname "$0")"

for dir in */; do
  slug=${dir%/}
  [ -f "$slug/Dockerfile" ] || continue
  image="taibah-ctf/${slug}:latest"
  echo ">> building ${image}"
  docker build -t "$image" "$slug"
done

echo ">> done. Built images:"
docker images "taibah-ctf/*" 2>/dev/null || docker images | grep '^taibah-ctf/' || true
