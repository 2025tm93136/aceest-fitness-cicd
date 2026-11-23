#!/usr/bin/env bash
# Promote the canary: move stable to the canary's image, then remove the canary.
set -euo pipefail
NS=aceest
IMG=$(kubectl -n $NS get deploy aceest-canary -o jsonpath='{.spec.template.spec.containers[0].image}')
kubectl -n $NS set image deployment/aceest-stable aceest="$IMG"
kubectl -n $NS rollout status deployment/aceest-stable --timeout=180s
kubectl -n $NS delete ingress aceest-canary --ignore-not-found
kubectl -n $NS scale deployment/aceest-canary --replicas=0
echo "Canary promoted: stable now runs $IMG"
