# Example Chart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a production-grade Helm chart in `example-chart/` that deploys a 3-tier web application to minikube, covering all K8s resource types for gantry TUI testing.

**Architecture:** 
- Frontend: nginx serving custom HTML
- Backend: ealen/echo-server (lightweight HTTP echo)
- Database: redis with persistent storage
- All tiers connected via Services and routed through nginx Ingress with path-based routing
- NetworkPolicy restricts traffic: frontend→backend→db only
- HPA on frontend/backend, Job for redis seeding, CronJob for health checks

**Tech Stack:** 
- Helm 3.x (chart format)
- minikube (target cluster)
- nginx Ingress Controller
- Redis 7 (StatefulSet)
- nginx Alpine (frontend image)
- ealen/echo-server (backend image)

---

## Task 1: Initialize Chart Structure and Metadata

**Files:**
- Create: `example-chart/Chart.yaml`
- Create: `example-chart/values.yaml`
- Create: `example-chart/templates/` directory

### Step 1: Create Chart.yaml

```bash
mkdir -p example-chart/templates
cd example-chart
```

Create `Chart.yaml`:

```yaml
apiVersion: v2
name: example-chart
description: A Helm chart for Gantry testing with comprehensive K8s resources
type: application
version: 0.1.0
appVersion: "1.0"
keywords:
  - kubernetes
  - gantry
  - test-fixture
maintainers:
  - name: Gantry Team
```

- [ ] Create `example-chart/Chart.yaml` with content above

### Step 2: Create values.yaml with all configuration parameters

Create `values.yaml`:

```yaml
global:
  nameOverride: ""
  fullnameOverride: ""

frontend:
  enabled: true
  replicaCount: 2
  image:
    repository: nginx
    tag: alpine
    pullPolicy: IfNotPresent
  port: 80
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 100m
      memory: 128Mi
  hpa:
    enabled: true
    minReplicas: 1
    maxReplicas: 5
    targetCPUUtilizationPercentage: 70

backend:
  enabled: true
  replicaCount: 1
  image:
    repository: ealen/echo-server
    tag: latest
    pullPolicy: IfNotPresent
  port: 8080
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 100m
      memory: 128Mi
  hpa:
    enabled: true
    minReplicas: 1
    maxReplicas: 3
    targetCPUUtilizationPercentage: 70

db:
  enabled: true
  image:
    repository: redis
    tag: "7-alpine"
    pullPolicy: IfNotPresent
  port: 6379
  password: "changeme123"
  persistence:
    enabled: true
    size: 1Gi
    storageClassName: standard
  resources:
    requests:
      cpu: 50m
      memory: 128Mi
    limits:
      cpu: 100m
      memory: 256Mi

ingress:
  enabled: true
  className: nginx
  host: example.local
  tls:
    enabled: false

cronjob:
  enabled: true
  schedule: "*/5 * * * *"
  image:
    repository: curlimages/curl
    tag: latest
    pullPolicy: IfNotPresent

networkPolicy:
  enabled: true
```

- [ ] Create `example-chart/values.yaml` with content above

### Step 3: Verify chart structure

```bash
cd example-chart
helm lint .
```

Expected output: `1 chart(s) linted, 0 chart(s) failed`

- [ ] Run `helm lint` to verify structure is valid

### Step 4: Commit

```bash
git add example-chart/Chart.yaml example-chart/values.yaml
git commit -m "feat: init example-chart with metadata and values"
```

- [ ] Commit Chart.yaml and values.yaml

---

## Task 2: Create Helpers and ServiceAccount Resources

**Files:**
- Create: `example-chart/templates/_helpers.tpl`
- Create: `example-chart/templates/serviceaccount.yaml`
- Create: `example-chart/templates/role.yaml`
- Create: `example-chart/templates/rolebinding.yaml`

### Step 1: Create _helpers.tpl with shared template functions

