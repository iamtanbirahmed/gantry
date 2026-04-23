"""Kubernetes API backend module."""

import logging
import os
from typing import Any, Dict, List, Optional

import yaml

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


def list_contexts() -> List[Dict[str, Any]]:
    """
    List all available Kubernetes contexts.

    Returns a list of dictionaries with context information.
    Returns empty list if kubeconfig is missing or invalid.
    """
    logger.debug("list_contexts called")
    try:
        _, active_context = config.list_kube_config_contexts()
        if active_context is None:
            return []

        contexts, _ = config.list_kube_config_contexts()
        result = []
        for ctx in contexts:
            result.append({
                "name": ctx["name"],
                "cluster": ctx["context"]["cluster"],
                "user": ctx["context"]["user"],
                "namespace": ctx["context"].get("namespace") or "default",
                "current": ctx["name"] == active_context["name"],
            })
        logger.debug(f"list_contexts returned {len(result)} contexts")
        return result
    except (config.config_exception.ConfigException, FileNotFoundError):
        return []
    except Exception as e:
        logger.error(f"Error in list_contexts: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_contexts_error"}]


def switch_context(context_name: str) -> Dict[str, Any]:
    """
    Switch to a different Kubernetes context.

    Args:
        context_name: Name of the context to switch to.

    Returns a dictionary with status of the operation.
    """
    logger.debug(f"switch_context called with context_name={context_name}")
    try:
        config.load_kube_config(context=context_name)
        logger.debug(f"Successfully switched to context {context_name}")
        return {
            "success": True,
            "context": context_name,
            "message": f"Switched to context '{context_name}'",
        }
    except config.config_exception.ConfigException as e:
        logger.error(f"Config error in switch_context: {e}")
        return {
            "success": False,
            "error": str(e),
            "type": "config_error",
        }
    except FileNotFoundError:
        logger.error("kubeconfig file not found in switch_context")
        return {
            "success": False,
            "error": "kubeconfig file not found",
            "type": "missing_kubeconfig",
        }
    except Exception as e:
        logger.error(f"Error in switch_context: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "type": "switch_context_error",
        }


def list_namespaces(context_name: Optional[str] = None) -> List[str]:
    """
    List all available Kubernetes namespaces.

    Args:
        context_name: Optional context name to load kubeconfig for. If None, uses active context.

    Returns a list of namespace names, or an empty list if unable to fetch.
    """
    logger.debug(f"list_namespaces called with context_name={context_name}")
    try:
        config.load_kube_config(context=context_name)
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace()
        result = [ns.metadata.name for ns in namespaces.items]
        logger.debug(f"list_namespaces returned {len(result)} namespaces")
        return result
    except (config.config_exception.ConfigException, FileNotFoundError):
        logger.debug("kubeconfig not found in list_namespaces")
        return []
    except Exception as e:
        logger.error(f"Error in list_namespaces: {e}", exc_info=True)
        return []


