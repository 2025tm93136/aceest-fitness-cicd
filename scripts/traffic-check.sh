#!/usr/bin/env bash
# Send requests through the ingress and count which version answered.
# usage: scripts/traffic-check.sh <host> [requests] [extra curl args...]
set -euo pipefail
HOST=${1:?host e.g. canary.aceest.local}; N=${2:-50}; shift $(( $# > 1 ? 2 : 1 ))
IP=$(minikube ip)
for _ in $(seq 1 "$N"); do
  curl -s -H "Host: $HOST" "$@" "http://$IP/version" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["version"], d["track"])'
done | sort | uniq -c
