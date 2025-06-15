#!/usr/bin/env python3
"""
CST Serialization for Lark Parse Trees
Converts between Lark CST objects and JSON-serializable dictionaries
"""

from lark import Tree, Token
from typing import Union, Dict, Any
import json


class CSTSerializer:
  """Serializes Lark CST to JSON-compatible format."""

  def serialize(self, node: Union[Tree, Token]) -> Dict[str, Any]:
    """Convert a Lark node to serializable dictionary."""
    if isinstance(node, Token):
      return self._serialize_token(node)
    elif isinstance(node, Tree):
      return self._serialize_tree(node)
    else:
      # Handle literal values (strings, etc)
      return {"type": "literal", "value": str(node)}

  def _serialize_token(self, token: Token) -> Dict[str, Any]:
    """Serialize a Token with all metadata."""
    return {
      "type": "token",
      "value": str(token),
      "token_type": token.type,
      "line": getattr(token, "line", None),
      "column": getattr(token, "column", None),
      "end_line": getattr(token, "end_line", None),
      "end_column": getattr(token, "end_column", None),
    }

  def _serialize_tree(self, tree: Tree) -> Dict[str, Any]:
    """Serialize a Tree node recursively."""
    return {
      "type": "tree",
      "name": tree.data,
      "children": [self.serialize(child) for child in tree.children],
      "meta": self._extract_meta(tree),
    }

  def _extract_meta(self, tree: Tree) -> Dict[str, Any]:
    """Extract metadata from tree if available."""
    meta = {}
    if hasattr(tree, "meta") and tree.meta:
      # Preserve position information
      if hasattr(tree.meta, "line"):
        meta["line"] = tree.meta.line
      if hasattr(tree.meta, "column"):
        meta["column"] = tree.meta.column
      if hasattr(tree.meta, "end_line"):
        meta["end_line"] = tree.meta.end_line
      if hasattr(tree.meta, "end_column"):
        meta["end_column"] = tree.meta.end_column
    return meta


class CSTDeserializer:
  """Deserializes JSON format back to Lark CST objects."""

  def deserialize(self, data: Dict[str, Any]) -> Union[Tree, Token]:
    """Convert serialized dictionary back to Lark node."""
    node_type = data.get("type")

    if node_type == "token":
      return self._deserialize_token(data)
    elif node_type == "tree":
      return self._deserialize_tree(data)
    elif node_type == "literal":
      return data["value"]
    else:
      raise ValueError(f"Unknown node type: {node_type}")

  def _deserialize_token(self, data: Dict[str, Any]) -> Token:
    """Recreate Token from serialized data."""
    token = Token(
      data["token_type"],
      data["value"],
      line=data.get("line"),
      column=data.get("column"),
      end_line=data.get("end_line"),
      end_column=data.get("end_column"),
    )
    return token

  def _deserialize_tree(self, data: Dict[str, Any]) -> Tree:
    """Recreate Tree from serialized data."""
    children = [self.deserialize(child) for child in data["children"]]
    tree = Tree(data["name"], children)

    # Restore metadata if present
    if "meta" in data and data["meta"]:
      # Create a simple meta object
      class Meta:
        pass

      tree.meta = Meta()
      for key, value in data["meta"].items():
        setattr(tree.meta, key, value)

    return tree


# Convenience functions
def serialize_cst(node: Union[Tree, Token]) -> str:
  """Serialize CST to JSON string."""
  serializer = CSTSerializer()
  data = serializer.serialize(node)
  return json.dumps(data, indent=2)


def deserialize_cst(json_str: str) -> Union[Tree, Token]:
  """Deserialize JSON string to CST."""
  data = json.loads(json_str)
  deserializer = CSTDeserializer()
  return deserializer.deserialize(data)


def to_dict(node: Union[Tree, Token]) -> Dict[str, Any]:
  """Convert CST to dictionary (not JSON string)."""
  serializer = CSTSerializer()
  return serializer.serialize(node)


def from_dict(data: Dict[str, Any]) -> Union[Tree, Token]:
  """Convert dictionary to CST."""
  deserializer = CSTDeserializer()
  return deserializer.deserialize(data)


# Integration with existing code
def roundtrip_test(tree: Tree) -> bool:
  """Test serialization roundtrip."""
  # Serialize
  json_str = serialize_cst(tree)

  # Deserialize
  restored = deserialize_cst(json_str)

  # Compare structures (basic check)
  return _trees_equal(tree, restored)


def _trees_equal(t1: Union[Tree, Token], t2: Union[Tree, Token]) -> bool:
  """Basic structural equality check."""
  if type(t1) is not type(t2):
    return False

  if isinstance(t1, Token):
    return str(t1) == str(t2) and t1.type == t2.type

  if isinstance(t1, Tree):
    if t1.data != t2.data:
      return False
    if len(t1.children) != len(t2.children):
      return False
    return all(_trees_equal(c1, c2) for c1, c2 in zip(t1.children, t2.children))

  # Literal values
  return t1 == t2
