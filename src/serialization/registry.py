#!/usr/bin/env python3
"""
Type Registry Module

Helpers for managing node type registrations for deserialization.
"""

from typing import Dict, Type
import importlib
import inspect


def build_ast_registry() -> Dict[str, Type]:
  """
  Build registry of AST node types for deserialization.

  Returns:
      Dictionary mapping type names to classes
  """
  from ast import Specification, Concept, StateDeclaration, Operation, Property

  return {
    "Specification": Specification,
    "Concept": Concept,
    "StateDeclaration": StateDeclaration,
    "Operation": Operation,
    "Property": Property,
  }


def discover_node_types(module_name: str) -> Dict[str, Type]:
  """
  Automatically discover node types from a module.

  Args:
      module_name: Name of module to scan for node types

  Returns:
      Dictionary mapping class names to types
  """
  try:
    module = importlib.import_module(module_name)
  except ImportError:
    return {}

  registry = {}

  # Find all classes that look like node types
  for name, obj in inspect.getmembers(module, inspect.isclass):
    # Skip private classes and imports from other modules
    if name.startswith("_") or obj.__module__ != module.__name__:
      continue

    # Check if it has node-like characteristics
    if hasattr(obj, "__dict__") and not name.endswith("Visitor"):
      registry[name] = obj

  return registry


class TypeRegistry:
  """
  Manages type registrations for serialization/deserialization.

  Provides a cleaner interface for managing multiple type sources.
  """

  def __init__(self):
    self.types: Dict[str, Type] = {}

  def register(self, name: str, cls: Type) -> None:
    """Register a single type."""
    self.types[name] = cls

  def register_module(self, module_name: str) -> None:
    """Register all suitable types from a module."""
    discovered = discover_node_types(module_name)
    self.types.update(discovered)

  def register_dict(self, type_dict: Dict[str, Type]) -> None:
    """Register types from a dictionary."""
    self.types.update(type_dict)

  def get(self, name: str) -> Type:
    """Get a registered type by name."""
    if name not in self.types:
      raise KeyError(f"Type '{name}' not registered")
    return self.types[name]

  def to_dict(self) -> Dict[str, Type]:
    """Get all registered types as dictionary."""
    return self.types.copy()
