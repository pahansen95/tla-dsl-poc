#!/usr/bin/env python3
"""
AST Node Definitions

This module defines the Abstract Syntax Tree nodes for the Natural Language
Specification DSL. Each node represents a semantic concept in the specification
domain, abstracting away syntactic details while preserving behavioral meaning.

The AST serves as an intermediate representation between the Concrete Syntax
Tree (CST) and potential target formats like TLA+ or the Intermediate
Representation (IR).
"""

from typing import List, Optional, Dict


class ASTNode:
  """
  Base class for all AST nodes.

  Provides common functionality including visitor pattern support
  and optional source location tracking for error reporting.
  """

  def __init__(self):
    self.source_location: Optional[Dict[str, int]] = None

  def accept(self, visitor):
    """
    Accept a visitor for traversal/transformation.

    Uses naming convention to find appropriate visit method.
    Falls back to generic_visit if specific method not found.
    """
    method_name = f"visit_{self.__class__.__name__}"
    method = getattr(visitor, method_name, visitor.generic_visit)
    return method(self)

  def __repr__(self):
    attrs = [f"{k}={repr(v)}" for k, v in self.__dict__.items() if not k.startswith("_") and k != "source_location"]
    return f"{self.__class__.__name__}({', '.join(attrs)})"


class Specification(ASTNode):
  """
  Root AST node representing a complete specification.

  Contains all major components of a specification including
  system metadata, type definitions, state declarations,
  operations, and properties.
  """

  def __init__(self, name: str, description: str):
    super().__init__()
    self.name = name
    self.description = description
    self.concepts: List[Concept] = []
    self.states: List[StateDeclaration] = []
    self.operations: List[Operation] = []
    self.constraints: List[Constraint] = []
    self.guarantees: List[Guarantee] = []


class Concept(ASTNode):
  """
  Type or concept definition used by the system.

  Represents domain concepts like "Client Identity" or "Request"
  that establish the vocabulary used throughout the specification.
  """

  def __init__(self, name: str, description: str):
    super().__init__()
    self.name = name
    self.description = description


class StateDeclaration(ASTNode):
  """
  State variable declaration with properties.

  Represents system state components with their behavioral
  properties and initial conditions.
  """

  def __init__(self, name: str, properties: List[str]):
    super().__init__()
    self.name = name
    self.properties = properties
    self.initial_condition: Optional[str] = None
    self._extract_initial_condition()

  def _extract_initial_condition(self):
    """Extract initial condition from properties if present."""
    for i, prop in enumerate(self.properties):
      if prop.lower().strip().startswith("initially"):
        self.initial_condition = prop
        self.properties.pop(i)
        break


class Operation(ASTNode):
  """
  Behavioral operation with trigger, preconditions, and effects.

  Represents state transitions in the system, capturing when
  transitions can occur and their resulting state changes.
  """

  def __init__(self, trigger: str, preconditions: List[str], effects: List[str]):
    super().__init__()
    self.trigger = trigger
    self.preconditions = preconditions
    self.effects = effects
    self.unchanged: List[str] = []
    self._extract_unchanged_variables()

  def _extract_unchanged_variables(self):
    """Identify variables marked as unchanged in effects."""
    remaining_effects = []
    for effect in self.effects:
      effect_lower = effect.lower()
      if "unchanged" in effect_lower or "remain" in effect_lower:
        self.unchanged.append(effect)
      else:
        remaining_effects.append(effect)
    self.effects = remaining_effects


class NamedProperty(ASTNode):
  """
  Base class for named properties (constraints and guarantees).

  Provides common structure for system properties that have
  a name and associated content/formula.
  """

  def __init__(self, name: str, content: str):
    super().__init__()
    self.name = name
    self.content = content


class Constraint(NamedProperty):
  """
  System constraint (safety property).

  Represents invariants that must always hold true
  in any valid system state.
  """

  pass


class Guarantee(NamedProperty):
  """
  System guarantee (liveness property).

  Represents properties that the system promises to
  eventually satisfy or maintain.
  """

  pass


# Visitor base class for AST traversal
class ASTVisitor:
  """
  Base visitor class for AST traversal and transformation.

  Subclasses should override specific visit_* methods to
  implement custom behavior for each node type.
  """

  def visit(self, node: ASTNode):
    """Visit a node using its accept method."""
    return node.accept(self)

  def generic_visit(self, node: ASTNode):
    """
    Default visit implementation.

    Recursively visits all child nodes stored as attributes.
    Handles both single nodes and lists of nodes.
    """
    for attr_name in node.__dict__:
      if attr_name.startswith("_"):
        continue

      attr_value = getattr(node, attr_name)

      if isinstance(attr_value, list):
        for item in attr_value:
          if isinstance(item, ASTNode):
            self.visit(item)
      elif isinstance(attr_value, ASTNode):
        self.visit(attr_value)

  # Specific visit methods to be overridden in subclasses
  def visit_Specification(self, node: Specification):
    self.generic_visit(node)

  def visit_Concept(self, node: Concept):
    self.generic_visit(node)

  def visit_StateDeclaration(self, node: StateDeclaration):
    self.generic_visit(node)

  def visit_Operation(self, node: Operation):
    self.generic_visit(node)

  def visit_Constraint(self, node: Constraint):
    self.generic_visit(node)

  def visit_Guarantee(self, node: Guarantee):
    self.generic_visit(node)


# Utility functions for AST manipulation
def find_nodes_by_type(root: ASTNode, node_type: type) -> List[ASTNode]:
  """
  Find all nodes of a specific type in the AST.

  Uses visitor pattern to collect all matching nodes.
  """

  class TypeCollector(ASTVisitor):
    def __init__(self, target_type):
      self.target_type = target_type
      self.results = []

    def generic_visit(self, node):
      if isinstance(node, self.target_type):
        self.results.append(node)
      super().generic_visit(node)

  collector = TypeCollector(node_type)
  collector.visit(root)
  return collector.results


def get_state_names(spec: Specification) -> List[str]:
  """Extract all state variable names from a specification."""
  return [state.name for state in spec.states]


def get_operation_triggers(spec: Specification) -> List[str]:
  """Extract all operation trigger descriptions."""
  return [op.trigger for op in spec.operations]
