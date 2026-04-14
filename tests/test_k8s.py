"""Tests for the Kubernetes backend module."""

import pytest
from unittest.mock import patch, MagicMock
from kubernetes.client.rest import ApiException
from kubernetes import config

from gantry import k8s


class TestListContexts:
    """Tests for list_contexts function."""

    @patch("gantry.k8s.config.list_kube_config_contexts")
    def test_list_contexts_success(self, mock_list_contexts):
        """Test listing contexts successfully."""
        # Mock context objects
        ctx1 = MagicMock()
        ctx1.name = "minikube"
        ctx1.context.cluster = "minikube"
        ctx1.context.user = "minikube"
        ctx1.context.namespace = "default"

        ctx2 = MagicMock()
        ctx2.name = "docker-desktop"
        ctx2.context.cluster = "docker-desktop"
        ctx2.context.user = "docker-desktop"
        ctx2.context.namespace = None

        active_ctx = MagicMock()
        active_ctx.name = "minikube"

        mock_list_contexts.return_value = ([ctx1, ctx2], active_ctx)

        result = k8s.list_contexts()

        assert len(result) == 2
        assert result[0]["name"] == "minikube"
        assert result[0]["current"] is True
        assert result[1]["name"] == "docker-desktop"
        assert result[1]["current"] is False
        assert result[1]["namespace"] == "default"

    @patch("gantry.k8s.config.list_kube_config_contexts")
    def test_list_contexts_missing_kubeconfig(self, mock_list_contexts):
        """Test list_contexts with missing kubeconfig."""
        mock_list_contexts.side_effect = config.config_exception.ConfigException("No kubeconfig")

        result = k8s.list_contexts()

        assert result == []

    @patch("gantry.k8s.config.list_kube_config_contexts")
    def test_list_contexts_file_not_found(self, mock_list_contexts):
        """Test list_contexts with FileNotFoundError."""
        mock_list_contexts.side_effect = FileNotFoundError("kubeconfig not found")

        result = k8s.list_contexts()

        assert result == []

    @patch("gantry.k8s.config.list_kube_config_contexts")
    def test_list_contexts_generic_error(self, mock_list_contexts):
        """Test list_contexts with generic exception."""
        mock_list_contexts.side_effect = Exception("Some error")

        result = k8s.list_contexts()

        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["type"] == "list_contexts_error"

    @patch("gantry.k8s.config.list_kube_config_contexts")
    def test_list_contexts_no_active_context(self, mock_list_contexts):
        """Test list_contexts when no active context."""
        mock_list_contexts.return_value = ([], None)

        result = k8s.list_contexts()

        assert result == []


class TestSwitchContext:
    """Tests for switch_context function."""

    @patch("gantry.k8s.config.load_kube_config")
    def test_switch_context_success(self, mock_load):
        """Test switching context successfully."""
        mock_load.return_value = None

        result = k8s.switch_context("minikube")

        assert result["success"] is True
        assert result["context"] == "minikube"
        mock_load.assert_called_once_with(context="minikube")

    @patch("gantry.k8s.config.load_kube_config")
    def test_switch_context_config_error(self, mock_load):
        """Test switching context with config error."""
        mock_load.side_effect = config.config_exception.ConfigException("Invalid context")

        result = k8s.switch_context("invalid")

        assert result["success"] is False
        assert result["type"] == "config_error"

    @patch("gantry.k8s.config.load_kube_config")
    def test_switch_context_missing_kubeconfig(self, mock_load):
        """Test switching context with missing kubeconfig."""
        mock_load.side_effect = FileNotFoundError("kubeconfig not found")

        result = k8s.switch_context("minikube")

        assert result["success"] is False
        assert result["type"] == "missing_kubeconfig"

    @patch("gantry.k8s.config.load_kube_config")
    def test_switch_context_generic_error(self, mock_load):
        """Test switching context with generic error."""
        mock_load.side_effect = Exception("Some error")

        result = k8s.switch_context("minikube")

        assert result["success"] is False
        assert result["type"] == "switch_context_error"


