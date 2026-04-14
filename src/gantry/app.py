"""Main Gantry application - Kubernetes TUI."""

from textual.app import ComposeResult
from textual.app import App
from textual.widgets import Header, Footer
from textual.binding import Binding

from gantry.screens import ClusterScreen, HelmScreen


class GantryApp(App):
    """Main Gantry application."""

    TITLE = "Gantry"
    SUBTITLE = "Kubernetes Cluster Management & Helm Orchestration"

    BINDINGS = [
        Binding("tab", "switch_screen", "Switch View", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    CSS = """
    Screen {
        background: $surface;
        color: $text;
    }

    Header {
        background: $boost;
        color: $text;
        height: 1;
    }

    Footer {
        background: $boost;
        color: $text;
        height: auto;
    }

    #cluster-label,
    #helm-label {
        width: 100%;
        height: 100%;
        content-align: center middle;
    }

    #cluster-container,
    #helm-container {
        width: 100%;
        height: 1fr;
    }
    """

    SCREENS = {
        "cluster": ClusterScreen,
        "helm": HelmScreen,
    }

    def on_mount(self) -> None:
        """Initialize the application on mount."""
        self.title = self.TITLE
        self.sub_title = self.SUBTITLE
        # Push the cluster screen as the initial screen
        self.push_screen("cluster")

    def action_switch_screen(self) -> None:
        """Switch between Cluster and Helm screens."""
        active_screen = self.screen
        if isinstance(active_screen, ClusterScreen):
            self.switch_screen("helm")
        else:
            self.switch_screen("cluster")
