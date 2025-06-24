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

