#!/usr/bin/env python3
"""
DSL Parser CLI Interface - With AST Integration

This version includes AST functionality for semantic analysis and
transformation of DSL documents. New operations include AST building,
serialization, and reformatting through AST transformation.
"""

import sys
import os
import argparse
from pathlib import Path
import logging
from typing import Callable
import difflib

# Import core functionality
from core.parser import create_parser, parse_document
from core.unparser import unparse_tree
from core.syntax import serialize_cst, deserialize_cst

# Import AST functionality
from core.ast import build_ast, format_ast, serialize_ast, Specification

from lark import Tree, Token, exceptions


# ============ Common Infrastructure ============
class ParseContext:
  """
  Encapsulates common parsing operations and state management.

  This class eliminates duplicate file loading, parser creation,
  and document parsing code that was repeated across all handler functions.
  """

  def __init__(self, grammar_path: Path, document_path: Path, debug: bool = False):
    self.grammar_path = grammar_path
    self.document_path = document_path
    self.grammar = None
    self.document = None
    self.parser = None
    self.tree = None
    self.debug = debug

  def load_files(self):
    """Load grammar and document files."""
    self.grammar = self.grammar_path.read_text()
    self.document = self.document_path.read_text()
    return self

  def create_parser(self):
    """Create parser from loaded grammar."""
    self.parser = create_parser(self.grammar, debug=self.debug)
    return self

  def parse(self):
    """Parse document with created parser."""
    self.tree = parse_document(self.parser, self.document)
    return self

  def execute(self):
    """Execute full parsing pipeline with method chaining."""
    return self.load_files().create_parser().parse()


def with_error_handling(operation_name: str):
  """
  Decorator for consistent error handling across all operations.

  Eliminates duplicate try/except blocks and provides uniform error
  formatting for parse errors and general exceptions.
  """

  def decorator(func: Callable) -> Callable:
    def wrapper(*args, **kwargs) -> bool:
      try:
        return func(*args, **kwargs)
      except exceptions.ParseError as e:
        # Format parse error with context
        logger.error(f"\nParse Error in {operation_name}:")
        if hasattr(e, "line"):
          logger.error(f"  Line {e.line}, Column {getattr(e, 'column', '?')}")

        # Try to get context from ParseContext if available
        if args and isinstance(args[0], ParseContext) and hasattr(e, "get_context"):
          ctx = args[0]
          if ctx.document:
            logger.error(f"  Context: {e.get_context(ctx.document)}")

        logger.error(f"  {e}")
        return False
      except Exception as e:
        logger.error(f"Error in {operation_name}: {e}")
        return False

    return wrapper

  return decorator


# ============ Utility Functions ============
def show_diff(text1: str, text2: str, label1: str, label2: str):
  """Display unified diff between two texts."""
  diff = difflib.unified_diff(
    text1.splitlines(keepends=True), text2.splitlines(keepends=True), fromfile=label1, tofile=label2
  )
  print("\nDifferences:")
  print("".join(diff))


def print_tree(tree: Tree, indent: int = 0):
  """Display parse tree structure with optional token details."""
  if isinstance(tree, Tree):
    print("  " * indent + f"[{tree.data}]")
    for child in tree.children:
      print_tree(child, indent + 1)
  elif isinstance(tree, Token) and logger.isEnabledFor(logging.DEBUG):
    value = repr(str(tree))
    if len(value) > 50:
      value = value[:47] + "..."
    print("  " * indent + f"Token: {value}")


def print_ast(ast: Specification, indent: int = 0):
  """Display AST structure in readable format."""

  def print_node(node, level):
    indent_str = "  " * level
    if isinstance(node, list):
      for item in node:
        print_node(item, level)
    elif hasattr(node, "__dict__"):
      # Print node type
      print(f"{indent_str}{node.__class__.__name__}:")
      # Print attributes
      for key, value in node.__dict__.items():
        if key.startswith("_") or key == "source_location":
          continue
        if isinstance(value, list) and value:
          print(f"{indent_str}  {key}:")
          for item in value:
            if hasattr(item, "__class__"):
              print_node(item, level + 2)
            else:
              print(f"{indent_str}    - {item}")
        elif hasattr(value, "__dict__"):
          print(f"{indent_str}  {key}:")
          print_node(value, level + 2)
        elif value:
          print(f"{indent_str}  {key}: {value}")

  print_node(ast, indent)


