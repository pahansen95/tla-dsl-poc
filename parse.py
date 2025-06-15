#!/usr/bin/env python3
"""
BNF Grammar Test Parser
Tests Natural Language Specification DSL against documents
"""

from lark import Lark, Tree, Token, exceptions
from lark.visitors import Interpreter
import sys
import argparse
from pathlib import Path
import re
import logging


CONTEXT = Path(__file__).parent


def setup_logging(level=logging.INFO):
  """Configure logging with appropriate format."""

  # Create custom formatter
  class CustomFormatter(logging.Formatter):
    """Formatter that adds context-specific formatting."""

    FORMATS = {
      logging.DEBUG: "%(asctime)s [%(levelname)s] %(message)s",
      logging.INFO: "%(message)s",
      logging.WARNING: "⚠ %(message)s",
      logging.ERROR: "✗ %(message)s",
      logging.CRITICAL: "✗✗ %(message)s",
    }

    def format(self, record):
      log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
      formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
      return formatter.format(record)

  # Configure root logger
  logger = logging.getLogger()
  logger.setLevel(level)

  # Remove existing handlers
  logger.handlers.clear()

  # Console handler with custom formatter
  console = logging.StreamHandler(sys.stdout)
  console.setFormatter(CustomFormatter())
  logger.addHandler(console)

  return logger


# Get module logger
logger = logging.getLogger(__name__)


def convert_bnf_to_lark(bnf_content):
  """
  Convert BNF notation to Lark grammar format.

  Handles:
  - Character ranges [a-z] → /[a-z]/
  - Epsilon rules E → ""
  - Maintains terminals and non-terminals
  """
  lines = bnf_content.split("\n")
  lark_grammar = []

  logger.info("\n[BNF → Lark Conversion]")
  logger.info("=" * 70)

  for i, line in enumerate(lines):
    original = line

    # Skip empty lines and comments
    if not line.strip() or line.strip().startswith("/*"):
      if line.strip().startswith("/*"):
        logger.debug(f"Line {i + 1}: Skipping comment")
      continue

    # Convert character ranges
    if "[" in line and "-" in line and "]" in line:
      line = re.sub(r"\[([a-zA-Z0-9]-[a-zA-Z0-9])\]", r"/[\1]/", line)
      if line != original:
        logger.debug(f"Line {i + 1}: Converted character range")
        logger.debug(f"  From: {original.strip()}")
        logger.debug(f"  To:   {line.strip()}")

    # Convert epsilon E to empty string
    if " E " in line or line.endswith(" E"):
      line = line.replace(" E ", ' "" ')
      line = line.replace(" E\n", ' ""\n')
      logger.debug(f"Line {i + 1}: Converted epsilon")

    # Convert BNF ::= to Lark :
    if "::=" in line:
      line = line.replace("::=", ":")
      logger.debug(f"Line {i + 1}: Converted ::= to :")

    # Remove angle brackets from non-terminals
    if "<" in line and ">" in line:
      line = re.sub(r"<(\w+)>", r"\1", line)
      logger.debug(f"Line {i + 1}: Removed angle brackets")
      logger.debug(f"  Result: {line.strip()}")

    lark_grammar.append(line)

  return "\n".join(lark_grammar)


def load_grammar(grammar_path):
  """Load and convert BNF grammar to Lark format."""
  try:
    logger.info(f"\n[Loading Grammar: {grammar_path}]")
    logger.info("=" * 70)

    with open(grammar_path, "r") as f:
      bnf_content = f.read()

    logger.info(f"Read {len(bnf_content)} characters from grammar file")
    logger.info(f"Grammar has {len(bnf_content.splitlines())} lines")

    # Convert BNF to Lark format
    lark_grammar = convert_bnf_to_lark(bnf_content)

    # Add Lark-specific directives
    lark_grammar = f"""
{lark_grammar}

%import common.WS_INLINE
%ignore WS_INLINE
"""

    logger.debug("\n[Final Lark Grammar]")
    logger.debug("-" * 50)
    if logger.isEnabledFor(logging.DEBUG):
      for i, line in enumerate(lark_grammar.split("\n")[:20]):  # Show first 20 lines
        if line.strip():
          logger.debug(f"{i + 1:3d}: {line}")
      if len(lark_grammar.split("\n")) > 20:
        logger.debug("     ... (truncated)")
    logger.debug("-" * 50)

    return lark_grammar
  except Exception as e:
    logger.error(f"Error loading grammar: {e}")
    return None


