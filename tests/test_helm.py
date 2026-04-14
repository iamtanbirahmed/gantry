"""Tests for the Helm backend module."""

import json
import pytest
from unittest.mock import patch, MagicMock
import subprocess

from gantry import helm


class TestListRepos:
    """Tests for list_repos function."""

    @patch("gantry.helm.subprocess.run")
    def test_list_repos_success(self, mock_run):
        """Test listing repos successfully."""
        mock_repos = [
            {"name": "stable", "url": "https://charts.helm.sh/stable", "type": ""},
            {"name": "bitnami", "url": "https://charts.bitnami.com/bitnami", "type": ""},
        ]
        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_repos),
            stderr="",
            returncode=0,
        )

        result = helm.list_repos()

        assert len(result) == 2
        assert result[0]["name"] == "stable"
        assert result[1]["name"] == "bitnami"
        mock_run.assert_called_once_with(
            ["helm", "repo", "list", "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("gantry.helm.subprocess.run")
    def test_list_repos_empty(self, mock_run):
        """Test listing repos when none are configured."""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

        result = helm.list_repos()

        assert result == []

    @patch("gantry.helm.subprocess.run")
    def test_list_repos_missing_helm(self, mock_run):
        """Test list_repos when helm binary is not found."""
        mock_run.side_effect = FileNotFoundError("helm not found")

        result = helm.list_repos()

        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["type"] == "missing_helm_binary"

    @patch("gantry.helm.subprocess.run")
    def test_list_repos_helm_error(self, mock_run):
        """Test list_repos when helm command fails."""
        error = subprocess.CalledProcessError(1, "helm repo list")
        error.stderr = "Error: no repositories configured"
        mock_run.side_effect = error

        result = helm.list_repos()

        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["type"] == "helm_error"

    @patch("gantry.helm.subprocess.run")
    def test_list_repos_invalid_json(self, mock_run):
        """Test list_repos with invalid JSON output."""
        mock_run.return_value = MagicMock(
            stdout="invalid json",
            stderr="",
            returncode=0,
        )

        result = helm.list_repos()

        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["type"] == "json_error"

    @patch("gantry.helm.subprocess.run")
    def test_list_repos_non_list_json(self, mock_run):
        """Test list_repos when JSON is not a list."""
        mock_run.return_value = MagicMock(
            stdout='{"error": "something"}',
            stderr="",
            returncode=0,
        )

        result = helm.list_repos()

        assert result == []


class TestSearchCharts:
    """Tests for search_charts function."""

    @patch("gantry.helm.subprocess.run")
    def test_search_charts_success(self, mock_run):
        """Test searching charts successfully."""
        mock_charts = [
            {
                "name": "stable/nginx",
                "version": "9.3.4",
                "app_version": "1.19.0",
                "description": "An nginx HTTP and reverse proxy server",
            },
            {
                "name": "stable/postgresql",
                "version": "11.2.0",
                "app_version": "11.9",
                "description": "PostgreSQL database",
            },
        ]
        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_charts),
            stderr="",
            returncode=0,
        )

        result = helm.search_charts("nginx")

        assert len(result) == 2
        assert result[0]["name"] == "stable/nginx"
        assert result[0]["version"] == "9.3.4"

    @patch("gantry.helm.subprocess.run")
    def test_search_charts_with_repo(self, mock_run):
        """Test searching charts in a specific repo."""
        mock_charts = [
            {
                "name": "bitnami/nginx",
                "version": "13.2.20",
                "app_version": "1.21.0",
                "description": "NGINX Open Source",
            },
        ]
        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_charts),
            stderr="",
            returncode=0,
        )

        result = helm.search_charts("nginx", repo="bitnami")

        assert len(result) == 1
        assert result[0]["name"] == "bitnami/nginx"
        mock_run.assert_called_once_with(
            ["helm", "search", "repo", "bitnami/nginx", "-o", "json"],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("gantry.helm.subprocess.run")
    def test_search_charts_no_results(self, mock_run):
        """Test searching charts with no results."""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

        result = helm.search_charts("nonexistent")

        assert result == []

    @patch("gantry.helm.subprocess.run")
    def test_search_charts_missing_helm(self, mock_run):
        """Test search_charts when helm binary is not found."""
        mock_run.side_effect = FileNotFoundError("helm not found")

        result = helm.search_charts("nginx")

        assert len(result) == 1
        assert result[0]["type"] == "missing_helm_binary"

    @patch("gantry.helm.subprocess.run")
    def test_search_charts_helm_error(self, mock_run):
        """Test search_charts when helm command fails."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="Error: repo not found",
            returncode=1,
        )

        result = helm.search_charts("nginx")

        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["type"] == "helm_error"

    @patch("gantry.helm.subprocess.run")
    def test_search_charts_invalid_json(self, mock_run):
        """Test search_charts with invalid JSON output."""
        mock_run.return_value = MagicMock(
            stdout="invalid json",
            stderr="",
            returncode=0,
        )

        result = helm.search_charts("nginx")

        assert len(result) == 1
        assert result[0]["type"] == "json_error"


class TestRepoAdd:
    """Tests for repo_add function."""

    @patch("gantry.helm.subprocess.run")
    def test_repo_add_success(self, mock_run):
        """Test adding a repo successfully."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
            returncode=0,
        )

        result = helm.repo_add("myrepo", "https://example.com/helm")

        assert result["success"] is True
        assert result["name"] == "myrepo"
        assert result["url"] == "https://example.com/helm"
        mock_run.assert_called_once_with(
            ["helm", "repo", "add", "myrepo", "https://example.com/helm"],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("gantry.helm.subprocess.run")
    def test_repo_add_already_exists(self, mock_run):
        """Test adding a repo that already exists."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="error: repository name (myrepo) already exists",
            returncode=1,
        )

        result = helm.repo_add("myrepo", "https://example.com/helm")

        assert result["success"] is False
        assert "error" in result

    @patch("gantry.helm.subprocess.run")
    def test_repo_add_missing_helm(self, mock_run):
        """Test repo_add when helm binary is not found."""
        mock_run.side_effect = FileNotFoundError("helm not found")

        result = helm.repo_add("myrepo", "https://example.com/helm")

        assert result["success"] is False
        assert result["type"] == "missing_helm_binary"

    @patch("gantry.helm.subprocess.run")
    def test_repo_add_generic_error(self, mock_run):
        """Test repo_add with generic error."""
        mock_run.side_effect = Exception("Some error")

        result = helm.repo_add("myrepo", "https://example.com/helm")

        assert result["success"] is False
        assert result["type"] == "repo_add_error"


class TestRepoRemove:
    """Tests for repo_remove function."""

    @patch("gantry.helm.subprocess.run")
    def test_repo_remove_success(self, mock_run):
        """Test removing a repo successfully."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
            returncode=0,
        )

        result = helm.repo_remove("myrepo")

        assert result["success"] is True
        assert result["name"] == "myrepo"
        mock_run.assert_called_once_with(
            ["helm", "repo", "remove", "myrepo"],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("gantry.helm.subprocess.run")
    def test_repo_remove_not_found(self, mock_run):
        """Test removing a repo that doesn't exist."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="error: no repository named 'myrepo'",
            returncode=1,
        )

        result = helm.repo_remove("myrepo")

        assert result["success"] is False
        assert "error" in result

    @patch("gantry.helm.subprocess.run")
    def test_repo_remove_missing_helm(self, mock_run):
        """Test repo_remove when helm binary is not found."""
        mock_run.side_effect = FileNotFoundError("helm not found")

        result = helm.repo_remove("myrepo")

        assert result["success"] is False
        assert result["type"] == "missing_helm_binary"

    @patch("gantry.helm.subprocess.run")
    def test_repo_remove_generic_error(self, mock_run):
        """Test repo_remove with generic error."""
        mock_run.side_effect = Exception("Some error")

        result = helm.repo_remove("myrepo")

        assert result["success"] is False
        assert result["type"] == "repo_remove_error"


class TestRepoUpdate:
    """Tests for repo_update function."""

    @patch("gantry.helm.subprocess.run")
    def test_repo_update_success(self, mock_run):
        """Test updating repos successfully."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
            returncode=0,
        )

        result = helm.repo_update()

        assert result["success"] is True
        assert "message" in result
        mock_run.assert_called_once_with(
            ["helm", "repo", "update"],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("gantry.helm.subprocess.run")
    def test_repo_update_error(self, mock_run):
        """Test repo_update when helm command fails."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="Error: failed to update repos",
            returncode=1,
        )

        result = helm.repo_update()

        assert result["success"] is False
        assert "error" in result

    @patch("gantry.helm.subprocess.run")
    def test_repo_update_missing_helm(self, mock_run):
        """Test repo_update when helm binary is not found."""
        mock_run.side_effect = FileNotFoundError("helm not found")

        result = helm.repo_update()

        assert result["success"] is False
        assert result["type"] == "missing_helm_binary"

    @patch("gantry.helm.subprocess.run")
    def test_repo_update_generic_error(self, mock_run):
        """Test repo_update with generic error."""
        mock_run.side_effect = Exception("Some error")

        result = helm.repo_update()

        assert result["success"] is False
        assert result["type"] == "repo_update_error"


class TestInstallChart:
    """Tests for install_chart function."""

    @patch("gantry.helm.subprocess.run")
    def test_install_chart_success(self, mock_run):
        """Test installing a chart successfully."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
            returncode=0,
        )

        result = helm.install_chart("my-release", "stable/nginx", namespace="production")

        assert result["success"] is True
        assert result["release_name"] == "my-release"
        assert result["chart"] == "stable/nginx"
        assert result["namespace"] == "production"
        mock_run.assert_called_once_with(
            ["helm", "install", "my-release", "stable/nginx", "-n", "production"],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("gantry.helm.subprocess.run")
    def test_install_chart_with_values(self, mock_run):
        """Test installing a chart with a values file."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
            returncode=0,
        )

        result = helm.install_chart(
            "my-release",
            "stable/nginx",
            namespace="default",
            values="/path/to/values.yaml",
        )

        assert result["success"] is True
        mock_run.assert_called_once_with(
            [
                "helm",
                "install",
                "my-release",
                "stable/nginx",
                "-n",
                "default",
                "--values",
                "/path/to/values.yaml",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("gantry.helm.subprocess.run")
    def test_install_chart_default_namespace(self, mock_run):
        """Test installing a chart with default namespace."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
            returncode=0,
        )

        result = helm.install_chart("my-release", "stable/nginx")

        assert result["success"] is True
        assert result["namespace"] == "default"
        mock_run.assert_called_once_with(
            ["helm", "install", "my-release", "stable/nginx", "-n", "default"],
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("gantry.helm.subprocess.run")
    def test_install_chart_chart_not_found(self, mock_run):
        """Test installing a chart that doesn't exist."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="Error: chart not found",
            returncode=1,
        )

        result = helm.install_chart("my-release", "nonexistent/chart")

        assert result["success"] is False
        assert "error" in result

    @patch("gantry.helm.subprocess.run")
    def test_install_chart_missing_helm(self, mock_run):
        """Test install_chart when helm binary is not found."""
        mock_run.side_effect = FileNotFoundError("helm not found")

        result = helm.install_chart("my-release", "stable/nginx")

        assert result["success"] is False
        assert result["type"] == "missing_helm_binary"

    @patch("gantry.helm.subprocess.run")
    def test_install_chart_generic_error(self, mock_run):
        """Test install_chart with generic error."""
        mock_run.side_effect = Exception("Some error")

        result = helm.install_chart("my-release", "stable/nginx")

        assert result["success"] is False
        assert result["type"] == "install_chart_error"

    @patch("gantry.helm.subprocess.run")
    def test_install_chart_helm_error_with_output(self, mock_run):
        """Test install_chart when helm returns error with output."""
        mock_run.return_value = MagicMock(
            stdout="Release 'my-release' already exists",
            stderr="",
            returncode=1,
        )

        result = helm.install_chart("my-release", "stable/nginx")

        assert result["success"] is False
        assert "Release 'my-release' already exists" in result["error"]
