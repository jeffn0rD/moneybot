#!/usr/bin/env python3
from __future__ import annotations
import sys
import os
from pathlib import Path

# Add the project root to Python path for cross-platform compatibility
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from libs.models.train_meta import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())