def list_pods(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all pods in a given namespace.

    Args:
        namespace: Kubernetes namespace (default: "default"). Use "all" for all namespaces.
        context: Kubernetes context name. If None, uses the active kubeconfig context.

    Returns a list of pod dictionaries with name, status, ready replicas, etc.
    """
    logger.debug(f"list_pods called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()

        if namespace == "all":
            pods = v1.list_pod_for_all_namespaces()
        else:
            pods = v1.list_namespaced_pod(namespace=namespace)

        result = []
        for pod in pods.items:
            result.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "ready": sum(
                    1 for container_status in (pod.status.container_statuses or [])
                    if container_status.ready
                ),
                "total_containers": len(pod.spec.containers),
                "restarts": sum(
                    container_status.restart_count
                    for container_status in (pod.status.container_statuses or [])
                ),
                "age_seconds": (
                    (pod.metadata.creation_timestamp.timestamp())
                    if pod.metadata.creation_timestamp
                    else None
                ),
            })
        logger.debug(f"list_pods returned {len(result)} pods for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_pods")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_pods: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_pods: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_pods_error"}]


def list_services(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all services in a given namespace.

    Args:
        namespace: Kubernetes namespace (default: "default"). Use "all" for all namespaces.
        context: Kubernetes context name. If None, uses the active kubeconfig context.

    Returns a list of service dictionaries with name, type, cluster IP, ports, etc.
    """
    logger.debug(f"list_services called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()

        if namespace == "all":
            services = v1.list_service_for_all_namespaces()
        else:
            services = v1.list_namespaced_service(namespace=namespace)

        result = []
        for svc in services.items:
            ports = []
            if svc.spec.ports:
                for port in svc.spec.ports:
                    ports.append({
                        "name": port.name,
                        "protocol": port.protocol,
                        "port": port.port,
                        "target_port": port.target_port,
                    })

            result.append({
                "name": svc.metadata.name,
                "namespace": svc.metadata.namespace,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "external_ips": svc.spec.external_i_ps or [],
                "ports": ports,
            })
        logger.debug(f"list_services returned {len(result)} services for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_services")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_services: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_services: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_services_error"}]


def list_deployments(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all deployments in a given namespace.

    Args:
        namespace: Kubernetes namespace (default: "default"). Use "all" for all namespaces.
        context: Kubernetes context name. If None, uses the active kubeconfig context.

    Returns a list of deployment dictionaries with name, replicas, status, etc.
    """
    logger.debug(f"list_deployments called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        apps_v1 = client.AppsV1Api()

        if namespace == "all":
            deployments = apps_v1.list_deployment_for_all_namespaces()
        else:
            deployments = apps_v1.list_namespaced_deployment(namespace=namespace)

        result = []
        for deploy in deployments.items:
            result.append({
                "name": deploy.metadata.name,
                "namespace": deploy.metadata.namespace,
                "replicas": deploy.spec.replicas or 0,
                "ready_replicas": deploy.status.ready_replicas or 0,
                "updated_replicas": deploy.status.updated_replicas or 0,
                "available_replicas": deploy.status.available_replicas or 0,
                "strategy_type": deploy.spec.strategy.type if deploy.spec.strategy else None,
            })
        logger.debug(f"list_deployments returned {len(result)} deployments for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_deployments")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_deployments: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_deployments: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_deployments_error"}]


def list_configmaps(namespace: str = "default", context: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all configmaps in a given namespace.

    Args:
        namespace: Kubernetes namespace (default: "default"). Use "all" for all namespaces.
        context: Kubernetes context name. If None, uses the active kubeconfig context.

    Returns a list of configmap dictionaries with name, data keys, etc.
    """
    logger.debug(f"list_configmaps called with namespace={namespace}")
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()

        if namespace == "all":
            configmaps = v1.list_config_map_for_all_namespaces()
        else:
            configmaps = v1.list_namespaced_config_map(namespace=namespace)

        result = []
        for cm in configmaps.items:
            data_keys = list(cm.data.keys()) if cm.data else []
            result.append({
                "name": cm.metadata.name,
                "namespace": cm.metadata.namespace,
                "keys": data_keys,
                "key_count": len(data_keys),
            })
        logger.debug(f"list_configmaps returned {len(result)} configmaps for namespace={namespace}")
        return result
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in list_configmaps")
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"API error in list_configmaps: {e}", exc_info=True)
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        logger.error(f"Error in list_configmaps: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_configmaps_error"}]


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
            hosts = ",".join(
                rule.host for rule in (ing.spec.rules or []) if rule.host
            )
            annotations = ing.metadata.annotations or {}
            ingress_class = ing.spec.ingress_class_name or annotations.get("kubernetes.io/ingress.class", "")
            lb_ingress = ing.status.load_balancer.ingress if ing.status and ing.status.load_balancer else []
            address = ",".join(
                lb.ip or lb.hostname or "" for lb in (lb_ingress or [])
            )
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


def list_nodes(context: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all Nodes (cluster-scoped)."""
    logger.debug("list_nodes called")
    try:
        config.load_kube_config(context=context)
        v1 = client.CoreV1Api()
        nodes = v1.list_node()

        result = []
        for node in nodes.items:
            ready_cond = next(
                (c for c in (node.status.conditions or []) if c.type == "Ready"),
                None,
            )
            node_status = "Ready" if (ready_cond and ready_cond.status == "True") else "NotReady"
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


def describe_resource(
    resource_type: str,
    resource_name: str,
    namespace: str = "default",
) -> Optional[Dict[str, Any]]:
    """
    Describe a Kubernetes resource and return its full specification.

    Args:
        resource_type: Type of resource (pod, service, deployment, configmap, etc.).
        resource_name: Name of the resource.
        namespace: Kubernetes namespace (default: "default").

    Returns a dictionary with the full resource spec, or None if not found.
    """
    logger.debug(f"describe_resource called for {resource_type}/{resource_name} in {namespace}")
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()

        resource_type_lower = resource_type.lower()

        if resource_type_lower == "pod":
            pod = v1.read_namespaced_pod(name=resource_name, namespace=namespace)
            return {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "spec": {
                    "containers": [
                        {
                            "name": c.name,
                            "image": c.image,
                            "ports": [
                                {"name": p.name, "port": p.container_port}
                                for p in (c.ports or [])
                            ],
                        }
                        for c in pod.spec.containers
                    ],
                    "restart_policy": pod.spec.restart_policy,
                },
                "status_detail": {
                    "phase": pod.status.phase,
                    "conditions": [
                        {
                            "type": c.type,
                            "status": c.status,
                            "reason": c.reason,
                        }
                        for c in (pod.status.conditions or [])
                    ],
                },
            }

        elif resource_type_lower == "service":
            svc = v1.read_namespaced_service(name=resource_name, namespace=namespace)
            ports = []
            if svc.spec.ports:
                for port in svc.spec.ports:
                    ports.append({
                        "name": port.name,
                        "protocol": port.protocol,
                        "port": port.port,
                        "target_port": port.target_port,
                    })
            return {
                "name": svc.metadata.name,
                "namespace": svc.metadata.namespace,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "external_ips": svc.spec.external_i_ps or [],
                "ports": ports,
                "selector": svc.spec.selector or {},
            }

        elif resource_type_lower == "deployment":
            deploy = apps_v1.read_namespaced_deployment(name=resource_name, namespace=namespace)
            return {
                "name": deploy.metadata.name,
                "namespace": deploy.metadata.namespace,
                "replicas": deploy.spec.replicas or 0,
                "status": {
                    "ready_replicas": deploy.status.ready_replicas or 0,
                    "updated_replicas": deploy.status.updated_replicas or 0,
                    "available_replicas": deploy.status.available_replicas or 0,
                },
                "strategy": deploy.spec.strategy.type if deploy.spec.strategy else None,
                "selector": deploy.spec.selector.match_labels or {},
            }

        elif resource_type_lower == "configmap":
            cm = v1.read_namespaced_config_map(name=resource_name, namespace=namespace)
            return {
                "name": cm.metadata.name,
                "namespace": cm.metadata.namespace,
                "data": cm.data or {},
            }

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

        else:
            return {
                "error": f"Unsupported resource type: {resource_type}",
                "type": "unsupported_resource_type",
            }

    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found or invalid in describe_resource")
        return {
            "error": "kubeconfig not found or invalid",
            "type": "missing_kubeconfig",
        }
    except ApiException as e:
        if e.status == 404:
            return None
        logger.error(f"API error in describe_resource: {e}", exc_info=True)
        return {
            "error": str(e),
            "type": "api_error",
            "status": e.status,
        }
    except Exception as e:
        logger.error(f"Error in describe_resource: {e}", exc_info=True)
        return {
            "error": str(e),
            "type": "describe_resource_error",
        }


def get_resource_yaml(
    resource_type: str,
    resource_name: str,
    namespace: str = "default",
) -> tuple[Optional[str], Optional[str]]:
    """
    Return (full_yaml, spec_yaml) for a Kubernetes resource.

    full_yaml: complete object (metadata, spec, status).
    spec_yaml: apiVersion/kind/metadata(name+namespace only)/spec — no status or managedFields.
    Returns (None, None) on any error.
    """
    logger.debug(f"get_resource_yaml called for {resource_type}/{resource_name} in {namespace}")
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()

        resource_type_lower = resource_type.lower()
        obj = None

        if resource_type_lower == "pod":
            obj = v1.read_namespaced_pod(name=resource_name, namespace=namespace)
        elif resource_type_lower == "service":
            obj = v1.read_namespaced_service(name=resource_name, namespace=namespace)
        elif resource_type_lower == "deployment":
            obj = apps_v1.read_namespaced_deployment(name=resource_name, namespace=namespace)
        elif resource_type_lower == "configmap":
            obj = v1.read_namespaced_config_map(name=resource_name, namespace=namespace)
        elif resource_type_lower == "replicaset":
            obj = apps_v1.read_namespaced_replica_set(name=resource_name, namespace=namespace)
        elif resource_type_lower == "statefulset":
            obj = apps_v1.read_namespaced_stateful_set(name=resource_name, namespace=namespace)
        elif resource_type_lower == "daemonset":
            obj = apps_v1.read_namespaced_daemon_set(name=resource_name, namespace=namespace)
        elif resource_type_lower == "job":
            batch_v1 = client.BatchV1Api()
            obj = batch_v1.read_namespaced_job(name=resource_name, namespace=namespace)
        elif resource_type_lower == "cronjob":
            batch_v1 = client.BatchV1Api()
            obj = batch_v1.read_namespaced_cron_job(name=resource_name, namespace=namespace)
        elif resource_type_lower == "ingress":
            networking_v1 = client.NetworkingV1Api()
            obj = networking_v1.read_namespaced_ingress(name=resource_name, namespace=namespace)
        elif resource_type_lower == "endpoints":
            obj = v1.read_namespaced_endpoints(name=resource_name, namespace=namespace)
        elif resource_type_lower == "secret":
            obj = v1.read_namespaced_secret(name=resource_name, namespace=namespace)
        elif resource_type_lower == "persistentvolumeclaim":
            obj = v1.read_namespaced_persistent_volume_claim(name=resource_name, namespace=namespace)
        elif resource_type_lower == "persistentvolume":
            obj = v1.read_persistent_volume(name=resource_name)
        elif resource_type_lower == "namespace":
            obj = v1.read_namespace(name=resource_name)
        elif resource_type_lower == "node":
            obj = v1.read_node(name=resource_name)
        else:
            logger.warning(f"get_resource_yaml: unsupported resource type {resource_type!r}")
            return (None, None)

        raw_dict = client.ApiClient().sanitize_for_serialization(obj)

        full_yaml = yaml.dump(raw_dict, default_flow_style=False, sort_keys=False)

        metadata = raw_dict.get("metadata", {})
        spec_dict: Dict[str, Any] = {
            "apiVersion": raw_dict.get("apiVersion", ""),
            "kind": raw_dict.get("kind", ""),
            "metadata": {k: v for k, v in {
                "name": metadata.get("name", ""),
                "namespace": metadata.get("namespace"),
            }.items() if v is not None},
            "spec": raw_dict.get("spec", {}),
        }
        spec_yaml = yaml.dump(spec_dict, default_flow_style=False, sort_keys=False)

        logger.debug(f"get_resource_yaml completed for {resource_type}/{resource_name}")
        return (full_yaml, spec_yaml)

    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found in get_resource_yaml")
        return (None, None)
    except ApiException as e:
        if e.status == 404:
            return (None, None)
        logger.error(f"API error in get_resource_yaml: {e}", exc_info=True)
        return (None, None)
    except Exception as e:
        logger.error(f"Error in get_resource_yaml: {e}", exc_info=True)
        return (None, None)


def get_pod_logs(
    pod_name: str,
    namespace: str = "default",
    tail_lines: int = 50,
) -> Optional[str]:
    """
    Get logs from a pod.

    Args:
        pod_name: Name of the pod.
        namespace: Kubernetes namespace (default: "default").
        tail_lines: Number of lines to retrieve (default: 50).

    Returns a string with the pod logs, or None if not found.
    """
    logger.debug(f"get_pod_logs called for {pod_name} in {namespace}")
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines,
        )
        logger.debug(f"Retrieved logs for pod {pod_name}")
        return logs
    except config.config_exception.ConfigException:
        logger.error("kubeconfig not found in get_pod_logs")
        return None
    except ApiException as e:
        if e.status == 404:
            return None
        logger.error(f"API error in get_pod_logs: {e}", exc_info=True)
        return f"API Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in get_pod_logs: {e}", exc_info=True)
        return f"Error: {str(e)}"
