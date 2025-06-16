#!/usr/bin/env python3
"""
DSL Parser CLI Interface

Command-line interface for parsing, transforming, and analyzing
Natural Language Specification DSL documents.
"""

import sys
import os
import argparse
from pathlib import Path
import logging
import difflib
import contextlib
import signal

# Import from reorganized package structure
from syntax.concrete import parse_document, unparse_tree
from syntax.abstract import build_ast, format_ast, Specification
from serialization import serialize_to_json, deserialize_from_json, build_ast_registry

from lark import exceptions


# Parse Context Management
class ParseContext:
  """Encapsulates parsing state and operations."""

  def __init__(self, grammar_path: Path, document_path: Path, debug: bool = False):
    self.grammar_path = grammar_path
    self.document_path = document_path
    self.debug = debug
    self.grammar = None
    self.document = None
    self.tree = None

  def load(self):
    """Load grammar and document files."""
    self.grammar = self.grammar_path.read_text()
    self.document = self.document_path.read_text()
    return self

  def parse(self):
    """Parse document using loaded grammar."""
    self.tree = parse_document(self.grammar, self.document, debug=self.debug)
    return self


# Output Utilities
def print_tree(tree, indent=0):
  """Display parse tree structure."""
  from lark import Tree, Token

  if isinstance(tree, Tree):
    print("  " * indent + f"[{tree.data}]")
    for child in tree.children:
      print_tree(child, indent + 1)
  elif isinstance(tree, Token) and logger.isEnabledFor(logging.DEBUG):
    value = repr(str(tree))
    if len(value) > 50:
      value = value[:47] + "..."
    print("  " * indent + f"Token: {value}")


def print_ast(ast: Specification, indent=0):
  """Display AST structure."""
  print(f"{'  ' * indent}Specification: {ast.name}")
  print(f"{'  ' * (indent + 1)}Description: {ast.description}")

  if ast.concepts:
    print(f"{'  ' * (indent + 1)}Concepts:")
    for c in ast.concepts:
      print(f"{'  ' * (indent + 2)}- {c.name}: {c.description}")

  if ast.states:
    print(f"{'  ' * (indent + 1)}States:")
    for s in ast.states:
      print(f"{'  ' * (indent + 2)}- {s.name}")
      for p in s.properties:
        print(f"{'  ' * (indent + 3)}  {p}")
      if s.initial_condition:
        print(f"{'  ' * (indent + 3)}  {s.initial_condition}")

  if ast.operations:
    print(f"{'  ' * (indent + 1)}Operations:")
    for o in ast.operations:
      print(f"{'  ' * (indent + 2)}- When {o.trigger}")

  if ast.properties:
    constraints = [p for p in ast.properties if p.property_type == "constraint"]
    guarantees = [p for p in ast.properties if p.property_type == "guarantee"]

    if constraints:
      print(f"{'  ' * (indent + 1)}Constraints:")
      for c in constraints:
        print(f"{'  ' * (indent + 2)}- {c.name}")

    if guarantees:
      print(f"{'  ' * (indent + 1)}Guarantees:")
      for g in guarantees:
        print(f"{'  ' * (indent + 2)}- {g.name}")


def show_diff(text1: str, text2: str, label1: str, label2: str):
  """Display unified diff between texts."""
  diff = difflib.unified_diff(
    text1.splitlines(keepends=True), text2.splitlines(keepends=True), fromfile=label1, tofile=label2
  )
  print("\nDifferences:")
  print("".join(diff))


# Operation Handlers
def handle_parse(ctx: ParseContext) -> bool:
  """Parse and display tree structure."""
  try:
    ctx.load().parse()
    logger.info("✓ Document parsed successfully")
    print("\nParse Tree:")
    print("-" * 50)
    print_tree(ctx.tree)
    return True
  except exceptions.ParseError as e:
    logger.error(f"Parse Error: {e}")
    return False


def handle_unparse(ctx: ParseContext) -> bool:
  """Parse and reconstruct document text."""
  try:
    ctx.load().parse()
    unparsed = unparse_tree(ctx.tree)
    logger.info("✓ Document unparsed successfully")
    print(unparsed)
    return True
  except Exception as e:
    logger.error(f"Error: {e}")
    return False