Create `example-chart/templates/_helpers.tpl`:

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "example-chart.name" -}}
{{- default .Chart.Name .Values.global.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "example-chart.fullname" -}}
{{- if .Values.global.fullnameOverride }}
{{- .Values.global.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.global.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "example-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.AppVersion | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "example-chart.labels" -}}
helm.sh/chart: {{ include "example-chart.chart" . }}
{{ include "example-chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "example-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "example-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "example-chart.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "example-chart.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
```

- [ ] Create `example-chart/templates/_helpers.tpl` with content above

### Step 2: Create ServiceAccount

Create `example-chart/templates/serviceaccount.yaml`:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "example-chart.fullname" . }}-sa
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
```

- [ ] Create `example-chart/templates/serviceaccount.yaml`

### Step 3: Create Role with pod-reader permissions

Create `example-chart/templates/role.yaml`:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ include "example-chart.fullname" . }}-pod-reader
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

- [ ] Create `example-chart/templates/role.yaml`

### Step 4: Create RoleBinding

Create `example-chart/templates/rolebinding.yaml`:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ include "example-chart.fullname" . }}-pod-reader-binding
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{ include "example-chart.fullname" . }}-pod-reader
subjects:
- kind: ServiceAccount
  name: {{ include "example-chart.fullname" . }}-sa
  namespace: {{ .Release.Namespace }}
```

- [ ] Create `example-chart/templates/rolebinding.yaml`

### Step 5: Run helm lint and commit

```bash
helm lint example-chart/
git add example-chart/templates/_helpers.tpl example-chart/templates/serviceaccount.yaml example-chart/templates/role.yaml example-chart/templates/rolebinding.yaml
git commit -m "feat: add RBAC resources and helpers"
```

- [ ] Run lint and commit RBAC resources

---

## Task 3: Create ConfigMap and Secret

**Files:**
- Create: `example-chart/templates/configmap.yaml`
- Create: `example-chart/templates/secret.yaml`

### Step 1: Create ConfigMap with nginx config and HTML

Create `example-chart/templates/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "example-chart.fullname" . }}-config
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
data:
  nginx.conf: |
    user nginx;
    worker_processes auto;
    error_log /var/log/nginx/error.log warn;
    pid /var/run/nginx.pid;

    events {
      worker_connections 1024;
    }

    http {
      include /etc/nginx/mime.types;
      default_type application/octet-stream;

      log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

      access_log /var/log/nginx/access.log main;
      sendfile on;
      tcp_nopush on;
      keepalive_timeout 65;
      gzip on;

      server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;

        location / {
          try_files $uri $uri/ =404;
        }

        location /health {
          access_log off;
          return 200 "healthy\n";
          add_header Content-Type text/plain;
        }
      }
    }

  index.html: |
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Gantry Example Chart</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 40px; max-width: 600px; width: 90%; }
        h1 { color: #333; margin-bottom: 20px; font-size: 2.5em; }
        .pod-info { background: #f5f5f5; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; border-radius: 4px; font-family: monospace; }
        .pod-info strong { display: block; color: #667eea; margin-bottom: 5px; }
        button { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 1em; cursor: pointer; transition: background 0.3s; }
        button:hover { background: #764ba2; }
        .response { background: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin-top: 20px; border-radius: 4px; white-space: pre-wrap; word-break: break-all; font-family: monospace; font-size: 0.9em; max-height: 300px; overflow-y: auto; }
        .error { background: #ffebee; border-left: 4px solid #f44336; }
        .loading { color: #999; font-style: italic; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>🚀 Gantry Example Chart</h1>
        <p>Welcome to the example Helm chart deployment. This chart demonstrates a 3-tier application with comprehensive Kubernetes resources for testing Gantry.</p>
        
        <div class="pod-info">
          <strong>Pod Information:</strong>
          <span id="pod-name">Loading...</span>
          <span id="pod-namespace">Loading...</span>
        </div>

        <button onclick="callBackend()">Call Backend API →</button>
        
        <div id="response"></div>
      </div>

      <script>
        // Get pod info from metadata
        fetch('/var/run/secrets/kubernetes.io/serviceaccount/namespace', { method: 'GET' })
          .catch(() => {
            document.getElementById('pod-name').textContent = 'Pod Name: (not available)';
            document.getElementById('pod-namespace').textContent = 'Namespace: (not available)';
          });
        
        document.getElementById('pod-name').textContent = 'Pod Name: ' + (process.env.HOSTNAME || 'unknown');
        document.getElementById('pod-namespace').textContent = 'Namespace: (see cluster info)';

        function callBackend() {
          const responseDiv = document.getElementById('response');
          responseDiv.className = 'response loading';
          responseDiv.textContent = 'Calling /api/health...';

          fetch('/api/health')
            .then(r => r.json())
            .then(data => {
              responseDiv.className = 'response';
              responseDiv.textContent = JSON.stringify(data, null, 2);
            })
            .catch(err => {
              responseDiv.className = 'response error';
              responseDiv.textContent = 'Error: ' + err.message;
            });
        }
      </script>
    </body>
    </html>
```

- [ ] Create `example-chart/templates/configmap.yaml`

### Step 2: Create Secret with redis password

Create `example-chart/templates/secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "example-chart.fullname" . }}-secret
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
type: Opaque
stringData:
  redis-password: {{ .Values.db.password | quote }}
```

- [ ] Create `example-chart/templates/secret.yaml`

### Step 3: Run lint and commit

```bash
helm lint example-chart/
git add example-chart/templates/configmap.yaml example-chart/templates/secret.yaml
git commit -m "feat: add ConfigMap and Secret resources"
```

- [ ] Lint and commit config resources

---

## Task 4: Create NetworkPolicy

**Files:**
- Create: `example-chart/templates/networkpolicy.yaml`

### Step 1: Create NetworkPolicy restricting traffic flow

Create `example-chart/templates/networkpolicy.yaml`:

```yaml
{{- if .Values.networkPolicy.enabled }}
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "example-chart.fullname" . }}-allow-traffic
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  
  # Default deny all
  ingress: []
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53

---
# Frontend: allow ingress from ingress controller, egress to backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "example-chart.fullname" . }}-frontend
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 80
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 8080
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53

---
# Backend: allow ingress from frontend, egress to db
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "example-chart.fullname" . }}-backend
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: db
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53

