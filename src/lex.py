#!/usr/bin/env python3
"""
DSL Parser - Simplified Pipeline CLI

Streamlined interface with intelligent type inference and minimal flags.
"""

import sys
import os
import json
import argparse
from pathlib import Path
import logging
from typing import Optional, Tuple, Any

# Import from package structure
from syntax.concrete import parse_document, unparse_tree
from syntax.abstract import build_ast, format_ast
from serialization import serialize_to_json, deserialize_from_json, build_ast_registry
from lark import exceptions


# Type definitions
RepType = str  # 'spec', 'cst', 'ast'
Format = str  # 'text', 'json'


class TypeInference:
  """Infer types and formats from file extensions and content."""

  @staticmethod
  def from_filename(path: Path) -> Tuple[Optional[RepType], Optional[Format]]:
    """Infer type and format from file extension."""
    name = path.name.lower()

    # Check compound extensions first
    if name.endswith(".ast.json"):
      return "ast", "json"
    elif name.endswith(".cst.json"):
      return "cst", "json"

    # Check simple extensions
    ext = path.suffix.lower()
    if ext == ".dsl":
      return "spec", "text"
    elif ext == ".json":
      # Try to infer from content structure
      return None, "json"
    elif ext in [".txt", ".text"]:
      return None, "text"

    return None, None

  @staticmethod
  def from_json_structure(data: dict) -> Optional[RepType]:
    """Infer type from JSON structure."""
    if "type" not in data:
      return None

    # CST has type='tree' or type='token'
    if data["type"] in ["tree", "token"]:
      return "cst"

    # AST has type='Specification' or other AST node names
    if data["type"] in ["Specification", "Concept", "StateDeclaration", "Operation", "Property"]:
      return "ast"

    return None

  @staticmethod
  def next_type(current: RepType) -> RepType:
    """Get next type in natural progression."""
    progression = {"spec": "cst", "cst": "ast", "ast": "spec"}
    return progression.get(current, "cst")

  @staticmethod
  def default_format(rep_type: RepType, is_stdout: bool) -> Format:
    """Get default format for type and destination."""
    if rep_type == "spec":
      return "text"
    # Use JSON for structured data when piping
    return "json" if is_stdout else "text"


