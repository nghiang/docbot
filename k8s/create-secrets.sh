#!/usr/bin/env bash
# Run this ONCE on the cluster to set up secrets before ArgoCD sync.
# These are NOT managed by ArgoCD to keep credentials out of git.
set -euo pipefail

NAMESPACE="docbot"
HARBOR_REGISTRY="100.87.103.100:8000"

echo "==> Creating namespace"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

echo "==> Creating Harbor image pull secret"
kubectl create secret docker-registry harbor-secret \
  --docker-server="$HARBOR_REGISTRY" \
  --docker-username="$HARBOR_USERNAME" \
  --docker-password="$HARBOR_PASSWORD" \
  --namespace="$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Creating app secret (edit values before running!)"
kubectl apply -f k8s/secret.yaml

echo "Done. You can now apply the ArgoCD Application:"
echo "  kubectl apply -f argocd/app.yaml"
