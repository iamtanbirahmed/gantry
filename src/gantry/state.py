"""State persistence for Gantry - saves/loads context and namespace selections."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_STATE_FILE = Path.home() / ".config" / "gantry" / "state.json"


def load_state() -> dict:
    """
    Load persisted context and namespace from state file.

    Returns a dict with 'context' and 'namespace' keys, or empty dict if file doesn't exist or is invalid.
    """
    try:
        if _STATE_FILE.exists():
            data = json.loads(_STATE_FILE.read_text())
            if isinstance(data, dict):
                return data
    except Exception as e:
        logger.debug(f"Could not load state: {e}")
    return {}


def save_state(context: str, namespace: str) -> None:
    """
    Save current context and namespace to state file.

    Args:
        context: Kubernetes context name to persist
        namespace: Kubernetes namespace to persist
    """
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps({"context": context, "namespace": namespace}))
        logger.debug(f"State saved: context={context}, namespace={namespace}")
    except Exception as e:
        logger.debug(f"Could not save state: {e}")
