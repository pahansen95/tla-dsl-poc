#!/usr/bin/env python3
"""
DSL Parser CLI Interface

This module provides the command-line interface for the Natural Language
Specification DSL parser. It orchestrates the core parsing, unparsing, and
serialization components to support various document processing workflows.

Responsibilities:
- Command-line argument handling and validation
- File I/O operations for grammars and documents
- Output formatting and display
- Error reporting and user feedback
- Orchestration of core modules for different operations

The CLI supports multiple output modes including parse tree display, 
document unparsing, CST serialization, and roundtrip validation. It serves
as the primary entry point for both interactive use and pipeline integration.
"""

import sys
import os
import argparse
from pathlib import Path
import logging
from typing import Optional
import difflib

# Import core functionality
from core import (
    create_parser, parse_document, validate_grammar,
    unparse_tree, serialize_cst, deserialize_cst
)
from lark import Tree, exceptions


# ============ Environment Setup ============
def find_project_root() -> Path:
    """Find project root by looking for .git directory."""
    for parent in Path(__file__).parents:
        if (parent / ".git").exists():
            return parent
    
    if context := os.environ.get("CONTEXT"):
        return Path(context)
    
    print("couldn't find project root, export CONTEXT & try again", file=sys.stderr)
    raise SystemExit(1)


# ============ Logging Configuration ============
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


# ============ Display Functions ============
def print_tree(tree: Tree, indent: int = 0):
    """Display parse tree structure."""
    from lark import Token
    
    if isinstance(tree, Tree):
        print("  " * indent + f"[{tree.data}]")
        for child in tree.children:
            print_tree(child, indent + 1)
    elif isinstance(tree, Token) and logger.isEnabledFor(logging.DEBUG):
        value = repr(str(tree))
        if len(value) > 50:
            value = value[:47] + "..."
        print("  " * indent + f"Token: {value}")


def format_parse_error(e: exceptions.ParseError, content: str) -> None:
    """Format parse errors with context."""
    if isinstance(e, exceptions.UnexpectedCharacters):
        logger.error("\nParse Error - Unexpected Character:")
        logger.error(f"  Line {e.line}, Column {e.column}")
        if content:
            logger.error(f"  Context: {e.get_context(content)}")
    elif isinstance(e, exceptions.UnexpectedToken):
        logger.error("\nParse Error - Unexpected Token:")
        logger.error(f"  Token: {e.token}")
    else:
        logger.error(f"\nParse Error: {e}")