class TestListPods:
    """Tests for list_pods function."""

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_pods_success(self, mock_api_class, mock_load):
        """Test listing pods successfully."""
        # Mock pod objects
        pod1 = MagicMock()
        pod1.metadata.name = "nginx-pod"
        pod1.metadata.namespace = "default"
        pod1.status.phase = "Running"
        pod1.metadata.creation_timestamp = MagicMock()
        pod1.metadata.creation_timestamp.timestamp.return_value = 1000.0
        pod1.spec.containers = [MagicMock(), MagicMock()]

        container_status1 = MagicMock()
        container_status1.ready = True
        container_status1.restart_count = 0

        container_status2 = MagicMock()
        container_status2.ready = True
        container_status2.restart_count = 2

        pod1.status.container_statuses = [container_status1, container_status2]

        pod_list = MagicMock()
        pod_list.items = [pod1]

        mock_api = MagicMock()
        mock_api.list_namespaced_pod.return_value = pod_list
        mock_api_class.return_value = mock_api

        result = k8s.list_pods("default")

        assert len(result) == 1
        assert result[0]["name"] == "nginx-pod"
        assert result[0]["status"] == "Running"
        assert result[0]["ready"] == 2
        assert result[0]["total_containers"] == 2
        assert result[0]["restarts"] == 2

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_pods_missing_kubeconfig(self, mock_load):
        """Test list_pods with missing kubeconfig."""
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")

        result = k8s.list_pods()

        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["type"] == "missing_kubeconfig"

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_pods_namespace_not_found(self, mock_api_class, mock_load):
        """Test list_pods with non-existent namespace."""
        mock_api = MagicMock()
        mock_api.list_namespaced_pod.side_effect = ApiException(status=404)
        mock_api_class.return_value = mock_api

        result = k8s.list_pods("nonexistent")

        assert result == []

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_pods_api_error(self, mock_api_class, mock_load):
        """Test list_pods with API error."""
        mock_api = MagicMock()
        mock_api.list_namespaced_pod.side_effect = ApiException(status=403)
        mock_api_class.return_value = mock_api

        result = k8s.list_pods()

        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["status"] == 403


class TestListServices:
    """Tests for list_services function."""

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_services_success(self, mock_api_class, mock_load):
        """Test listing services successfully."""
        svc1 = MagicMock()
        svc1.metadata.name = "nginx-svc"
        svc1.metadata.namespace = "default"
        svc1.spec.type = "ClusterIP"
        svc1.spec.cluster_ip = "10.0.0.1"
        svc1.spec.external_i_ps = None

        port = MagicMock()
        port.name = "http"
        port.protocol = "TCP"
        port.port = 80
        port.target_port = 8080

        svc1.spec.ports = [port]

        svc_list = MagicMock()
        svc_list.items = [svc1]

        mock_api = MagicMock()
        mock_api.list_namespaced_service.return_value = svc_list
        mock_api_class.return_value = mock_api

        result = k8s.list_services()

        assert len(result) == 1
        assert result[0]["name"] == "nginx-svc"
        assert result[0]["type"] == "ClusterIP"
        assert result[0]["cluster_ip"] == "10.0.0.1"
        assert len(result[0]["ports"]) == 1
        assert result[0]["ports"][0]["port"] == 80

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_services_missing_kubeconfig(self, mock_load):
        """Test list_services with missing kubeconfig."""
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")

        result = k8s.list_services()

        assert len(result) == 1
        assert result[0]["type"] == "missing_kubeconfig"


class TestListDeployments:
    """Tests for list_deployments function."""

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.AppsV1Api")
    def test_list_deployments_success(self, mock_api_class, mock_load):
        """Test listing deployments successfully."""
        deploy1 = MagicMock()
        deploy1.metadata.name = "nginx-deploy"
        deploy1.metadata.namespace = "default"
        deploy1.spec.replicas = 3
        deploy1.status.ready_replicas = 3
        deploy1.status.updated_replicas = 3
        deploy1.status.available_replicas = 3
        deploy1.spec.strategy.type = "RollingUpdate"

        deploy_list = MagicMock()
        deploy_list.items = [deploy1]

        mock_api = MagicMock()
        mock_api.list_namespaced_deployment.return_value = deploy_list
        mock_api_class.return_value = mock_api

        result = k8s.list_deployments()

        assert len(result) == 1
        assert result[0]["name"] == "nginx-deploy"
        assert result[0]["replicas"] == 3
        assert result[0]["ready_replicas"] == 3
        assert result[0]["strategy_type"] == "RollingUpdate"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_deployments_missing_kubeconfig(self, mock_load):
        """Test list_deployments with missing kubeconfig."""
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")

        result = k8s.list_deployments()

        assert len(result) == 1
        assert result[0]["type"] == "missing_kubeconfig"


class TestListConfigmaps:
    """Tests for list_configmaps function."""

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_configmaps_success(self, mock_api_class, mock_load):
        """Test listing configmaps successfully."""
        cm1 = MagicMock()
        cm1.metadata.name = "app-config"
        cm1.metadata.namespace = "default"
        cm1.data = {"app.properties": "key=value", "config.yaml": "yaml: content"}

        cm_list = MagicMock()
        cm_list.items = [cm1]

        mock_api = MagicMock()
        mock_api.list_namespaced_config_map.return_value = cm_list
        mock_api_class.return_value = mock_api

        result = k8s.list_configmaps()

        assert len(result) == 1
        assert result[0]["name"] == "app-config"
        assert result[0]["key_count"] == 2
        assert "app.properties" in result[0]["keys"]
        assert "config.yaml" in result[0]["keys"]

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_configmaps_empty(self, mock_api_class, mock_load):
        """Test listing configmaps with empty data."""
        cm1 = MagicMock()
        cm1.metadata.name = "empty-config"
        cm1.metadata.namespace = "default"
        cm1.data = None

        cm_list = MagicMock()
        cm_list.items = [cm1]

        mock_api = MagicMock()
        mock_api.list_namespaced_config_map.return_value = cm_list
        mock_api_class.return_value = mock_api

        result = k8s.list_configmaps()

        assert len(result) == 1
        assert result[0]["key_count"] == 0
        assert result[0]["keys"] == []


