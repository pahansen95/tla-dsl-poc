"""
Type definitions and protocols for the Natural Specification Language.

Provides the foundational type contracts used throughout the NSL system,
including protocols for extensibility and type aliases for clarity.
"""

from typing import Protocol, TypeAlias, Optional, Union, Any
from dataclasses import dataclass


# Type aliases for semantic clarity
NodeId: TypeAlias = str
TokenType: TypeAlias = str
TokenValue: TypeAlias = str
RuleName: TypeAlias = str


@dataclass(frozen=True, slots=True)
class Position:
    """Immutable position in source text."""
    line: int
    column: int
    offset: int


# Tree element protocols
class TreeElement(Protocol):
    """Base protocol for all tree elements."""
    
    @property
    def position(self) -> Optional[Position]:
        """Source position if available."""
        ...


class TreeNode(Protocol):
    """Protocol for internal tree nodes."""
    kind: str
    children: tuple[TreeElement, ...]


class TreeToken(Protocol):
    """Protocol for leaf tokens."""
    type: TokenType
    value: TokenValue
    position: Position


# Visitor protocol for tree traversal
class TreeVisitor(Protocol):
    """Visitor protocol for tree traversal."""
    
    def visit(self, node: TreeElement) -> Any:
        """Visit a tree element."""
        ...
    
    def generic_visit(self, node: TreeElement) -> Any:
        """Default visitor for unhandled nodes."""
        ...


# AST node protocol
class ASTNode(Protocol):
    """Protocol for abstract syntax tree nodes."""
    
    def accept(self, visitor: TreeVisitor) -> Any:
        """Accept a visitor."""
        ...


# Serialization protocol
class Serializable(Protocol):
    """Protocol for JSON-serializable objects."""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        ...
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Serializable':
        """Reconstruct from dictionary."""
        ...


# Handler protocol for observability
class EventHandler(Protocol):
    """Protocol for event handlers."""
    
    def __call__(self, event: dict[str, Any]) -> None:
        """Process an event."""
        ...


# Transformation types
TransformResult = Union[Any, str]  # Will be SyntaxTree, Specification, or str
"""Result of a transformation operation."""

FormatStyle = dict[str, Any]
"""Formatting style configuration."""