def find_project_root() -> Path:
  """Find project root by looking for .git directory or using CONTEXT env var."""
  for parent in Path(__file__).parents:
    if (parent / ".git").exists():
      return parent

  if context := os.environ.get("CONTEXT"):
    return Path(context)

  print("couldn't find project root, export CONTEXT & try again", file=sys.stderr)
  raise SystemExit(1)


# ============ Operation Handlers ============
@with_error_handling("parse")
def handle_parse(ctx: ParseContext) -> bool:
  """Parse and display tree structure."""
  ctx.execute()
  logger.info("✓ Document parsed successfully")
  print("\nParse Tree:")
  print("-" * 50)
  print_tree(ctx.tree)
  return True


@with_error_handling("unparse")
def handle_unparse(ctx: ParseContext) -> bool:
  """Parse and unparse document."""
  ctx.execute()
  unparsed = unparse_tree(ctx.tree)
  logger.info("✓ Document unparsed successfully")
  print(unparsed)
  return True


@with_error_handling("serialize")
def handle_serialize(ctx: ParseContext) -> bool:
  """Parse and serialize to JSON."""
  ctx.execute()
  json_output = serialize_cst(ctx.tree)
  logger.info("✓ CST serialized successfully")
  print(json_output)
  return True


@with_error_handling("roundtrip")
def handle_roundtrip(ctx: ParseContext) -> bool:
  """Validate parse/unparse roundtrip."""
  ctx.execute()

  # Test unparsing roundtrip
  unparsed = unparse_tree(ctx.tree)
  if ctx.document != unparsed:
    logger.error("✗ Unparsing roundtrip failed")
    logger.error(f"  Original: {len(ctx.document)} chars")
    logger.error(f"  Unparsed: {len(unparsed)} chars")

    if logger.isEnabledFor(logging.DEBUG):
      show_diff(ctx.document, unparsed, "original", "unparsed")
    return False

  # Test serialization roundtrip
  json_str = serialize_cst(ctx.tree)
  restored = deserialize_cst(json_str)
  restored_text = unparse_tree(restored)

  if ctx.document != restored_text:
    logger.error("✗ Serialization roundtrip failed")
    return False

  logger.info("✓ Roundtrip validation passed")
  return True


@with_error_handling("validate")
def handle_validate_against(ctx: ParseContext, comparison_path: Path) -> bool:
  """Validate unparsed CST against another document."""
  ctx.execute()
  unparsed = unparse_tree(ctx.tree)
  comparison = comparison_path.read_text()

  # Normalize line endings for cross-platform comparison
  unparsed_n = unparsed.replace("\r\n", "\n")
  comparison_n = comparison.replace("\r\n", "\n")

  if unparsed_n == comparison_n:
    logger.info("✓ Validation passed - documents are equivalent")
    return True
  else:
    logger.error("✗ Validation failed - documents differ")
    logger.error(f"  Unparsed: {len(unparsed)} chars")
    logger.error(f"  Comparison: {len(comparison)} chars")
    show_diff(unparsed, comparison, "unparsed", "comparison")
    return False


# ============ AST Operation Handlers ============
@with_error_handling("ast")
def handle_ast(ctx: ParseContext) -> bool:
  """Build and display AST structure."""
  ctx.execute()
  ast = build_ast(ctx.tree)
  logger.info("✓ AST built successfully")
  print("\nAbstract Syntax Tree:")
  print("-" * 50)
  print_ast(ast)
  return True


@with_error_handling("serialize-ast")
def handle_serialize_ast(ctx: ParseContext) -> bool:
  """Build AST and serialize to JSON."""
  ctx.execute()
  ast = build_ast(ctx.tree)
  json_output = serialize_ast(ast)
  logger.info("✓ AST serialized successfully")
  print(json_output)
  return True


@with_error_handling("reformat")
def handle_reformat(ctx: ParseContext) -> bool:
  """Reformat document through AST transformation."""
  ctx.execute()
  ast = build_ast(ctx.tree)
  reformatted_cst = format_ast(ast)
  reformatted_text = unparse_tree(reformatted_cst)
  logger.info("✓ Document reformatted through AST")
  print(reformatted_text)
  return True


