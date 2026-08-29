"""
name: index.py
description: Vercel Serverless Function entrypoint for FastAPI backend.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory and root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.main import app
