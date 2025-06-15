#!/usr/bin/env python3
"""
CST to AST Builder

Transforms Concrete Syntax Trees produced by the parser into Abstract
Syntax Trees suitable for semantic analysis and code generation.

The builder extracts semantic content from the CST while discarding
syntactic details like whitespace and punctuation.
"""

from typing import List, Optional
from lark import Tree, Token

from .nodes import Specification, Concept, StateDeclaration, Operation, Constraint, Guarantee


class TextExtractor:
  """
  Utilities for extracting clean text from CST nodes.

  Handles the complexity of token sequences, providing
  normalized text suitable for AST construction.
  """

  @staticmethod
  def extract_raw_text(node) -> str:
    """Extract all text content from a CST subtree."""
    if isinstance(node, Token):
      return str(node)
    elif isinstance(node, Tree):
      return "".join(TextExtractor.extract_raw_text(child) for child in node.children)
    else:
      return str(node)

  @staticmethod
  def extract_line(node) -> str:
    """Extract single line of text, normalizing whitespace."""
    raw = TextExtractor.extract_raw_text(node)
    # Collapse whitespace and trim
    return " ".join(raw.split())

  @staticmethod
  def extract_lines(node) -> List[str]:
    """
    Extract multiple lines from a node.

    Preserves line boundaries while normalizing whitespace
    within each line.
    """
    lines = []
    current_line = []

    def process_node(n):
      if isinstance(n, Token):
        if n.type == "NEWLINE":
          if current_line:
            # Join and normalize the current line
            line_text = "".join(current_line)
            normalized = " ".join(line_text.split())
            if normalized:
              lines.append(normalized)
            current_line.clear()
        else:
          current_line.append(str(n))
      elif isinstance(n, Tree):
        for child in n.children:
          process_node(child)
      else:
        current_line.append(str(n))

    process_node(node)

    # Don't forget the last line
    if current_line:
      line_text = "".join(current_line)
      normalized = " ".join(line_text.split())
      if normalized:
        lines.append(normalized)

    return lines


