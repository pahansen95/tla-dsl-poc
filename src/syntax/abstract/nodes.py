#!/usr/bin/env python3
"""
AST Node Definitions

Abstract Syntax Tree nodes for the Natural Language Specification DSL.
"""

from typing import List, Optional


class ASTNode:
  """Base class for all AST nodes with visitor support."""

  def accept(self, visitor):
    """Accept visitor for traversal/transformation."""
    method_name = f"visit_{self.__class__.__name__}"
    method = getattr(visitor, method_name, visitor.generic_visit)
    return method(self)


class Specification(ASTNode):
  """Root node representing a complete specification."""

  def __init__(self, name: str, description: str):
    self.name = name
    self.description = description
    self.concepts: List[Concept] = []
    self.states: List[StateDeclaration] = []
    self.operations: List[Operation] = []
    self.properties: List[Property] = []  # Unified constraints/guarantees


class Concept(ASTNode):
  """Domain concept or type definition."""

  def __init__(self, name: str, description: str):
    self.name = name
    self.description = description


class StateDeclaration(ASTNode):
  """State variable with properties and initial condition."""

  def __init__(self, name: str, properties: List[str]):
    self.name = name
    self.properties = []
    self.initial_condition: Optional[str] = None

    # Extract initial condition from properties
    for prop in properties:
      if prop.lower().strip().startswith("initially"):
        self.initial_condition = prop
      else:
        self.properties.append(prop)


class Operation(ASTNode):
  """State transition with trigger, preconditions, and effects."""

  def __init__(self, trigger: str, preconditions: List[str], effects: List[str]):
    self.trigger = trigger
    self.preconditions = preconditions
    self.effects = []
    self.unchanged = []

    # Separate unchanged variables from effects
    for effect in effects:
      effect_lower = effect.lower()
      if "unchanged" in effect_lower or "remain" in effect_lower:
        self.unchanged.append(effect)
      else:
        self.effects.append(effect)


class Property(ASTNode):
  """Unified property for constraints and guarantees."""

  def __init__(self, name: str, content: str, property_type: str):
    self.name = name
    self.content = content
    self.property_type = property_type  # 'constraint' or 'guarantee'


class ASTVisitor:
  """Base visitor for AST traversal."""

  def visit(self, node: ASTNode):
    """Entry point for visiting nodes."""
    return node.accept(self)

  def generic_visit(self, node: ASTNode):
    """Default traversal implementation."""
    for attr_name, attr_value in node.__dict__.items():
      if isinstance(attr_value, list):
        for item in attr_value:
          if isinstance(item, ASTNode):
            self.visit(item)
      elif isinstance(attr_value, ASTNode):
        self.visit(attr_value)
