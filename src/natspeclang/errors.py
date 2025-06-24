"""
Domain-specific exceptions for the Natural Specification Language.

Provides rich error types with position context and helpful diagnostics
for lexical, syntactic, and semantic errors encountered during processing.
"""

from typing import Optional
from .types import Position


class NSLError(Exception):
  """Base exception for all NSL errors with position context."""

  def __init__(
    self, message: str, position: Optional[Position] = None, source: Optional[str] = None, hint: Optional[str] = None
  ):
    self.message = message
    self.position = position
    self.source = source
    self.hint = hint

    # Build formatted error message
    error_parts = [message]

    if position:
      error_parts.append(f" at line {position.line}, column {position.column}")

    if source and position:
      # Extract source line for context
      lines = source.split("\n")
      if 0 <= position.line - 1 < len(lines):
        line_text = lines[position.line - 1]
        pointer = " " * (position.column - 1) + "^"
        error_parts.extend([f"\n{line_text}", f"\n{pointer}"])

    if hint:
      error_parts.append(f"\nHint: {hint}")

    super().__init__("".join(error_parts))


class LexicalError(NSLError):
  """Token recognition or pattern matching failure."""

  def __init__(
    self,
    message: str,
    position: Optional[Position] = None,
    source: Optional[str] = None,
    expected: Optional[str] = None,
    found: Optional[str] = None,
  ):
    if expected and found:
      hint = f"Expected {expected}, but found {found}"
    elif expected:
      hint = f"Expected {expected}"
    elif found:
      hint = f"Unexpected {found}"
    else:
      hint = None

    super().__init__(message, position, source, hint)
    self.expected = expected
    self.found = found


class SyntaxError(NSLError):
  """Grammar rule violation or structural error."""

  def __init__(
    self,
    message: str,
    position: Optional[Position] = None,
    source: Optional[str] = None,
    rule: Optional[str] = None,
    recovery_hint: Optional[str] = None,
  ):
    hint = recovery_hint
    if rule and not hint:
      hint = f"Error occurred while parsing '{rule}'"

    super().__init__(message, position, source, hint)
    self.rule = rule
    self.recovery_hint = recovery_hint


class SemanticError(NSLError):
  """AST construction or validation failure."""

  def __init__(
    self,
    message: str,
    position: Optional[Position] = None,
    source: Optional[str] = None,
    node_type: Optional[str] = None,
    constraint: Optional[str] = None,
  ):
    hint = None
    if constraint:
      hint = f"Constraint violated: {constraint}"
    elif node_type:
      hint = f"Error in {node_type} node"

    super().__init__(message, position, source, hint)
    self.node_type = node_type
    self.constraint = constraint


class TransformationError(NSLError):
  """Transformation between representations failed."""

  def __init__(
    self,
    message: str,
    from_type: str,
    to_type: str,
    position: Optional[Position] = None,
    source: Optional[str] = None,
    reason: Optional[str] = None,
  ):
    hint = f"Failed to transform {from_type} to {to_type}"
    if reason:
      hint += f": {reason}"

    super().__init__(message, position, source, hint)
    self.from_type = from_type
    self.to_type = to_type
    self.reason = reason


class SerializationError(NSLError):
  """JSON serialization or deserialization failure."""

  def __init__(
    self,
    message: str,
    operation: str,  # 'serialize' or 'deserialize'
    node_type: Optional[str] = None,
    position: Optional[Position] = None,
    source: Optional[str] = None,
  ):
    hint = f"Failed to {operation}"
    if node_type:
      hint += f" {node_type}"

    super().__init__(message, position, source, hint)
    self.operation = operation
    self.node_type = node_type
