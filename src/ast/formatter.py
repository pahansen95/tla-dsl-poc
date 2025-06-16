#!/usr/bin/env python3
"""
AST Formatter Module

Transforms Abstract Syntax Trees back into formatted Concrete Syntax Trees.
"""

from typing import List, Dict, Any
from lark import Tree

from common import TokenFactory
from .utils import create_indent
from .nodes import Specification, Property


class ASTFormatter:
  """Format AST nodes into CST with canonical style."""

  def __init__(self, style: Dict[str, Any] = None):
    self.style = style or {"indent_size": 2, "section_spacing": 1, "bullet_char": "-"}
    self.tokens = TokenFactory()

  def format(self, ast: Specification) -> Tree:
    """Convert AST specification to formatted CST."""
    sections = []

    # Build sections
    sections.append(self._format_header(ast))

    if ast.concepts:
      sections.append(self._format_definitions(ast))

    if ast.states:
      sections.append(self._format_states(ast))

    if ast.operations:
      sections.append(self._format_operations(ast))

    # Split properties back into constraints/guarantees
    constraints = [p for p in ast.properties if p.property_type == "constraint"]
    guarantees = [p for p in ast.properties if p.property_type == "guarantee"]

    if constraints or guarantees:
      sections.append(self._format_properties(constraints, guarantees))

    # Join sections with spacing
    children = []
    for i, section in enumerate(sections):
      children.append(section)
      if i < len(sections) - 1:
        for _ in range(self.style["section_spacing"]):
          children.append(self.tokens.newline())

    children.append(self.tokens.newline())

    return Tree("specification", children)

  def _format_header(self, ast: Specification) -> Tree:
    """Format header section."""
    children = [self.tokens.literal("System:"), self.tokens.whitespace()]

    name_tokens = self.tokens.from_text(ast.name)
    children.append(Tree("system_name", name_tokens))
    children.append(self.tokens.newline())

    if ast.description:
      children.append(self.tokens.newline())
      desc_tokens = self.tokens.from_text(ast.description)
      children.append(Tree("description", desc_tokens))

    return Tree("header", children)

  def _format_definitions(self, ast: Specification) -> Tree:
    """Format concepts section."""
    children = [self.tokens.newline()]
    children.extend(self.tokens.from_text("The system uses these concepts:"))
    children.append(self.tokens.newline())

    concept_items = []
    for concept in ast.concepts:
      concept_items.extend([self.tokens.literal(self.style["bullet_char"]), self.tokens.whitespace()])

      name_tokens = self.tokens.from_text(concept.name)
      concept_items.append(Tree("concept_name", name_tokens))

      concept_items.extend([self.tokens.literal(":"), self.tokens.whitespace()])

      desc_tokens = self.tokens.from_text(concept.description)
      concept_items.append(Tree("concept_description", desc_tokens))
      concept_items.append(self.tokens.newline())

    children.append(Tree("concept_list", concept_items))

    return Tree("definitions", children)

  def _format_states(self, ast: Specification) -> Tree:
    """Format state section."""
    children = [self.tokens.newline()]
    children.extend(self.tokens.from_text("The system maintains:"))
    children.extend([self.tokens.newline(), self.tokens.newline()])

    state_items = []
    for i, state in enumerate(ast.states):
      # State header
      name_tokens = self.tokens.from_text(state.name)
      header = Tree("state_header", [Tree("state_name", name_tokens), self.tokens.literal(":"), self.tokens.newline()])

      # Properties
      prop_items = []
      all_props = state.properties[:]
      if state.initial_condition:
        all_props.append(state.initial_condition)

      for prop in all_props:
        prop_items.append(create_indent(1, self.style["indent_size"]))
        prop_tokens = self.tokens.from_text(prop)
        prop_items.append(Tree("property_line", prop_tokens))
        prop_items.append(self.tokens.newline())

      state_items.append(header)
      state_items.append(Tree("state_properties", prop_items))

      if i < len(ast.states) - 1:
        state_items.append(self.tokens.newline())

    children.append(Tree("state_list", state_items))

    return Tree("state_section", children)

  def _format_operations(self, ast: Specification) -> Tree:
    """Format operations section."""
    op_items = []

    for op in ast.operations:
      items = [self.tokens.newline(), self.tokens.literal("When"), self.tokens.whitespace()]

      trigger_tokens = self.tokens.from_text(op.trigger)
      items.append(Tree("trigger", trigger_tokens))
      items.extend([self.tokens.literal(":"), self.tokens.newline()])

      # Preconditions
      precond_items = []
      for precond in op.preconditions:
        precond_items.append(create_indent(1, self.style["indent_size"]))
        line_tokens = self.tokens.from_text(precond)
        precond_items.append(Tree("precondition_line", line_tokens))
        precond_items.append(self.tokens.newline())

      # Then marker
      trans_items = [create_indent(1, self.style["indent_size"]), self.tokens.literal("Then:"), self.tokens.newline()]

      # Effects
      effect_items = []
      all_effects = op.effects + op.unchanged
      for effect in all_effects:
        effect_items.append(create_indent(2, self.style["indent_size"]))
        effect_items.extend([self.tokens.literal(self.style["bullet_char"]), self.tokens.whitespace()])

        effect_tokens = self.tokens.from_text(effect)
        content = Tree("effect_content", effect_tokens + [self.tokens.newline()])
        effect_items.append(Tree("effect", [content]))

      # Build operation
      body = Tree("operation_body", precond_items + [Tree("transition_marker", trans_items)] + effect_items)

      op_items.append(Tree("operation", items + [body]))

    return Tree("operations", op_items)

  def _format_properties(self, constraints: List[Property], guarantees: List[Property]) -> Tree:
    """Format constraints and guarantees sections."""
    children = []

    # Constraints
    if constraints:
      children.append(self.tokens.newline())
      children.extend(self.tokens.from_text("System Constraints:"))
      children.extend([self.tokens.newline(), self.tokens.newline()])

      constraint_items = []
      for prop in constraints:
        constraint_items.extend(self._format_property(prop, "constraint_item"))
        constraint_items.append(self.tokens.newline())

      children.append(Tree("constraint_list", constraint_items))

    # Guarantees
    if guarantees:
      children.append(self.tokens.newline())
      children.extend(self.tokens.from_text("System Guarantees:"))
      children.extend([self.tokens.newline(), self.tokens.newline()])

      guarantee_items = []
      for prop in guarantees:
        guarantee_items.extend(self._format_property(prop, "guarantee_item"))
        guarantee_items.append(self.tokens.newline())

      children.append(Tree("guarantee_list", guarantee_items))

    return Tree("constraints", children)

  def _format_property(self, prop: Property, node_type: str) -> List:
    """Format a single property."""
    items = []

    name_tokens = self.tokens.from_text(prop.name)
    items.append(Tree("property_name", name_tokens))
    items.extend([self.tokens.literal(":"), self.tokens.newline(), create_indent(1, self.style["indent_size"])])

    content_tokens = self.tokens.from_text(prop.content)
    items.append(Tree("property_content", content_tokens))

    return [Tree(node_type, items)]


# Convenience function
def format_ast(ast: Specification, style: Dict[str, Any] = None) -> Tree:
  """Format AST to CST using canonical formatter."""
  return ASTFormatter(style).format(ast)
