# K8s Resource Sidebar Expansion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the ClusterScreen sidebar from 4 resource types (Pods, Services, Deployments, ConfigMaps) to a complete flat list of 16 resource types matching the minikube dashboard.

**Architecture:** Add 12 new `list_*()` functions to `k8s.py` following the existing pattern (CoreV1Api/AppsV1Api/BatchV1Api/NetworkingV1Api + namespace-scoped vs cluster-scoped). Update `screens.py` to expand `_RESOURCE_TYPES`, sidebar items, fetch dispatch, and column definitions. No new abstractions — extend existing string-based dispatch.

**Tech Stack:** Python 3.11+, Textual TUI, kubernetes Python client, pytest + pytest-asyncio

---

## File Map

| File | Change |
|---|---|
| `src/gantry/k8s.py` | Add 12 list functions; extend `describe_resource()` |
| `src/gantry/screens.py` | Expand `_RESOURCE_TYPES`, `_TYPE_SINGULAR`, sidebar items, CSS width, fetch dispatch, column defs |
| `tests/test_k8s.py` | Add test classes for each new list function |
| `tests/test_app.py` | Update 3 tests that hardcode old sidebar order |

---

## Task 1: Add namespace-scoped list functions to k8s.py

**Files:**
- Modify: `src/gantry/k8s.py` (after `list_configmaps`)
- Test: `tests/test_k8s.py`

### 1a — ReplicaSets

- [ ] **Write failing test**

```python
# tests/test_k8s.py
class TestListReplicaSets:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.AppsV1Api")
    def test_list_replicasets_success(self, mock_api_class, mock_load):
        rs1 = MagicMock()
        rs1.metadata.name = "nginx-rs"
        rs1.metadata.namespace = "default"
        rs1.spec.replicas = 3
        rs1.status.ready_replicas = 3
        rs1.status.available_replicas = 3
        rs_list = MagicMock()
        rs_list.items = [rs1]
        mock_api = MagicMock()
        mock_api.list_namespaced_replica_set.return_value = rs_list
        mock_api_class.return_value = mock_api

        result = k8s.list_replicasets()

        assert len(result) == 1
        assert result[0]["name"] == "nginx-rs"
        assert result[0]["desired"] == 3
        assert result[0]["ready"] == 3
        assert result[0]["available"] == 3

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_replicasets_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_replicasets()
        assert result[0]["type"] == "missing_kubeconfig"

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.AppsV1Api")
    def test_list_replicasets_all_namespaces(self, mock_api_class, mock_load):
        rs_list = MagicMock()
        rs_list.items = []
        mock_api = MagicMock()
        mock_api.list_replica_set_for_all_namespaces.return_value = rs_list
        mock_api_class.return_value = mock_api
        result = k8s.list_replicasets(namespace="all")
        assert result == []
        mock_api.list_replica_set_for_all_namespaces.assert_called_once()
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListReplicaSets -v
```
Expected: `AttributeError: module 'gantry.k8s' has no attribute 'list_replicasets'`

- [ ] **Implement `list_replicasets` in `src/gantry/k8s.py`** (after `list_configmaps`, before `describe_resource`)

```python
def list_replicasets(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all ReplicaSets in a given namespace."""
    logger.debug(f"list_replicasets called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        apps_v1 = client.AppsV1Api()

        if namespace == "all":
            replicasets = apps_v1.list_replica_set_for_all_namespaces()
        else:
            replicasets = apps_v1.list_namespaced_replica_set(namespace=namespace)

        result = []
        for rs in replicasets.items:
            result.append({
                "name": rs.metadata.name,
                "namespace": rs.metadata.namespace,
                "desired": rs.spec.replicas or 0,
                "ready": rs.status.ready_replicas or 0,
                "available": rs.status.available_replicas or 0,
            })
        logger.debug(f"list_replicasets returned {len(result)} replicasets for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_replicasets")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_replicasets: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_replicasets: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_replicasets_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListReplicaSets -v
```

### 1b — StatefulSets

- [ ] **Write failing test**

```python
class TestListStatefulSets:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.AppsV1Api")
    def test_list_statefulsets_success(self, mock_api_class, mock_load):
        ss1 = MagicMock()
        ss1.metadata.name = "postgres-ss"
        ss1.metadata.namespace = "default"
        ss1.spec.replicas = 1
        ss1.status.ready_replicas = 1
        ss1.metadata.creation_timestamp = MagicMock()
        ss1.metadata.creation_timestamp.isoformat.return_value = "2024-01-01T00:00:00"
        ss_list = MagicMock()
        ss_list.items = [ss1]
        mock_api = MagicMock()
        mock_api.list_namespaced_stateful_set.return_value = ss_list
        mock_api_class.return_value = mock_api

        result = k8s.list_statefulsets()

        assert len(result) == 1
        assert result[0]["name"] == "postgres-ss"
        assert result[0]["ready"] == "1/1"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_statefulsets_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_statefulsets()
        assert result[0]["type"] == "missing_kubeconfig"
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListStatefulSets -v
```

- [ ] **Implement `list_statefulsets` in `src/gantry/k8s.py`**

