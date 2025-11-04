"""Configuration files for VLM mission environments."""

from __future__ import annotations

import os
from pathlib import Path

# Get the directory where config files are located
CONFIG_DIR = Path(__file__).parent

__all__ = ["CONFIG_DIR"]
