#!/usr/bin/env bash
# Milestone 3 - load distribution check:
# sends N POSTs through the ingress and counts how many each pod served.
# Usage: ./scripts/count_servedby.sh 30
# Uses curl --resolve so it works even without a /etc/hosts entry.
set -e
cd "$(dirname "$0")/.."
N=${1:-30}
IP=$(minikube ip)
OUT=results/servedby_$(date +%s).txt
mkdir -p results
for i in $(seq 1 $N); do
  curl -s --resolve emi.local:80:$IP -X POST http://emi.local/api/emi \
    -H "Content-Type: application/json" \
    -d "{\"principal\": $((RANDOM % 900000 + 10000)), \"rate\": $((RANDOM % 15 + 5)), \"months\": $((RANDOM % 300 + 12))}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['servedBy'])"
done | sort | uniq -c | tee "$OUT"