```python
def list_statefulsets(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all StatefulSets in a given namespace."""
    logger.debug(f"list_statefulsets called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        apps_v1 = client.AppsV1Api()

        if namespace == "all":
            statefulsets = apps_v1.list_stateful_set_for_all_namespaces()
        else:
            statefulsets = apps_v1.list_namespaced_stateful_set(namespace=namespace)

        result = []
        for ss in statefulsets.items:
            result.append({
                "name": ss.metadata.name,
                "namespace": ss.metadata.namespace,
                "ready": f"{ss.status.ready_replicas or 0}/{ss.spec.replicas or 0}",
                "age": ss.metadata.creation_timestamp.isoformat() if ss.metadata.creation_timestamp else "",
            })
        logger.debug(f"list_statefulsets returned {len(result)} statefulsets for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_statefulsets")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_statefulsets: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_statefulsets: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_statefulsets_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListStatefulSets -v
```

### 1c — DaemonSets

- [ ] **Write failing test**

```python
class TestListDaemonSets:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.AppsV1Api")
    def test_list_daemonsets_success(self, mock_api_class, mock_load):
        ds1 = MagicMock()
        ds1.metadata.name = "fluentd-ds"
        ds1.metadata.namespace = "kube-system"
        ds1.status.desired_number_scheduled = 3
        ds1.status.number_ready = 3
        ds1.spec.template.spec.node_selector = None
        ds_list = MagicMock()
        ds_list.items = [ds1]
        mock_api = MagicMock()
        mock_api.list_namespaced_daemon_set.return_value = ds_list
        mock_api_class.return_value = mock_api

        result = k8s.list_daemonsets()

        assert len(result) == 1
        assert result[0]["name"] == "fluentd-ds"
        assert result[0]["desired"] == 3
        assert result[0]["ready"] == 3

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_daemonsets_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_daemonsets()
        assert result[0]["type"] == "missing_kubeconfig"
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListDaemonSets -v
```

- [ ] **Implement `list_daemonsets` in `src/gantry/k8s.py`**

```python
def list_daemonsets(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all DaemonSets in a given namespace."""
    logger.debug(f"list_daemonsets called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        apps_v1 = client.AppsV1Api()

        if namespace == "all":
            daemonsets = apps_v1.list_daemon_set_for_all_namespaces()
        else:
            daemonsets = apps_v1.list_namespaced_daemon_set(namespace=namespace)

        result = []
        for ds in daemonsets.items:
            result.append({
                "name": ds.metadata.name,
                "namespace": ds.metadata.namespace,
                "desired": ds.status.desired_number_scheduled or 0,
                "ready": ds.status.number_ready or 0,
                "node_selector": str(ds.spec.template.spec.node_selector or {}),
            })
        logger.debug(f"list_daemonsets returned {len(result)} daemonsets for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_daemonsets")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_daemonsets: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_daemonsets: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_daemonsets_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListDaemonSets -v
```

### 1d — Jobs

- [ ] **Write failing test**

```python
class TestListJobs:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.BatchV1Api")
    def test_list_jobs_success_complete(self, mock_api_class, mock_load):
        job1 = MagicMock()
        job1.metadata.name = "backup-job"
        job1.metadata.namespace = "default"
        job1.spec.completions = 1
        job1.status.succeeded = 1
        job1.status.active = 0
        job1.status.failed = 0
        job1.status.completion_time = None
        job1.status.start_time = None
        job_list = MagicMock()
        job_list.items = [job1]
        mock_api = MagicMock()
        mock_api.list_namespaced_job.return_value = job_list
        mock_api_class.return_value = mock_api

        result = k8s.list_jobs()

        assert result[0]["name"] == "backup-job"
        assert result[0]["status"] == "Complete"
        assert result[0]["completions"] == "1/1"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_jobs_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_jobs()
        assert result[0]["type"] == "missing_kubeconfig"

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.BatchV1Api")
    def test_list_jobs_all_namespaces(self, mock_api_class, mock_load):
        job_list = MagicMock()
        job_list.items = []
        mock_api = MagicMock()
        mock_api.list_job_for_all_namespaces.return_value = job_list
        mock_api_class.return_value = mock_api
        result = k8s.list_jobs(namespace="all")
        assert result == []
        mock_api.list_job_for_all_namespaces.assert_called_once()
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListJobs -v
```

- [ ] **Implement `list_jobs` in `src/gantry/k8s.py`**

```python
def list_jobs(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all Jobs in a given namespace."""
    logger.debug(f"list_jobs called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        batch_v1 = client.BatchV1Api()

        if namespace == "all":
            jobs = batch_v1.list_job_for_all_namespaces()
        else:
            jobs = batch_v1.list_namespaced_job(namespace=namespace)

        result = []
        for job in jobs.items:
            completions = job.spec.completions or 1
            succeeded = job.status.succeeded or 0
            active = job.status.active or 0
            failed = job.status.failed or 0
            if succeeded >= completions:
                job_status = "Complete"
            elif active > 0:
                job_status = "Running"
            elif failed > 0:
                job_status = "Failed"
            else:
                job_status = "Pending"
            result.append({
                "name": job.metadata.name,
                "namespace": job.metadata.namespace,
                "completions": f"{succeeded}/{completions}",
                "duration": str(job.status.completion_time - job.status.start_time) if (job.status.completion_time and job.status.start_time) else "N/A",
                "status": job_status,
            })
        logger.debug(f"list_jobs returned {len(result)} jobs for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_jobs")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_jobs: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_jobs: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_jobs_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListJobs -v
```

### 1e — CronJobs

- [ ] **Write failing test**

