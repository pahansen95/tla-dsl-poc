#!/usr/bin/env python3
"""
AST to CST Formatter

Generates Concrete Syntax Trees from Abstract Syntax Trees using
canonical formatting rules. This enables AST-based transformations
while producing consistently formatted output.

The formatter applies deterministic formatting rules, ensuring
reproducible output regardless of the original source formatting.
"""

from typing import List, Dict, Any
from lark import Tree, Token

from .nodes import Specification, Concept, StateDeclaration, Operation, Constraint, Guarantee


class CanonicalFormatter:
  """
  Formats AST nodes into CST structures with canonical style.

  Applies consistent formatting rules for indentation, spacing,
  and structure to produce well-formatted DSL documents.
  """

  def __init__(self, style: Dict[str, Any] = None):
    """
    Initialize formatter with style configuration.

    Args:
        style: Formatting preferences (indent size, spacing, etc.)
    """
    self.style = style or self._default_style()

  def _default_style(self) -> Dict[str, Any]:
    """Default formatting style."""
    return {
      "indent_size": 2,
      "section_spacing": 1,  # Blank lines between sections
      "bullet_char": "-",
      "colon_space": True,  # Space before colons
    }

  def format(self, ast: Specification) -> Tree:
    """
    Format an AST specification into a CST.

    Generates a complete CST structure with canonical formatting
    that can be unparsed to produce formatted DSL text.
    """
    sections = []

    # Header section
    sections.append(self._format_header(ast))

    # Definitions section
    if ast.concepts:
      sections.append(self._format_definitions(ast))

    # State section
    if ast.states:
      sections.append(self._format_state_section(ast))

    # Operations section
    if ast.operations:
      sections.append(self._format_operations(ast))

    # Constraints section
    if ast.constraints or ast.guarantees:
      sections.append(self._format_constraints(ast))

    # Combine sections with spacing
    children = self._join_sections(sections)

    return Tree("specification", children)

  def _format_header(self, ast: Specification) -> Tree:
    """Format the header section."""
    children = []

    # "System:" label
    children.append(Token("LITERAL", "System:"))
    children.append(Token("WS", " "))

    # System name
    name_tokens = self._text_to_tokens(ast.name)
    children.append(Tree("system_name", name_tokens))
    children.append(Token("NEWLINE", "\n"))

    # Description (can be multi-line)
    if ast.description:
      children.append(Token("NEWLINE", "\n"))
      desc_tokens = self._text_to_tokens(ast.description)
      children.append(Tree("description", desc_tokens))

    return Tree("header", children)

  def _format_definitions(self, ast: Specification) -> Tree:
    """Format the concepts/definitions section."""
    children = []

    # Section header
    children.append(Token("NEWLINE", "\n"))
    children.extend(self._text_to_tokens("The system uses these concepts:"))
    children.append(Token("NEWLINE", "\n"))

    # Concept list
    concept_children = []
    for concept in ast.concepts:
      concept_children.extend(self._format_concept(concept))

    children.append(Tree("concept_list", concept_children))

    return Tree("definitions", children)

  def _format_concept(self, concept: Concept) -> List:
    """Format a single concept definition."""
    tokens = []

    # Bullet point
    tokens.append(Token("LITERAL", self.style["bullet_char"]))
    tokens.append(Token("WS", " "))

    # Concept name
    name_tokens = self._text_to_tokens(concept.name)
    tokens.append(Tree("concept_name", name_tokens))

    # Colon separator
    tokens.append(Token("LITERAL", ":"))
    tokens.append(Token("WS", " "))

    # Description
    desc_tokens = self._text_to_tokens(concept.description)
    tokens.append(Tree("concept_description", desc_tokens))

    tokens.append(Token("NEWLINE", "\n"))

    return tokens

  def _format_state_section(self, ast: Specification) -> Tree:
    """Format the state maintenance section."""
    children = []

    # Section header
    children.append(Token("NEWLINE", "\n"))
    children.extend(self._text_to_tokens("The system maintains:"))
    children.append(Token("NEWLINE", "\n"))
    children.append(Token("NEWLINE", "\n"))

    # State blocks
    state_children = []
    for i, state in enumerate(ast.states):
      state_children.extend(self._format_state_block(state))
      # Add spacing between blocks except after last
      if i < len(ast.states) - 1:
        state_children.append(Token("NEWLINE", "\n"))

    children.append(Tree("state_list", state_children))

    return Tree("state_section", children)

  def _format_state_block(self, state: StateDeclaration) -> List:
    """Format a state declaration block."""
    # State name and colon
    header_tokens = []
    name_tokens = self._text_to_tokens(state.name)
    header_tokens.append(Tree("state_name", name_tokens))
    header_tokens.append(Token("LITERAL", ":"))
    header_tokens.append(Token("NEWLINE", "\n"))

    # Properties with indentation
    prop_tokens = []
    all_props = state.properties[:]
    if state.initial_condition:
      all_props.append(state.initial_condition)

    for prop in all_props:
      prop_tokens.append(self._indent_token())
      prop_line_tokens = self._text_to_tokens(prop)
      prop_tokens.append(Tree("property_line", prop_line_tokens))
      prop_tokens.append(Token("NEWLINE", "\n"))

    return [Tree("state_header", header_tokens), Tree("state_properties", prop_tokens)]

  def _format_operations(self, ast: Specification) -> Tree:
    """Format the operations section."""
    op_children = []

    for operation in ast.operations:
      op_children.extend(self._format_operation(operation))

    return Tree("operations", op_children)

  def _format_operation(self, op: Operation) -> List:
    """Format a single operation."""
    tokens = []

    # Operation header
    tokens.append(Token("NEWLINE", "\n"))
    tokens.append(Token("LITERAL", "When"))
    tokens.append(Token("WS", " "))
    trigger_tokens = self._text_to_tokens(op.trigger)
    tokens.append(Tree("trigger", trigger_tokens))
    tokens.append(Token("LITERAL", ":"))
    tokens.append(Token("NEWLINE", "\n"))

    # Preconditions
    precond_tokens = []
    for precond in op.preconditions:
      precond_tokens.append(self._indent_token())
      line_tokens = self._text_to_tokens(precond)
      precond_tokens.append(Tree("precondition_line", line_tokens))
      precond_tokens.append(Token("NEWLINE", "\n"))

    # Then marker
    trans_tokens = []
    trans_tokens.append(self._indent_token())
    trans_tokens.append(Token("LITERAL", "Then:"))
    trans_tokens.append(Token("NEWLINE", "\n"))

    # Effects
    effect_tokens = []
    all_effects = op.effects + op.unchanged
    for effect in all_effects:
      effect_tokens.append(self._double_indent_token())
      effect_tokens.append(Token("LITERAL", self.style["bullet_char"]))
      effect_tokens.append(Token("WS", " "))

      effect_content_tokens = self._text_to_tokens(effect)
      effect_content = Tree("effect_content", effect_content_tokens)
      effect_content.append(Token("NEWLINE", "\n"))

      effect_tokens.append(Tree("effect", [effect_content]))

    # Build operation body
    body = Tree("operation_body", precond_tokens + [Tree("transition_marker", trans_tokens)] + effect_tokens)

    return [Tree("operation", tokens + [body])]

  def _format_constraints(self, ast: Specification) -> Tree:
    """Format constraints and guarantees section."""
    children = []

    # Constraints subsection
    if ast.constraints:
      children.append(Token("NEWLINE", "\n"))
      children.extend(self._text_to_tokens("System Constraints:"))
      children.append(Token("NEWLINE", "\n"))
      children.append(Token("NEWLINE", "\n"))

      constraint_items = []
      for constraint in ast.constraints:
        constraint_items.extend(self._format_named_property(constraint))
        constraint_items.append(Token("NEWLINE", "\n"))

      children.append(Tree("constraint_list", constraint_items))

    # Guarantees subsection
    if ast.guarantees:
      children.append(Token("NEWLINE", "\n"))
      children.extend(self._text_to_tokens("System Guarantees:"))
      children.append(Token("NEWLINE", "\n"))
      children.append(Token("NEWLINE", "\n"))

      guarantee_items = []
      for guarantee in ast.guarantees:
        guarantee_items.extend(self._format_named_property(guarantee))
        guarantee_items.append(Token("NEWLINE", "\n"))

      children.append(Tree("guarantee_list", guarantee_items))

    return Tree("constraints", children)

  def _format_named_property(self, prop: Constraint | Guarantee) -> List:
    """Format a named property (constraint or guarantee)."""
    tokens = []

    # Property name
    name_tokens = self._text_to_tokens(prop.name)
    tokens.append(Tree("property_name", name_tokens))
    tokens.append(Token("LITERAL", ":"))
    tokens.append(Token("NEWLINE", "\n"))

    # Property content (may be multi-line)
    tokens.append(self._indent_token())
    content_tokens = self._text_to_tokens(prop.content)
    tokens.append(Tree("property_content", content_tokens))

    node_type = "constraint_item" if isinstance(prop, Constraint) else "guarantee_item"
    return [Tree(node_type, tokens)]

  # Utility methods
  def _text_to_tokens(self, text: str) -> List[Token]:
    """Convert text string to list of tokens."""
    tokens = []
    words = text.split()

    for i, word in enumerate(words):
      # Classify token type
      if word.isdigit():
        tokens.append(Token("NUMBER", word))
      elif word.isalpha() or "_" in word:
        tokens.append(Token("WORD", word))
      else:
        # Mixed or symbolic
        tokens.append(Token("SYMBOL", word))

      # Add space between words
      if i < len(words) - 1:
        tokens.append(Token("WS", " "))

    return tokens

  def _indent_token(self) -> Token:
    """Create indent token based on style."""
    spaces = " " * self.style["indent_size"]
    return Token("INDENT", spaces)

  def _double_indent_token(self) -> Token:
    """Create double indent token."""
    spaces = " " * (self.style["indent_size"] * 2)
    return Token("DOUBLE_INDENT", spaces)

  def _join_sections(self, sections: List[Tree]) -> List:
    """Join sections with appropriate spacing."""
    if not sections:
      return []

    result = []
    for i, section in enumerate(sections):
      result.append(section)
      # Add spacing between sections
      if i < len(sections) - 1:
        for _ in range(self.style["section_spacing"]):
          result.append(Token("NEWLINE", "\n"))

    # End with newline
    result.append(Token("NEWLINE", "\n"))

    return result


# Convenience function
def format_ast(ast: Specification, style: Dict[str, Any] = None) -> Tree:
  """Format AST to CST using canonical formatter."""
  formatter = CanonicalFormatter(style)
  return formatter.format(ast)
