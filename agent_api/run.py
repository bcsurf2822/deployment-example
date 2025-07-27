#!/usr/bin/env python
"""
Run script for the Pydantic AI agent.
This script handles imports properly when running the agent directly.
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
# This is necessary to import local modules when running the script directly
sys.path.insert(0, str(Path(__file__).parent))

from agent import main

if __name__ == "__main__":
    main()