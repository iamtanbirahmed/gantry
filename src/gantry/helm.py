"""Helm orchestration backend module."""

import json
import logging
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def list_repos() -> List[Dict[str, Any]]:
    """
    List all configured Helm repositories.

    Returns a list of dictionaries with repository information (name, url, type).
    Returns empty list if helm is not installed or no repos are configured.
    """
    logger.debug("list_repos called")
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
        logger.debug(f"list_repos returned {len(repos) if isinstance(repos, list) else 0} repos")
        return repos if isinstance(repos, list) else []
    except FileNotFoundError:
        logger.error("helm binary not found in list_repos")
        return [{"error": "helm binary not found", "type": "missing_helm_binary"}]
    except subprocess.CalledProcessError as e:
        logger.error(f"helm command failed in list_repos: {e.stderr or e.stdout or str(e)}")
        return [{"error": str(e.stderr or e.stdout or str(e)), "type": "helm_error"}]
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in list_repos: {e}")
        return [{"error": f"Failed to parse helm output: {str(e)}", "type": "json_error"}]
    except Exception as e:
        logger.error(f"Error in list_repos: {e}", exc_info=True)
        return [{"error": str(e), "type": "list_repos_error"}]


def search_charts(query: str, repo: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for Helm charts in repositories.

    Args:
        query: Search query string.
        repo: Optional specific repository to search in.

    Returns a list of dictionaries with chart information (name, version, app_version, description).
    """
    logger.debug(f"search_charts called with query={query}, repo={repo}")
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
            logger.error(f"helm search failed: {result.stderr or result.stdout}")
            return [{"error": str(result.stderr or result.stdout or "search failed"), "type": "helm_error"}]

        if not result.stdout.strip():
            return []

        charts = json.loads(result.stdout)
        logger.debug(f"search_charts returned {len(charts) if isinstance(charts, list) else 0} charts")
        return charts if isinstance(charts, list) else []
    except FileNotFoundError:
        logger.error("helm binary not found in search_charts")
        return [{"error": "helm binary not found", "type": "missing_helm_binary"}]
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in search_charts: {e}")
        return [{"error": f"Failed to parse helm output: {str(e)}", "type": "json_error"}]
    except Exception as e:
        logger.error(f"Error in search_charts: {e}", exc_info=True)
        return [{"error": str(e), "type": "search_charts_error"}]


def repo_add(name: str, url: str) -> Dict[str, Any]:
    """
    Add a new Helm repository.

    Args:
        name: Name for the repository.
        url: URL of the Helm repository.

    Returns a dictionary with success status and message.
    """
    logger.debug(f"repo_add called with name={name}, url={url}")
    try:
        result = subprocess.run(
            ["helm", "repo", "add", name, url],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error(f"helm repo add failed: {result.stderr or result.stdout}")
            return {
                "success": False,
                "error": str(result.stderr or result.stdout or "add failed"),
                "type": "helm_error",
            }

        logger.debug(f"Successfully added repo {name}")
        return {
            "success": True,
            "name": name,
            "url": url,
            "message": f"Repository '{name}' added successfully",
        }
    except FileNotFoundError:
        logger.error("helm binary not found in repo_add")
        return {
            "success": False,
            "error": "helm binary not found",
            "type": "missing_helm_binary",
        }
    except Exception as e:
        logger.error(f"Error in repo_add: {e}", exc_info=True)
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
    logger.debug(f"repo_remove called with name={name}")
    try:
        result = subprocess.run(
            ["helm", "repo", "remove", name],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error(f"helm repo remove failed: {result.stderr or result.stdout}")
            return {
                "success": False,
                "error": str(result.stderr or result.stdout or "remove failed"),
                "type": "helm_error",
            }

        logger.debug(f"Successfully removed repo {name}")
        return {
            "success": True,
            "name": name,
            "message": f"Repository '{name}' removed successfully",
        }
    except FileNotFoundError:
        logger.error("helm binary not found in repo_remove")
        return {
            "success": False,
            "error": "helm binary not found",
            "type": "missing_helm_binary",
        }
    except Exception as e:
        logger.error(f"Error in repo_remove: {e}", exc_info=True)
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
    logger.debug("repo_update called")
    try:
        result = subprocess.run(
            ["helm", "repo", "update"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error(f"helm repo update failed: {result.stderr or result.stdout}")
            return {
                "success": False,
                "error": str(result.stderr or result.stdout or "update failed"),
                "type": "helm_error",
            }

        logger.debug("Successfully updated all repos")
        return {
            "success": True,
            "message": "All repositories updated successfully",
        }
    except FileNotFoundError:
        logger.error("helm binary not found in repo_update")
        return {
            "success": False,
            "error": "helm binary not found",
            "type": "missing_helm_binary",
        }
    except Exception as e:
        logger.error(f"Error in repo_update: {e}", exc_info=True)
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
    logger.debug(f"install_chart called with release_name={release_name}, chart={chart}, namespace={namespace}")
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
            logger.error(f"helm install failed: {result.stderr or result.stdout}")
            return {
                "success": False,
                "error": str(result.stderr or result.stdout or "install failed"),
                "type": "helm_error",
            }

        logger.debug(f"Successfully installed chart {chart} as release {release_name}")
        return {
            "success": True,
            "release_name": release_name,
            "chart": chart,
            "namespace": namespace,
            "message": f"Chart '{chart}' installed as release '{release_name}' in namespace '{namespace}'",
        }
    except FileNotFoundError:
        logger.error("helm binary not found in install_chart")
        return {
            "success": False,
            "error": "helm binary not found",
            "type": "missing_helm_binary",
        }
    except Exception as e:
        logger.error(f"Error in install_chart: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "type": "install_chart_error",
        }