# ============ Operation Handlers ============
def handle_parse(grammar_path: Path, document_path: Path) -> bool:
    """Parse and display tree structure."""
    try:
        grammar = grammar_path.read_text()
        document = document_path.read_text()
        
        parser = create_parser(grammar, debug=logger.isEnabledFor(logging.DEBUG))
        tree = parse_document(parser, document)
        
        logger.info("✓ Document parsed successfully")
        print("\nParse Tree:")
        print("-" * 50)
        print_tree(tree)
        return True
        
    except exceptions.ParseError as e:
        format_parse_error(e, document if 'document' in locals() else "")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def handle_validate_against(grammar_path: Path, document_path: Path, 
                           comparison_path: Path) -> bool:
    """Validate unparsed CST against another document."""
    try:
        grammar = grammar_path.read_text()
        document = document_path.read_text()
        comparison = comparison_path.read_text()
        
        # Parse primary document
        parser = create_parser(grammar)
        tree = parse_document(parser, document)
        unparsed = unparse_tree(tree)
        
        # Normalize line endings for comparison
        unparsed_normalized = unparsed.replace('\r\n', '\n')
        comparison_normalized = comparison.replace('\r\n', '\n')
        
        if unparsed_normalized == comparison_normalized:
            logger.info("✓ Validation passed - documents are equivalent")
            return True
        else:
            logger.error("✗ Validation failed - documents differ")
            logger.error(f"  Unparsed: {len(unparsed)} chars")
            logger.error(f"  Comparison: {len(comparison)} chars")
            
            # Show differences
            diff = difflib.unified_diff(
                unparsed.splitlines(keepends=True),
                comparison.splitlines(keepends=True),
                fromfile="unparsed",
                tofile="comparison"
            )
            print("\nDifferences:")
            print("".join(diff))
            return False
            
    except exceptions.ParseError as e:
        format_parse_error(e, document if 'document' in locals() else "")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def handle_unparse(grammar_path: Path, document_path: Path) -> bool:
    """Parse and unparse document."""
    try:
        grammar = grammar_path.read_text()
        document = document_path.read_text()
        
        parser = create_parser(grammar)
        tree = parse_document(parser, document)
        unparsed = unparse_tree(tree)
        
        logger.info("✓ Document unparsed successfully")
        print(unparsed)
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def handle_serialize(grammar_path: Path, document_path: Path) -> bool:
    """Parse and serialize to JSON."""
    try:
        grammar = grammar_path.read_text()
        document = document_path.read_text()
        
        parser = create_parser(grammar)
        tree = parse_document(parser, document)
        json_output = serialize_cst(tree)
        
        logger.info("✓ CST serialized successfully")
        print(json_output)
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def handle_roundtrip(grammar_path: Path, document_path: Path) -> bool:
    """Validate parse/unparse roundtrip."""
    try:
        grammar = grammar_path.read_text()
        document = document_path.read_text()
        
        # Test unparsing roundtrip
        parser = create_parser(grammar)
        tree = parse_document(parser, document)
        unparsed = unparse_tree(tree)
        
        if document != unparsed:
            logger.error("✗ Roundtrip validation failed")
            logger.error(f"  Original: {len(document)} chars")
            logger.error(f"  Unparsed: {len(unparsed)} chars")
            
            if logger.isEnabledFor(logging.DEBUG):
                diff = difflib.unified_diff(
                    document.splitlines(keepends=True),
                    unparsed.splitlines(keepends=True),
                    fromfile="original",
                    tofile="unparsed"
                )
                print("\nDifferences:")
                print("".join(diff))
            return False
        
        # Test serialization roundtrip
        json_str = serialize_cst(tree)
        restored = deserialize_cst(json_str)
        restored_text = unparse_tree(restored)
        
        if document != restored_text:
            logger.error("✗ Serialization roundtrip failed")
            return False
            
        logger.info("✓ Roundtrip validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


# ============ CLI Interface ============
def main():
    """Main entry point for CLI."""
    root = find_project_root()
    
    parser = argparse.ArgumentParser(
        description="Parse Natural Language Specification DSL documents",
        epilog="Examples:\n"
               "  %(prog)s                    # Parse default example\n" 
               "  %(prog)s --unparse          # Unparse to stdout\n"
               "  %(prog)s --serialize        # Output JSON CST\n"
               "  %(prog)s doc.dsl --debug    # Debug custom document\n"
               "  %(prog)s a.dsl -v b.dsl     # Validate unparsed a.dsl equals b.dsl",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "document",
        type=Path,
        nargs="?",
        default=root / "spec/example.dsl",
        help="DSL document to parse"
    )
    parser.add_argument(
        "-g", "--grammar",
        type=Path,
        default=root / "grammar/TLA.lark",
        help="Lark grammar file"
    )
    
    # Output modes
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "-u", "--unparse",
        action="store_true",
        help="Unparse the document (text output)"
    )
    output.add_argument(
        "-s", "--serialize", 
        action="store_true",
        help="Serialize CST to JSON"
    )
    output.add_argument(
        "-r", "--roundtrip",
        action="store_true",
        help="Validate roundtrip parsing"
    )
    output.add_argument(
        "-v", "--validate-against",
        type=Path,
        metavar="FILE",
        help="Validate unparsed CST against another document"
    )
    
    # Options
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug output"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true", 
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.debug else logging.WARNING if args.quiet else logging.INFO
    setup_logging(level)
    
    # Validate files
    if not args.grammar.exists():
        logger.critical(f"Grammar file not found: {args.grammar}")
        return 1
        
    if not args.document.exists():
        logger.critical(f"Document file not found: {args.document}")
        return 1
    
    # Execute requested operation
    if args.unparse:
        success = handle_unparse(args.grammar, args.document)
    elif args.serialize:
        success = handle_serialize(args.grammar, args.document)
    elif args.roundtrip:
        success = handle_roundtrip(args.grammar, args.document)
    elif args.validate_against:
        if not args.validate_against.exists():
            logger.critical(f"Comparison file not found: {args.validate_against}")
            return 1
        success = handle_validate_against(args.grammar, args.document, 
                                         args.validate_against)
    else:
        success = handle_parse(args.grammar, args.document)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())