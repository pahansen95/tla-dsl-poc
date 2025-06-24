"""
Unified lexical analysis for Natural Specification Language.

Consolidates all lexical components including token patterns, parsing,
AST definitions, transformations, and serialization into a cohesive module
leveraging the Lexical framework.
"""

import json
from dataclasses import dataclass
from typing import Optional, List

from lexical import Lexer, Parser, Token, token, rule, SyntaxTree, FrozenNode, LexicalContext, Match, State, Stack

from .types import FormatStyle


# ===== DSL Token Patterns =====


class DSLLexer(Lexer):
  """
  Stateful lexer for Natural Specification Language.

  Handles indentation-sensitive parsing, multi-line content aggregation,
  and context-aware token recognition based on document structure.
  """

  # State tracking
  section_state = State(initial="header")
  indent_stack = Stack(initial=[0])
  line_state = State(initial="start")

  # Track if we're collecting multi-line content
  content_buffer = State(initial=None)
  content_indent = State(initial=0)

  # Section header patterns (Priority 10)
  @token(priority=10)
  def section_header(self, nav):
    """Recognize section headers and transition state."""
    if not nav.at_line_start:
      return None

    # Check each section pattern
    sections = {
      "System:": "header",
      "The system uses these concepts:": "definitions",
      "The system maintains:": "states",
      "System Constraints:": "constraints",
      "System Guarantees:": "guarantees",
    }

    for pattern_text, section in sections.items():
      if nav.match_literal(pattern_text):
        self.section_state.set(section)
        nav.advance(len(pattern_text))
        return Match("SECTION_" + section.upper(), pattern_text)

    return None

  # Keywords (Priority 9)
  @token(priority=9)
  def keyword(self, nav):
    """Context-sensitive keyword recognition."""
    keywords = {
      "When": ("operations", "states", "constraints", "guarantees"),
      "Then:": ("operations",),
      "Initially": ("states",),
      "must": ("operations",),
    }

    for kw, valid_sections in keywords.items():
      if self.section_state.value in valid_sections and nav.match_literal(kw):
        nav.advance(len(kw))
        return Match(kw.upper().replace(":", ""), kw)

    return None

  # Structural tokens (Priority 8)
  @token(priority=8)
  def indentation(self, nav):
    """Track indentation changes for structure."""
    if not nav.at_line_start:
      return None

    # Count spaces at line start
    spaces = 0
    while nav.peek(spaces) == " ":
      spaces += 1

    # Skip blank lines
    if nav.peek(spaces) in ("\n", None):
      return None

    current_indent = self.indent_stack.current

    if spaces > current_indent:
      # Indent increase
      self.indent_stack.push(spaces)
      nav.advance(spaces)
      return Match("INDENT", "")
    elif spaces < current_indent:
      # Dedent - may pop multiple levels
      dedent_count = 0
      while self.indent_stack.depth > 1 and spaces < self.indent_stack.current:
        self.indent_stack.pop()
        dedent_count += 1

      if dedent_count > 0:
        nav.advance(spaces)
        # Emit multiple dedent tokens if needed
        return Match("DEDENT", "", count=dedent_count)
    else:
      # Same level - consume spaces but no token
      nav.advance(spaces)
      return None

  # Multi-line content (Priority 7)
  @token(priority=7)
  def multiline_content(self, nav):
    """Aggregate multi-line content blocks."""
    # Check if we should start collecting content
    if self._should_collect_content(nav):
      return self._collect_content_block(nav)
    return None

  # Bullet points (Priority 6)
  @token(priority=6)
  def bullet(self, nav):
    """Bullet points in appropriate contexts."""
    valid_sections = ("definitions", "operations")

    if self.section_state.value in valid_sections:
      if nav.match_literal("- "):
        nav.advance(2)
        return Match("BULLET", "-")

    return None

  # Colon separator (Priority 6)
  @token(priority=6)
  def colon(self, nav):
    """Colon separator in appropriate contexts."""
    if nav.match_literal(":"):
      nav.advance(1)
      return Match("COLON", ":")
    return None

  # Identifiers (Priority 5)
  @token(priority=5)
  def identifier(self, nav):
    """Multi-word identifiers for names."""
    # First word must start with letter
    if not nav.peek() or not nav.peek().isalpha():
      return None

    words = []
    pos = 0

    # Capture first word
    while nav.peek(pos) and (nav.peek(pos).isalnum() or nav.peek(pos) == "_"):
      pos += 1

    if pos == 0:
      return None

    words.append(nav.peek_many(pos))
    nav.advance(pos)

    # Capture additional words separated by single spaces
    while nav.peek() == " " and nav.peek(1) and nav.peek(1).isalpha():
      nav.advance(1)  # space
      pos = 0
      while nav.peek(pos) and (nav.peek(pos).isalnum() or nav.peek(pos) == "_"):
        pos += 1
      if pos > 0:
        words.append(nav.peek_many(pos))
        nav.advance(pos)
      else:
        break

    return Match("IDENTIFIER", " ".join(words))

  # Text line (Priority 4)
  @token(priority=4)
  def text_line(self, nav):
    """Single line of text content."""
    # Don't match if we're in a multi-line context
    if self.content_buffer.value is not None:
      return None

    # Capture until newline
    pos = 0
    while nav.peek(pos) and nav.peek(pos) != "\n":
      pos += 1

    if pos > 0:
      text = nav.peek_many(pos)
      nav.advance(pos)
      return Match("TEXT_LINE", text.strip())

    return None

  # Newline handling (Priority 3)
  @token(priority=3)
  def newline(self, nav):
    """Track newlines for line-based parsing."""
    if nav.peek() == "\n":
      nav.advance(1)
      self.line_state.set("start")
      return Match("NEWLINE", "\n")
    return None

  # Whitespace (Priority 2)
  @token(priority=2, skip=True)
  def whitespace(self, nav):
    """Skip non-structural whitespace."""
    if self.line_state.value != "start" and nav.peek() in " \t":
      pos = 0
      while nav.peek(pos) in " \t":
        pos += 1
      nav.advance(pos)
      return Match("WS", "")
    return None

  # Helper methods
  def _should_collect_content(self, nav) -> bool:
    """Determine if we should start collecting multi-line content."""
    # Content collection contexts
    contexts = {
      "states": self._at_property_start,
      "operations": self._at_precondition_or_effect,
      "constraints": self._at_property_content,
      "guarantees": self._at_property_content,
    }

    checker = contexts.get(self.section_state.value)
    return checker(nav) if checker else False

  def _at_property_start(self, nav) -> bool:
    """Check if at start of property content in states."""
    # After identifier and colon, we expect property content
    return nav.at_line_start and self._measure_indent(nav) > 0

  def _at_precondition_or_effect(self, nav) -> bool:
    """Check if at precondition or effect content."""
    indent = self._measure_indent(nav)
    return nav.at_line_start and indent > 0 and not nav.match_literal("Then:")

  def _at_property_content(self, nav) -> bool:
    """Check if at property content in constraints/guarantees."""
    # After property name and colon
    return nav.at_line_start and self._measure_indent(nav) > 0

  def _collect_content_block(self, nav) -> Optional[Match]:
    """Collect a multi-line content block."""
    lines = []
    base_indent = self._measure_indent(nav)

    # Consume the base indentation
    nav.advance(base_indent)

    # Collect first line
    first_line = self._capture_line(nav)
    if not first_line:
      return None

    lines.append(first_line)

    # Collect continuation lines
    while True:
      # Save position before checking next line
      saved_pos = nav.save_state()

      # Consume newline if present
      if nav.peek() == "\n":
        nav.advance(1)
      else:
        break

      # Check indentation of next line
      next_indent = self._measure_indent(nav)

      # Continue if same or greater indentation
      if next_indent >= base_indent:
        nav.advance(next_indent)
        line = self._capture_line(nav)
        if line:
          # Preserve relative indentation
          rel_indent = " " * (next_indent - base_indent)
          lines.append(rel_indent + line)
        else:
          # Blank line within content
          lines.append("")
      else:
        # Dedent ends content block
        nav.restore_state(saved_pos)
        break

    # Determine token type based on context
    token_type = self._content_token_type()
    return Match(token_type, "\n".join(lines))

  def _measure_indent(self, nav) -> int:
    """Measure indentation at current position."""
    indent = 0
    while nav.peek(indent) == " ":
      indent += 1
    return indent

  def _capture_line(self, nav) -> str:
    """Capture text until end of line."""
    chars = []
    while nav.peek() and nav.peek() != "\n":
      chars.append(nav.peek())
      nav.advance(1)
    return "".join(chars).strip()

  def _content_token_type(self) -> str:
    """Determine content token type from context."""
    type_map = {
      "states": "PROPERTY_CONTENT",
      "operations": "OPERATION_CONTENT",
      "constraints": "CONSTRAINT_CONTENT",
      "guarantees": "GUARANTEE_CONTENT",
    }
    return type_map.get(self.section_state.value, "CONTENT")

  # Override lex to reset state between documents
  def lex(self, text: str):
    """Reset state and lex the document."""
    # Reset all state
    self.section_state.reset()
    self.indent_stack = Stack(initial=[0])
    self.line_state.reset()
    self.content_buffer.reset()
    self.content_indent.reset()

    # Ensure trailing newline
    if text and not text.endswith("\n"):
      text += "\n"

    # Use parent lex implementation
    return super().lex(text)