```python
class TestListCronJobs:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.BatchV1Api")
    def test_list_cronjobs_success(self, mock_api_class, mock_load):
        cj1 = MagicMock()
        cj1.metadata.name = "daily-backup"
        cj1.metadata.namespace = "default"
        cj1.spec.schedule = "0 2 * * *"
        cj1.status.last_schedule_time = None
        cj1.status.active = []
        cj_list = MagicMock()
        cj_list.items = [cj1]
        mock_api = MagicMock()
        mock_api.list_namespaced_cron_job.return_value = cj_list
        mock_api_class.return_value = mock_api

        result = k8s.list_cronjobs()

        assert result[0]["name"] == "daily-backup"
        assert result[0]["schedule"] == "0 2 * * *"
        assert result[0]["last_run"] == "Never"
        assert result[0]["active"] == 0

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_cronjobs_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_cronjobs()
        assert result[0]["type"] == "missing_kubeconfig"
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListCronJobs -v
```

- [ ] **Implement `list_cronjobs` in `src/gantry/k8s.py`**

```python
def list_cronjobs(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all CronJobs in a given namespace."""
    logger.debug(f"list_cronjobs called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        batch_v1 = client.BatchV1Api()

        if namespace == "all":
            cronjobs = batch_v1.list_cron_job_for_all_namespaces()
        else:
            cronjobs = batch_v1.list_namespaced_cron_job(namespace=namespace)

        result = []
        for cj in cronjobs.items:
            result.append({
                "name": cj.metadata.name,
                "namespace": cj.metadata.namespace,
                "schedule": cj.spec.schedule,
                "last_run": cj.status.last_schedule_time.isoformat() if cj.status.last_schedule_time else "Never",
                "active": len(cj.status.active or []),
            })
        logger.debug(f"list_cronjobs returned {len(result)} cronjobs for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_cronjobs")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_cronjobs: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_cronjobs: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_cronjobs_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListCronJobs -v
```

### 1f — Ingresses

- [ ] **Write failing test**

```python
class TestListIngresses:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.NetworkingV1Api")
    def test_list_ingresses_success(self, mock_api_class, mock_load):
        ing1 = MagicMock()
        ing1.metadata.name = "app-ingress"
        ing1.metadata.namespace = "default"
        ing1.metadata.annotations = {}
        ing1.spec.ingress_class_name = "nginx"
        rule = MagicMock()
        rule.host = "app.example.com"
        ing1.spec.rules = [rule]
        ing1.status.load_balancer.ingress = []
        ing_list = MagicMock()
        ing_list.items = [ing1]
        mock_api = MagicMock()
        mock_api.list_namespaced_ingress.return_value = ing_list
        mock_api_class.return_value = mock_api

        result = k8s.list_ingresses()

        assert result[0]["name"] == "app-ingress"
        assert result[0]["class"] == "nginx"
        assert result[0]["hosts"] == "app.example.com"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_ingresses_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_ingresses()
        assert result[0]["type"] == "missing_kubeconfig"
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListIngresses -v
```

- [ ] **Implement `list_ingresses` in `src/gantry/k8s.py`**

```python
def list_ingresses(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all Ingresses in a given namespace."""
    logger.debug(f"list_ingresses called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        networking_v1 = client.NetworkingV1Api()

        if namespace == "all":
            ingresses = networking_v1.list_ingress_for_all_namespaces()
        else:
            ingresses = networking_v1.list_namespaced_ingress(namespace=namespace)

        result = []
        for ing in ingresses.items:
            hosts = ",".join(rule.host for rule in (ing.spec.rules or []) if rule.host)
            annotations = ing.metadata.annotations or {}
            ingress_class = ing.spec.ingress_class_name or annotations.get("kubernetes.io/ingress.class", "")
            lb_ingress = ing.status.load_balancer.ingress if ing.status and ing.status.load_balancer else []
            address = ",".join(lb.ip or lb.hostname or "" for lb in (lb_ingress or []))
            result.append({
                "name": ing.metadata.name,
                "namespace": ing.metadata.namespace,
                "class": ingress_class,
                "hosts": hosts,
                "address": address,
            })
        logger.debug(f"list_ingresses returned {len(result)} ingresses for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_ingresses")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_ingresses: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_ingresses: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_ingresses_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListIngresses -v
```

### 1g — Endpoints

- [ ] **Write failing test**

```python
class TestListEndpoints:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_endpoints_success(self, mock_api_class, mock_load):
        ep1 = MagicMock()
        ep1.metadata.name = "nginx-svc"
        ep1.metadata.namespace = "default"
        ep1.subsets = [MagicMock(), MagicMock()]
        ep_list = MagicMock()
        ep_list.items = [ep1]
        mock_api = MagicMock()
        mock_api.list_namespaced_endpoints.return_value = ep_list
        mock_api_class.return_value = mock_api

        result = k8s.list_endpoints()

        assert result[0]["name"] == "nginx-svc"
        assert result[0]["endpoints"] == "2"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_endpoints_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_endpoints()
        assert result[0]["type"] == "missing_kubeconfig"
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListEndpoints -v
```

- [ ] **Implement `list_endpoints` in `src/gantry/k8s.py`**

