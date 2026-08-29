"""
name: index.py
description: Vercel Serverless Function entrypoint for FastAPI backend.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Redirect HOME to /tmp in Serverless environment
_tmp_dir = tempfile.gettempdir()
os.environ.setdefault("HOME", _tmp_dir)
os.environ.setdefault("MPLCONFIGDIR", _tmp_dir)
os.environ.setdefault("XDG_CACHE_HOME", os.path.join(_tmp_dir, ".cache"))
os.environ.setdefault("XDG_CONFIG_HOME", os.path.join(_tmp_dir, ".config"))

# Add backend directory and root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from app.main import app
