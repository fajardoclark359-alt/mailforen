"""Shared pytest fixtures.

Isolates the mailforen data directory (SQLite DB, reports) into a temp dir
for every test session so tests never touch ~/.mailforen.
"""

import os
import tempfile

# Must be set before mailforen.core.config is imported.
_TEST_DIR = tempfile.mkdtemp(prefix="mailforen-test-")
os.environ.setdefault("MAILFOREN_DATA_DIR", _TEST_DIR)

# Deterministic, network-free GUI tests.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
