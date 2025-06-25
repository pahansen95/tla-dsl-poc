"""Command-line interface for Natural Specification Language transformations.

Provides a declarative pipeline interface that automatically determines
transformation paths between formats.
"""

import sys
import argparse

from .pipeline import get_pipeline_builder, describe_pipeline
from .format import FormatDetector


def create_parser() -> argparse.ArgumentParser:
  """Create command-line argument parser."""
  parser = argparse.ArgumentParser(
    prog="natspeclang",
    description="Natural Specification Language transformation tool",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Parse NSL to CST JSON
  %(prog)s -if nsl -of cst:json < spec.nsl > spec.cst.json

  # Convert NSL file to AST
  %(prog)s spec.nsl spec.ast

  # Pipeline through stdin/stdout
  cat spec.nsl | %(prog)s -if nsl -of ast:json | jq .

Formats:
  nsl, dsl     Natural Specification Language
  cst          Concrete Syntax Tree (JSON)
  ast          Abstract Syntax Tree (text or JSON)

Format specifications:
  -of ast      Use default encoding (text for ast)
  -of ast:json Use JSON encoding
  -of cst:json Use JSON encoding (default for CST)
""",
  )

  # Input/output files
  parser.add_argument("input", nargs="?", default="-", help="Input file (default: stdin)")
  parser.add_argument("output", nargs="?", default="-", help="Output file (default: stdout)")

  # Format options
  parser.add_argument("-if", "--input-format", metavar="FORMAT", help="Input format (auto-detected if not specified)")
  parser.add_argument("-of", "--output-format", metavar="FORMAT", help="Output format (auto-detected if not specified)")

  # Pipeline options
  parser.add_argument("--show-pipeline", action="store_true", help="Show transformation pipeline without executing")
  parser.add_argument("--debug", action="store_true", help="Enable debug output")

  return parser


def main():
  """Main CLI entry point."""
  parser = create_parser()
  args = parser.parse_args()

  # Initialize components
  builder = get_pipeline_builder()
  detector = FormatDetector()

  # Determine input format
  if args.input_format:
    input_format = detector.parse_format_spec(args.input_format)
  elif args.input != "-":
    input_format = detector.from_filename(args.input)
    if not input_format:
      parser.error(f"Cannot detect input format from {args.input}")
  else:
    parser.error("Input format must be specified when reading from stdin")

  # Determine output format
  if args.output_format:
    output_format = detector.parse_format_spec(args.output_format)
  elif args.output != "-":
    output_format = detector.from_filename(args.output)
    if not output_format:
      parser.error(f"Cannot detect output format from {args.output}")
  else:
    # Default output format based on input
    output_format = detector.get_default_output_format(input_format)

  # Show pipeline if requested
  if args.show_pipeline:
    try:
      steps = describe_pipeline(input_format, output_format)
      print(f"Transformation pipeline: {input_format.name} → {output_format.name}")
      for i, step in enumerate(steps):
        print(f"  {i + 1}. {step}")
    except ValueError as e:
      parser.error(str(e))
    return 0

  # Read input
  if args.input == "-":
    input_data = sys.stdin.read()
  else:
    with open(args.input, "r", encoding="utf-8") as f:
      input_data = f.read()

  # Execute transformation
  try:
    result = builder.transform(input_data, input_format, output_format)
  except Exception as e:
    if args.debug:
      import traceback

      traceback.print_exc()
    parser.error(f"Transformation failed: {e}")

  # Write output
  if isinstance(result, str):
    output_data = result
  else:
    # Handle non-string results (shouldn't happen with current formats)
    output_data = str(result)

  if args.output == "-":
    sys.stdout.write(output_data)
    if not output_data.endswith("\n"):
      sys.stdout.write("\n")
  else:
    with open(args.output, "w", encoding="utf-8") as f:
      f.write(output_data)
      if not output_data.endswith("\n"):
        f.write("\n")

  return 0
