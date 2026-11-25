#!/usr/bin/env bash
# Milestone 4 - fixed-replica experiments:
# rates 10/25/50/100/200 req/s x 1/2/3 replicas, 60 s each (15 runs).
# Saves raw latency CSVs, per-pod and host usage CSVs, and a summary.
set -e
cd "$(dirname "$0")/.."
mkdir -p results
SUMMARY=results/summary_fixed.csv
# talk to the ingress via the cluster IP (works without a /etc/hosts entry)
IP=$(minikube ip)
URL="http://$IP/api/emi"
echo "replicas,rate,requests,errors,avg_latency_ms" > "$SUMMARY"

for REPLICAS in 1 2 3; do
  minikube kubectl -- scale deployment emi-web -n emi --replicas=$REPLICAS
  minikube kubectl -- rollout status deployment emi-web -n emi
  sleep 5
  for RATE in 10 25 50 100 200; do
    echo "=== replicas=$REPLICAS rate=$RATE ==="
    python3 scripts/monitor.py --duration 70 --prefix results/fixed_r${RATE}_rep${REPLICAS} &
    MON_PID=$!
    sleep 5   # let monitoring start before the load
    OUT=$(python3 scripts/loadgen.py --url "$URL" --host emi.local --rate $RATE --duration 60 --out results/fixed_r${RATE}_rep${REPLICAS}.csv)
    wait $MON_PID
    echo "$OUT"
    REQ=$(echo "$OUT" | sed 's/requests=\([0-9]*\).*/\1/')
    ERR=$(echo "$OUT" | sed 's/.*errors=\([0-9]*\).*/\1/')
    AVG=$(echo "$OUT" | sed 's/.*avg_latency_ms=\([0-9.]*\)/\1/')
    echo "$REPLICAS,$RATE,$REQ,$ERR,$AVG" >> "$SUMMARY"
    sleep 10  # cool-down between runs
  done
done
echo "All fixed-replica runs finished. Summary in $SUMMARY"