class VerboseInterpreter(Interpreter):
  """Visitor that logs parsing progress."""

  def __init__(self):
    self.depth = 0
    self.rule_count = 0
    self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

  def visit(self, tree):
    if isinstance(tree, Tree):
      self.rule_count += 1
      indent = "  " * self.depth
      self.logger.debug(f"{indent}→ Entering rule: {tree.data}")
      self.depth += 1

      for child in tree.children:
        if isinstance(child, Token):
          child_indent = "  " * self.depth
          value = str(child)[:30] + "..." if len(str(child)) > 30 else str(child)
          self.logger.debug(f"{child_indent}• Token[{child.type}]: '{value}'")
        else:
          self.visit(child)

      self.depth -= 1
      self.logger.debug(f"{indent}← Completed rule: {tree.data}")


def create_parser(grammar):
  """Create Lark parser from grammar string."""
  try:
    logger.info("\n[Creating Parser]")
    logger.info("=" * 70)

    parser = Lark(
      grammar,
      start="specification",
      parser="earley",  # More robust for complex grammars
      debug=logger.isEnabledFor(logging.DEBUG),
      ambiguity="resolve",  # Auto-resolve ambiguities
      keep_all_tokens=True,  # Keep all tokens for tracing
    )

    logger.info("✓ Parser created successfully")
    logger.debug("  Parser type: Earley")
    logger.debug("  Start symbol: specification")
    logger.debug(f"  Debug mode: {logger.isEnabledFor(logging.DEBUG)}")

    return parser
  except Exception as e:
    logger.error(f"Error creating parser: {e}")
    if logger.isEnabledFor(logging.DEBUG):
      logger.debug("\nGrammar that failed:")
      logger.debug("=" * 50)
      logger.debug(grammar)
      logger.debug("=" * 50)
    raise


def parse_document(parser, document_path):
  """Parse document using the grammar."""
  try:
    with open(document_path, "r") as f:
      content = f.read()

    logger.info(f"\n[Parsing Document: {document_path}]")
    logger.info(f"Document length: {len(content)} characters")
    logger.info(f"Document lines: {len(content.splitlines())}")
    logger.info("-" * 50)

    if logger.isEnabledFor(logging.DEBUG):
      logger.debug("\n[Document Preview]")
      for i, line in enumerate(content.splitlines()[:10]):
        logger.debug(f"{i + 1:3d}: {line}")
      if len(content.splitlines()) > 10:
        logger.debug("     ... (truncated)")
      logger.debug("-" * 50)

    logger.info("\n[Starting Parse]")
    logger.info("=" * 70)

    tree = parser.parse(content)

    if logger.isEnabledFor(logging.DEBUG):
      logger.debug("\n[Parse Trace]")
      logger.debug("-" * 50)
      interpreter = VerboseInterpreter()
      interpreter.visit(tree)
      logger.debug(f"\nTotal rules processed: {interpreter.rule_count}")

    return tree

  except exceptions.UnexpectedCharacters as e:
    logger.error("\nParse Error - Unexpected Character:")
    logger.error(f"  Line {e.line}, Column {e.column}")
    logger.error(f"  Expected: {e.expected}")
    logger.error(f"  Context: {e.get_context(content)}")

    if logger.isEnabledFor(logging.DEBUG):
      logger.debug("\n[Error Details]")
      logger.debug(f"  Allowed characters: {', '.join(sorted(e.allowed))}")
      logger.debug(f"  Found character: '{content[e.pos]}' (ASCII: {ord(content[e.pos])})")

      # Show line with error marker
      lines = content.splitlines()
      if 0 <= e.line - 1 < len(lines):
        error_line = lines[e.line - 1]
        logger.debug("\n  Error line:")
        logger.debug(f"  {error_line}")
        logger.debug(f"  {' ' * (e.column - 1)}^")

    return None

  except exceptions.UnexpectedToken as e:
    logger.error("\nParse Error - Unexpected Token:")
    logger.error(f"  Token: {e.token}")
    logger.error(f"  Expected: {e.expected}")
    logger.error(f"  Line {e.line}, Column {e.column}")

    if logger.isEnabledFor(logging.DEBUG):
      logger.debug("\n[Error Details]")
      logger.debug(f"  Token type: {e.token.type}")
      logger.debug(f"  Token value: '{e.token.value}'")
      logger.debug(f"  Valid next tokens: {', '.join(sorted(e.accepts))}")

    return None

  except Exception as e:
    logger.error(f"\nParse Error: {type(e).__name__}: {e}")
    if logger.isEnabledFor(logging.DEBUG):
      logger.exception("Stack trace:")
    return None


