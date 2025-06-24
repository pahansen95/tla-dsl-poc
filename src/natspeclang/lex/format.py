"""AST formatting and text generation.

Converts abstract syntax trees back to human-readable DSL text
with customizable formatting styles.
"""

from typing import Optional

from .ast import Specification
from ..types import FormatStyle


class ASTFormatter:
  """Format AST back to DSL text."""

  def __init__(self, style: Optional[FormatStyle] = None):
    self.style = style or {"indent_size": 2, "bullet_char": "-", "section_spacing": 1}

  def format(self, spec: Specification) -> str:
    """Format specification as text."""
    lines = []

    # Header
    lines.append(f"System: {spec.name}")
    if spec.description:
      lines.append("")
      lines.append(spec.description)

    # Concepts
    if spec.concepts:
      lines.append("")
      lines.append("The system uses these concepts:")
      for concept in spec.concepts:
        lines.append(f"{self.style['bullet_char']} {concept.name}: {concept.description}")

    # States
    if spec.states:
      lines.append("")
      lines.append("The system maintains:")
      lines.append("")
      for state in spec.states:
        lines.append(f"{state.name}:")
        for prop in state.properties:
          lines.append(f"  {prop}")
        if state.initial_condition:
          lines.append(f"  {state.initial_condition}")
        lines.append("")

    # Operations
    for op in spec.operations:
      lines.append(f"When {op.trigger}:")
      for precond in op.preconditions:
        lines.append(f"  {precond}")
      if op.effects or op.unchanged:
        lines.append("  Then:")
        for effect in op.effects:
          lines.append(f"    {self.style['bullet_char']} {effect}")
        for unchanged in op.unchanged:
          lines.append(f"    {self.style['bullet_char']} {unchanged}")
      lines.append("")

    # Constraints
    constraints = [p for p in spec.properties if p.property_type == "constraint"]
    if constraints:
      lines.append("System Constraints:")
      lines.append("")
      for prop in constraints:
        lines.append(f"{prop.name}:")
        lines.append(f"  {prop.content}")
        lines.append("")

    # Guarantees
    guarantees = [p for p in spec.properties if p.property_type == "guarantee"]
    if guarantees:
      lines.append("System Guarantees:")
      lines.append("")
      for prop in guarantees:
        lines.append(f"{prop.name}:")
        lines.append(f"  {prop.content}")
        lines.append("")

    return "\n".join(lines)
