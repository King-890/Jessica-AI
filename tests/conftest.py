import os
import sys

# Ensure project root is on sys.path for imports in test environment
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)