# ===== AST Node Definitions =====


@dataclass(frozen=True, slots=True)
class Concept:
  """Domain concept definition."""

  name: str
  description: str


@dataclass(frozen=True, slots=True)
class StateDeclaration:
  """State variable declaration."""

  name: str
  properties: tuple[str, ...] = ()
  initial_condition: Optional[str] = None


@dataclass(frozen=True, slots=True)
class Operation:
  """System operation with trigger and effects."""

  trigger: str
  preconditions: tuple[str, ...] = ()
  effects: tuple[str, ...] = ()
  unchanged: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Property:
  """System property (constraint or guarantee)."""

  name: str
  content: str
  property_type: str  # 'constraint' or 'guarantee'


@dataclass(frozen=True, slots=True)
class Specification:
  """Complete system specification."""

  name: str
  description: str
  concepts: tuple[Concept, ...] = ()
  states: tuple[StateDeclaration, ...] = ()
  operations: tuple[Operation, ...] = ()
  properties: tuple[Property, ...] = ()


# ===== Parser with Integrated AST Building =====


class DSLParser(Parser):
  """Parser for Natural Specification Language."""

  def __init__(self, tokens: List[Token], obs_context: Optional[LexicalContext] = None):
    super().__init__(tokens, obs_context)
    # Set up for DSL parsing
    self.skip_structural = True
    self.structural_tokens = {"whitespace", "newline"}

  def parse_root(self) -> Specification:
    """Parse complete specification."""
    # Parse header
    name, description = self.parse_header()

    # Initialize collections
    concepts = []
    states = []
    operations = []
    constraints = []
    guarantees = []

    # Parse sections in order
    if self.match("the_system", "uses_concepts"):
      concepts = self.parse_concepts()

    if self.match("the_system", "maintains"):
      states = self.parse_states()

    # Parse operations
    operations = self.parse_operations()

    # Parse properties
    if self.match("constraints"):
      constraints = self.parse_constraints()

    if self.match("guarantees"):
      guarantees = self.parse_guarantees()

    # Combine properties
    properties = constraints + guarantees

    return Specification(
      name=name,
      description=description,
      concepts=tuple(concepts),
      states=tuple(states),
      operations=tuple(operations),
      properties=tuple(properties),
    )

  @rule()
  def parse_header(self) -> tuple[str, str]:
    """Parse system header."""
    self.expect("system_kw")
    name_token = self.expect("identifier", "text_line")
    name = name_token.value.strip()

    # Collect description lines
    description_lines = []
    while not self.match("the_system"):
      if self.match("text_line"):
        line = self.consume()
        description_lines.append(line.value.strip())
      else:
        break

    description = " ".join(description_lines)
    return name, description

  @rule()
  def parse_concepts(self) -> List[Concept]:
    """Parse concept definitions."""
    self.expect("the_system")
    self.expect("uses_concepts")

    concepts = []
    while self.match("bullet"):
      self.consume()  # bullet
      name = self.expect("identifier").value
      self.expect("colon")
      desc = self.expect("text_line").value.strip()
      concepts.append(Concept(name, desc))

    return concepts

  @rule()
  def parse_states(self) -> List[StateDeclaration]:
    """Parse state declarations."""
    self.expect("the_system")
    self.expect("maintains")

    states = []
    while self.match("identifier") and not self.match("when_kw"):
      # State name
      name = self.consume().value
      self.expect("colon")

      # Properties
      properties = []
      initial = None

      # Consume properties with indentation
      while self.match("indent", "text_line"):
        if self.match("indent"):
          self.consume()  # indent

        prop = self.expect("text_line").value.strip()
        if prop.lower().startswith("initially"):
          initial = prop
        else:
          properties.append(prop)

      states.append(StateDeclaration(name=name, properties=tuple(properties), initial_condition=initial))

    return states

  @rule()
  def parse_operations(self) -> List[Operation]:
    """Parse all operations."""
    operations = []

    while self.match("when_kw"):
      operations.append(self.parse_operation())

    return operations

  @rule()
  def parse_operation(self) -> Operation:
    """Parse single operation."""
    self.expect("when_kw")
    trigger = self.expect("text_line").value.strip()

    # Remove trailing colon if present
    if trigger.endswith(":"):
      trigger = trigger[:-1].strip()

    # Parse preconditions
    preconditions = []
    while self.match("indent") and not self.peek_ahead_for_then():
      self.consume()  # indent
      if self.match("text_line"):
        line = self.consume().value.strip()
        if not line.startswith("Then:"):
          preconditions.append(line)

    # Parse effects
    effects = []
    unchanged = []

    if self.match("indent", "then_kw"):
      self.consume()  # indent
      self.expect("then_kw")

      # Parse effect list
      while self.match("indent"):
        self.consume()  # indent
        if self.match("bullet"):
          self.consume()  # bullet
          effect = self.expect("text_line").value.strip()

          # Separate unchanged from effects
          effect_lower = effect.lower()
          if "unchanged" in effect_lower or "remain" in effect_lower:
            unchanged.append(effect)
          else:
            effects.append(effect)

    return Operation(
      trigger=trigger, preconditions=tuple(preconditions), effects=tuple(effects), unchanged=tuple(unchanged)
    )

  def peek_ahead_for_then(self) -> bool:
    """Check if 'Then:' is coming without consuming."""
    state = self.tokens.save()
    try:
      if self.match("then_kw"):
        return True
      if self.match("text_line"):
        line = self.consume()
        return line.value.strip().startswith("Then:")
      return False
    finally:
      self.tokens.restore(state)

  @rule()
  def parse_constraints(self) -> List[Property]:
    """Parse constraint properties."""
    self.expect("constraints")
    return self.parse_properties("constraint")

  @rule()
  def parse_guarantees(self) -> List[Property]:
    """Parse guarantee properties."""
    self.expect("guarantees")
    return self.parse_properties("guarantee")

  def parse_properties(self, property_type: str) -> List[Property]:
    """Parse named properties."""
    properties = []

    while self.match("identifier"):
      # Property name
      name = self.consume().value
      self.expect("colon")

      # Property content (may be multi-line)
      content_lines = []
      while self.match("indent", "text_line"):
        if self.match("indent"):
          self.consume()
        line = self.expect("text_line").value.strip()
        content_lines.append(line)

      content = " ".join(content_lines)
      properties.append(Property(name, content, property_type))

    return properties