def handle_serialize(ctx: ParseContext) -> bool:
  """Serialize CST to JSON."""
  try:
    ctx.load().parse()
    json_output = serialize_to_json(ctx.tree)
    logger.info("✓ CST serialized successfully")
    print(json_output)
    return True
  except Exception as e:
    logger.error(f"Error: {e}")
    return False


def handle_roundtrip(ctx: ParseContext) -> bool:
  """Validate parse/unparse roundtrip."""
  try:
    ctx.load().parse()

    # Test unparsing
    unparsed = unparse_tree(ctx.tree)
    if ctx.document != unparsed:
      logger.error("✗ Unparsing roundtrip failed")
      if logger.isEnabledFor(logging.DEBUG):
        show_diff(ctx.document, unparsed, "original", "unparsed")
      return False

    # Test serialization
    json_str = serialize_to_json(ctx.tree)
    restored = deserialize_from_json(json_str)
    restored_text = unparse_tree(restored)

    if ctx.document != restored_text:
      logger.error("✗ Serialization roundtrip failed")
      return False

    logger.info("✓ Roundtrip validation passed")
    return True
  except Exception as e:
    logger.error(f"Error: {e}")
    return False


def handle_ast(ctx: ParseContext) -> bool:
  """Build and display AST."""
  try:
    ctx.load().parse()
    ast = build_ast(ctx.tree)
    logger.info("✓ AST built successfully")
    print("\nAbstract Syntax Tree:")
    print("-" * 50)
    print_ast(ast)
    return True
  except Exception as e:
    logger.error(f"Error: {e}")
    return False


def handle_serialize_ast(ctx: ParseContext) -> bool:
  """Serialize AST to JSON."""
  try:
    ctx.load().parse()
    ast = build_ast(ctx.tree)

    # Use registry for AST types
    build_ast_registry()

    json_output = serialize_to_json(ast)
    logger.info("✓ AST serialized successfully")
    print(json_output)
    return True
  except Exception as e:
    logger.error(f"Error: {e}")
    return False


def handle_reformat(ctx: ParseContext) -> bool:
  """Reformat document via AST transformation."""
  try:
    ctx.load().parse()
    ast = build_ast(ctx.tree)
    reformatted_cst = format_ast(ast)
    reformatted_text = unparse_tree(reformatted_cst)
    logger.info("✓ Document reformatted through AST")
    print(reformatted_text)
    return True
  except Exception as e:
    logger.error(f"Error: {e}")
    return False


def handle_ast_roundtrip(ctx: ParseContext) -> bool:
  """Validate CST → AST → CST transformation."""
  try:
    ctx.load().parse()

    # Build AST from CST
    ast1 = build_ast(ctx.tree)

    # Format AST back to CST
    formatted_cst = format_ast(ast1)
    formatted_text = unparse_tree(formatted_cst)

    # Parse formatted text
    formatted_tree = parse_document(ctx.grammar, formatted_text)

    # Build AST from formatted CST
    ast2 = build_ast(formatted_tree)

    # Compare AST structures (simplified comparison)
    if (
      ast1.name != ast2.name
      or ast1.description != ast2.description
      or len(ast1.concepts) != len(ast2.concepts)
      or len(ast1.states) != len(ast2.states)
      or len(ast1.operations) != len(ast2.operations)
      or len(ast1.properties) != len(ast2.properties)
    ):
      logger.error("✗ AST roundtrip failed - semantic difference")
      return False

    logger.info("✓ AST roundtrip validation passed")
    return True
  except Exception as e:
    logger.error(f"Error: {e}")
    return False


class CompactFormatter(logging.Formatter):
  """Minimal log formatting."""

  FORMATS = {
    logging.INFO: "%(message)s",
    logging.WARNING: "⚠ %(message)s",
    logging.ERROR: "✗ %(message)s",
    logging.DEBUG: "[%(levelname)s] %(message)s",
  }

  def format(self, record):
    fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
    return logging.Formatter(fmt).format(record)


class SafeStreamHandler(logging.StreamHandler):
  """Stream handler that ignores broken pipe errors."""

  def emit(self, record):
    try:
      super().emit(record)
    except BrokenPipeError:
      pass
    except IOError as e:
      if e.errno == 32:  # EPIPE
        pass
      else:
        raise