```python
def list_endpoints(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all Endpoints in a given namespace."""
    logger.debug(f"list_endpoints called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()

        if namespace == "all":
            endpoints = v1.list_endpoints_for_all_namespaces()
        else:
            endpoints = v1.list_namespaced_endpoints(namespace=namespace)

        result = []
        for ep in endpoints.items:
            result.append({
                "name": ep.metadata.name,
                "namespace": ep.metadata.namespace,
                "endpoints": str(len(ep.subsets or [])),
            })
        logger.debug(f"list_endpoints returned {len(result)} endpoints for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_endpoints")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_endpoints: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_endpoints: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_endpoints_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListEndpoints -v
```

### 1h — Secrets

- [ ] **Write failing test**

```python
class TestListSecrets:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_secrets_success(self, mock_api_class, mock_load):
        s1 = MagicMock()
        s1.metadata.name = "db-secret"
        s1.metadata.namespace = "default"
        s1.type = "Opaque"
        s1.data = {"username": "dXNlcg==", "password": "cGFzcw=="}
        s_list = MagicMock()
        s_list.items = [s1]
        mock_api = MagicMock()
        mock_api.list_namespaced_secret.return_value = s_list
        mock_api_class.return_value = mock_api

        result = k8s.list_secrets()

        assert result[0]["name"] == "db-secret"
        assert result[0]["type"] == "Opaque"
        assert result[0]["keys"] == 2

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_secrets_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_secrets()
        assert result[0]["type"] == "missing_kubeconfig"
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListSecrets -v
```

- [ ] **Implement `list_secrets` in `src/gantry/k8s.py`**

```python
def list_secrets(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all Secrets in a given namespace."""
    logger.debug(f"list_secrets called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()

        if namespace == "all":
            secrets = v1.list_secret_for_all_namespaces()
        else:
            secrets = v1.list_namespaced_secret(namespace=namespace)

        result = []
        for secret in secrets.items:
            result.append({
                "name": secret.metadata.name,
                "namespace": secret.metadata.namespace,
                "type": secret.type or "",
                "keys": len(secret.data or {}),
            })
        logger.debug(f"list_secrets returned {len(result)} secrets for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_secrets")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_secrets: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_secrets: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_secrets_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListSecrets -v
```

### 1i — PersistentVolumeClaims

- [ ] **Write failing test**

```python
class TestListPersistentVolumeClaims:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_pvcs_success(self, mock_api_class, mock_load):
        pvc1 = MagicMock()
        pvc1.metadata.name = "data-pvc"
        pvc1.metadata.namespace = "default"
        pvc1.status.phase = "Bound"
        pvc1.spec.volume_name = "pv-001"
        pvc1.status.capacity = {"storage": "10Gi"}
        pvc_list = MagicMock()
        pvc_list.items = [pvc1]
        mock_api = MagicMock()
        mock_api.list_namespaced_persistent_volume_claim.return_value = pvc_list
        mock_api_class.return_value = mock_api

        result = k8s.list_persistentvolumeclaims()

        assert result[0]["name"] == "data-pvc"
        assert result[0]["status"] == "Bound"
        assert result[0]["volume"] == "pv-001"
        assert result[0]["capacity"] == "10Gi"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_pvcs_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_persistentvolumeclaims()
        assert result[0]["type"] == "missing_kubeconfig"
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListPersistentVolumeClaims -v
```

- [ ] **Implement `list_persistentvolumeclaims` in `src/gantry/k8s.py`**

```python
def list_persistentvolumeclaims(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all PersistentVolumeClaims in a given namespace."""
    logger.debug(f"list_persistentvolumeclaims called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()

        if namespace == "all":
            pvcs = v1.list_persistent_volume_claim_for_all_namespaces()
        else:
            pvcs = v1.list_namespaced_persistent_volume_claim(namespace=namespace)

        result = []
        for pvc in pvcs.items:
            capacity = ""
            if pvc.status.capacity:
                capacity = pvc.status.capacity.get("storage", "")
            result.append({
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": pvc.status.phase or "",
                "volume": pvc.spec.volume_name or "",
                "capacity": capacity,
            })
        logger.debug(f"list_persistentvolumeclaims returned {len(result)} pvcs for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_persistentvolumeclaims")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_persistentvolumeclaims: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_persistentvolumeclaims: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_persistentvolumeclaims_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListPersistentVolumeClaims -v
```

- [ ] **Commit namespace-scoped list functions**

```bash
git add src/gantry/k8s.py tests/test_k8s.py
git commit -m "feat: add list functions for ReplicaSets, StatefulSets, DaemonSets, Jobs, CronJobs, Ingresses, Endpoints, Secrets, PVCs"
```

---

## Task 2: Add cluster-scoped list functions to k8s.py

**Files:**
- Modify: `src/gantry/k8s.py`
- Test: `tests/test_k8s.py`

> **Note:** `list_namespaces(context_name)` already exists (line 86) and returns `List[str]` for the context picker modal. The new function is named `list_namespace_resources` to avoid collision and returns `List[Dict]`.

### 2a — PersistentVolumes (cluster-scoped)

- [ ] **Write failing test**

```python
class TestListPersistentVolumes:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_pvs_success(self, mock_api_class, mock_load):
        pv1 = MagicMock()
        pv1.metadata.name = "pv-001"
        pv1.spec.capacity = {"storage": "10Gi"}
        pv1.spec.access_modes = ["ReadWriteOnce"]
        pv1.status.phase = "Available"
        pv_list = MagicMock()
        pv_list.items = [pv1]
        mock_api = MagicMock()
        mock_api.list_persistent_volume.return_value = pv_list
        mock_api_class.return_value = mock_api

        result = k8s.list_persistentvolumes()

        assert result[0]["name"] == "pv-001"
        assert result[0]["capacity"] == "10Gi"
        assert result[0]["access_modes"] == "ReadWriteOnce"
        assert result[0]["status"] == "Available"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_pvs_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_persistentvolumes()
        assert result[0]["type"] == "missing_kubeconfig"
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListPersistentVolumes -v
```