---
# DB: allow ingress from backend only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "example-chart.fullname" . }}-db
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
spec:
  podSelector:
    matchLabels:
      app: db
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 6379
  - from:
    - podSelector:
        matchLabels:
          app: job-db-seed
    ports:
    - protocol: TCP
      port: 6379
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
{{- end }}
```

- [ ] Create `example-chart/templates/networkpolicy.yaml`

### Step 2: Lint and commit

```bash
helm lint example-chart/
git add example-chart/templates/networkpolicy.yaml
git commit -m "feat: add NetworkPolicy resources"
```

- [ ] Lint and commit NetworkPolicy

---

## Task 5: Create Frontend Deployment

**Files:**
- Create: `example-chart/templates/frontend-deployment.yaml`

### Step 1: Create Frontend Deployment

Create `example-chart/templates/frontend-deployment.yaml`:

```yaml
{{- if .Values.frontend.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "example-chart.fullname" . }}-frontend
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: frontend
spec:
  {{- if not .Values.frontend.hpa.enabled }}
  replicas: {{ .Values.frontend.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "example-chart.selectorLabels" . | nindent 6 }}
      app: frontend
  template:
    metadata:
      labels:
        {{- include "example-chart.selectorLabels" . | nindent 8 }}
        app: frontend
      annotations:
        prometheus.io/scrape: "false"
    spec:
      serviceAccountName: {{ include "example-chart.serviceAccountName" . }}-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 101
        fsGroup: 101
      containers:
      - name: nginx
        image: "{{ .Values.frontend.image.repository }}:{{ .Values.frontend.image.tag }}"
        imagePullPolicy: {{ .Values.frontend.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.frontend.port }}
          protocol: TCP
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          {{- toYaml .Values.frontend.resources | nindent 12 }}
        volumeMounts:
        - name: config
          mountPath: /etc/nginx
          readOnly: true
        - name: html
          mountPath: /usr/share/nginx/html
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: {{ include "example-chart.fullname" . }}-config
          items:
          - key: nginx.conf
            path: nginx.conf
      - name: html
        configMap:
          name: {{ include "example-chart.fullname" . }}-config
          items:
          - key: index.html
            path: index.html
{{- end }}
```

- [ ] Create `example-chart/templates/frontend-deployment.yaml`

### Step 2: Lint and commit

```bash
helm lint example-chart/
git add example-chart/templates/frontend-deployment.yaml
git commit -m "feat: add frontend Deployment"
```

- [ ] Lint and commit frontend Deployment

---

## Task 6: Create Frontend Service and HPA

**Files:**
- Create: `example-chart/templates/frontend-service.yaml`
- Create: `example-chart/templates/frontend-hpa.yaml`

### Step 1: Create Frontend Service

Create `example-chart/templates/frontend-service.yaml`:

```yaml
{{- if .Values.frontend.enabled }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "example-chart.fullname" . }}-frontend-svc
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: frontend
spec:
  type: ClusterIP
  ports:
  - port: {{ .Values.frontend.port }}
    targetPort: http
    protocol: TCP
    name: http
  selector:
    {{- include "example-chart.selectorLabels" . | nindent 4 }}
    app: frontend
{{- end }}
```

- [ ] Create `example-chart/templates/frontend-service.yaml`

### Step 2: Create Frontend HPA

Create `example-chart/templates/frontend-hpa.yaml`:

```yaml
{{- if and .Values.frontend.enabled .Values.frontend.hpa.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "example-chart.fullname" . }}-frontend-hpa
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: frontend
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "example-chart.fullname" . }}-frontend
  minReplicas: {{ .Values.frontend.hpa.minReplicas }}
  maxReplicas: {{ .Values.frontend.hpa.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.frontend.hpa.targetCPUUtilizationPercentage }}
{{- end }}
```

- [ ] Create `example-chart/templates/frontend-hpa.yaml`

### Step 3: Lint and commit

```bash
helm lint example-chart/
git add example-chart/templates/frontend-service.yaml example-chart/templates/frontend-hpa.yaml
git commit -m "feat: add frontend Service and HPA"
```

- [ ] Lint and commit frontend service/HPA

---

## Task 7: Create Backend Deployment

**Files:**
- Create: `example-chart/templates/backend-deployment.yaml`

### Step 1: Create Backend Deployment

Create `example-chart/templates/backend-deployment.yaml`:

```yaml
{{- if .Values.backend.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "example-chart.fullname" . }}-backend
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: backend
spec:
  {{- if not .Values.backend.hpa.enabled }}
  replicas: {{ .Values.backend.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "example-chart.selectorLabels" . | nindent 6 }}
      app: backend
  template:
    metadata:
      labels:
        {{- include "example-chart.selectorLabels" . | nindent 8 }}
        app: backend
      annotations:
        prometheus.io/scrape: "false"
    spec:
      serviceAccountName: {{ include "example-chart.serviceAccountName" . }}-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: echo-server
        image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
        imagePullPolicy: {{ .Values.backend.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.backend.port }}
          protocol: TCP
        env:
        - name: PORT
          value: {{ .Values.backend.port | quote }}
        livenessProbe:
          httpGet:
            path: /
            port: http
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          {{- toYaml .Values.backend.resources | nindent 12 }}
{{- end }}
```

- [ ] Create `example-chart/templates/backend-deployment.yaml`

### Step 2: Lint and commit

```bash
helm lint example-chart/
git add example-chart/templates/backend-deployment.yaml
git commit -m "feat: add backend Deployment"
```

- [ ] Lint and commit backend Deployment

---

## Task 8: Create Backend Service and HPA

**Files:**
- Create: `example-chart/templates/backend-service.yaml`
- Create: `example-chart/templates/backend-hpa.yaml`

### Step 1: Create Backend Service

Create `example-chart/templates/backend-service.yaml`:

```yaml
{{- if .Values.backend.enabled }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "example-chart.fullname" . }}-backend-svc
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: backend
spec:
  type: ClusterIP
  ports:
  - port: {{ .Values.backend.port }}
    targetPort: http
    protocol: TCP
    name: http
  selector:
    {{- include "example-chart.selectorLabels" . | nindent 4 }}
    app: backend
{{- end }}
```

- [ ] Create `example-chart/templates/backend-service.yaml`

### Step 2: Create Backend HPA

Create `example-chart/templates/backend-hpa.yaml`:

```yaml
{{- if and .Values.backend.enabled .Values.backend.hpa.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "example-chart.fullname" . }}-backend-hpa
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: backend
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "example-chart.fullname" . }}-backend
  minReplicas: {{ .Values.backend.hpa.minReplicas }}
  maxReplicas: {{ .Values.backend.hpa.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.backend.hpa.targetCPUUtilizationPercentage }}
{{- end }}
```

- [ ] Create `example-chart/templates/backend-hpa.yaml`

### Step 3: Lint and commit

```bash
helm lint example-chart/
git add example-chart/templates/backend-service.yaml example-chart/templates/backend-hpa.yaml
git commit -m "feat: add backend Service and HPA"
```

- [ ] Lint and commit backend service/HPA

---

## Task 9: Create Database StatefulSet and Service

**Files:**
- Create: `example-chart/templates/db-statefulset.yaml`
- Create: `example-chart/templates/db-service.yaml`

### Step 1: Create Database Service (headless + regular)

Create `example-chart/templates/db-service.yaml`:

```yaml
{{- if .Values.db.enabled }}
# Headless service for StatefulSet
apiVersion: v1
kind: Service
metadata:
  name: {{ include "example-chart.fullname" . }}-db-headless
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: db
spec:
  clusterIP: None
  ports:
  - port: {{ .Values.db.port }}
    targetPort: redis
    protocol: TCP
    name: redis
  selector:
    {{- include "example-chart.selectorLabels" . | nindent 4 }}
    app: db

