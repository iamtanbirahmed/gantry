"""Kubernetes API backend module."""

import os
from typing import Any, Dict, List, Optional

from kubernetes import client, config
from kubernetes.client.rest import ApiException


def list_contexts() -> List[Dict[str, Any]]:
    """
    List all available Kubernetes contexts.

    Returns a list of dictionaries with context information.
    Returns empty list if kubeconfig is missing or invalid.
    """
    try:
        _, active_context = config.list_kube_config_contexts()
        if active_context is None:
            return []

        contexts, _ = config.list_kube_config_contexts()
        result = []
        for ctx in contexts:
            result.append({
                "name": ctx.name,
                "cluster": ctx.context.cluster,
                "user": ctx.context.user,
                "namespace": ctx.context.namespace or "default",
                "current": ctx.name == active_context.name,
            })
        return result
    except (config.config_exception.ConfigException, FileNotFoundError):
        return []
    except Exception as e:
        return [{"error": str(e), "type": "list_contexts_error"}]


def switch_context(context_name: str) -> Dict[str, Any]:
    """
    Switch to a different Kubernetes context.

    Args:
        context_name: Name of the context to switch to.

    Returns a dictionary with status of the operation.
    """
    try:
        config.load_kube_config(context=context_name)
        return {
            "success": True,
            "context": context_name,
            "message": f"Switched to context '{context_name}'",
        }
    except config.config_exception.ConfigException as e:
        return {
            "success": False,
            "error": str(e),
            "type": "config_error",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "kubeconfig file not found",
            "type": "missing_kubeconfig",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": "switch_context_error",
        }


def list_namespaces() -> List[str]:
    """
    List all available Kubernetes namespaces.

    Returns a list of namespace names, or an empty list if unable to fetch.
    """
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace()
        return [ns.metadata.name for ns in namespaces.items]
    except (config.config_exception.ConfigException, FileNotFoundError):
        return []
    except Exception:
        return []


def list_pods(namespace: str = "default") -> List[Dict[str, Any]]:
    """
    List all pods in a given namespace.

    Args:
        namespace: Kubernetes namespace (default: "default"). Use "all" for all namespaces.

    Returns a list of pod dictionaries with name, status, ready replicas, etc.
    """
    try:
        config.load_kube_config()
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
        return result
    except config.config_exception.ConfigException:
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        return [{"error": str(e), "type": "list_pods_error"}]


def list_services(namespace: str = "default") -> List[Dict[str, Any]]:
    """
    List all services in a given namespace.

    Args:
        namespace: Kubernetes namespace (default: "default"). Use "all" for all namespaces.

    Returns a list of service dictionaries with name, type, cluster IP, ports, etc.
    """
    try:
        config.load_kube_config()
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
        return result
    except config.config_exception.ConfigException:
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        return [{"error": str(e), "type": "list_services_error"}]


def list_deployments(namespace: str = "default") -> List[Dict[str, Any]]:
    """
    List all deployments in a given namespace.

    Args:
        namespace: Kubernetes namespace (default: "default"). Use "all" for all namespaces.

    Returns a list of deployment dictionaries with name, replicas, status, etc.
    """
    try:
        config.load_kube_config()
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
        return result
    except config.config_exception.ConfigException:
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        return [{"error": str(e), "type": "list_deployments_error"}]


def list_configmaps(namespace: str = "default") -> List[Dict[str, Any]]:
    """
    List all configmaps in a given namespace.

    Args:
        namespace: Kubernetes namespace (default: "default"). Use "all" for all namespaces.

    Returns a list of configmap dictionaries with name, data keys, etc.
    """
    try:
        config.load_kube_config()
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
        return result
    except config.config_exception.ConfigException:
        return [{"error": "kubeconfig not found or invalid", "type": "missing_kubeconfig"}]
    except ApiException as e:
        if e.status == 404:
            return []
        return [{"error": str(e), "type": "api_error", "status": e.status}]
    except Exception as e:
        return [{"error": str(e), "type": "list_configmaps_error"}]


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

        else:
            return {
                "error": f"Unsupported resource type: {resource_type}",
                "type": "unsupported_resource_type",
            }

    except config.config_exception.ConfigException:
        return {
            "error": "kubeconfig not found or invalid",
            "type": "missing_kubeconfig",
        }
    except ApiException as e:
        if e.status == 404:
            return None
        return {
            "error": str(e),
            "type": "api_error",
            "status": e.status,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": "describe_resource_error",
        }


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
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines,
        )
        return logs
    except config.config_exception.ConfigException:
        return None
    except ApiException as e:
        if e.status == 404:
            return None
        return f"API Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