def setup_logging(level: int) -> logging.Logger:
  """Configure logging with broken pipe protection."""
  logger = logging.getLogger()
  logger.setLevel(level)
  logger.handlers.clear()

  # Use safe handler instead of regular StreamHandler
  handler = SafeStreamHandler(sys.stdout)
  handler.setFormatter(CompactFormatter())
  logger.addHandler(handler)

  return logger


logger = logging.getLogger(__name__)


# CLI Entry Point
def find_project_root() -> Path:
  """Locate project root directory."""
  for parent in Path(__file__).parents:
    if (parent / ".git").exists():
      return parent

  if context := os.environ.get("CONTEXT"):
    return Path(context)

  print("couldn't find project root, export CONTEXT & try again", file=sys.stderr)
  raise SystemExit(1)


def main():
  """Main CLI entry point."""
  root = find_project_root()

  # Setup argument parser
  parser = argparse.ArgumentParser(
    description="Parse Natural Language Specification DSL documents",
    epilog="""Examples:
  %(prog)s                    # Parse default example
  %(prog)s --unparse          # Reconstruct text
  %(prog)s --serialize        # Output JSON CST
  %(prog)s --ast              # Display AST structure
  %(prog)s --reformat         # Reformat via AST""",
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )

  parser.add_argument("document", type=Path, nargs="?", default=root / "spec/example.dsl", help="DSL document to parse")
  parser.add_argument("-g", "--grammar", type=Path, default=root / "grammar/TLA.lark", help="Lark grammar file")

  # Operations
  ops = parser.add_mutually_exclusive_group()
  ops.add_argument("-u", "--unparse", action="store_true", help="Reconstruct document text")
  ops.add_argument("-s", "--serialize", action="store_true", help="Serialize CST to JSON")
  ops.add_argument("-r", "--roundtrip", action="store_true", help="Validate roundtrip parsing")
  ops.add_argument("-a", "--ast", action="store_true", help="Build and display AST")
  ops.add_argument("--serialize-ast", action="store_true", help="Serialize AST to JSON")
  ops.add_argument("--reformat", action="store_true", help="Reformat document via AST")
  ops.add_argument("--ast-roundtrip", action="store_true", help="Validate AST roundtrip")

  # Options
  parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
  parser.add_argument("-q", "--quiet", action="store_true", help="Minimal output")

  args = parser.parse_args()

  # Configure logging
  level = logging.DEBUG if args.debug else logging.WARNING if args.quiet else logging.INFO
  setup_logging(level)

  # Validate files
  for path, name in [(args.grammar, "Grammar"), (args.document, "Document")]:
    if not path.exists():
      logger.critical(f"{name} file not found: {path}")
      return 1

  # Create context
  ctx = ParseContext(args.grammar, args.document, args.debug)

  # Route to handler
  handlers = {
    "unparse": handle_unparse,
    "serialize": handle_serialize,
    "roundtrip": handle_roundtrip,
    "ast": handle_ast,
    "serialize_ast": handle_serialize_ast,
    "reformat": handle_reformat,
    "ast_roundtrip": handle_ast_roundtrip,
  }

  # Determine which handler to use
  handler = handle_parse  # default
  for arg_name, handler_func in handlers.items():
    if getattr(args, arg_name, False):
      handler = handler_func
      break

  # Execute handler
  success = handler(ctx)
  return 0 if success else 1


@contextlib.contextmanager
def cli_session(*args):
  # Handle SIGPIPE for Unix pipelines
  try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
  except AttributeError:
    # Windows doesn't have SIGPIPE
    pass

  rc = 0

  try:
    yield
  except SystemExit as e:
    rc = e.code
  except BrokenPipeError:
    rc = 1
  except IOError as e:
    rc = 2
    if e.errno not in {
      32,
    }:  # EPIPE
      logger.critical("Unhandled IO Error", exc_info=True)
  except Exception:
    rc = 2
    logger.critical("Unhandled Exception", exc_info=True)
  finally:
    # Suppress broken pipe errors during cleanup
    try:
      logging.shutdown()
      sys.stdout.flush()
    except (BrokenPipeError, IOError):
      pass

  # Use os._exit to avoid further cleanup issues
  os._exit(rc)


if __name__ == "__main__":
  with cli_session():
    main()