- [ ] **Implement `list_persistentvolumes` in `src/gantry/k8s.py`**

```python
def list_persistentvolumes(context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all PersistentVolumes (cluster-scoped)."""
    logger.debug("list_persistentvolumes called")
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()
        pvs = v1.list_persistent_volume()

        result = []
        for pv in pvs.items:
            capacity = ""
            if pv.spec.capacity:
                capacity = pv.spec.capacity.get("storage", "")
            result.append({
                "name": pv.metadata.name,
                "namespace": "",
                "capacity": capacity,
                "access_modes": ",".join(pv.spec.access_modes or []),
                "status": pv.status.phase or "",
            })
        logger.debug(f"list_persistentvolumes returned {len(result)} pvs")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_persistentvolumes")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_persistentvolumes: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_persistentvolumes: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_persistentvolumes_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListPersistentVolumes -v
```

### 2b — Namespace resources (cluster-scoped)

- [ ] **Write failing test**

```python
class TestListNamespaceResources:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_namespace_resources_success(self, mock_api_class, mock_load):
        ns1 = MagicMock()
        ns1.metadata.name = "default"
        ns1.status.phase = "Active"
        ns1.metadata.creation_timestamp = MagicMock()
        ns1.metadata.creation_timestamp.isoformat.return_value = "2024-01-01T00:00:00"
        ns_list = MagicMock()
        ns_list.items = [ns1]
        mock_api = MagicMock()
        mock_api.list_namespace.return_value = ns_list
        mock_api_class.return_value = mock_api

        result = k8s.list_namespace_resources()

        assert result[0]["name"] == "default"
        assert result[0]["status"] == "Active"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_namespace_resources_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_namespace_resources()
        assert result[0]["type"] == "missing_kubeconfig"
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListNamespaceResources -v
```

- [ ] **Implement `list_namespace_resources` in `src/gantry/k8s.py`**

```python
def list_namespace_resources(context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all Namespaces as resource dicts (cluster-scoped)."""
    logger.debug("list_namespace_resources called")
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace()

        result = []
        for ns in namespaces.items:
            result.append({
                "name": ns.metadata.name,
                "namespace": "",
                "status": ns.status.phase or "",
                "age": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else "",
            })
        logger.debug(f"list_namespace_resources returned {len(result)} namespaces")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_namespace_resources")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_namespace_resources: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_namespace_resources: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_namespace_resources_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListNamespaceResources -v
```

### 2c — Nodes (cluster-scoped)

- [ ] **Write failing test**

```python
class TestListNodes:
    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_nodes_success(self, mock_api_class, mock_load):
        node1 = MagicMock()
        node1.metadata.name = "minikube"
        node1.metadata.labels = {"node-role.kubernetes.io/control-plane": ""}
        cond = MagicMock()
        cond.type = "Ready"
        cond.status = "True"
        node1.status.conditions = [cond]
        node1.status.node_info.kubelet_version = "v1.28.0"
        node_list = MagicMock()
        node_list.items = [node1]
        mock_api = MagicMock()
        mock_api.list_node.return_value = node_list
        mock_api_class.return_value = mock_api

        result = k8s.list_nodes()

        assert result[0]["name"] == "minikube"
        assert result[0]["status"] == "Ready"
        assert "control-plane" in result[0]["roles"]
        assert result[0]["version"] == "v1.28.0"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_nodes_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_nodes()
        assert result[0]["type"] == "missing_kubeconfig"
```

- [ ] **Run to confirm FAIL**

```bash
uv run pytest tests/test_k8s.py::TestListNodes -v
```

- [ ] **Implement `list_nodes` in `src/gantry/k8s.py`**

```python
def list_nodes(context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all Nodes (cluster-scoped)."""
    logger.debug("list_nodes called")
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()
        nodes = v1.list_node()

        result = []
        for node in nodes.items:
            node_status = next(
                (c.type for c in (node.status.conditions or []) if c.status == "True"),
                "Unknown",
            )
            labels = node.metadata.labels or {}
            roles = ",".join(
                k.replace("node-role.kubernetes.io/", "")
                for k in labels
                if k.startswith("node-role.kubernetes.io/")
            )
            version = node.status.node_info.kubelet_version if node.status and node.status.node_info else ""
            result.append({
                "name": node.metadata.name,
                "namespace": "",
                "status": node_status,
                "roles": roles or "none",
                "version": version,
            })
        logger.debug(f"list_nodes returned {len(result)} nodes")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_nodes")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_nodes: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_nodes: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_nodes_error"}]
```

- [ ] **Run to confirm PASS**

```bash
uv run pytest tests/test_k8s.py::TestListNodes -v
```

- [ ] **Commit cluster-scoped list functions**

```bash
git add src/gantry/k8s.py tests/test_k8s.py
git commit -m "feat: add list functions for PersistentVolumes, Namespaces, Nodes (cluster-scoped)"
```

---

## Task 3: Extend describe_resource() for all new types

**Files:**
- Modify: `src/gantry/k8s.py` — `describe_resource()` function

