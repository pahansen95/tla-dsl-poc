#!/usr/bin/env python3
"""
AST Builder Module

Transforms Concrete Syntax Trees into Abstract Syntax Trees.
"""

from typing import List, Optional
from lark import Tree

from cst import find_child, find_all
from common import extract_text
from .nodes import Specification, Concept, StateDeclaration, Operation, Property


class ASTBuilder:
  """Build AST from CST by extracting semantic content."""

  def build(self, cst: Tree) -> Specification:
    """Transform CST to AST specification."""
    # Extract header
    header = self._find_required(cst, "header", "Missing header section")
    spec = Specification(
      name=self._extract_from_child(header, "system_name", "Unnamed"), description=self._extract_description(header)
    )

    # Extract sections
    if definitions := find_child(cst, "definitions"):
      spec.concepts = self._extract_named_items(
        definitions, "concept_def", Concept, "concept_name", "concept_description"
      )

    if states := find_child(cst, "state_section"):
      spec.states = self._extract_states(states)

    if operations := find_child(cst, "operations"):
      spec.operations = self._extract_operations(operations)

    if constraints := find_child(cst, "constraints"):
      spec.properties = self._extract_properties(constraints)

    return spec

  def _extract_description(self, header: Tree) -> str:
    """Extract multi-line description from header."""
    if desc := find_child(header, "description"):
      lines = extract_text(desc, "lines")
      return " ".join(lines)
    return ""

  def _extract_named_items(
    self, parent: Tree, item_type: str, constructor, name_field: str, desc_field: str = None
  ) -> List:
    """
    Generic extraction for named items.

    Reduces duplication in extracting concepts, properties, etc.
    """
    items = []
    for node in find_all(parent, item_type):
      name = self._extract_from_child(node, name_field)
      if name:
        if desc_field:
          desc = self._extract_from_child(node, desc_field, "")
          items.append(constructor(name, desc))
        else:
          items.append(constructor(name))
    return items

  def _extract_states(self, state_section: Tree) -> List[StateDeclaration]:
    """Extract state declarations."""
    states = []

    for block in find_all(state_section, "state_block"):
      if name := self._extract_from_child(block, "state_name"):
        properties = []
        if props := find_child(block, "state_properties"):
          properties = [extract_text(line, "line") for line in find_all(props, "property_line")]

        states.append(StateDeclaration(name, properties))

    return states

  def _extract_operations(self, operations_node: Tree) -> List[Operation]:
    """Extract operation definitions."""
    operations = []

    for op in find_all(operations_node, "operation"):
      trigger = self._extract_from_child(op, "trigger", "")

      # Extract preconditions
      preconditions = [extract_text(line, "line") for line in find_all(op, "precondition_line")]

      # Extract effects
      effects = []
      for effect in find_all(op, "effect"):
        if content := find_child(effect, "effect_content"):
          lines = extract_text(content, "lines")
          effects.append(" ".join(lines))

      operations.append(Operation(trigger, preconditions, effects))

    return operations

  def _extract_properties(self, constraints_node: Tree) -> List[Property]:
    """Extract both constraints and guarantees as unified properties."""
    properties = []

    # Extract constraints
    if constraint_list := find_child(constraints_node, "constraint_list"):
      for item in find_all(constraint_list, "constraint_item"):
        if prop := self._extract_named_property(item):
          properties.append(Property(prop[0], prop[1], "constraint"))

    # Extract guarantees
    if guarantee_list := find_child(constraints_node, "guarantee_list"):
      for item in find_all(guarantee_list, "guarantee_item"):
        if prop := self._extract_named_property(item):
          properties.append(Property(prop[0], prop[1], "guarantee"))

    return properties

  def _extract_named_property(self, node: Tree) -> Optional[tuple[str, str]]:
    """Extract name and content from property node."""
    name = self._extract_from_child(node, "property_name")
    content = ""

    if content_node := find_child(node, "property_content"):
      lines = extract_text(content_node, "lines")
      content = " ".join(lines)

    return (name, content) if name and content else None

  def _extract_from_child(self, parent: Tree, child_name: str, default: str = None) -> Optional[str]:
    """Extract text from named child node."""
    if child := find_child(parent, child_name):
      return extract_text(child, "line")
    return default

  def _find_required(self, parent: Tree, child_name: str, error_msg: str) -> Tree:
    """Find required child node or raise error."""
    if child := find_child(parent, child_name):
      return child
    raise ValueError(error_msg)


# Convenience function
def build_ast(cst: Tree) -> Specification:
  """Build AST from CST using default builder."""
  return ASTBuilder().build(cst)