# ===== CST to AST Transformation =====


class ASTBuilder:
  """Transform CST to AST."""

  def build(self, tree: SyntaxTree) -> Specification:
    """Build AST from syntax tree."""
    # For integrated parser, CST already contains AST
    # This is a placeholder for compatibility
    return tree.root  # Assuming root is already a Specification


# ===== AST to CST Formatting =====


class ASTFormatter:
  """Format AST back to CST."""

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


# ===== Serialization =====


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


# ===== High-Level API =====


def parse(text: str, obs_context: Optional[LexicalContext] = None) -> Specification:
  """Parse DSL text to AST."""
  # Validate input
  if not isinstance(text, str):
    raise TypeError(f"Expected str, got {type(text).__name__}")

  # Lexical analysis
  lexer = DSLLexer(obs_context)
  tokens = list(lexer.lex(text))

  # Syntax analysis
  parser = DSLParser(tokens, obs_context)
  return parser.parse_root()


def format_ast(spec: Specification, style: Optional[FormatStyle] = None) -> str:
  """Format AST to DSL text."""
  formatter = ASTFormatter(style)
  return formatter.format(spec)


def parse_to_json(text: str, obs_context: Optional[LexicalContext] = None) -> str:
  """Parse DSL text to JSON."""
  spec = parse(text, obs_context)
  return serialize_ast(spec)


def format_from_json(json_str: str, style: Optional[FormatStyle] = None) -> str:
  """Format JSON to DSL text."""
  spec = deserialize_ast(json_str)
  return format_ast(spec, style)