Add `elif` branches inside `describe_resource()` after the `configmap` branch. Cluster-scoped types (persistentvolume, namespace, node) call non-namespaced API methods.

- [ ] **Add elif branches in `describe_resource()`**

Inside `describe_resource()`, after the `configmap` elif block and before the `else` block, add:

```python
elif resource_type_lower == "replicaset":
    rs = apps_v1.read_namespaced_replica_set(name=resource_name, namespace=namespace)
    return {
        "name": rs.metadata.name,
        "namespace": rs.metadata.namespace,
        "desired": rs.spec.replicas or 0,
        "ready": rs.status.ready_replicas or 0,
        "available": rs.status.available_replicas or 0,
    }

elif resource_type_lower == "statefulset":
    ss = apps_v1.read_namespaced_stateful_set(name=resource_name, namespace=namespace)
    return {
        "name": ss.metadata.name,
        "namespace": ss.metadata.namespace,
        "replicas": ss.spec.replicas or 0,
        "ready": ss.status.ready_replicas or 0,
    }

elif resource_type_lower == "daemonset":
    ds = apps_v1.read_namespaced_daemon_set(name=resource_name, namespace=namespace)
    return {
        "name": ds.metadata.name,
        "namespace": ds.metadata.namespace,
        "desired": ds.status.desired_number_scheduled or 0,
        "ready": ds.status.number_ready or 0,
    }

elif resource_type_lower == "job":
    batch_v1 = client.BatchV1Api()
    job = batch_v1.read_namespaced_job(name=resource_name, namespace=namespace)
    return {
        "name": job.metadata.name,
        "namespace": job.metadata.namespace,
        "completions": job.spec.completions or 1,
        "succeeded": job.status.succeeded or 0,
        "active": job.status.active or 0,
        "failed": job.status.failed or 0,
    }

elif resource_type_lower == "cronjob":
    batch_v1 = client.BatchV1Api()
    cj = batch_v1.read_namespaced_cron_job(name=resource_name, namespace=namespace)
    return {
        "name": cj.metadata.name,
        "namespace": cj.metadata.namespace,
        "schedule": cj.spec.schedule,
        "active": len(cj.status.active or []),
        "last_run": cj.status.last_schedule_time.isoformat() if cj.status.last_schedule_time else "Never",
    }

elif resource_type_lower == "ingress":
    networking_v1 = client.NetworkingV1Api()
    ing = networking_v1.read_namespaced_ingress(name=resource_name, namespace=namespace)
    hosts = [rule.host for rule in (ing.spec.rules or []) if rule.host]
    return {
        "name": ing.metadata.name,
        "namespace": ing.metadata.namespace,
        "class": ing.spec.ingress_class_name or "",
        "hosts": hosts,
    }

elif resource_type_lower == "endpoints":
    ep = v1.read_namespaced_endpoints(name=resource_name, namespace=namespace)
    return {
        "name": ep.metadata.name,
        "namespace": ep.metadata.namespace,
        "subsets": len(ep.subsets or []),
    }

elif resource_type_lower == "secret":
    secret = v1.read_namespaced_secret(name=resource_name, namespace=namespace)
    return {
        "name": secret.metadata.name,
        "namespace": secret.metadata.namespace,
        "type": secret.type or "",
        "keys": list((secret.data or {}).keys()),
    }

elif resource_type_lower == "persistentvolumeclaim":
    pvc = v1.read_namespaced_persistent_volume_claim(name=resource_name, namespace=namespace)
    capacity = ""
    if pvc.status.capacity:
        capacity = pvc.status.capacity.get("storage", "")
    return {
        "name": pvc.metadata.name,
        "namespace": pvc.metadata.namespace,
        "status": pvc.status.phase or "",
        "volume": pvc.spec.volume_name or "",
        "capacity": capacity,
    }

elif resource_type_lower == "persistentvolume":
    pv = v1.read_persistent_volume(name=resource_name)
    capacity = ""
    if pv.spec.capacity:
        capacity = pv.spec.capacity.get("storage", "")
    return {
        "name": pv.metadata.name,
        "namespace": "",
        "capacity": capacity,
        "access_modes": pv.spec.access_modes or [],
        "status": pv.status.phase or "",
    }

elif resource_type_lower == "namespace":
    ns = v1.read_namespace(name=resource_name)
    return {
        "name": ns.metadata.name,
        "namespace": "",
        "status": ns.status.phase or "",
    }

elif resource_type_lower == "node":
    node = v1.read_node(name=resource_name)
    labels = node.metadata.labels or {}
    roles = ",".join(
        k.replace("node-role.kubernetes.io/", "")
        for k in labels
        if k.startswith("node-role.kubernetes.io/")
    )
    version = node.status.node_info.kubelet_version if node.status and node.status.node_info else ""
    return {
        "name": node.metadata.name,
        "namespace": "",
        "roles": roles or "none",
        "version": version,
    }
```

- [ ] **Run tests to confirm nothing broke**

```bash
uv run pytest tests/test_k8s.py::TestDescribeResource -v
```

- [ ] **Commit**

```bash
git add src/gantry/k8s.py
git commit -m "feat: extend describe_resource() for all 16 resource types"
```

---

## Task 4: Update screens.py — resource types, sidebar, dispatch, columns

**Files:**
- Modify: `src/gantry/screens.py`
- Test: `tests/test_app.py`

### 4a — Expand `_RESOURCE_TYPES` and add `_TYPE_SINGULAR`

