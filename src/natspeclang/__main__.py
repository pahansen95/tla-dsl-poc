"""
Natural Specification Language CLI entry point.

Allows the package to be executed as a module:
    python -m nsl [arguments]
"""

import sys
from .cli import main

if __name__ == "__main__":
  sys.exit(main())
