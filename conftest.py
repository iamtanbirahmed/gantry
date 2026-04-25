"""
Conftest to ensure the worktree's src is loaded, not any installed package.
This is needed when the test runner (e.g. system pytest) uses a Python
interpreter that has an editable install of gantry from a different path.
"""
import sys
import os

# Prepend the worktree's src directory so it takes precedence over any
# system-level editable install pointing to the main repo.
_worktree_src = os.path.join(os.path.dirname(__file__), "src")
if _worktree_src not in sys.path:
    sys.path.insert(0, _worktree_src)

# Evict any already-cached gantry modules so the above path takes effect.
for _key in list(sys.modules):
    if _key == "gantry" or _key.startswith("gantry."):
        del sys.modules[_key]
