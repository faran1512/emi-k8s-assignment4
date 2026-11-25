# Assignment 4 – Loan EMI Calculator on Kubernetes (Minikube)

A Loan EMI (Equated Monthly Instalment) calculator web app that stores every
calculation in MongoDB. The app runs as a Deployment behind a ClusterIP
Service, MongoDB runs as a 3-member replica set in a StatefulSet with
persistent volumes, and traffic enters through the NGINX Ingress controller.
A HorizontalPodAutoscaler scales the web pods between 1 and 5 replicas.

## Repository structure

```
app/        web application (Node.js/Express + HTML/jQuery/Bootstrap)
k8s/        all Kubernetes manifests
scripts/    load generator, monitoring and experiment scripts
results/    raw outputs and graphs from Milestones 3 and 4
images/     screenshots used in the report
report.md   milestone-by-milestone report (export to PDF for submission)
README.md   this file
```

## Prerequisites

- minikube, kubectl (or `minikube kubectl --`), docker
- Python 3 with `psutil` and `matplotlib` (only for the Milestone 3/4 scripts)

## Bring up the whole system on a fresh cluster

```bash
minikube start
minikube addons enable ingress

# build the app image and load it into minikube
docker build -t emi-web:1.0 app/
minikube image load emi-web:1.0

# deploy everything (namespace, MongoDB, web app, ingress, HPA)
minikube kubectl -- apply -f k8s/

# map emi.local to the cluster (Linux)
echo "$(minikube ip) emi.local" | sudo tee -a /etc/hosts
# on Windows/macOS with the docker driver run `minikube tunnel` instead
# and map 127.0.0.1 emi.local

# watch the pods come up
minikube kubectl -- get pods -n emi -w
```

Then open http://emi.local in a browser.

(Alternatively, build directly against Minikube's Docker daemon after
`eval $(minikube docker-env)`. The Deployment uses
`imagePullPolicy: IfNotPresent`, so the local image is used.)

## Useful commands

```bash
# port-forward instead of ingress (Milestone 2 verification)
minikube kubectl -- port-forward svc/emi-web 8080:80 -n emi

# scale the web tier by hand
minikube kubectl -- scale deployment emi-web -n emi --replicas=5

# rolling update to a new image and rollback
minikube kubectl -- set image deployment/emi-web emi-web=emi-web:1.1 -n emi
minikube kubectl -- rollout undo deployment/emi-web -n emi

# check the MongoDB replica set
minikube kubectl -- exec mongo-0 -n emi -- mongosh --quiet --eval 'rs.status()'
```

## Milestone 3/4 scripts

All scripts are in `scripts/` and write into `results/`:

- `count_servedby.sh N` – send N POSTs through the ingress and count how many
  each pod served.
- `run_fixed_experiments.sh` – the 15 fixed-replica runs
  (rates 10/25/50/100/200 req/s × 1/2/3 replicas, 60 s each) with per-pod and
  host monitoring. **Delete the HPA first** (`minikube kubectl -- delete hpa
  emi-web -n emi`) so it does not interfere with the fixed replica counts.
- `run_autoscale_test.sh` – the 10-minute autoscaling test
  (2 min @ 10 req/s, 5 min @ 100 req/s, 3 min @ 10 req/s). Apply
  `k8s/05-hpa.yaml` first.
- `make_graphs.py` – builds the three required graphs into `results/graphs/`.