---
# Regular ClusterIP service for direct access
apiVersion: v1
kind: Service
metadata:
  name: {{ include "example-chart.fullname" . }}-db-svc
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: db
spec:
  type: ClusterIP
  ports:
  - port: {{ .Values.db.port }}
    targetPort: redis
    protocol: TCP
    name: redis
  selector:
    {{- include "example-chart.selectorLabels" . | nindent 4 }}
    app: db
{{- end }}
```

- [ ] Create `example-chart/templates/db-service.yaml`

### Step 2: Create Database StatefulSet

Create `example-chart/templates/db-statefulset.yaml`:

```yaml
{{- if .Values.db.enabled }}
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ include "example-chart.fullname" . }}-db
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: db
spec:
  serviceName: {{ include "example-chart.fullname" . }}-db-headless
  replicas: 1
  selector:
    matchLabels:
      {{- include "example-chart.selectorLabels" . | nindent 6 }}
      app: db
  template:
    metadata:
      labels:
        {{- include "example-chart.selectorLabels" . | nindent 8 }}
        app: db
      annotations:
        prometheus.io/scrape: "false"
    spec:
      serviceAccountName: {{ include "example-chart.serviceAccountName" . }}-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 999
        fsGroup: 999
      containers:
      - name: redis
        image: "{{ .Values.db.image.repository }}:{{ .Values.db.image.tag }}"
        imagePullPolicy: {{ .Values.db.image.pullPolicy }}
        ports:
        - name: redis
          containerPort: {{ .Values.db.port }}
          protocol: TCP
        command:
        - redis-server
        args:
        - "--requirepass"
        - "$(REDIS_PASSWORD)"
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {{ include "example-chart.fullname" . }}-secret
              key: redis-password
        livenessProbe:
          exec:
            command:
            - redis-cli
            - "-a"
            - "$(REDIS_PASSWORD)"
            - "PING"
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - "-a"
            - "$(REDIS_PASSWORD)"
            - "PING"
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          {{- toYaml .Values.db.resources | nindent 12 }}
        volumeMounts:
        - name: data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: {{ .Values.db.persistence.storageClassName }}
      resources:
        requests:
          storage: {{ .Values.db.persistence.size }}
{{- end }}
```

- [ ] Create `example-chart/templates/db-statefulset.yaml`

### Step 3: Lint and commit

```bash
helm lint example-chart/
git add example-chart/templates/db-service.yaml example-chart/templates/db-statefulset.yaml
git commit -m "feat: add database StatefulSet and Services"
```

- [ ] Lint and commit database resources

---

## Task 10: Create Job and CronJob

**Files:**
- Create: `example-chart/templates/job.yaml`
- Create: `example-chart/templates/cronjob.yaml`

### Step 1: Create Job for redis seeding

Create `example-chart/templates/job.yaml`:

```yaml
{{- if .Values.db.enabled }}
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "example-chart.fullname" . }}-db-seed
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: job-db-seed
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
spec:
  backoffLimit: 3
  template:
    metadata:
      labels:
        {{- include "example-chart.selectorLabels" . | nindent 8 }}
        app: job-db-seed
    spec:
      serviceAccountName: {{ include "example-chart.serviceAccountName" . }}-sa
      restartPolicy: Never
      containers:
      - name: redis-seed
        image: "{{ .Values.db.image.repository }}:{{ .Values.db.image.tag }}"
        command:
        - redis-cli
        - "-h"
        - {{ include "example-chart.fullname" . }}-db-svc
        - "-a"
        - "$(REDIS_PASSWORD)"
        - "SET"
        - "gantry:example"
        - '{"message": "Hello from Gantry Example Chart", "timestamp": "2026-05-06"}'
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {{ include "example-chart.fullname" . }}-secret
              key: redis-password
{{- end }}
```

- [ ] Create `example-chart/templates/job.yaml`

### Step 2: Create CronJob for health checks

Create `example-chart/templates/cronjob.yaml`:

```yaml
{{- if .Values.cronjob.enabled }}
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {{ include "example-chart.fullname" . }}-health-ping
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
    app: cronjob-health-ping
