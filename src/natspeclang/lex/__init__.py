"""Natural Specification Language lexical analysis package.

Provides comprehensive lexical analysis, parsing, and transformation
capabilities for the Natural Specification Language. The package exposes
a clean public API while organizing implementation details into focused
modules.

Basic usage:
    from natspeclang.lex import parse, format_ast
    
    spec = parse(dsl_text)
    formatted = format_ast(spec)

Advanced usage:
    from natspeclang.lex import DSLLexer, DSLParser, ASTBuilder
    
    lexer = DSLLexer()
    tokens = list(lexer.lex(text))
    parser = DSLParser(tokens)
    cst = parser.parse()
"""

from typing import Optional

from lexical import LexicalContext

from ..types import FormatStyle

# Import AST types
from .ast import (
    Specification,
    Concept,
    StateDeclaration,
    Operation,
    Property,
)

# Import core components
from .tokenize import DSLLexer
from .parse import DSLParser
from .transform import ASTBuilder
from .format import ASTFormatter
from .serde import serialize_ast, deserialize_ast, serialize_cst, deserialize_cst


# High-level API functions

def parse(text: str, obs_context: Optional[LexicalContext] = None) -> Specification:
    """
    Parse DSL text to AST.
    
    Args:
        text: Natural Specification Language text
        obs_context: Optional observability context for instrumentation
        
    Returns:
        Parsed specification AST
        
    Raises:
        LexicalError: Token recognition failure
        SyntaxError: Grammar rule violation
        SemanticError: AST construction failure
    """
    # Lexical analysis
    lexer = DSLLexer(obs_context)
    tokens = list(lexer.lex(text))
    
    # Syntax analysis
    parser = DSLParser(tokens, obs_context)
    cst = parser.parse()
    
    # For integrated parser, CST root is the AST
    return cst.root


def format_ast(spec: Specification, style: Optional[FormatStyle] = None) -> str:
    """
    Format AST to DSL text.
    
    Args:
        spec: Specification AST to format
        style: Optional formatting style configuration
        
    Returns:
        Formatted DSL text
    """
    formatter = ASTFormatter(style)
    return formatter.format(spec)


def parse_to_json(text: str, obs_context: Optional[LexicalContext] = None) -> str:
    """
    Parse DSL text and serialize to JSON.
    
    Args:
        text: Natural Specification Language text
        obs_context: Optional observability context
        
    Returns:
        JSON serialized AST
    """
    spec = parse(text, obs_context)
    return serialize_ast(spec)


def format_from_json(json_str: str, style: Optional[FormatStyle] = None) -> str:
    """
    Deserialize JSON and format to DSL text.
    
    Args:
        json_str: JSON serialized AST
        style: Optional formatting style
        
    Returns:
        Formatted DSL text
    """
    spec = deserialize_ast(json_str)
    return format_ast(spec, style)


# Public API exports
__all__ = [
    # AST types
    'Specification',
    'Concept', 
    'StateDeclaration',
    'Operation',
    'Property',
    # Core classes
    'DSLLexer',
    'DSLParser',
    'ASTBuilder',
    'ASTFormatter',
    # High-level functions
    'parse',
    'format_ast',
    'parse_to_json',
    'format_from_json',
    # Serialization
    'serialize_ast',
    'deserialize_ast',
    'serialize_cst',
    'deserialize_cst',
]