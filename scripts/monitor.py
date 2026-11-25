#!/usr/bin/env python3
"""Simple profiler: records pod and host resource usage to CSV files.

- Every 15 s: per-pod CPU and memory from `kubectl top pods -n emi`
- Every 1 s : host overall CPU % (psutil)

Usage: python3 monitor.py --duration 70 --prefix results/run1
Writes: results/run1_pods.csv and results/run1_host.csv
"""
import argparse, csv, subprocess, time

try:
    import psutil
except ImportError:
    raise SystemExit("please install psutil: pip3 install psutil")


def top_pods():
    """Return list of (pod, cpu_millicores, memory_mi)."""
    out = subprocess.run(
        ["minikube", "kubectl", "--", "top", "pods", "-n", "emi", "--no-headers"],
        capture_output=True, text=True).stdout
    result = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            cpu = parts[1].rstrip("m")
            mem = parts[2].rstrip("Mi")
            result.append((parts[0], cpu, mem))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, required=True, help="seconds to record")
    ap.add_argument("--prefix", required=True, help="output file prefix")
    args = ap.parse_args()

    pods_file = open(args.prefix + "_pods.csv", "w", newline="")
    host_file = open(args.prefix + "_host.csv", "w", newline="")
    pods_csv = csv.writer(pods_file)
    host_csv = csv.writer(host_file)
    pods_csv.writerow(["timestamp", "pod", "cpu_millicores", "memory_mi"])
    host_csv.writerow(["timestamp", "host_cpu_percent"])

    start = time.time()
    next_pod_sample = 0
    while time.time() - start < args.duration:
        now = time.time()
        host_csv.writerow([f"{now:.3f}", psutil.cpu_percent(interval=None)])
        if now - start >= next_pod_sample:
            for pod, cpu, mem in top_pods():
                pods_csv.writerow([f"{now:.3f}", pod, cpu, mem])
            pods_file.flush()
            next_pod_sample += 15
        host_file.flush()
        time.sleep(1)

    pods_file.close()
    host_file.close()


if __name__ == "__main__":
    main()
