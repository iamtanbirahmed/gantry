"""Helm orchestration backend module."""

import json
import subprocess
from typing import Any, Dict, List, Optional


def list_repos() -> List[Dict[str, Any]]:
    """
    List all configured Helm repositories.

    Returns a list of dictionaries with repository information (name, url, type).
    Returns empty list if helm is not installed or no repos are configured.
    """
    try:
        result = subprocess.run(
            ["helm", "repo", "list", "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        if not result.stdout.strip():
            return []
        repos = json.loads(result.stdout)
        return repos if isinstance(repos, list) else []
    except FileNotFoundError:
        return [{"error": "helm binary not found", "type": "missing_helm_binary"}]
    except subprocess.CalledProcessError as e:
        return [{"error": str(e.stderr or e.stdout or str(e)), "type": "helm_error"}]
    except json.JSONDecodeError as e:
        return [{"error": f"Failed to parse helm output: {str(e)}", "type": "json_error"}]
    except Exception as e:
        return [{"error": str(e), "type": "list_repos_error"}]


def search_charts(query: str, repo: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for Helm charts in repositories.

    Args:
        query: Search query string.
        repo: Optional specific repository to search in.

    Returns a list of dictionaries with chart information (name, version, app_version, description).
    """
    try:
        cmd = ["helm", "search", "repo", query, "-o", "json"]
        if repo:
            cmd = ["helm", "search", "repo", f"{repo}/{query}", "-o", "json"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return [{"error": str(result.stderr or result.stdout or "search failed"), "type": "helm_error"}]

        if not result.stdout.strip():
            return []

        charts = json.loads(result.stdout)
        return charts if isinstance(charts, list) else []
    except FileNotFoundError:
        return [{"error": "helm binary not found", "type": "missing_helm_binary"}]
    except json.JSONDecodeError as e:
        return [{"error": f"Failed to parse helm output: {str(e)}", "type": "json_error"}]
    except Exception as e:
        return [{"error": str(e), "type": "search_charts_error"}]


def repo_add(name: str, url: str) -> Dict[str, Any]:
    """
    Add a new Helm repository.

    Args:
        name: Name for the repository.
        url: URL of the Helm repository.

    Returns a dictionary with success status and message.
    """
    try:
        result = subprocess.run(
            ["helm", "repo", "add", name, url],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": str(result.stderr or result.stdout or "add failed"),
                "type": "helm_error",
            }

        return {
            "success": True,
            "name": name,
            "url": url,
            "message": f"Repository '{name}' added successfully",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "helm binary not found",
            "type": "missing_helm_binary",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": "repo_add_error",
        }


def repo_remove(name: str) -> Dict[str, Any]:
    """
    Remove a Helm repository.

    Args:
        name: Name of the repository to remove.

    Returns a dictionary with success status and message.
    """
    try:
        result = subprocess.run(
            ["helm", "repo", "remove", name],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": str(result.stderr or result.stdout or "remove failed"),
                "type": "helm_error",
            }

        return {
            "success": True,
            "name": name,
            "message": f"Repository '{name}' removed successfully",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "helm binary not found",
            "type": "missing_helm_binary",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": "repo_remove_error",
        }


def repo_update() -> Dict[str, Any]:
    """
    Update all Helm repositories.

    Returns a dictionary with success status and message.
    """
    try:
        result = subprocess.run(
            ["helm", "repo", "update"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": str(result.stderr or result.stdout or "update failed"),
                "type": "helm_error",
            }

        return {
            "success": True,
            "message": "All repositories updated successfully",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "helm binary not found",
            "type": "missing_helm_binary",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": "repo_update_error",
        }


def install_chart(
    release_name: str,
    chart: str,
    namespace: str = "default",
    values: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Install a Helm chart.

    Args:
        release_name: Name for the Helm release.
        chart: Chart name or path (e.g., "repo/chart").
        namespace: Kubernetes namespace to install to (default: "default").
        values: Optional path to a values file.

    Returns a dictionary with success status and message.
    """
    try:
        cmd = ["helm", "install", release_name, chart, "-n", namespace]
        if values:
            cmd.extend(["--values", values])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": str(result.stderr or result.stdout or "install failed"),
                "type": "helm_error",
            }

        return {
            "success": True,
            "release_name": release_name,
            "chart": chart,
            "namespace": namespace,
            "message": f"Chart '{chart}' installed as release '{release_name}' in namespace '{namespace}'",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "helm binary not found",
            "type": "missing_helm_binary",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": "install_chart_error",
        }