class PipelineProcessor:
  """Simplified pipeline processor with inference support."""

  def __init__(self, grammar_path: Path):
    self.grammar = grammar_path.read_text()
    self.ast_registry = build_ast_registry()

  def process(
    self,
    input_content: str,
    from_type: Optional[RepType],
    to_type: Optional[RepType],
    format_override: Optional[Format],
    input_path: Optional[Path],
    output_path: Optional[Path],
  ) -> str:
    """Process transformation with intelligent defaults."""

    # Infer input type if needed
    if from_type is None:
      from_type = self._infer_input_type(input_content, input_path)

    # Load input based on type
    data = self._load_input(input_content, from_type)

    # Infer output type if needed
    if to_type is None:
      to_type = TypeInference.next_type(from_type)

    # Transform data
    result = self._transform(data, from_type, to_type)

    # Determine output format
    output_format = self._determine_format(to_type, format_override, output_path)

    # Format output
    return self._format_output(result, to_type, output_format)

  def _infer_input_type(self, content: str, path: Optional[Path]) -> RepType:
    """Infer input type from content and path."""
    # Try filename first
    if path:
      file_type, _ = TypeInference.from_filename(path)
      if file_type:
        return file_type

    # Try to parse as JSON and check structure
    try:
      data = json.loads(content)
      json_type = TypeInference.from_json_structure(data)
      if json_type:
        return json_type
    except json.JSONDecodeError:
      # Not JSON, assume spec
      return "spec"

    # Default to spec for text input
    return "spec"

  def _load_input(self, content: str, input_type: RepType) -> Any:
    """Load input based on type."""
    if input_type == "spec":
      return parse_document(self.grammar, content)

    elif input_type == "cst":
      data = json.loads(content)
      return deserialize_from_json(json.dumps(data))

    elif input_type == "ast":
      data = json.loads(content)
      return deserialize_from_json(json.dumps(data), self.ast_registry)

    raise ValueError(f"Unknown input type: {input_type}")

  def _transform(self, data: Any, from_type: RepType, to_type: RepType) -> Any:
    """Transform between representations."""
    if from_type == to_type:
      return data

    # Define transformation paths
    if from_type == "spec" and to_type == "cst":
      return data  # Already CST from parse
    elif from_type == "spec" and to_type == "ast":
      return build_ast(data)
    elif from_type == "cst" and to_type == "ast":
      return build_ast(data)
    elif from_type == "cst" and to_type == "spec":
      return unparse_tree(data)
    elif from_type == "ast" and to_type == "cst":
      return format_ast(data)
    elif from_type == "ast" and to_type == "spec":
      cst = format_ast(data)
      return unparse_tree(cst)

    raise ValueError(f"Cannot transform {from_type} to {to_type}")

  def _determine_format(
    self, output_type: RepType, format_override: Optional[Format], output_path: Optional[Path]
  ) -> Format:
    """Determine output format with smart defaults."""
    # Explicit override takes precedence
    if format_override:
      return format_override

    # Infer from output filename
    if output_path:
      _, file_format = TypeInference.from_filename(output_path)
      if file_format:
        return file_format

    # Use defaults based on type and destination
    is_stdout = output_path is None
    return TypeInference.default_format(output_type, is_stdout)

  def _format_output(self, data: Any, output_type: RepType, format: Format) -> str:
    """Format output based on type and format."""
    if output_type == "spec":
      # Spec is always text
      return data if isinstance(data, str) else str(data)

    if format == "json":
      return serialize_to_json(data)

    # Text representation
    if output_type == "cst":
      return self._format_cst_text(data)
    elif output_type == "ast":
      return self._format_ast_text(data)

    raise ValueError(f"Cannot format {output_type} as {format}")

  def _format_cst_text(self, tree) -> str:
    """Human-readable CST representation."""
    from lark import Tree, Token

    lines = []

    def print_tree(node, indent=0):
      if isinstance(node, Tree):
        lines.append("  " * indent + f"[{node.data}]")
        for child in node.children:
          print_tree(child, indent + 1)
      elif isinstance(node, Token):
        value = repr(str(node))
        if len(value) > 50:
          value = value[:47] + "..."
        lines.append("  " * indent + f"{node.type}: {value}")

    print_tree(tree)
    return "\n".join(lines)

  def _format_ast_text(self, ast) -> str:
    """Human-readable AST representation."""
    lines = []
    lines.append(f"Specification: {ast.name}")
    lines.append(f"  Description: {ast.description}")

    if ast.concepts:
      lines.append("  Concepts:")
      for c in ast.concepts:
        lines.append(f"    - {c.name}: {c.description}")

    if ast.states:
      lines.append("  States:")
      for s in ast.states:
        lines.append(f"    - {s.name}")

    if ast.operations:
      lines.append("  Operations:")
      for o in ast.operations:
        lines.append(f"    - When {o.trigger}")

    return "\n".join(lines)


# I/O utilities
def setup_logging(verbose: bool = False, quiet: bool = False):
  """Configure logging to stderr."""
  if quiet:
    level = logging.WARNING
  elif verbose:
    level = logging.DEBUG
  else:
    level = logging.INFO

  logging.basicConfig(
    level=level, format="[%(levelname)s] %(message)s" if verbose else "%(message)s", stream=sys.stderr
  )


