#!/usr/bin/env python3
"""
Lark Grammar Parser with CST Unparsing Support
Tests Natural Language Specification DSL against documents
Includes roundtrip validation and unparsing capabilities
"""

from lark import Lark, Tree, Token, exceptions
import sys
import os
import argparse
from pathlib import Path
import logging
from typing import Union, Optional

for parent in Path(__file__).parents:
  if (parent / ".git").exists():
    CONTEXT = parent
    break
else:
  CONTEXT = os.environ.get("CONTEXT", None)
  if CONTEXT is None:
    print("couldn't find project root, export CONTEXT & try again", file=sys.stderr)
    sys.stderr.flush()
    raise SystemExit(1)

assert isinstance(CONTEXT, Path)


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


# ============ CST Unparsing ============
class CSTUnparser:
  """Unparses a Lark CST back to its original text representation."""

  def __init__(self, tree: Tree):
    """Initialize with a parsed CST."""
    self.tree = tree

  def unparse(self) -> str:
    """Reconstruct the original document from the CST."""
    return self._unparse_node(self.tree)

  def _unparse_node(self, node: Union[Tree, Token]) -> str:
    """Recursively unparse a tree node or token."""
    if isinstance(node, Token):
      return str(node)
    elif isinstance(node, Tree):
      return "".join(self._unparse_node(child) for child in node.children)
    else:
      return str(node)


def unparse_cst(tree: Tree) -> str:
  """Convenience function to unparse a CST tree."""
  return CSTUnparser(tree).unparse()


def validate_roundtrip(original: str, tree: Tree) -> tuple[bool, Optional[str]]:
  """
  Validate that unparsing produces the exact original text.

  Returns:
    (success, error_message): success is True if roundtrip succeeds
  """
  unparsed = unparse_cst(tree)

  if original == unparsed:
    return True, None

  # Generate detailed diff
  import difflib

  diff_lines = list(
    difflib.unified_diff(
      original.splitlines(keepends=True),
      unparsed.splitlines(keepends=True),
      fromfile="original",
      tofile="unparsed",
      n=3,
    )
  )

  diff_text = "".join(diff_lines) if diff_lines else "No line differences, but texts differ"
  return False, diff_text


# ============ Tree Printing ============
def print_tree(tree, indent=0):
  """Recursively print parse tree."""
  if isinstance(tree, Tree):
    print("  " * indent + f"[{tree.data}]")
    for child in tree.children:
      print_tree(child, indent + 1)
  elif logger.isEnabledFor(logging.DEBUG):
    value = repr(str(tree))
    if len(value) > 50:
      value = value[:47] + "..." + value[0]

    prefix = f"Token({tree.type}): " if hasattr(tree, "type") else ""
    print("  " * indent + f"{prefix}{value}")


def handle_parse_error(e, content):
  """Unified error handler for parse exceptions."""
  if isinstance(e, exceptions.UnexpectedCharacters):
    logger.error("\nParse Error - Unexpected Character:")
    logger.error(f"  Line {e.line}, Column {e.column}")
    if hasattr(e, "allowed") and e.allowed:
      logger.error(f"  Expected: {', '.join(sorted(e.allowed))}")
    logger.error(f"  Context: {e.get_context(content)}")

    if logger.isEnabledFor(logging.DEBUG) and e.line > 0:
      lines = content.splitlines()
      if e.line - 1 < len(lines):
        logger.debug(f"\n  {lines[e.line - 1]}")
        logger.debug(f"  {' ' * (e.column - 1)}^")

  elif isinstance(e, exceptions.UnexpectedToken):
    logger.error("\nParse Error - Unexpected Token:")
    logger.error(f"  Token: {e.token} at line {e.line}, column {e.column}")
    if hasattr(e, "expected") and e.expected:
      logger.error(f"  Expected: {', '.join(sorted(e.expected))}")

  else:
    logger.error(f"\nParse Error: {type(e).__name__}: {e}")
    if logger.isEnabledFor(logging.DEBUG):
      logger.exception("Stack trace:")


# ============ Main Processing ============
def process_document(grammar_path, document_path, unparse=False, roundtrip=False):
  """Parse document with grammar and optionally unparse or validate roundtrip."""
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
    logger.info("\n✓ Document parsed successfully!")

    # Show parse tree
    if not unparse and not roundtrip:
      logger.info("\nParse Tree:")
      logger.info("-" * 50)
      print_tree(tree)

      if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"\nTotal nodes: {sum(1 for _ in tree.iter_subtrees())}")

    # Unparse mode
    if unparse:
      logger.info("\n[Unparsing CST]")
      unparsed = unparse_cst(tree)
      logger.info("✓ CST unparsed successfully")
      logger.info(f"Unparsed document: {len(unparsed)} chars")
      print("\n" + "=" * 50 + " UNPARSED OUTPUT " + "=" * 50)
      print(unparsed)
      print("=" * 117)

    # Roundtrip validation
    if roundtrip:
      logger.info("\n[Validating Roundtrip]")
      success, error = validate_roundtrip(content, tree)

      if success:
        logger.info("✓ Roundtrip validation passed!")
        logger.info("  Original and unparsed documents are identical")
      else:
        logger.error("Roundtrip validation failed!")
        logger.error(f"  Original length: {len(content)} chars")
        unparsed = unparse_cst(tree)
        logger.error(f"  Unparsed length: {len(unparsed)} chars")

        if error and not logger.isEnabledFor(logging.DEBUG):
          logger.error("\n  Run with --debug to see differences")
        elif error:
          logger.debug("\nDifferences:")
          print(error)

        return False

    return True

  except FileNotFoundError as e:
    logger.error(f"File not found: {e.filename}")
    return False

  except Exception as e:
    if hasattr(e, "get_context"):
      handle_parse_error(e, content if "content" in locals() else "")
    else:
      logger.error(f"Grammar error: {e}")
      if logger.isEnabledFor(logging.DEBUG) and "grammar" in locals():
        logger.debug("\nGrammar content:")
        logger.debug("=" * 50)
        logger.debug(grammar[:500] + "..." if len(grammar) > 500 else grammar)
    return False


def main():
  parser = argparse.ArgumentParser(
    description="Parse and unparse Natural Language Specification DSL documents",
    epilog="Examples:\n"
    "  %(prog)s                           # Parse with default files\n"
    "  %(prog)s --unparse                 # Parse and unparse document\n"
    "  %(prog)s --roundtrip               # Validate parse/unparse roundtrip\n"
    "  %(prog)s custom.dsl --debug        # Debug custom document",
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )

  parser.add_argument("document", type=Path, nargs="?", default=CONTEXT / "spec/example.dsl", help="Document to parse")
  parser.add_argument("-g", "--grammar", type=Path, default=CONTEXT / "grammar/TLA.lark", help="Lark grammar file")
  parser.add_argument("-u", "--unparse", action="store_true", help="Unparse the CST back to text")
  parser.add_argument("-r", "--roundtrip", action="store_true", help="Validate parse/unparse roundtrip")
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

  # Run processing
  success = process_document(args.grammar, args.document, unparse=args.unparse, roundtrip=args.roundtrip)
  sys.exit(0 if success else 1)


if __name__ == "__main__":
  main()
