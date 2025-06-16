#!/usr/bin/env python3
"""
Universal Serialization Module

Core serialization logic for both CST and AST structures.
"""

from lark import Tree, Token
from typing import Dict, Any
import json


class UniversalSerializer:
  """Serialize any tree structure to JSON-compatible format."""

  def serialize(self, node) -> Dict[str, Any]:
    """Convert node to dictionary representation."""
    # CST Token
    if isinstance(node, Token):
      return {"type": "token", "value": str(node), "token_type": node.type, **self._extract_position(node)}

    # CST Tree
    elif isinstance(node, Tree):
      return {
        "type": "tree",
        "name": node.data,
        "children": [self.serialize(child) for child in node.children],
        "meta": self._extract_position(node),
      }

    # AST Node (has __dict__)
    elif hasattr(node, "__dict__"):
      data = {"type": node.__class__.__name__}

      # Serialize public attributes
      for key, value in node.__dict__.items():
        if key.startswith("_") or key == "source_location":
          continue

        if value is None or callable(value):
          continue

        # Handle collections and nested nodes
        if isinstance(value, list):
          data[key] = [self.serialize(item) if self._is_node(item) else item for item in value]
        elif self._is_node(value):
          data[key] = self.serialize(value)
        else:
          data[key] = value

      return data

    # Literal value
    else:
      return {"type": "literal", "value": str(node)}

  def _extract_position(self, obj) -> Dict[str, Any]:
    """Extract position metadata from CST nodes."""
    meta = {}
    source = getattr(obj, "meta", obj) if hasattr(obj, "meta") else obj

    for attr in ["line", "column", "end_line", "end_column"]:
      if hasattr(source, attr) and (val := getattr(source, attr)) is not None:
        meta[attr] = val

    return meta

  def _is_node(self, obj) -> bool:
    """Check if object is a serializable node."""
    return isinstance(obj, (Tree, Token)) or hasattr(obj, "__dict__")


class UniversalDeserializer:
  """Deserialize JSON back to tree structures."""

  def __init__(self, node_types: Dict[str, type] = None):
    """Initialize with optional AST node type registry."""
    self.node_types = node_types or {}

  def deserialize(self, data: Dict[str, Any]):
    """Convert dictionary back to appropriate node type."""
    node_type = data.get("type")

    if node_type == "token":
      return self._deserialize_token(data)
    elif node_type == "tree":
      return self._deserialize_tree(data)
    elif node_type == "literal":
      return data["value"]
    elif node_type in self.node_types:
      return self._deserialize_ast(data)
    else:
      raise ValueError(f"Unknown node type: {node_type}")

  def _deserialize_token(self, data: Dict[str, Any]) -> Token:
    """Reconstruct CST Token."""
    return Token(
      data["token_type"],
      data["value"],
      line=data.get("line"),
      column=data.get("column"),
      end_line=data.get("end_line"),
      end_column=data.get("end_column"),
    )

  def _deserialize_tree(self, data: Dict[str, Any]) -> Tree:
    """Reconstruct CST Tree."""
    children = [self.deserialize(child) for child in data["children"]]
    tree = Tree(data["name"], children)

    # Apply metadata
    if meta := data.get("meta"):
      tree.meta = type("Meta", (), {})()
      for key, value in meta.items():
        setattr(tree.meta, key, value)

    return tree

  def _deserialize_ast(self, data: Dict[str, Any]):
    """Reconstruct AST node using type registry."""
    node_class = self.node_types[data["type"]]

    # Remove type field
    kwargs = {k: v for k, v in data.items() if k != "type"}

    # Recursively deserialize nested structures
    for key, value in kwargs.items():
      if isinstance(value, list):
        kwargs[key] = [self.deserialize(item) if isinstance(item, dict) and "type" in item else item for item in value]
      elif isinstance(value, dict) and "type" in value:
        kwargs[key] = self.deserialize(value)

    # Create instance based on constructor signature
    try:
      # Try direct instantiation
      return node_class(**kwargs)
    except TypeError:
      # Fallback: create empty and set attributes
      instance = object.__new__(node_class)
      for key, value in kwargs.items():
        setattr(instance, key, value)
      return instance


# Convenience functions
def serialize_to_json(node, indent: int = 2) -> str:
  """Serialize any node to formatted JSON string."""
  serializer = UniversalSerializer()
  data = serializer.serialize(node)
  return json.dumps(data, indent=indent)


def deserialize_from_json(json_str: str, node_types: Dict[str, type] = None):
  """Deserialize JSON string back to node."""
  data = json.loads(json_str)
  deserializer = UniversalDeserializer(node_types)
  return deserializer.deserialize(data)