spec:
  schedule: {{ .Values.cronjob.schedule | quote }}
  jobTemplate:
    spec:
      backoffLimit: 1
      template:
        metadata:
          labels:
            {{- include "example-chart.selectorLabels" . | nindent 12 }}
            app: cronjob-health-ping
        spec:
          serviceAccountName: {{ include "example-chart.serviceAccountName" . }}-sa
          restartPolicy: Never
          containers:
          - name: curl
            image: "{{ .Values.cronjob.image.repository }}:{{ .Values.cronjob.image.tag }}"
            command:
            - curl
            - "-sf"
            - "http://{{ include "example-chart.fullname" . }}-frontend-svc:{{ .Values.frontend.port }}/health"
{{- end }}
```

- [ ] Create `example-chart/templates/cronjob.yaml`

### Step 3: Lint and commit

```bash
helm lint example-chart/
git add example-chart/templates/job.yaml example-chart/templates/cronjob.yaml
git commit -m "feat: add Job and CronJob resources"
```

- [ ] Lint and commit Job/CronJob

---

## Task 11: Create Ingress

**Files:**
- Create: `example-chart/templates/ingress.yaml`

### Step 1: Create Ingress with path-based routing

Create `example-chart/templates/ingress.yaml`:

```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "example-chart.fullname" . }}-ingress
  labels:
    {{- include "example-chart.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  ingressClassName: {{ .Values.ingress.className }}
  rules:
  - host: {{ .Values.ingress.host }}
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: {{ include "example-chart.fullname" . }}-backend-svc
            port:
              number: {{ .Values.backend.port }}
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {{ include "example-chart.fullname" . }}-frontend-svc
            port:
              number: {{ .Values.frontend.port }}
{{- end }}
```

- [ ] Create `example-chart/templates/ingress.yaml`

### Step 2: Lint and commit

```bash
helm lint example-chart/
git add example-chart/templates/ingress.yaml
git commit -m "feat: add Ingress with path-based routing"
```

- [ ] Lint and commit Ingress

---

## Task 12: Deploy and Verify

**Files:**
- (No new files, verification only)

### Step 1: Verify all resources are templated correctly

```bash
helm template example example-chart/ > /tmp/manifests.yaml
wc -l /tmp/manifests.yaml
```

Expected: 500+ lines of manifest YAML

- [ ] Run helm template and verify output

### Step 2: Add ingress-nginx annotation to values.yaml

Update `values.yaml` to include ingress annotations:

```yaml
ingress:
  enabled: true
  className: nginx
  host: example.local
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "*"
  tls:
    enabled: false
```

- [ ] Update ingress annotations in values.yaml

### Step 3: Verify minikube prerequisites

```bash
minikube addons enable ingress
echo "Waiting for ingress controller..."
kubectl wait --namespace ingress-nginx --for=condition=ready pod -l app.kubernetes.io/component=controller --timeout=120s
```

- [ ] Enable minikube ingress addon

### Step 4: Add /etc/hosts entry

```bash
echo "$(minikube ip) example.local" | sudo tee -a /etc/hosts
```

- [ ] Add example.local to /etc/hosts

### Step 5: Deploy chart to minikube

```bash
helm install example ./example-chart/
```

Expected output: Helm creates release named "example"

- [ ] Deploy chart with helm install

### Step 6: Verify all resources are created

```bash
kubectl get all,ingress,configmap,secret,hpa,pvc,networkpolicy,sa,role,rolebinding,job,cronjob -l app.kubernetes.io/instance=example
```

Expected: All 18+ resources showing as created/running

- [ ] Verify resources exist

### Step 7: Wait for pods to be ready

```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=example --timeout=120s
```

- [ ] Wait for pod readiness

### Step 8: Test frontend access

```bash
curl http://example.local
```

Expected: HTML with "Gantry Example Chart" title

- [ ] Curl frontend and verify response

### Step 9: Test backend API access

```bash
curl http://example.local/api/
```

Expected: JSON response from echo-server

- [ ] Curl backend API and verify response

### Step 10: Verify Job completed

```bash
kubectl get job example-db-seed
kubectl logs -l app.kubernetes.io/name=example-chart,app=job-db-seed
```

Expected: Job shows as "1/1" complete

- [ ] Verify Job execution

### Step 11: Verify redis data was seeded

```bash
kubectl exec -it example-db-0 -- redis-cli -a changeme123 GET gantry:example
```

Expected: JSON string: `{"message": "Hello from Gantry Example Chart", ...}`

- [ ] Verify redis contains seeded data

### Step 12: Launch gantry and verify all resource types

```bash
uv run python -m gantry
# Navigate through:
# - Deployments: frontend, backend
# - StatefulSet: db
# - Services: frontend-svc, backend-svc, db-svc
# - Ingress: main
# - ConfigMap: app-config
# - Secret: db-secret
# - HPA: frontend-hpa, backend-hpa
# - PVC: db-0 data volume
# - ServiceAccount: app-sa
# - Role: pod-reader
# - RoleBinding: pod-reader-binding
# - NetworkPolicy: allow-traffic (and others)
# - Job: db-seed
# - CronJob: health-ping
```

- [ ] Open gantry and verify all resources visible

### Step 13: Final commit and summary

```bash
git log --oneline -n 13
# Should show 12 commits for example-chart implementation + 1 for spec doc
```

- [ ] Verify commit history

### Step 14: Cleanup (optional)

```bash
helm uninstall example
```

- [ ] Uninstall release after testing

---

## Verification Checklist

✅ All 18 template files created
✅ Chart lints without errors
✅ All 14+ resource types visible in gantry UI
✅ Frontend serves HTML correctly
✅ Backend echoes requests as JSON
✅ Redis StatefulSet has persistent PVC
✅ Job completes and seeds redis
✅ CronJob runs on schedule
✅ Ingress routes traffic correctly
✅ NetworkPolicy restricts pod communication
✅ HPA shows scaling metrics
✅ RBAC ServiceAccount + Role + RoleBinding configured

---

## Next Steps

After implementation:
1. Push to feature branch and create PR
2. Ask for code review via `superpowers:requesting-code-review`
3. Document chart usage in README
4. Consider adding unit tests via `helm test`