- [ ] **Replace `_RESOURCE_TYPES` at line ~288 of `src/gantry/screens.py`**

```python
_RESOURCE_TYPES = [
    "Pods", "Deployments", "ReplicaSets", "StatefulSets", "DaemonSets",
    "Jobs", "CronJobs", "Services", "Ingresses", "Endpoints",
    "ConfigMaps", "Secrets", "PersistentVolumeClaims", "PersistentVolumes",
    "Namespaces", "Nodes",
]

_TYPE_SINGULAR = {
    "Pods": "pod",
    "Deployments": "deployment",
    "ReplicaSets": "replicaset",
    "StatefulSets": "statefulset",
    "DaemonSets": "daemonset",
    "Jobs": "job",
    "CronJobs": "cronjob",
    "Services": "service",
    "Ingresses": "ingress",
    "Endpoints": "endpoints",
    "ConfigMaps": "configmap",
    "Secrets": "secret",
    "PersistentVolumeClaims": "persistentvolumeclaim",
    "PersistentVolumes": "persistentvolume",
    "Namespaces": "namespace",
    "Nodes": "node",
}
```

### 4b — Expand `_all_resources` in `__init__`

- [ ] **Replace hardcoded dict in `__init__` (~line 303)**

```python
self._all_resources: Dict[str, List[Dict[str, Any]]] = {
    t: [] for t in self._RESOURCE_TYPES
}
```

### 4c — Widen sidebar CSS and add 12 ListItems

- [ ] **Update CSS: change `width: 20` → `width: 24` for `#resource-type-sidebar`**

- [ ] **Replace ListView in `compose()` (~line 315)**

```python
yield ListView(
    ListItem(Label("Pods")),
    ListItem(Label("Deployments")),
    ListItem(Label("ReplicaSets")),
    ListItem(Label("StatefulSets")),
    ListItem(Label("DaemonSets")),
    ListItem(Label("Jobs")),
    ListItem(Label("CronJobs")),
    ListItem(Label("Services")),
    ListItem(Label("Ingresses")),
    ListItem(Label("Endpoints")),
    ListItem(Label("ConfigMaps")),
    ListItem(Label("Secrets")),
    ListItem(Label("PersistentVolumeClaims")),
    ListItem(Label("PersistentVolumes")),
    ListItem(Label("Namespaces")),
    ListItem(Label("Nodes")),
    id="resource-type-sidebar",
    initial_index=0,
)
```

### 4d — Update fetch dispatch in `_fetch_resources_worker()`

- [ ] **Replace the `if/elif` block (~lines 425-432)**

```python
if resource_type == "Pods":
    resources = k8s.list_pods(namespace, context=context)
elif resource_type == "Deployments":
    resources = k8s.list_deployments(namespace, context=context)
elif resource_type == "ReplicaSets":
    resources = k8s.list_replicasets(namespace, context=context)
elif resource_type == "StatefulSets":
    resources = k8s.list_statefulsets(namespace, context=context)
elif resource_type == "DaemonSets":
    resources = k8s.list_daemonsets(namespace, context=context)
elif resource_type == "Jobs":
    resources = k8s.list_jobs(namespace, context=context)
elif resource_type == "CronJobs":
    resources = k8s.list_cronjobs(namespace, context=context)
elif resource_type == "Services":
    resources = k8s.list_services(namespace, context=context)
elif resource_type == "Ingresses":
    resources = k8s.list_ingresses(namespace, context=context)
elif resource_type == "Endpoints":
    resources = k8s.list_endpoints(namespace, context=context)
elif resource_type == "ConfigMaps":
    resources = k8s.list_configmaps(namespace, context=context)
elif resource_type == "Secrets":
    resources = k8s.list_secrets(namespace, context=context)
elif resource_type == "PersistentVolumeClaims":
    resources = k8s.list_persistentvolumeclaims(namespace, context=context)
elif resource_type == "PersistentVolumes":
    resources = k8s.list_persistentvolumes(context=context)
elif resource_type == "Namespaces":
    resources = k8s.list_namespace_resources(context=context)
elif resource_type == "Nodes":
    resources = k8s.list_nodes(context=context)
```

### 4e — Update column definitions in `_display_resources()`

- [ ] **Replace the column definition block (~lines 467-495)**