def print_tree(tree, indent=0, show_tokens=True):
  """Pretty print parse tree."""
  if isinstance(tree, Tree):
    print("  " * indent + f"[{tree.data}]")
    for child in tree.children:
      print_tree(child, indent + 1, show_tokens)
  elif show_tokens:
    # Terminal - show abbreviated version if too long
    value = str(tree)
    if len(value) > 50:
      value = value[:47] + "..."
    # Show token type if available
    if hasattr(tree, "type"):
      print("  " * indent + f'Token({tree.type}): "{value}"')
    else:
      print("  " * indent + f'"{value}"')


def validate_grammar(grammar_path, document_path):
  """Main validation function."""
  logger.info(f"BNF Grammar: {grammar_path}")
  logger.info(f"Test Document: {document_path}")
  logger.info("=" * 70)

  # Load and convert grammar
  grammar = load_grammar(grammar_path)
  if not grammar:
    return False

  # Create parser
  try:
    parser = create_parser(grammar)
    logger.info("✓ Grammar loaded successfully")
  except Exception:
    logger.error("Failed to create parser")
    return False

  # Parse document
  tree = parse_document(parser, document_path)

  if tree:
    logger.info("\n✓ Document parsed successfully!")
    logger.info("\nParse Tree:")
    logger.info("-" * 50)
    print_tree(tree, show_tokens=logger.isEnabledFor(logging.DEBUG))

    if logger.isEnabledFor(logging.DEBUG):
      logger.debug("\n[Parse Statistics]")
      logger.debug(f"  Tree depth: {tree.meta.depth if hasattr(tree, 'meta') else 'N/A'}")
      logger.debug(f"  Total nodes: {sum(1 for _ in tree.iter_subtrees())}")

    return True
  else:
    logger.error("\nDocument parsing failed")
    return False


def main():
  parser = argparse.ArgumentParser(
    description="Test BNF grammar against specification documents",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Parse with info output (default)
  %(prog)s grammar.bnf document.tla

  # Parse with minimal output
  %(prog)s grammar.bnf document.tla --quiet

  # Parse with debug output
  %(prog)s grammar.bnf document.tla --debug

  # Parse with custom log level
  %(prog)s grammar.bnf document.tla --log-level WARNING
    """,
  )

  parser.add_argument(
    "grammar",
    type=Path,
    nargs="?",
    default=(CONTEXT / "grammar/TLA.lark"),
    help="Path to BNF grammar file (default: grammar/TLA.lark)",
  )
  parser.add_argument(
    "document",
    type=Path,
    nargs="?",
    default=(CONTEXT / "spec/example.tla"),
    help="Path to document to parse (default: spec.tla)",
  )
  parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output (sets log level to WARNING)")
  parser.add_argument("--debug", "-d", action="store_true", help="Show debug output (sets log level to DEBUG)")
  parser.add_argument(
    "--log-level",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    default="INFO",
    help="Set explicit log level (default: INFO)",
  )

  args = parser.parse_args()

  # Determine log level
  if args.debug:
    log_level = logging.DEBUG
  elif args.quiet:
    log_level = logging.WARNING
  else:
    log_level = getattr(logging, args.log_level)

  # Setup logging
  setup_logging(log_level)

  # Log configuration
  logger.debug(f"Log level set to: {logging.getLevelName(log_level)}")

  # Validate files exist
  if not args.grammar.exists():
    logger.critical(f"Grammar file not found: {args.grammar}")
    sys.exit(1)

  if not args.document.exists():
    logger.critical(f"Document file not found: {args.document}")
    sys.exit(1)

  # Run validation
  success = validate_grammar(args.grammar, args.document)
  sys.exit(0 if success else 1)


if __name__ == "__main__":
  main()
