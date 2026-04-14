"""Screen components for Gantry TUI."""

from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Label


class ClusterScreen(Screen):
    """Screen for Kubernetes cluster exploration and management."""

    BINDINGS = [
        ("tab", "switch_screen('helm')", "Switch to Helm View"),
        ("q", "quit", "Quit Gantry"),
    ]

    def compose(self):
        """Compose the cluster screen."""
        yield Container(
            Label("Cluster View", id="cluster-label"),
            id="cluster-container",
        )

    def on_mount(self) -> None:
        """Initialize cluster screen on mount."""
        self.title = "Gantry - Cluster Management"


class HelmScreen(Screen):
    """Screen for Helm chart exploration and deployment."""

    BINDINGS = [
        ("tab", "switch_screen('cluster')", "Switch to Cluster View"),
        ("q", "quit", "Quit Gantry"),
    ]

    def compose(self):
        """Compose the helm screen."""
        yield Container(
            Label("Helm View", id="helm-label"),
            id="helm-container",
        )

    def on_mount(self) -> None:
        """Initialize helm screen on mount."""
        self.title = "Gantry - Helm Orchestration"
