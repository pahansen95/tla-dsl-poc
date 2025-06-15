#!/usr/bin/env python3
"""
Lark Grammar Test Parser - Minimal Version
Tests Natural Language Specification DSL against documents
"""

from lark import Lark, Tree, exceptions
import sys
import argparse
from pathlib import Path
import logging

CONTEXT = Path(__file__).parent


# Configure logging
class CompactFormatter(logging.Formatter):
  """Compact log formatter with level-specific prefixes."""

  FORMATS = {
    logging.INFO: "%(message)s",
    logging.WARNING: "⚠ %(message)s",
    logging.ERROR: "✗ %(message)s",
    logging.DEBUG: "%(asctime)s [%(levelname)s] %(message)s",
  }

  def format(self, record):
    fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
    return logging.Formatter(fmt, datefmt="%H:%M:%S").format(record)


def setup_logging(level):
  """Configure minimal logging."""
  logger = logging.getLogger()
  logger.setLevel(level)
  logger.handlers.clear()

  handler = logging.StreamHandler(sys.stdout)
  handler.setFormatter(CompactFormatter())
  logger.addHandler(handler)

  return logger


logger = logging.getLogger(__name__)


def print_tree(tree, indent=0):
  """Recursively print parse tree."""
  if isinstance(tree, Tree):
    print("  " * indent + f"[{tree.data}]")
    for child in tree.children:
      print_tree(child, indent + 1)
  elif logger.isEnabledFor(logging.DEBUG):
    value = str(tree)[:50] + "..." if len(str(tree)) > 50 else str(tree)
    prefix = f"Token({tree.type}): " if hasattr(tree, "type") else ""
    print("  " * indent + f'{prefix}"{value}"')


def handle_parse_error(e, content):
  """Unified error handler for parse exceptions."""
  if isinstance(e, exceptions.UnexpectedCharacters):
    logger.error("\nParse Error - Unexpected Character:")
    logger.error(f"  Line {e.line}, Column {e.column}")
    logger.error(f"  Expected: {e.expected}")
    logger.error(f"  Context: {e.get_context(content)}")

    if logger.isEnabledFor(logging.DEBUG) and e.line > 0:
      lines = content.splitlines()
      if e.line - 1 < len(lines):
        logger.debug(f"\n  {lines[e.line - 1]}")
        logger.debug(f"  {' ' * (e.column - 1)}^")

  elif isinstance(e, exceptions.UnexpectedToken):
    logger.error("\nParse Error - Unexpected Token:")
    logger.error(f"  Token: {e.token} at line {e.line}, column {e.column}")
    logger.error(f"  Expected: {e.expected}")

  else:
    logger.error(f"\nParse Error: {type(e).__name__}: {e}")
    if logger.isEnabledFor(logging.DEBUG):
      logger.exception("Stack trace:")


def validate_grammar(grammar_path, document_path):
  """Parse document with grammar and report results."""
  logger.info(f"Grammar File: {grammar_path}")
  logger.info(f"Test Document: {document_path}")
  logger.info("=" * 70)

  try:
    # Load grammar
    logger.info(f"\n[Loading Grammar: {grammar_path}]")
    with open(grammar_path) as f:
      grammar = f.read()
    logger.info(f"Read {len(grammar)} characters")

    # Create parser
    logger.info("\n[Creating Parser]")
    parser = Lark(
      grammar,
      start="specification",
      parser="earley",
      debug=logger.isEnabledFor(logging.DEBUG),
      ambiguity="resolve",
      keep_all_tokens=True,
    )
    logger.info("✓ Parser created successfully")

    # Parse document
    logger.info(f"\n[Parsing Document: {document_path}]")
    with open(document_path) as f:
      content = f.read()
    logger.info(f"Document: {len(content)} chars, {len(content.splitlines())} lines")

    tree = parser.parse(content)

    # Success
    logger.info("\n✓ Document parsed successfully!")
    logger.info("\nParse Tree:")
    logger.info("-" * 50)
    print_tree(tree)

    if logger.isEnabledFor(logging.DEBUG):
      logger.debug(f"\nTotal nodes: {sum(1 for _ in tree.iter_subtrees())}")

    return True

  except FileNotFoundError as e:
    logger.error(f"File not found: {e.filename}")
    return False

  except Exception as e:
    if hasattr(e, "get_context"):  # Parse error
      handle_parse_error(e, content if "content" in locals() else "")
    else:  # Grammar error
      logger.error(f"Grammar error: {e}")
      if logger.isEnabledFor(logging.DEBUG) and "grammar" in locals():
        logger.debug("\nGrammar content:")
        logger.debug("=" * 50)
        logger.debug(grammar[:500] + "..." if len(grammar) > 500 else grammar)
    return False


def main():
  parser = argparse.ArgumentParser(
    description="Test Lark grammar against specification documents",
    epilog="Examples:\n"
    "  %(prog)s                    # Use defaults\n"
    "  %(prog)s --debug            # Show debug output\n"
    "  %(prog)s custom.lark spec.tla",
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )

  parser.add_argument("grammar", type=Path, nargs="?", default=CONTEXT / "grammar/TLA.lark", help="Lark grammar file")
  parser.add_argument("document", type=Path, nargs="?", default=CONTEXT / "spec/example.tla", help="Document to parse")
  parser.add_argument("-d", "--debug", action="store_true", help="Show debug output")
  parser.add_argument("-q", "--quiet", action="store_true", help="Minimal output")

  args = parser.parse_args()

  # Set log level
  level = logging.DEBUG if args.debug else logging.WARNING if args.quiet else logging.INFO
  setup_logging(level)

  # Validate files exist
  for path, name in [(args.grammar, "Grammar"), (args.document, "Document")]:
    if not path.exists():
      logger.critical(f"{name} file not found: {path}")
      sys.exit(1)

  # Run validation
  sys.exit(0 if validate_grammar(args.grammar, args.document) else 1)


if __name__ == "__main__":
  main()