```python
if resource_type == "Pods":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Status", "Ready", "Restarts"]
        keys = ["name", "namespace", "status", "ready", "restarts"]
    else:
        columns = ["Name", "Status", "Ready", "Restarts"]
        keys = ["name", "status", "ready", "restarts"]
elif resource_type == "Deployments":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Replicas", "Ready", "Available"]
        keys = ["name", "namespace", "replicas", "ready_replicas", "available_replicas"]
    else:
        columns = ["Name", "Replicas", "Ready", "Available"]
        keys = ["name", "replicas", "ready_replicas", "available_replicas"]
elif resource_type == "ReplicaSets":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Desired", "Ready", "Available"]
        keys = ["name", "namespace", "desired", "ready", "available"]
    else:
        columns = ["Name", "Desired", "Ready", "Available"]
        keys = ["name", "desired", "ready", "available"]
elif resource_type == "StatefulSets":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Ready", "Age"]
        keys = ["name", "namespace", "ready", "age"]
    else:
        columns = ["Name", "Ready", "Age"]
        keys = ["name", "ready", "age"]
elif resource_type == "DaemonSets":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Desired", "Ready", "Node Selector"]
        keys = ["name", "namespace", "desired", "ready", "node_selector"]
    else:
        columns = ["Name", "Desired", "Ready", "Node Selector"]
        keys = ["name", "desired", "ready", "node_selector"]
elif resource_type == "Jobs":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Completions", "Duration", "Status"]
        keys = ["name", "namespace", "completions", "duration", "status"]
    else:
        columns = ["Name", "Completions", "Duration", "Status"]
        keys = ["name", "completions", "duration", "status"]
elif resource_type == "CronJobs":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Schedule", "Last Run", "Active"]
        keys = ["name", "namespace", "schedule", "last_run", "active"]
    else:
        columns = ["Name", "Schedule", "Last Run", "Active"]
        keys = ["name", "schedule", "last_run", "active"]
elif resource_type == "Services":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Type", "Cluster IP"]
        keys = ["name", "namespace", "type", "cluster_ip"]
    else:
        columns = ["Name", "Type", "Cluster IP"]
        keys = ["name", "type", "cluster_ip"]
elif resource_type == "Ingresses":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Class", "Hosts", "Address"]
        keys = ["name", "namespace", "class", "hosts", "address"]
    else:
        columns = ["Name", "Class", "Hosts", "Address"]
        keys = ["name", "class", "hosts", "address"]
elif resource_type == "Endpoints":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Endpoints"]
        keys = ["name", "namespace", "endpoints"]
    else:
        columns = ["Name", "Endpoints"]
        keys = ["name", "endpoints"]
elif resource_type == "ConfigMaps":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Keys"]
        keys = ["name", "namespace", "key_count"]
    else:
        columns = ["Name", "Keys"]
        keys = ["name", "key_count"]
elif resource_type == "Secrets":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Type", "Keys"]
        keys = ["name", "namespace", "type", "keys"]
    else:
        columns = ["Name", "Type", "Keys"]
        keys = ["name", "type", "keys"]
elif resource_type == "PersistentVolumeClaims":
    if is_all_namespaces:
        columns = ["Name", "Namespace", "Status", "Volume", "Capacity"]
        keys = ["name", "namespace", "status", "volume", "capacity"]
    else:
        columns = ["Name", "Status", "Volume", "Capacity"]
        keys = ["name", "status", "volume", "capacity"]
elif resource_type == "PersistentVolumes":
    columns = ["Name", "Capacity", "Access Modes", "Status"]
    keys = ["name", "capacity", "access_modes", "status"]
elif resource_type == "Namespaces":
    columns = ["Name", "Status", "Age"]
    keys = ["name", "status", "age"]
elif resource_type == "Nodes":
    columns = ["Name", "Status", "Roles", "Version"]
    keys = ["name", "status", "roles", "version"]
else:
    return
```

### 4f — Fix `action_describe_resource` singular mapping

- [ ] **Replace the `rstrip("s")` line in `action_describe_resource`**

Old:
```python
resource_type = self.current_resource_type.rstrip("s")  # Remove trailing 's'
```

New:
```python
resource_type = self._TYPE_SINGULAR.get(self.current_resource_type, self.current_resource_type.lower())
```

### 4g — Update stale tests in test_app.py

- [ ] **Update `test_cluster_screen_has_sidebar`** — old test asserts exact 4-item list:

```python
def test_cluster_screen_has_sidebar():
    screen = ClusterScreen()
    assert hasattr(screen, "_RESOURCE_TYPES")
    assert "Pods" in screen._RESOURCE_TYPES
    assert "Deployments" in screen._RESOURCE_TYPES
    assert "Services" in screen._RESOURCE_TYPES
    assert len(screen._RESOURCE_TYPES) == 16
```

- [ ] **Update `test_sidebar_selection_changes_resource_type`** — second item is now Deployments, not Services:

```python
async def test_sidebar_selection_changes_resource_type():
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)
        # Arrow down to Deployments (second item), press Enter
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        assert screen.current_resource_type == "Deployments"
```

- [ ] **Update `test_sidebar_up_down_updates_resources`** — new order: Pods → Deployments → ReplicaSets:

```python
async def test_sidebar_up_down_updates_resources():
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        assert screen.current_resource_type == "Pods"

        # Down arrow to Deployments (index 1)
        await pilot.press("down")
        await pilot.pause()
        assert screen.current_resource_type == "Deployments"

        # Down arrow to ReplicaSets (index 2)
        await pilot.press("down")
        await pilot.pause()
        assert screen.current_resource_type == "ReplicaSets"

        # Up arrow back to Deployments
        await pilot.press("up")
        await pilot.pause()
        assert screen.current_resource_type == "Deployments"
```

- [ ] **Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all 107 tests pass

- [ ] **Commit**

```bash
git add src/gantry/screens.py tests/test_app.py
git commit -m "feat: expand sidebar to 16 k8s resource types with full column defs and dispatch"
```

---

## Verification

```bash
# Full test suite
uv run pytest tests/ -v

# Manual smoke test
uv run python -m gantry

# Verify in the running app:
# 1. Sidebar shows 16 items (Pods → Nodes)
# 2. Up/down arrows cycle through all 16, table updates each time
# 3. Press 'd' on each resource — describe panel shows relevant fields
# 4. Switch to "all" namespace — Namespace column appears for ns-scoped types
# 5. PVs, Namespaces, Nodes never show a Namespace column (cluster-scoped)
```
