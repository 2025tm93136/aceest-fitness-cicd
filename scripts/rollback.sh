#!/usr/bin/env bash
# Revert to the last stable version for the given strategy.
# usage: scripts/rollback.sh <rolling|blue-green|canary|ab-testing|shadow>
set -euo pipefail
NS=aceest
case "${1:?strategy}" in
  rolling)
    kubectl -n $NS rollout undo deployment/aceest-rolling
    kubectl -n $NS rollout status deployment/aceest-rolling --timeout=180s ;;
  blue-green)
    PREV=$(kubectl -n $NS get svc aceest-bluegreen -o jsonpath='{.metadata.annotations.aceest/previous-color}')
    CUR=$(kubectl -n $NS get svc aceest-bluegreen -o jsonpath='{.spec.selector.track}')
    kubectl -n $NS patch svc aceest-bluegreen -p "{\"spec\":{\"selector\":{\"app\":\"aceest-fitness\",\"track\":\"$PREV\"}}}"
    kubectl -n $NS annotate svc aceest-bluegreen aceest/previous-color="$CUR" --overwrite
    echo "Blue-Green rollback: $CUR -> $PREV" ;;
  canary)
    kubectl -n $NS delete ingress aceest-canary --ignore-not-found
    kubectl -n $NS scale deployment/aceest-canary --replicas=0
    echo "Canary removed: 100% traffic on stable" ;;
  ab-testing)
    kubectl -n $NS delete ingress aceest-ab-b --ignore-not-found
    echo "A/B variant B disabled: all traffic on variant A" ;;
  shadow)
    kubectl -n $NS annotate ingress aceest-shadow-main nginx.ingress.kubernetes.io/mirror-target- || true
    kubectl -n $NS scale deployment/aceest-shadow --replicas=0
    echo "Shadow traffic stopped" ;;
  *) echo "unknown strategy" >&2; exit 2 ;;
esac