@with_error_handling("ast-roundtrip")
def handle_ast_roundtrip(ctx: ParseContext) -> bool:
  """Validate CST → AST → CST roundtrip."""
  ctx.execute()

  # Build AST from CST
  ast = build_ast(ctx.tree)

  # Format AST back to CST
  formatted_cst = format_ast(ast)
  formatted_text = unparse_tree(formatted_cst)

  # Parse the formatted text to get normalized CST
  formatted_tree = parse_document(ctx.parser, formatted_text)

  # Build AST from formatted CST
  ast2 = build_ast(formatted_tree)

  # Compare AST representations
  if repr(ast) != repr(ast2):
    logger.error("✗ AST roundtrip failed - semantic difference")
    return False

  logger.info("✓ AST roundtrip validation passed")
  return True


# ============ Logging Setup ============
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


def setup_logging(level: int) -> logging.Logger:
  """Configure logging with appropriate level and format."""
  logger = logging.getLogger()
  logger.setLevel(level)
  logger.handlers.clear()

  handler = logging.StreamHandler(sys.stdout)
  handler.setFormatter(CompactFormatter())
  logger.addHandler(handler)

  return logger


logger = logging.getLogger(__name__)


# ============ CLI Interface ============
def main():
  """Main entry point with routing table pattern."""
  root = find_project_root()

  # Setup argument parser
  parser = argparse.ArgumentParser(
    description="Parse Natural Language Specification DSL documents",
    epilog="Examples:\n"
    "  %(prog)s                    # Parse default example\n"
    "  %(prog)s --unparse          # Unparse to stdout\n"
    "  %(prog)s --serialize        # Output JSON CST\n"
    "  %(prog)s --ast              # Display AST structure\n"
    "  %(prog)s --reformat         # Reformat via AST\n"
    "  %(prog)s doc.dsl --debug    # Debug custom document\n"
    "  %(prog)s a.dsl -v b.dsl     # Validate unparsed a.dsl equals b.dsl",
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )

  parser.add_argument("document", type=Path, nargs="?", default=root / "spec/example.dsl", help="DSL document to parse")
  parser.add_argument("-g", "--grammar", type=Path, default=root / "grammar/TLA.lark", help="Lark grammar file")

  # Output modes
  output = parser.add_mutually_exclusive_group()
  output.add_argument("-u", "--unparse", action="store_true", help="Unparse the document (text output)")
  output.add_argument("-s", "--serialize", action="store_true", help="Serialize CST to JSON")
  output.add_argument("-r", "--roundtrip", action="store_true", help="Validate CST roundtrip parsing")
  output.add_argument(
    "-v", "--validate-against", type=Path, metavar="FILE", help="Validate unparsed CST against another document"
  )

  # AST operations
  output.add_argument("-a", "--ast", action="store_true", help="Build and display AST structure")
  output.add_argument("--serialize-ast", action="store_true", help="Serialize AST to JSON")
  output.add_argument("--reformat", action="store_true", help="Reformat document via AST transformation")
  output.add_argument("--ast-roundtrip", action="store_true", help="Validate AST roundtrip transformation")

  # Options
  parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
  parser.add_argument("-q", "--quiet", action="store_true", help="Minimal output")

  args = parser.parse_args()

  # Configure logging
  level = logging.DEBUG if args.debug else logging.WARNING if args.quiet else logging.INFO
  setup_logging(level)

  # Validate files exist
  for path, name in [(args.grammar, "Grammar"), (args.document, "Document")]:
    if not path.exists():
      logger.critical(f"{name} file not found: {path}")
      return 1

  # Create context for all operations
  ctx = ParseContext(args.grammar, args.document, args.debug)

  # Route to appropriate handler using routing table pattern
  if args.unparse:
    success = handle_unparse(ctx)
  elif args.serialize:
    success = handle_serialize(ctx)
  elif args.roundtrip:
    success = handle_roundtrip(ctx)
  elif args.validate_against:
    if not args.validate_against.exists():
      logger.critical(f"Comparison file not found: {args.validate_against}")
      return 1
    success = handle_validate_against(ctx, args.validate_against)
  elif args.ast:
    success = handle_ast(ctx)
  elif args.serialize_ast:
    success = handle_serialize_ast(ctx)
  elif args.reformat:
    success = handle_reformat(ctx)
  elif args.ast_roundtrip:
    success = handle_ast_roundtrip(ctx)
  else:
    success = handle_parse(ctx)

  return 0 if success else 1


if __name__ == "__main__":
  sys.exit(main())
