"""
Natural Specification Language (NSL) Package.

A unified parsing and transformation system for structured natural language
specifications. Provides bidirectional transformations between textual DSL,
concrete syntax trees, and abstract syntax trees.

Basic Usage:
    from natspeclang import DSLLexer, DSLParser, ASTBuilder
    from lexical import LexicalContext

    # Parse DSL text to AST
    lexer = DSLLexer()
    tokens = list(lexer.lex(text))

    parser = DSLParser(tokens)
    cst = parser.parse()

    builder = ASTBuilder()
    ast = builder.build(cst)

Advanced Usage:
    from natspeclang import TransformationPipeline
    from observability import SharedContext
    from lexical import LexicalContext

    # With observability
    obs_context = LexicalContext(SharedContext.get())
    pipeline = TransformationPipeline(obs_context)

    # Transform with automatic type detection
    result = pipeline.transform(request)
"""

# Core types
from .types import (
  Position,
  TreeElement,
  TreeNode,
  TreeToken,
  TreeVisitor,
  ASTNode,
  EventHandler,
  TransformResult,
  FormatStyle,
)

# Error types
from .errors import NSLError, LexicalError, SyntaxError, SemanticError, TransformationError, SerializationError

# AST node types and core components from lex module
from .lex import (
  # AST nodes
  Concept,
  StateDeclaration,
  Operation,
  Property,
  Specification,
  # Core classes
  DSLLexer,
  DSLParser,
  ASTBuilder,
  ASTFormatter,
  # Serialization
  serialize_ast,
  deserialize_ast,
  serialize_cst,
  deserialize_cst,
)

# Pipeline API
from .pipeline import TransformationPipeline, TransformRequest, TypeInference

# Observability
from .instruments import configure_observability

# Version information
__version__ = "0.1.0"
__author__ = "NSL Contributors"

# Module-level documentation
__doc__ = __doc__

__all__ = [
  # Core types
  "Position",
  "TreeElement",
  "TreeNode",
  "TreeToken",
  "TreeVisitor",
  "ASTNode",
  "EventHandler",
  "TransformResult",
  "FormatStyle",
  # Errors
  "NSLError",
  "LexicalError",
  "SyntaxError",
  "SemanticError",
  "TransformationError",
  "SerializationError",
  # AST nodes
  "Concept",
  "StateDeclaration",
  "Operation",
  "Property",
  "Specification",
  # Core classes
  "DSLLexer",
  "DSLParser",
  "ASTBuilder",
  "ASTFormatter",
  # Serialization
  "serialize_ast",
  "deserialize_ast",
  "serialize_cst",
  "deserialize_cst",
  # Pipeline
  "TransformationPipeline",
  "TransformRequest",
  "TypeInference",
  # Observability
  "configure_observability",
  # Version
  "__version__",
]
