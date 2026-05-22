import os
import sys

# Ensure the project root is on the path so 'src' and 'config' are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import app  # noqa: E402 — must come after sys.path setup
