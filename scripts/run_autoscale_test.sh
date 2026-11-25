#!/usr/bin/env bash
# Milestone 4 - autoscaling test (10 minutes):
#   2 min at 10 req/s, 5 min at 100 req/s, 3 min at 10 req/s.
# Records the HPA replica count every 15 s and pod/host usage.
set -e
cd "$(dirname "$0")/.."
mkdir -p results
HPA_CSV=results/autoscale_hpa.csv
IP=$(minikube ip)
URL="http://$IP/api/emi"
echo "timestamp,replicas,cpu_percent" > "$HPA_CSV"

# Record HPA state every 15 s for 10 minutes (40 samples)
(
  for i in $(seq 1 40); do
    LINE=$(minikube kubectl -- get hpa emi-web -n emi --no-headers)
    # columns: NAME REFERENCE "cpu: cur%/target%" MINPODS MAXPODS REPLICAS AGE
    REPLICAS=$(echo "$LINE" | awk '{print $(NF-1)}')
    CPU=$(echo "$LINE" | grep -oP 'cpu: \K[0-9]+(?=%/)')
    echo "$(date +%s),$REPLICAS,${CPU:-0}" >> "$HPA_CSV"
    sleep 15
  done
) &
HPA_PID=$!

# Monitor pods and host for the whole test
python3 scripts/monitor.py --duration 600 --prefix results/autoscale &
MON_PID=$!

# Phase 1: 2 min at 10 req/s
echo "Phase 1: 10 req/s for 120 s"
python3 scripts/loadgen.py --url "$URL" --host emi.local --rate 10 --duration 120 --out results/autoscale_p1.csv
# Phase 2: 5 min at 100 req/s
echo "Phase 2: 100 req/s for 300 s"
python3 scripts/loadgen.py --url "$URL" --host emi.local --rate 100 --duration 300 --out results/autoscale_p2.csv
# Phase 3: 3 min at 10 req/s
echo "Phase 3: 10 req/s for 180 s"
python3 scripts/loadgen.py --url "$URL" --host emi.local --rate 10 --duration 180 --out results/autoscale_p3.csv

wait $HPA_PID $MON_PID
echo "Autoscaling test finished."
