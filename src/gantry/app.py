"""Main Gantry application - Kubernetes TUI."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from textual import work
from textual.app import App


class GantryApp(App):
    """Main Gantry application."""

    TITLE = "Gantry"
    SUBTITLE = "Kubernetes Cluster Management & Helm Orchestration"

    CSS = """
    Screen {
        background: $surface;
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Container(
            Static("Gantry - Kubernetes TUI", classes="header"),
            id="main",
        )

    def on_mount(self) -> None:
        """Initialize the application on mount."""
        self.title = self.TITLE
        self.sub_title = self.SUBTITLE
