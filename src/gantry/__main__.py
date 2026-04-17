"""Entry point for Gantry TUI application."""

import argparse
import logging
import sys
from pathlib import Path

from gantry.app import GantryApp


def setup_logging(debug: bool, log_path: Path) -> None:
    """Configure logging to file.

    Args:
        debug: If True, set logging level to DEBUG. Otherwise, WARNING.
        log_path: Path to write log file to.
    """
    level = logging.DEBUG if debug else logging.WARNING

    # Get root logger and configure
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Only attach file handler when debug is enabled
    if debug:
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Configure file handler
        file_handler = logging.FileHandler(log_path, mode="a")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def main() -> None:
    """Launch the Gantry application."""
    parser = argparse.ArgumentParser(description="Gantry - Kubernetes TUI")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to gantry.log",
    )

    args = parser.parse_args()

    # Resolve log file path to project root
    log_path = Path(__file__).resolve().parents[2] / "gantry.log"

    # Setup logging
    setup_logging(args.debug, log_path)
    logger = logging.getLogger(__name__)

    logger.info(f"Gantry starting (debug={args.debug}, log_file={log_path})")

    try:
        app = GantryApp()
        app.run()
    except Exception as e:
        logger.exception(f"Crash in GantryApp: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
