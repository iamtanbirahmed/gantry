"""Entry point for Gantry TUI application."""

from gantry.app import GantryApp


def main() -> None:
    """Launch the Gantry application."""
    app = GantryApp()
    app.run()


if __name__ == "__main__":
    main()
