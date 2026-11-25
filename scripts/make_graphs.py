#!/usr/bin/env python3
"""Create the three graphs required by Milestone 4 from the files in results/.

Graph 1: average response time vs request rate (one line per replica count)
Graph 2: per-pod CPU over time during the 100 req/s run with 3 replicas
Graph 3: request rate, average CPU and replica count over the autoscaling test
"""
import csv, glob, os, collections

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
OUT = os.path.join(RESULTS, "graphs")
os.makedirs(OUT, exist_ok=True)


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def graph1():
    """Average response time vs request rate, one line per replica count."""
    data = read_csv(os.path.join(RESULTS, "summary_fixed.csv"))
    by_replicas = collections.defaultdict(list)
    for row in data:
        by_replicas[int(row["replicas"])].append((int(row["rate"]), float(row["avg_latency_ms"])))
    for replicas, points in sorted(by_replicas.items()):
        points.sort()
        rates = [p[0] for p in points]
        avgs = [p[1] for p in points]
        plt.plot(rates, avgs, marker="o", label=f"{replicas} replica{'s' if replicas > 1 else ''}")
    plt.xlabel("Request rate (requests/s)")
    plt.ylabel("Average response time (ms)")
    plt.title("Graph 1: Response time vs request rate")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(OUT, "graph1_response_time.png"), dpi=150)
    plt.close()


def graph2():
    """Per-pod CPU over time during the 100 req/s, 3-replica run."""
    rows = read_csv(os.path.join(RESULTS, "fixed_r100_rep3_pods.csv"))
    per_pod = collections.defaultdict(list)
    t0 = min(float(r["timestamp"]) for r in rows)
    for r in rows:
        # 100m is the CPU request, so millicores == % of the request
        per_pod[r["pod"]].append((float(r["timestamp"]) - t0, float(r["cpu_millicores"])))
    for pod, points in sorted(per_pod.items()):
        if pod.startswith("emi-web"):
            points.sort()
            plt.plot([p[0] for p in points], [p[1] for p in points], marker="o", label=pod)
    plt.xlabel("Time (s)")
    plt.ylabel("CPU utilization (% of requested 100m)")
    plt.title("Graph 2: Pod CPU during 100 req/s run (3 replicas)")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(OUT, "graph2_pod_cpu.png"), dpi=150)
    plt.close()


def graph3():
    """Request rate, average CPU and replica count over the autoscaling test."""
    hpa = read_csv(os.path.join(RESULTS, "autoscale_hpa.csv"))
    t0 = float(hpa[0]["timestamp"])
    t_hpa = [(float(r["timestamp"]) - t0) / 60.0 for r in hpa]
    replicas = [int(r["replicas"]) for r in hpa]
    cpu = [float(r["cpu_percent"]) for r in hpa]

    # request rate timeline from the three phase CSVs
    t_rate, rate = [], []
    phases = [("autoscale_p1.csv", 10), ("autoscale_p2.csv", 100), ("autoscale_p3.csv", 10)]
    for fname, r in phases:
        path = os.path.join(RESULTS, fname)
        if not os.path.exists(path):
            continue
        rows = read_csv(path)
        start = (float(rows[0]["timestamp"]) - t0) / 60.0
        end = (float(rows[-1]["timestamp"]) - t0) / 60.0
        t_rate += [start, end]
        rate += [r, r]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 2]})
    # top: request rate
    ax1.plot(t_rate, rate, color="tab:blue", drawstyle="steps-post")
    ax1.set_ylabel("Request rate (req/s)")
    ax1.set_ylim(0, 120)
    ax1.grid(True)

    # bottom: CPU (left axis) and replica count (right axis)
    ax2.plot(t_hpa, cpu, color="tab:red", marker="o", label="Average CPU (%)")
    ax2.set_xlabel("Time (minutes)")
    ax2.set_ylabel("Average CPU (%)", color="tab:red")
    ax2.set_ylim(0, 120)
    ax2.grid(True)

    ax3 = ax2.twinx()
    ax3.plot(t_hpa, replicas, color="tab:green", marker="s", drawstyle="steps-post",
             label="Replicas")
    ax3.set_ylabel("Replicas", color="tab:green")
    ax3.set_ylim(0, 6)

    lines = ax2.get_lines() + ax3.get_lines()
    ax2.legend(lines, [l.get_label() for l in lines], loc="upper right")
    plt.suptitle("Graph 3: Autoscaling test (10 minutes)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "graph3_autoscaling.png"), dpi=150)
    plt.close()


if __name__ == "__main__":
    graph1()
    graph2()
    graph3()
    print("Graphs saved to", OUT)