def find_grammar() -> Path:
  """Find grammar file with fallback locations."""
  # Try project root first
  for parent in Path(__file__).parents:
    if (parent / ".git").exists():
      grammar = parent / "grammar/TLA.lark"
      if grammar.exists():
        return grammar

  # Try relative to script
  script_dir = Path(__file__).parent
  grammar = script_dir.parent / "grammar/TLA.lark"
  if grammar.exists():
    return grammar

  # Environment variable fallback
  if context := os.environ.get("CONTEXT"):
    grammar = Path(context) / "grammar/TLA.lark"
    if grammar.exists():
      return grammar

  raise FileNotFoundError("Cannot find grammar file. Set CONTEXT environment variable.")


# Main entry point
def main():
  """Simplified CLI entry point."""
  parser = argparse.ArgumentParser(
    prog="lex",
    description="Transform between spec/cst/ast representations",
    epilog="""Examples:
  %(prog)s example.dsl                    # spec → cst (json to stdout)
  %(prog)s example.dsl output.ast.json    # spec → ast (inferred from extension)
  %(prog)s input.json output.dsl          # auto-detect → spec
  %(prog)s -f cst -t spec < input.json   # explicit types
  %(prog)s example.dsl --text             # force text output""",
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )

  # Positional arguments
  parser.add_argument("input_file", nargs="?", type=Path, help="Input file (default: stdin)")
  parser.add_argument("output_file", nargs="?", type=Path, help="Output file (default: stdout)")

  # Type specification
  parser.add_argument(
    "-f", "--from", dest="from_type", choices=["spec", "cst", "ast"], help="Input type (default: auto-detect)"
  )
  parser.add_argument(
    "-t", "--to", dest="to_type", choices=["spec", "cst", "ast"], help="Output type (default: next in progression)"
  )

  # Format override
  format_group = parser.add_mutually_exclusive_group()
  format_group.add_argument("--text", action="store_const", const="text", dest="format", help="Force text output")
  format_group.add_argument("--json", action="store_const", const="json", dest="format", help="Force JSON output")

  # Other options
  parser.add_argument("-g", "--grammar", type=Path, help="Grammar file (default: auto-detect)")

  verbosity = parser.add_mutually_exclusive_group()
  verbosity.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
  verbosity.add_argument("-q", "--quiet", action="store_true", help="Suppress info messages")

  args = parser.parse_args()

  # Setup logging
  setup_logging(args.verbose, args.quiet)

  # Find grammar
  try:
    grammar_path = args.grammar or find_grammar()
  except FileNotFoundError as e:
    logging.error(str(e))
    return 1

  # Read input
  if args.input_file:
    if not args.input_file.exists():
      logging.error(f"Input file not found: {args.input_file}")
      return 1
    input_content = args.input_file.read_text()
    logging.debug(f"Read {len(input_content)} bytes from {args.input_file}")
  else:
    input_content = sys.stdin.read()
    logging.debug(f"Read {len(input_content)} bytes from stdin")

  # Process pipeline
  processor = PipelineProcessor(grammar_path)

  try:
    output = processor.process(
      input_content, args.from_type, args.to_type, args.format, args.input_file, args.output_file
    )

    # Write output
    if args.output_file:
      args.output_file.write_text(output)
      if args.output_file.suffix == ".json":
        # Pretty-print JSON files
        data = json.loads(output)
        args.output_file.write_text(json.dumps(data, indent=2))
      else:
        args.output_file.write_text(output)
      logging.info(f"Wrote output to {args.output_file}")
    else:
      print(output, end="")

    return 0

  except exceptions.ParseError as e:
    logging.error(f"Parse error: {e}")
    return 1
  except json.JSONDecodeError as e:
    logging.error(f"Invalid JSON: {e}")
    return 1
  except Exception as e:
    logging.error(f"Error: {e}")
    if args.verbose:
      import traceback

      traceback.print_exc()
    return 1


if __name__ == "__main__":
  try:
    sys.exit(main())
  except KeyboardInterrupt:
    sys.exit(130)
  except BrokenPipeError:
    # Silent exit for broken pipes
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    sys.exit(1)
