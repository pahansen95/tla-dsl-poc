"""Error types for Natural Specification Language.

Provides structured exceptions for different error categories with
position tracking and contextual information.
"""

# Standard library imports
from typing import Any, Optional

# Local imports
from lexical import Position


class NSLError(Exception):
  """Base exception for all NSL-related errors.

  Provides common error context tracking and formatting.
  """

  __slots__ = ("message", "context")

  def __init__(self, message: str, **context: Any):
    """Initialize with message and optional context."""
    super().__init__(message)
    self.message = message
    self.context = context


class SyntaxError(NSLError):
  """Syntax error in NSL document.

  Raised during lexing or parsing when document structure
  violates NSL grammar rules.
  """

  __slots__ = ("position",)

  def __init__(self, message: str, position: Optional[Position] = None, **context: Any):
    """Initialize with position information."""
    super().__init__(message, position=position, **context)
    self.position = position

  def __str__(self) -> str:
    """Format error with position context."""
    if self.position:
      return f"{self.message} at line {self.position.line}, column {self.position.column}"
    return self.message


class SemanticError(NSLError):
  """Semantic error in NSL document.

  Raised during AST construction when document meaning
  violates NSL semantic rules.
  """

  __slots__ = ("node_type",)

  def __init__(self, message: str, node_type: Optional[str] = None, **context: Any):
    """Initialize with node type information."""
    super().__init__(message, node_type=node_type, **context)
    self.node_type = node_type

  def __str__(self) -> str:
    """Format error with semantic context."""
    if self.node_type:
      return f"{self.message} in {self.node_type} node"
    return self.message


class TransformationError(NSLError):
  """Error during format transformation.

  Raised when transformation between formats fails due to
  incompatible structures or missing information.
  """

  __slots__ = ("source_format", "target_format")

  def __init__(
    self, message: str, source_format: Optional[str] = None, target_format: Optional[str] = None, **context: Any
  ):
    """Initialize with format information."""
    super().__init__(message, source_format=source_format, target_format=target_format, **context)
    self.source_format = source_format
    self.target_format = target_format

  def __str__(self) -> str:
    """Format error with transformation context."""
    if self.source_format and self.target_format:
      return f"{self.message} transforming {self.source_format} to {self.target_format}"
    return self.message


# Explicit exports
__all__ = [
  "NSLError",
  "SyntaxError",
  "SemanticError",
  "TransformationError",
]
