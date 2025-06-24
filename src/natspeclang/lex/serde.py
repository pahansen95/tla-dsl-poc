"""Serialization and deserialization utilities.

Provides JSON conversion for AST and CST structures to enable
persistence, transport, and interoperability.
"""

import json


from .ast import Specification, Concept, StateDeclaration, Operation, Property


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


# def serialize_cst(...): ...
# def deserialize_cst(...) ...