class CSTToASTBuilder:
  """
  Builds AST from CST by extracting semantic content.

  Walks the CST structure and creates corresponding AST nodes,
  handling the mapping between syntactic and semantic representations.
  """

  def __init__(self):
    self.extractor = TextExtractor()

  def build(self, cst: Tree) -> Specification:
    """Transform root CST to AST specification."""
    # Extract main sections from CST
    header = self._find_child(cst, "header")
    if not header:
      raise ValueError("Missing header section in CST")

    # Create root specification
    spec = Specification(name=self._extract_system_name(header), description=self._extract_description(header))

    # Extract components
    if definitions := self._find_child(cst, "definitions"):
      spec.concepts = self._extract_concepts(definitions)

    if state_section := self._find_child(cst, "state_section"):
      spec.states = self._extract_states(state_section)

    if operations := self._find_child(cst, "operations"):
      spec.operations = self._extract_operations(operations)

    if constraints := self._find_child(cst, "constraints"):
      spec.constraints = self._extract_constraints(constraints)
      spec.guarantees = self._extract_guarantees(constraints)

    return spec

  def _extract_system_name(self, header: Tree) -> str:
    """Extract system name from header."""
    if name_node := self._find_child(header, "system_name"):
      return self.extractor.extract_line(name_node)
    return "Unnamed"

  def _extract_description(self, header: Tree) -> str:
    """Extract system description from header."""
    if desc_node := self._find_child(header, "description"):
      # Join multi-line descriptions
      lines = self.extractor.extract_lines(desc_node)
      return " ".join(lines)
    return ""

  def _extract_concepts(self, definitions: Tree) -> List[Concept]:
    """Extract concept definitions."""
    concepts = []

    for concept_def in self._find_all(definitions, "concept_def"):
      if name_node := self._find_child(concept_def, "concept_name"):
        name = self.extractor.extract_line(name_node)
      else:
        continue

      if desc_node := self._find_child(concept_def, "concept_description"):
        description = self.extractor.extract_line(desc_node)
      else:
        description = ""

      concepts.append(Concept(name, description))

    return concepts

  def _extract_states(self, state_section: Tree) -> List[StateDeclaration]:
    """Extract state variable declarations."""
    states = []

    for state_block in self._find_all(state_section, "state_block"):
      if name_node := self._find_child(state_block, "state_name"):
        name = self.extractor.extract_line(name_node)
      else:
        continue

      properties = []
      if props_node := self._find_child(state_block, "state_properties"):
        properties = self._extract_property_lines(props_node)

      states.append(StateDeclaration(name, properties))

    return states

  def _extract_property_lines(self, properties_node: Tree) -> List[str]:
    """Extract property lines from state properties."""
    lines = []

    for prop_line in self._find_all(properties_node, "property_line"):
      if line_text := self.extractor.extract_line(prop_line):
        lines.append(line_text)

    return lines

  def _extract_operations(self, operations_node: Tree) -> List[Operation]:
    """Extract operation definitions."""
    operations = []

    for op_node in self._find_all(operations_node, "operation"):
      # Extract trigger
      trigger = ""
      if trigger_node := self._find_child(op_node, "trigger"):
        trigger = self.extractor.extract_line(trigger_node)

      # Extract preconditions
      preconditions = []
      if precond_nodes := self._find_all(op_node, "precondition_line"):
        for pc_node in precond_nodes:
          if pc_text := self.extractor.extract_line(pc_node):
            preconditions.append(pc_text)

      # Extract effects
      effects = []
      if effect_nodes := self._find_all(op_node, "effect"):
        for effect_node in effect_nodes:
          if effect_content := self._find_child(effect_node, "effect_content"):
            # Handle multi-line effects
            effect_lines = self.extractor.extract_lines(effect_content)
            effects.append(" ".join(effect_lines))

      operations.append(Operation(trigger, preconditions, effects))

    return operations

  def _extract_constraints(self, constraints_node: Tree) -> List[Constraint]:
    """Extract constraint definitions."""
    constraints = []

    if constraint_list := self._find_child(constraints_node, "constraint_list"):
      for item in self._find_all(constraint_list, "constraint_item"):
        if prop := self._extract_named_property(item):
          constraints.append(Constraint(prop[0], prop[1]))

    return constraints

  def _extract_guarantees(self, constraints_node: Tree) -> List[Guarantee]:
    """Extract guarantee definitions."""
    guarantees = []

    if guarantee_list := self._find_child(constraints_node, "guarantee_list"):
      for item in self._find_all(guarantee_list, "guarantee_item"):
        if prop := self._extract_named_property(item):
          guarantees.append(Guarantee(prop[0], prop[1]))

    return guarantees

  def _extract_named_property(self, prop_node: Tree) -> Optional[tuple[str, str]]:
    """Extract name and content from a named property."""
    name = ""
    if name_node := self._find_child(prop_node, "property_name"):
      name = self.extractor.extract_line(name_node)

    content = ""
    if content_node := self._find_child(prop_node, "property_content"):
      # Join multi-line content
      lines = self.extractor.extract_lines(content_node)
      content = " ".join(lines)

    if name and content:
      return (name, content)
    return None

  # Tree navigation utilities
  def _find_child(self, tree: Tree, name: str) -> Optional[Tree]:
    """Find first child with given name."""
    if not isinstance(tree, Tree):
      return None

    for child in tree.children:
      if isinstance(child, Tree) and child.data == name:
        return child
    return None

  def _find_all(self, tree: Tree, name: str) -> List[Tree]:
    """Find all children with given name."""
    if not isinstance(tree, Tree):
      return []

    results = []
    for child in tree.children:
      if isinstance(child, Tree) and child.data == name:
        results.append(child)
    return results


# Convenience function
def build_ast(cst: Tree) -> Specification:
  """Build AST from CST using default builder."""
  builder = CSTToASTBuilder()
  return builder.build(cst)
