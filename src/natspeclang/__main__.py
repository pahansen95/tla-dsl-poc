"""
Natural Specification Language CLI entry point.

Allows the package to be executed as a module:
    python -m nsl [arguments]
"""

if __name__ == "__main__":
  import sys
  from observability import SharedContext

  SharedContext.setup()
  from .cli import main

  sys.exit(main())
