#!/usr/bin/env python3
"""
AST Serialization Module

Provides JSON serialization and deserialization for AST nodes,
enabling pipeline processing and intermediate storage of AST structures.

The serialization format is designed to be human-readable while
preserving all semantic information from the AST.
"""

import json
from typing import Dict, Any, Type

from .nodes import ASTNode, Specification, Concept, StateDeclaration, Operation, Constraint, Guarantee


class ASTSerializer:
  """
  Serializes AST nodes to JSON-compatible dictionaries.

  Each node is represented with a 'type' field indicating its
  class and additional fields for its attributes.
  """

  def serialize(self, node: ASTNode) -> Dict[str, Any]:
    """Convert an AST node to a dictionary."""
    if isinstance(node, Specification):
      return self._serialize_specification(node)
    elif isinstance(node, Concept):
      return self._serialize_concept(node)
    elif isinstance(node, StateDeclaration):
      return self._serialize_state(node)
    elif isinstance(node, Operation):
      return self._serialize_operation(node)
    elif isinstance(node, Constraint):
      return self._serialize_constraint(node)
    elif isinstance(node, Guarantee):
      return self._serialize_guarantee(node)
    else:
      raise ValueError(f"Unknown AST node type: {type(node).__name__}")

  def _serialize_specification(self, spec: Specification) -> Dict[str, Any]:
    """Serialize a Specification node."""
    return {
      "type": "Specification",
      "name": spec.name,
      "description": spec.description,
      "concepts": [self.serialize(c) for c in spec.concepts],
      "states": [self.serialize(s) for s in spec.states],
      "operations": [self.serialize(o) for o in spec.operations],
      "constraints": [self.serialize(c) for c in spec.constraints],
      "guarantees": [self.serialize(g) for g in spec.guarantees],
    }

  def _serialize_concept(self, concept: Concept) -> Dict[str, Any]:
    """Serialize a Concept node."""
    return {"type": "Concept", "name": concept.name, "description": concept.description}

  def _serialize_state(self, state: StateDeclaration) -> Dict[str, Any]:
    """Serialize a StateDeclaration node."""
    data = {"type": "StateDeclaration", "name": state.name, "properties": state.properties}
    if state.initial_condition:
      data["initial_condition"] = state.initial_condition
    return data

  def _serialize_operation(self, op: Operation) -> Dict[str, Any]:
    """Serialize an Operation node."""
    data = {"type": "Operation", "trigger": op.trigger, "preconditions": op.preconditions, "effects": op.effects}
    if op.unchanged:
      data["unchanged"] = op.unchanged
    return data

  def _serialize_constraint(self, constraint: Constraint) -> Dict[str, Any]:
    """Serialize a Constraint node."""
    return {"type": "Constraint", "name": constraint.name, "content": constraint.content}

  def _serialize_guarantee(self, guarantee: Guarantee) -> Dict[str, Any]:
    """Serialize a Guarantee node."""
    return {"type": "Guarantee", "name": guarantee.name, "content": guarantee.content}


class ASTDeserializer:
  """
  Deserializes JSON dictionaries back to AST nodes.

  Reconstructs the full AST structure from serialized form.
  """

  def __init__(self):
    # Map type names to classes for reconstruction
    self.node_types: Dict[str, Type[ASTNode]] = {
      "Specification": Specification,
      "Concept": Concept,
      "StateDeclaration": StateDeclaration,
      "Operation": Operation,
      "Constraint": Constraint,
      "Guarantee": Guarantee,
    }

  def deserialize(self, data: Dict[str, Any]) -> ASTNode:
    """Convert a dictionary back to an AST node."""
    node_type = data.get("type")
    if not node_type:
      raise ValueError("Missing 'type' field in serialized data")

    if node_type not in self.node_types:
      raise ValueError(f"Unknown node type: {node_type}")

    # Dispatch to specific deserializer
    method_name = f"_deserialize_{node_type.lower()}"
    method = getattr(self, method_name)
    return method(data)

  def _deserialize_specification(self, data: Dict[str, Any]) -> Specification:
    """Deserialize a Specification node."""
    spec = Specification(name=data["name"], description=data["description"])

    # Deserialize child nodes
    spec.concepts = [self.deserialize(c) for c in data.get("concepts", [])]
    spec.states = [self.deserialize(s) for s in data.get("states", [])]
    spec.operations = [self.deserialize(o) for o in data.get("operations", [])]
    spec.constraints = [self.deserialize(c) for c in data.get("constraints", [])]
    spec.guarantees = [self.deserialize(g) for g in data.get("guarantees", [])]

    return spec

  def _deserialize_concept(self, data: Dict[str, Any]) -> Concept:
    """Deserialize a Concept node."""
    return Concept(name=data["name"], description=data["description"])

  def _deserialize_statedeclaration(self, data: Dict[str, Any]) -> StateDeclaration:
    """Deserialize a StateDeclaration node."""
    state = StateDeclaration(name=data["name"], properties=data["properties"])

    # Restore initial condition if present
    if "initial_condition" in data:
      state.initial_condition = data["initial_condition"]
      # Don't re-extract since it's already separated

    return state

  def _deserialize_operation(self, data: Dict[str, Any]) -> Operation:
    """Deserialize an Operation node."""
    op = Operation(
      trigger=data["trigger"], preconditions=data.get("preconditions", []), effects=data.get("effects", [])
    )

    # Restore unchanged list if present
    if "unchanged" in data:
      op.unchanged = data["unchanged"]

    return op

  def _deserialize_constraint(self, data: Dict[str, Any]) -> Constraint:
    """Deserialize a Constraint node."""
    return Constraint(name=data["name"], content=data["content"])

  def _deserialize_guarantee(self, data: Dict[str, Any]) -> Guarantee:
    """Deserialize a Guarantee node."""
    return Guarantee(name=data["name"], content=data["content"])


# Convenience functions for JSON string operations
def serialize_ast(node: ASTNode) -> str:
  """Serialize AST to formatted JSON string."""
  serializer = ASTSerializer()
  data = serializer.serialize(node)
  return json.dumps(data, indent=2)


def deserialize_ast(json_str: str) -> ASTNode:
  """Deserialize JSON string to AST."""
  data = json.loads(json_str)
  deserializer = ASTDeserializer()
  return deserializer.deserialize(data)


def to_dict(node: ASTNode) -> Dict[str, Any]:
  """Convert AST to dictionary (not JSON string)."""
  serializer = ASTSerializer()
  return serializer.serialize(node)


def from_dict(data: Dict[str, Any]) -> ASTNode:
  """Convert dictionary to AST."""
  deserializer = ASTDeserializer()
  return deserializer.deserialize(data)


# Testing utility
def roundtrip_test(ast: ASTNode) -> bool:
  """
  Test serialization roundtrip integrity.

  Verifies that serialize -> deserialize produces
  an equivalent AST structure.
  """
  json_str = serialize_ast(ast)
  restored = deserialize_ast(json_str)

  # Compare string representations as simple equality check
  # More sophisticated comparison could be implemented
  return repr(ast) == repr(restored)
