# Example Chart Design Spec

Date: 2026-05-06

## Context

Gantry is a Kubernetes TUI for cluster management. This chart provides a realistic multi-resource test fixture deployed to minikube, allowing gantry developers to test the UI against real cluster resources spanning all major K8s resource types.

## Goal

Create `example-chart/` at gantry repo root — a self-contained Helm chart that deploys a 3-tier web application with comprehensive resource coverage (Deployments, StatefulSet, Services, Ingress, ConfigMap, Secret, HPA, PVC, ServiceAccount, RBAC, NetworkPolicy, Job, CronJob).

---

## Architecture

```
Browser → Ingress (nginx class, host: example.local)
           ├── /        → frontend-svc → Deployment: nginx (custom HTML)
           ├── /api     → backend-svc  → Deployment: ealen/echo-server
           └── (internal) backend → db-svc → StatefulSet: redis
```

### Prerequisites (minikube)

```bash
minikube addons enable ingress
echo "$(minikube ip) example.local" | sudo tee -a /etc/hosts
```

---

## Resources

| Resource | Name | Purpose |
|---|---|---|
| **Deployments** | | |
| Deployment | frontend | nginx serving custom HTML via ConfigMap |
| Deployment | backend | ealen/echo-server — echoes requests as JSON |
| **Stateful** | | |
| StatefulSet | db | redis — persistent key/value store |
| **Networking** | | |
| Service (ClusterIP) | frontend-svc | routes Ingress → frontend pods |
| Service (ClusterIP) | backend-svc | routes Ingress → backend pods |
| Service (ClusterIP) | db-svc | ClusterIP + headless for redis |
| Ingress | main | nginx class, host: example.local, path routing |
| **Config** | | |
| ConfigMap | app-config | nginx.conf + index.html for frontend |
| Secret | db-secret | redis password (base64 encoded) |
| **Scaling** | | |
| HPA | frontend-hpa | cpu-based, min 1 max 5, targets frontend Deployment |
| HPA | backend-hpa | cpu-based, min 1 max 3, targets backend Deployment |
| **Storage** | | |
| PVC | db-pvc | redis persistence, 1Gi, ReadWriteOnce |
| **RBAC** | | |
| ServiceAccount | app-sa | shared ServiceAccount for all pods |
| Role | pod-reader | get/list/watch pods in namespace |
| RoleBinding | pod-reader-binding | binds pod-reader Role to app-sa |
| **Policies** | | |
| NetworkPolicy | allow-traffic | frontend→backend, backend→db, deny all else |
| **Jobs** | | |
| Job | db-seed | one-shot: seeds redis with sample key/value on install |
| CronJob | health-ping | every 5 min: curl frontend health endpoint |

---

## File Structure

```
example-chart/
├── Chart.yaml                      # name: example-chart, version: 0.1.0
├── values.yaml                     # configurable parameters
└── templates/
    ├── _helpers.tpl
    ├── serviceaccount.yaml
    ├── role.yaml
    ├── rolebinding.yaml
    ├── configmap.yaml
    ├── secret.yaml
    ├── frontend-deployment.yaml
    ├── frontend-service.yaml
    ├── frontend-hpa.yaml
    ├── backend-deployment.yaml
    ├── backend-service.yaml
    ├── backend-hpa.yaml
    ├── db-statefulset.yaml
    ├── db-service.yaml
    ├── ingress.yaml
    ├── networkpolicy.yaml
    ├── job.yaml
    └── cronjob.yaml
```

---

## values.yaml Structure

```yaml
global:
  nameOverride: ""

frontend:
  image: nginx:alpine
  replicas: 2
  hpa:
    enabled: true
    minReplicas: 1
    maxReplicas: 5
    cpuTarget: 70

backend:
  image: ealen/echo-server:latest
  replicas: 1
  hpa:
    enabled: true
    minReplicas: 1
    maxReplicas: 3
    cpuTarget: 70

db:
  image: redis:7-alpine
  password: "changeme"
  storage: 1Gi

ingress:
  host: example.local
  className: nginx

cronjob:
  schedule: "*/5 * * * *"
  image: curlimages/curl:latest
```

---

## Ingress Path Routing

```yaml
rules:
  - host: example.local
    http:
      paths:
        - path: /api
          pathType: Prefix
          backend: backend-svc:80
        - path: /
          pathType: Prefix
          backend: frontend-svc:80
```

---

## NetworkPolicy Rules

- **frontend pods**: deny all, allow egress to backend pods only
- **backend pods**: allow ingress from frontend, allow egress to db pods, deny else
- **db pods**: allow ingress from backend pods, deny else

---

## Frontend HTML

Simple page that:
- Displays "Hello from Gantry Example Chart"
- Shows current pod name (via k8s metadata)
- Has a button that calls `/api` via fetch
- Includes CSS for basic styling

---

## Backend Behavior

`ealen/echo-server` image — echoes incoming HTTP requests as JSON response. No additional configuration needed.

---

## Database (Redis)

- Initialized via Job on install
- Job name: `<release>-db-seed`
- Seeds key: `gantry:example` → value: `{"message": "Hello from Gantry"}`
- StatefulSet: 1 pod, persistent 1Gi PVC
- Health checked via CronJob: `redis-cli PING`

---

## Verification

```bash
# Deploy to minikube
helm install example ./example-chart

# Check all resources
kubectl get all,ingress,configmap,secret,hpa,pvc,networkpolicy,sa,role,rolebinding,job,cronjob

# Access frontend
curl http://example.local

# Access backend echo
curl http://example.local/api/health

# View logs
kubectl logs -l app=frontend
kubectl logs -l app=backend
kubectl logs -l app=db

# Verify gantry UI
# Open gantry TUI and navigate cluster to see all resource types
uv run python -m gantry
```

---

## Design Decisions

1. **Single namespace** — all resources in default namespace (simplicity for testing)
2. **nginx alpine** — minimal image, widely available
3. **ealen/echo-server** — no external dependencies, self-contained backend
4. **redis** — common stateful example, persistent storage + ClusterIP service
5. **NetworkPolicy** — demonstrates traffic restriction for gantry UI testing
6. **HPA targets** — frontend/backend only (db StatefulSet stays at 1 replica)
7. **CronJob** — health ping demonstrates periodic jobs to gantry
8. **Job on install** — db-seed runs once, seeds redis with sample data

---

## Testing with Gantry

After deploy, open gantry and verify:
- ✓ Deployments visible with replica count and pod status
- ✓ StatefulSet visible with ordinal naming
- ✓ Services show endpoints and selectors
- ✓ Ingress shows routing rules
- ✓ ConfigMap visible with data keys
- ✓ Secret visible (masked values)
- ✓ HPA shows current/target replicas
- ✓ PVC shows storage usage
- ✓ ServiceAccount + Role + RoleBinding visible
- ✓ NetworkPolicy shows pod selectors
- ✓ Job shows completion status
- ✓ CronJob shows last execution time
