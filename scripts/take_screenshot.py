#!/usr/bin/env python
"""Take a screenshot of the Gantry app and save it as SVG."""

import asyncio
import sys
import logging
from pathlib import Path

# Suppress error logging from background workers
logging.getLogger("gantry.screens").setLevel(logging.CRITICAL)

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from gantry.app import GantryApp


async def take_screenshot(output_path: str) -> None:
    """Run the app and export a screenshot."""
    app = GantryApp()

    try:
        async with app.run_test(headless=True) as pilot:
            await asyncio.sleep(0.5)  # Give app time to render

            # Export as SVG
            svg_output = app.export_screenshot(title="Gantry")

            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(svg_output)

            print(f"Screenshot saved to {output_path}")
    except Exception as e:
        print(f"Error taking screenshot: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "docs/images/screenshot.svg"
    asyncio.run(take_screenshot(output))
