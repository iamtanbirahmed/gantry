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
        # Mock context dicts (as returned by kubernetes library)
        ctx1 = {
            "name": "minikube",
            "context": {
                "cluster": "minikube",
                "user": "minikube",
                "namespace": "default"
            }
        }

        ctx2 = {
            "name": "docker-desktop",
            "context": {
                "cluster": "docker-desktop",
                "user": "docker-desktop"
            }
        }

        active_ctx = {"name": "minikube"}

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


class TestListReplicaSets:
    """Tests for list_replicasets function."""

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
        assert len(result) == 1
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


class TestListStatefulSets:
    """Tests for list_statefulsets function."""

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


class TestListDaemonSets:
    """Tests for list_daemonsets function."""

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


class TestListJobs:
    """Tests for list_jobs function."""

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

        assert len(result) == 1
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


class TestListCronJobs:
    """Tests for list_cronjobs function."""

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

        assert len(result) == 1
        assert result[0]["name"] == "daily-backup"
        assert result[0]["schedule"] == "0 2 * * *"
        assert result[0]["last_run"] == "Never"
        assert result[0]["active"] == 0

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_cronjobs_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_cronjobs()
        assert result[0]["type"] == "missing_kubeconfig"


class TestListIngresses:
    """Tests for list_ingresses function."""

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

        assert len(result) == 1
        assert result[0]["name"] == "app-ingress"
        assert result[0]["class"] == "nginx"
        assert result[0]["hosts"] == "app.example.com"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_ingresses_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_ingresses()
        assert result[0]["type"] == "missing_kubeconfig"


class TestListEndpoints:
    """Tests for list_endpoints function."""

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

        assert len(result) == 1
        assert result[0]["name"] == "nginx-svc"
        assert result[0]["endpoints"] == "2"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_endpoints_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_endpoints()
        assert result[0]["type"] == "missing_kubeconfig"


class TestListSecrets:
    """Tests for list_secrets function."""

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

        assert len(result) == 1
        assert result[0]["name"] == "db-secret"
        assert result[0]["type"] == "Opaque"
        assert result[0]["keys"] == 2

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_secrets_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_secrets()
        assert result[0]["type"] == "missing_kubeconfig"


class TestListPersistentVolumeClaims:
    """Tests for list_persistentvolumeclaims function."""

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

        assert len(result) == 1
        assert result[0]["name"] == "data-pvc"
        assert result[0]["status"] == "Bound"
        assert result[0]["volume"] == "pv-001"
        assert result[0]["capacity"] == "10Gi"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_pvcs_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_persistentvolumeclaims()
        assert result[0]["type"] == "missing_kubeconfig"


class TestListPersistentVolumes:
    """Tests for list_persistentvolumes function (cluster-scoped)."""

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

        assert len(result) == 1
        assert result[0]["name"] == "pv-001"
        assert result[0]["capacity"] == "10Gi"
        assert result[0]["access_modes"] == "ReadWriteOnce"
        assert result[0]["status"] == "Available"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_pvs_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_persistentvolumes()
        assert result[0]["type"] == "missing_kubeconfig"


class TestListNamespaceResources:
    """Tests for list_namespace_resources function (cluster-scoped)."""

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

        assert len(result) == 1
        assert result[0]["name"] == "default"
        assert result[0]["status"] == "Active"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_namespace_resources_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_namespace_resources()
        assert result[0]["type"] == "missing_kubeconfig"


class TestListNodes:
    """Tests for list_nodes function (cluster-scoped)."""

    @patch("gantry.k8s.config.load_kube_config")
    @patch("gantry.k8s.client.CoreV1Api")
    def test_list_nodes_success(self, mock_api_class, mock_load):
        node1 = MagicMock()
        node1.metadata.name = "minikube"
        node1.metadata.labels = {
            "node-role.kubernetes.io/control-plane": "",
        }
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

        assert len(result) == 1
        assert result[0]["name"] == "minikube"
        assert result[0]["status"] == "Ready"
        assert "control-plane" in result[0]["roles"]
        assert result[0]["version"] == "v1.28.0"

    @patch("gantry.k8s.config.load_kube_config")
    def test_list_nodes_missing_kubeconfig(self, mock_load):
        mock_load.side_effect = config.config_exception.ConfigException("No kubeconfig")
        result = k8s.list_nodes()
        assert result[0]["type"] == "missing_kubeconfig"
