#!/usr/bin/env bash
# Build and push one Docker image per released version (git tag v*).
# usage: DOCKERHUB_USER=<user> scripts/build-all-versions.sh   (run after: docker login)
set -euo pipefail
: "${DOCKERHUB_USER:?set DOCKERHUB_USER}"
IMAGE=$DOCKERHUB_USER/aceest-fitness
cd "$(dirname "$0")/.."
WORK=$(mktemp -d)
for tag in $(git tag -l 'v*' --sort=v:refname); do
  ver=${tag#v}
  git worktree add -f "$WORK/$ver" "$tag" >/dev/null
  echo "=== $tag"
  docker build --target test -t "$IMAGE:$ver-test" "$WORK/$ver"
  docker run --rm "$IMAGE:$ver-test"
  docker build --target runtime --build-arg APP_VERSION="$ver" -t "$IMAGE:$ver" "$WORK/$ver"
  docker push "$IMAGE:$ver"
  git worktree remove -f "$WORK/$ver"
done
docker tag "$IMAGE:$ver" "$IMAGE:latest" && docker push "$IMAGE:latest"
