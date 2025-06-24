# ===== CST to AST Transformation =====


class ASTBuilder:
  """Transform CST to AST."""

  def __init__(self):
    self.errors = []
    
  def build(self, tree: SyntaxTree) -> Specification:
    """Build AST from syntax tree."""
    root = tree.root
    if root.kind != "specification":
      raise SemanticError(
        f"Expected specification node, got {root.kind}",
        node_type=root.kind
      )
    
    # Extract sections
    header_name, header_desc = self._extract_header(root)
    concepts = self._extract_concepts(root)
    states = self._extract_states(root)
    operations = self._extract_operations(root)
    constraints, guarantees = self._extract_properties(root)
    
    return Specification(
      name=header_name,
      description=header_desc,
      concepts=tuple(concepts),
      states=tuple(states),
      operations=tuple(operations),
      properties=tuple(constraints + guarantees)
    )
  
  def _extract_header(self, spec_node: NodeView) -> tuple[str, str]:
    """Extract system name and description from header."""
    header = self._find_child(spec_node, "header")
    if not header:
      raise SemanticError("Missing system header", node_type="specification")
    
    # Extract name
    name_node = self._find_child(header, "system_name")
    if not name_node:
      raise SemanticError("Missing system name", node_type="header")
    name = self._extract_text(name_node).strip()
    
    # Extract description (optional)
    desc_node = self._find_child(header, "description")
    description = self._extract_text(desc_node).strip() if desc_node else ""
    
    return name, description
  
  def _extract_concepts(self, spec_node: NodeView) -> list[Concept]:
    """Extract concept definitions."""
    concepts = []
    
    defs_node = self._find_child(spec_node, "definitions")
    if not defs_node:
      return concepts
    
    concept_list = self._find_child(defs_node, "concept_list")
    if not concept_list:
      return concepts
    
    for concept_def in self._find_all_children(concept_list, "concept_def"):
      name_node = self._find_child(concept_def, "concept_name")
      desc_node = self._find_child(concept_def, "concept_description")
      
      if name_node and desc_node:
        name = self._extract_text(name_node).strip()
        description = self._extract_text(desc_node).strip()
        concepts.append(Concept(name=name, description=description))
    
    return concepts
  
  def _extract_states(self, spec_node: NodeView) -> list[StateDeclaration]:
    """Extract state declarations."""
    states = []
    
    state_section = self._find_child(spec_node, "state_section")
    if not state_section:
      return states
    
    state_list = self._find_child(state_section, "state_list")
    if not state_list:
      return states
    
    for state_block in self._find_all_children(state_list, "state_block"):
      # Extract state name
      header = self._find_child(state_block, "state_header")
      if not header:
        continue
        
      name_node = self._find_child(header, "state_name")
      if not name_node:
        continue
        
      name = self._extract_text(name_node).strip()
      
      # Extract properties
      properties = []
      initial_condition = None
      
      props_node = self._find_child(state_block, "state_properties")
      if props_node:
        for prop_line in self._find_all_children(props_node, "property_line"):
          text = self._extract_text(prop_line).strip()
          if text.lower().startswith("initially"):
            initial_condition = text
          else:
            properties.append(text)
      
      states.append(StateDeclaration(
        name=name,
        properties=tuple(properties),
        initial_condition=initial_condition
      ))
    
    return states
  
  def _extract_operations(self, spec_node: NodeView) -> list[Operation]:
    """Extract operations (When blocks)."""
    operations = []
    
    for op_node in self._find_all_children(spec_node, "operation"):
      # Extract trigger
      trigger_node = self._find_child(op_node, "trigger")
      if not trigger_node:
        continue
        
      trigger_text = self._extract_text(trigger_node).strip()
      # Remove trailing colon if present
      if trigger_text.endswith(":"):
        trigger_text = trigger_text[:-1].strip()
      
      # Extract operation body
      body = self._find_child(op_node, "operation_body")
      if not body:
        continue
      
      # Extract preconditions
      preconditions = []
      precond_node = self._find_child(body, "preconditions")
      if precond_node:
        for line in self._find_all_children(precond_node, "precondition_line"):
          text = self._extract_text(line).strip()
          if text and not text.startswith("Then:"):
            preconditions.append(text)
      
      # Extract effects
      effects = []
      unchanged = []
      
      effects_node = self._find_child(body, "effects")
      if effects_node:
        for effect in self._find_all_children(effects_node, "effect"):
          content_node = self._find_child(effect, "effect_content")
          if content_node:
            text = self._extract_text(content_node).strip()
            # Check for unchanged pattern
            if "unchanged" in text.lower() or "remain" in text.lower():
              unchanged.append(text)
            else:
              effects.append(text)
      
      operations.append(Operation(
        trigger=trigger_text,
        preconditions=tuple(preconditions),
        effects=tuple(effects),
        unchanged=tuple(unchanged)
      ))
    
    return operations
  
  def _extract_properties(self, spec_node: NodeView) -> tuple[list[Property], list[Property]]:
    """Extract constraints and guarantees."""
    constraints = []
    guarantees = []
    
    # Extract constraints
    constraints_node = self._find_child(spec_node, "constraints")
    if constraints_node:
      constraint_list = self._find_child(constraints_node, "constraint_list")
      if constraint_list:
        for item in self._find_all_children(constraint_list, "constraint_item"):
          prop = self._extract_property(item, "constraint")
          if prop:
            constraints.append(prop)
    
    # Extract guarantees
    guarantees_node = self._find_child(spec_node, "guarantees")
    if guarantees_node:
      guarantee_list = self._find_child(guarantees_node, "guarantee_list")
      if guarantee_list:
        for item in self._find_all_children(guarantee_list, "guarantee_item"):
          prop = self._extract_property(item, "guarantee")
          if prop:
            guarantees.append(prop)
    
    return constraints, guarantees
  
  def _extract_property(self, prop_node: NodeView, prop_type: str) -> Optional[Property]:
    """Extract a single property."""
    named_prop = self._find_child(prop_node, "named_property")
    if not named_prop:
      return None
    
    # Extract name
    name_node = self._find_child(named_prop, "property_name")
    if not name_node:
      return None
    name = self._extract_text(name_node).strip()
    
    # Extract content
    content_node = self._find_child(named_prop, "property_content")
    if not content_node:
      return None
    content = self._extract_text(content_node).strip()
    
    return Property(
      name=name,
      content=content,
      property_type=prop_type
    )
  
  # Helper methods
  
  def _find_child(self, node: NodeView, kind: str) -> Optional[NodeView]:
    """Find first child of given kind."""
    for child in node.children:
      if child.kind == kind:
        return child
    return None
  
  def _find_all_children(self, node: NodeView, kind: str) -> list[NodeView]:
    """Find all children of given kind."""
    return [child for child in node.children if child.kind == kind]
  
  def _extract_text(self, node: NodeView) -> str:
    """Extract all text content from a node."""
    if node.is_token:
      # Skip structural tokens
      if node.kind in {"INDENT", "DEDENT", "NEWLINE", "BULLET", "COLON", "EOF"}:
        return ""
      return node.text or ""
    
    # Recursively extract from children
    parts = []
    for child in node.children:
      text = self._extract_text(child)
      if text:
        parts.append(text)
    
    # Join with appropriate separator
    if node.kind in {"property_content", "operation_content", "description"}:
      # Multi-line content
      return "\n".join(parts)
    else:
      # Single line content
      return " ".join(parts)