"""Serialization and deserialization utilities.

Provides JSON conversion for AST and CST structures to enable
persistence, transport, and interoperability.
"""

import json
from typing import Optional

from lexical import SyntaxTree, FrozenNode, LexicalContext

from .ast import Specification, Concept, StateDeclaration, Operation, Property
from .parse import parse
from .format import format_ast
from ..types import FormatStyle


def serialize_ast(spec: Specification) -> str:
  """Serialize AST to JSON."""

  def to_dict(obj):
    if hasattr(obj, "__dict__"):
      d = {"_type": obj.__class__.__name__}
      for key, value in obj.__dict__.items():
        if isinstance(value, tuple):
          d[key] = [to_dict(item) for item in value]
        else:
          d[key] = value
      return d
    return obj

  return json.dumps(to_dict(spec), indent=2)


def deserialize_ast(json_str: str) -> Specification:
  """Deserialize AST from JSON."""
  data = json.loads(json_str)

  def from_dict(d):
    if isinstance(d, dict) and "_type" in d:
      cls_name = d.pop("_type")

      # Convert lists back to tuples for frozen dataclasses
      for key, value in d.items():
        if isinstance(value, list):
          d[key] = tuple(from_dict(item) for item in value)

      # Instantiate appropriate class
      if cls_name == "Specification":
        return Specification(**d)
      elif cls_name == "Concept":
        return Concept(**d)
      elif cls_name == "StateDeclaration":
        return StateDeclaration(**d)
      elif cls_name == "Operation":
        return Operation(**d)
      elif cls_name == "Property":
        return Property(**d)
    return d

  return from_dict(data)


def serialize_cst(tree: SyntaxTree) -> str:
  """Serialize CST to JSON."""
  # Simplified for integrated parser
  return serialize_ast(tree.root)


def deserialize_cst(json_str: str) -> SyntaxTree:
  """Deserialize CST from JSON."""
  # Simplified for integrated parser
  spec = deserialize_ast(json_str)
  return SyntaxTree(FrozenNode("specification", (spec,)))


# Public API convenience functions


def parse_to_json(text: str, obs_context: Optional[LexicalContext] = None) -> str:
  """
  Parse DSL text directly to JSON representation.

  Args:
      text: NSL specification text
      obs_context: Optional observability context

  Returns:
      JSON string representation of AST
  """
  spec = parse(text, obs_context)
  return serialize_ast(spec)


def format_from_json(json_str: str, style: Optional[FormatStyle] = None) -> str:
  """
  Format JSON AST representation to DSL text.

  Args:
      json_str: JSON representation of AST
      style: Optional formatting configuration

  Returns:
      Formatted DSL text
  """
  spec = deserialize_ast(json_str)
  return format_ast(spec, style)
