"""
Natural Specification Language (NSL) Package.

A unified parsing and transformation system for structured natural language
specifications. Provides bidirectional transformations between textual DSL,
concrete syntax trees, and abstract syntax trees.

Basic Usage:
    from nsl import parse, format_ast
    
    # Parse DSL text to AST
    spec = parse(text)
    
    # Format AST back to text
    text = format_ast(spec)

Advanced Usage:
    from nsl import TransformationPipeline, LexicalContext
    from observability import SharedContext
    
    # With observability
    obs_context = LexicalContext(SharedContext.get())
    pipeline = TransformationPipeline(obs_context)
    
    # Transform with automatic type detection
    result = pipeline.transform(request)
"""

# Public API exports

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
    FormatStyle
)

# Error types
from .errors import (
    NSLError,
    LexicalError,
    SyntaxError,
    SemanticError,
    TransformationError,
    SerializationError
)

# AST node types
from .lex import (
    Concept,
    StateDeclaration,
    Operation,
    Property,
    Specification
)

# High-level API
from .lex import (
    parse,
    format_ast,
    parse_to_json,
    format_from_json,
    serialize_ast,
    deserialize_ast
)

# Pipeline API
from .pipeline import (
    TransformationPipeline,
    TransformRequest,
    TypeInference
)

# Observability
from .instruments import configure_observability

# Version information
__version__ = '0.1.0'
__author__ = 'NSL Contributors'

# Module-level documentation
__doc__ = __doc__

__all__ = [
    # Core types
    'Position',
    'TreeElement',
    'TreeNode', 
    'TreeToken',
    'TreeVisitor',
    'ASTNode',
    'EventHandler',
    'TransformResult',
    'FormatStyle',
    
    # Errors
    'NSLError',
    'LexicalError',
    'SyntaxError',
    'SemanticError',
    'TransformationError',
    'SerializationError',
    
    # AST nodes
    'Concept',
    'StateDeclaration',
    'Operation',
    'Property',
    'Specification',
    
    # High-level API
    'parse',
    'format_ast',
    'parse_to_json',
    'format_from_json',
    'serialize_ast',
    'deserialize_ast',
    
    # Pipeline
    'TransformationPipeline',
    'TransformRequest',
    'TypeInference',
    
    # Observability
    'configure_observability',
    
    # Version
    '__version__'
]