#!/usr/bin/env bash
# Deploy a version of ACEest to Kubernetes with the chosen strategy.
# usage: scripts/deploy.sh <rolling|blue-green|canary|ab-testing|shadow> <image> <new-tag>
#   STABLE_TAG     version kept as the baseline (default 3.1.2)
#   CANARY_WEIGHT  % of traffic sent to the canary (default 20)
set -euo pipefail
STRATEGY=${1:?strategy}; IMAGE=${2:?image}; NEW_TAG=${3:?tag}
STABLE_TAG=${STABLE_TAG:-3.1.2}; CANARY_WEIGHT=${CANARY_WEIGHT:-20}
NS=aceest
cd "$(dirname "$0")/.."

render() { # file -> stdout with placeholders filled in
  sed -e "s#__IMAGE__#${IMAGE}#g" -e "s#__NEW_TAG__#${NEW_TAG}#g" -e "s#__STABLE_TAG__#${STABLE_TAG}#g" \
      -e "s#__CANARY_WEIGHT__#${CANARY_WEIGHT}#g" -e "s#__BLUE_TAG__#${BLUE_TAG:-}#g" \
      -e "s#__GREEN_TAG__#${GREEN_TAG:-}#g" -e "s#__LIVE_COLOR__#${LIVE_COLOR:-blue}#g" "$1"
}
apply() { for f in "$@"; do render "$f" | kubectl apply -f -; done; }
wait_rollout() { kubectl -n $NS rollout status "deployment/$1" --timeout=180s; }
smoke() { # deployment -> checks /health inside one of its pods
  kubectl -n $NS exec "deploy/$1" -- python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5000/health').status==200 else 1)"
}

kubectl apply -f k8s/base/namespace.yaml

case "$STRATEGY" in
  rolling)
    apply k8s/rolling/rolling.yaml
    kubectl -n $NS annotate deployment/aceest-rolling kubernetes.io/change-cause="deploy ${NEW_TAG}" --overwrite
    wait_rollout aceest-rolling && smoke aceest-rolling
    ;;
  blue-green)
    LIVE=$(kubectl -n $NS get svc aceest-bluegreen -o jsonpath='{.spec.selector.track}' 2>/dev/null || true)
    if [ -z "$LIVE" ]; then   # first run: blue = stable is live
      BLUE_TAG=$STABLE_TAG; LIVE_COLOR=blue
      apply k8s/blue-green/blue-deployment.yaml k8s/blue-green/service-ingress.yaml
      wait_rollout aceest-blue; LIVE=blue
    fi
    if [ "$LIVE" = blue ]; then TARGET=green; GREEN_TAG=$NEW_TAG; apply k8s/blue-green/green-deployment.yaml
    else TARGET=blue; BLUE_TAG=$NEW_TAG; apply k8s/blue-green/blue-deployment.yaml; fi
    wait_rollout aceest-$TARGET && smoke aceest-$TARGET
    kubectl -n $NS annotate svc aceest-bluegreen aceest/previous-color="$LIVE" --overwrite
    kubectl -n $NS patch svc aceest-bluegreen -p "{\"spec\":{\"selector\":{\"app\":\"aceest-fitness\",\"track\":\"$TARGET\"}}}"
    echo "Blue-Green: traffic switched $LIVE -> $TARGET (${NEW_TAG})"
    ;;
  canary)
    apply k8s/canary/stable.yaml k8s/canary/canary.yaml
    wait_rollout aceest-stable && wait_rollout aceest-canary && smoke aceest-canary
    echo "Canary: ${CANARY_WEIGHT}% of canary.aceest.local -> ${NEW_TAG}; promote with scripts/promote-canary.sh"
    ;;
  ab-testing)
    apply k8s/ab-testing/variant-a.yaml k8s/ab-testing/variant-b.yaml
    wait_rollout aceest-variant-a && wait_rollout aceest-variant-b && smoke aceest-variant-b
    echo "A/B: header X-Variant: B -> ${NEW_TAG}, everyone else -> ${STABLE_TAG}"
    ;;
  shadow)
    apply k8s/shadow/shadow.yaml k8s/shadow/primary.yaml
    wait_rollout aceest-primary && wait_rollout aceest-shadow && smoke aceest-shadow
    echo "Shadow: users served by ${STABLE_TAG}; traffic mirrored to ${NEW_TAG}"
    ;;
  *) echo "unknown strategy $STRATEGY" >&2; exit 2 ;;
esac
kubectl -n $NS get deploy,svc,ingress -o wide
