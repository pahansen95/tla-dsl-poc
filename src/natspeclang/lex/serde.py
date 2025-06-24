"""Serialization and deserialization utilities.

Provides JSON conversion for AST and CST structures to enable
persistence, transport, and interoperability.
"""

import json


from .ast import Specification, Concept, StateDeclaration, Operation, Property
from typing import Union, Dict, Any

from lexical import SyntaxTree, FrozenNode, FrozenToken, Position


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
  """Serialize CST to JSON preserving all structural information.

  The serialization format captures:
  - Node structure with kind and children
  - Token values with type and position
  - Complete position information (line, column, offset)

  Args:
      tree: SyntaxTree to serialize

  Returns:
      JSON string representation
  """

  def element_to_dict(element: Union[FrozenNode, FrozenToken]) -> Dict[str, Any]:
    """Convert a tree element to dictionary."""
    if isinstance(element, FrozenToken):
      # Serialize token with position
      return {
        "_type": "token",
        "token_type": element.type,
        "value": element.value,
        "position": {
          "line": element.position.line,
          "column": element.position.column,
          "offset": element.position.offset,
        },
      }
    elif isinstance(element, FrozenNode):
      # Serialize node with children
      return {"_type": "node", "kind": element.kind, "children": [element_to_dict(child) for child in element.children]}
    else:
      raise ValueError(f"Unknown element type: {type(element)}")

  # Convert root node
  root_dict = element_to_dict(tree._frozen_root)

  # Wrap in metadata
  cst_dict = {"_format": "nsl-cst", "_version": "1.0", "root": root_dict}

  return json.dumps(cst_dict, indent=2)


def deserialize_cst(json_str: str) -> SyntaxTree:
  """Deserialize CST from JSON.

  Reconstructs the immutable tree structure with all tokens
  and position information preserved.

  Args:
      json_str: JSON string representation

  Returns:
      Reconstructed SyntaxTree

  Raises:
      ValueError: If JSON format is invalid
  """
  data = json.loads(json_str)

  # Validate format
  if data.get("_format") != "nsl-cst":
    raise ValueError(f"Invalid CST format: {data.get('_format')}")

  if "_version" not in data:
    raise ValueError("Missing version information")

  def dict_to_element(d: Dict[str, Any]) -> Union[FrozenNode, FrozenToken]:
    """Convert dictionary back to tree element."""
    element_type = d.get("_type")

    if element_type == "token":
      # Reconstruct position
      pos_data = d["position"]
      position = Position(line=pos_data["line"], column=pos_data["column"], offset=pos_data["offset"])

      # Create frozen token
      return FrozenToken(type=d["token_type"], value=d["value"], position=position)

    elif element_type == "node":
      # Recursively reconstruct children
      children = tuple(dict_to_element(child) for child in d["children"])

      # Create frozen node
      return FrozenNode(kind=d["kind"], children=children)

    else:
      raise ValueError(f"Unknown element type: {element_type}")

  # Reconstruct root
  root = dict_to_element(data["root"])

  if not isinstance(root, FrozenNode):
    raise ValueError("Root must be a FrozenNode")

  return SyntaxTree(root)
