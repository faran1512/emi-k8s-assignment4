#!/usr/bin/env python3
"""Simple load generator for the EMI app.

Sends POST /api/emi with random valid inputs at a fixed rate for a fixed time.
Saves every request's latency to a CSV and prints a summary.
Usage: python3 loadgen.py --rate 50 --duration 60 --out results/run.csv
"""
import argparse, csv, json, random, threading, time, urllib.request, urllib.error


def send_request(url, host=None):
    """Send one POST with random inputs. Returns (latency_ms, error, served_by)."""
    body = json.dumps({
        "principal": round(random.uniform(10000, 1000000), 2),
        "rate": round(random.uniform(5, 20), 2),
        "months": random.randint(6, 360),
    }).encode()
    headers = {"Content-Type": "application/json"}
    if host:
        headers["Host"] = host
    req = urllib.request.Request(url, data=body, headers=headers)
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            served_by = json.loads(resp.read()).get("servedBy", "?")
            return (time.time() - start) * 1000, 0, served_by
    except Exception:
        return (time.time() - start) * 1000, 1, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://emi.local/api/emi")
    ap.add_argument("--host", default=None,
                    help="optional Host header, e.g. when using --url http://$(minikube ip)/api/emi --host emi.local")
    ap.add_argument("--rate", type=int, required=True, help="requests per second")
    ap.add_argument("--duration", type=int, required=True, help="seconds")
    ap.add_argument("--out", required=True, help="CSV file for raw results")
    args = ap.parse_args()

    rows = []          # (timestamp, latency_ms, error, served_by)
    lock = threading.Lock()

    def worker():
        latency, error, served_by = send_request(args.url, args.host)
        with lock:
            rows.append((time.time(), latency, error, served_by))

    # fire `rate` requests per second, spread over the second
    t_end = time.time() + args.duration
    while time.time() < t_end:
        tick = time.time()
        for i in range(args.rate):
            threading.Timer(i / args.rate, worker).start()
        time.sleep(max(0, 1.0 - (time.time() - tick)))

    time.sleep(2)  # let the last threads finish
    rows.sort()

    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "latency_ms", "error", "served_by"])
        w.writerows(rows)

    errors = sum(1 for r in rows if r[2])
    avg = sum(r[1] for r in rows) / len(rows) if rows else 0
    print(f"requests={len(rows)} errors={errors} avg_latency_ms={avg:.2f}")


if __name__ == "__main__":
    main()