class TestDescribeResource:
    """Tests for describe_resource function."""

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_describe_pod(self, mock_api_class, mock_load):
        """Test describing a pod."""
        pod = MagicMock()
        pod.metadata.name = "test-pod"
        pod.metadata.namespace = "default"
        pod.status.phase = "Running"

        container = MagicMock()
        container.name = "nginx"
        container.image = "nginx:latest"
        container.ports = []
        pod.spec.containers = [container]
        pod.spec.restart_policy = "Always"

        condition = MagicMock()
        condition.type = "Ready"
        condition.status = "True"
        condition.reason = "PodCompleted"
        pod.status.conditions = [condition]

        mock_api = MagicMock()
        mock_api.read_namespaced_pod.return_value = pod
        mock_api_class.return_value = mock_api

        result = k8s.describe_resource("pod", "test-pod")

        assert result["name"] == "test-pod"
        assert result["status"] == "Running"
        assert result["spec"]["containers"][0]["name"] == "nginx"
        assert result["spec"]["restart_policy"] == "Always"

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_describe_service(self, mock_api_class, mock_load):
        """Test describing a service."""
        svc = MagicMock()
        svc.metadata.name = "nginx-svc"
        svc.metadata.namespace = "default"
        svc.spec.type = "LoadBalancer"
        svc.spec.cluster_ip = "10.0.0.1"
        svc.spec.external_i_ps = ["203.0.113.1"]
        svc.spec.ports = []
        svc.spec.selector = {"app": "nginx"}

        mock_api = MagicMock()
        mock_api.read_namespaced_service.return_value = svc
        mock_api_class.return_value = mock_api

        result = k8s.describe_resource("service", "nginx-svc")

        assert result["name"] == "nginx-svc"
        assert result["type"] == "LoadBalancer"
        assert result["selector"] == {"app": "nginx"}

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.AppsV1Api")
    def test_describe_deployment(self, mock_api_class, mock_load):
        """Test describing a deployment."""
        deploy = MagicMock()
        deploy.metadata.name = "nginx-deploy"
        deploy.metadata.namespace = "default"
        deploy.spec.replicas = 3
        deploy.status.ready_replicas = 2
        deploy.status.updated_replicas = 3
        deploy.status.available_replicas = 2
        deploy.spec.strategy.type = "RollingUpdate"
        deploy.spec.selector.match_labels = {"app": "nginx"}

        mock_api = MagicMock()
        mock_api.read_namespaced_deployment.return_value = deploy
        mock_api_class.return_value = mock_api

        result = k8s.describe_resource("deployment", "nginx-deploy")

        assert result["name"] == "nginx-deploy"
        assert result["replicas"] == 3
        assert result["status"]["ready_replicas"] == 2
        assert result["strategy"] == "RollingUpdate"

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_describe_configmap(self, mock_api_class, mock_load):
        """Test describing a configmap."""
        cm = MagicMock()
        cm.metadata.name = "app-config"
        cm.metadata.namespace = "default"
        cm.data = {"app.properties": "key=value"}

        mock_api = MagicMock()
        mock_api.read_namespaced_config_map.return_value = cm
        mock_api_class.return_value = mock_api

        result = k8s.describe_resource("configmap", "app-config")

        assert result["name"] == "app-config"
        assert result["data"] == {"app.properties": "key=value"}

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_describe_resource_not_found(self, mock_api_class, mock_load):
        """Test describing a resource that doesn't exist."""
        mock_api = MagicMock()
        mock_api.read_namespaced_pod.side_effect = ApiException(status=404)
        mock_api_class.return_value = mock_api

        result = k8s.describe_resource("pod", "nonexistent")

        assert result is None

    @patch("gantry.k8s.config.load_kube_config")
    def test_describe_resource_missing_kubeconfig(self, mock_load):
        """Test describe_resource with missing kubeconfig."""
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")

        result = k8s.describe_resource("pod", "test-pod")

        assert "error" in result
        assert result["type"] == "missing_kubeconfig"

    @patch("gantry.k8s.config.load_kube_config")
    def test_describe_resource_unsupported_type(self, mock_load):
        """Test describe_resource with unsupported resource type."""
        result = k8s.describe_resource("unsupported", "name")

        assert "error" in result
        assert result["type"] == "unsupported_resource_type"
