"""AST node definitions for Natural Specification Language.

Provides frozen dataclass definitions for all AST nodes used in the
Natural Specification Language. These immutable structures form the
core data model for parsed specifications.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Concept:
  """Domain concept definition."""

  name: str
  description: str


@dataclass(frozen=True, slots=True)
class StateDeclaration:
  """State variable declaration."""

  name: str
  properties: tuple[str, ...] = ()
  initial_condition: Optional[str] = None


@dataclass(frozen=True, slots=True)
class Operation:
  """System operation with trigger and effects."""

  trigger: str
  preconditions: tuple[str, ...] = ()
  effects: tuple[str, ...] = ()
  unchanged: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Property:
  """System property (constraint or guarantee)."""

  name: str
  content: str
  property_type: str  # 'constraint' or 'guarantee'


@dataclass(frozen=True, slots=True)
class Specification:
  """Complete system specification."""

  name: str
  description: str
  concepts: tuple[Concept, ...] = ()
  states: tuple[StateDeclaration, ...] = ()
  operations: tuple[Operation, ...] = ()
  properties: tuple[Property, ...] = ()