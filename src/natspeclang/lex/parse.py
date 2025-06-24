"""Parser implementation for Natural Specification Language.

Provides integrated parsing and CST construction through the
lexical framework's unified Parser base class.
"""

from typing import List, Optional

from lexical import Parser, Token, FrozenNode, FrozenToken, LexicalContext, Position

from .ast import Specification
from .tokenize import DSLLexer
from ..errors import SyntaxError


class DSLParser(Parser):
  """Parser that builds CST from DSL tokens."""

  def __init__(self, tokens: List[Token], obs_context: Optional[LexicalContext] = None):
    super().__init__(tokens, obs_context)
    # Don't skip structural tokens - we need them in CST
    self.skip_structural = False
    self.structural_tokens = set()  # Empty - preserve all tokens

  def parse_root(self) -> FrozenNode:
    """Parse complete specification into CST."""
    with self.rule("specification"):
      # Required header
      self._parse_header()

      # Optional definitions
      if self._peek_text("The system uses these concepts:"):
        self._parse_definitions()

      # Optional states
      if self._peek_text("The system maintains:"):
        self._parse_state_section()

      # Operations (zero or more)
      while self.match("when_kw"):
        self._parse_operation()

      # Optional constraints
      if self.match("constraints"):
        self._parse_constraints()

      # Optional guarantees
      if self.match("guarantees"):
        self._parse_guarantees()

      # Expect EOF
      self.expect("EOF")

  def _parse_header(self) -> None:
    """Parse system header preserving all tokens."""
    with self.rule("header"):
      # System keyword
      self._add_token(self.expect("system_kw"))

      # Skip whitespace if present
      self._consume_whitespace()

      # System name
      with self.rule("system_name"):
        self._add_token(self.expect("identifier", "text_line"))

      # Consume newlines
      self._consume_newlines()

      # Description (optional multi-line)
      if self.match("text_line"):
        with self.rule("description"):
          while self.match("text_line") and not self._at_section_start():
            self._add_token(self.consume())
            self._consume_newlines()

  def _parse_definitions(self) -> None:
    """Parse concept definitions section."""
    with self.rule("definitions"):
      # Section header
      self._consume_text("The system uses these concepts:")
      self._consume_newlines()

      # Concept list
      with self.rule("concept_list"):
        while self.match("bullet"):
          self._parse_concept_def()

  def _parse_concept_def(self) -> None:
    """Parse single concept definition."""
    with self.rule("concept_def"):
      self._add_token(self.expect("bullet"))
      self._consume_whitespace()

      with self.rule("concept_name"):
        self._add_token(self.expect("identifier"))

      self._add_token(self.expect("colon"))
      self._consume_whitespace()

      with self.rule("concept_description"):
        self._add_token(self.expect("text_line"))

      self._consume_newlines()

  def _parse_state_section(self) -> None:
    """Parse state declarations section."""
    with self.rule("state_section"):
      # Section header
      self._consume_text("The system maintains:")
      self._consume_newlines()

      # State list
      with self.rule("state_list"):
        while self._is_state_start():
          self._parse_state_block()

  def _parse_state_block(self) -> None:
    """Parse single state declaration block."""
    with self.rule("state_block"):
      # State header
      with self.rule("state_header"):
        with self.rule("state_name"):
          self._add_token(self.expect("identifier"))
        self._add_token(self.expect("colon"))
        self._consume_newlines()

      # State properties
      with self.rule("state_properties"):
        while self.match("indent"):
          self._add_token(self.consume())  # Preserve indent

          with self.rule("property_line"):
            self._add_token(self.expect("text_line"))

          self._consume_newlines()

      # Extra newline between states
      self._consume_newlines()

  def _parse_operation(self) -> None:
    """Parse operation (When block)."""
    with self.rule("operation"):
      # When clause
      self._add_token(self.expect("when_kw"))
      self._consume_whitespace()

      with self.rule("trigger"):
        self._add_token(self.expect("text_line"))

      # Remove trailing colon from trigger if present
      self._consume_newlines()

      # Preconditions and effects
      with self.rule("operation_body"):
        # Preconditions (indented lines before "Then:")
        self._parse_preconditions()

        # Then marker
        if self.match("indent"):
          self._parse_transition_and_effects()

      self._consume_newlines()

  def _parse_preconditions(self) -> None:
    """Parse operation preconditions."""
    with self.rule("preconditions"):
      while self.match("indent") and not self._peek_then():
        self._add_token(self.consume())  # indent

        with self.rule("precondition_line"):
          self._add_token(self.expect("text_line"))

        self._consume_newlines()

  def _parse_transition_and_effects(self) -> None:
    """Parse Then: marker and effects."""
    # Transition marker
    with self.rule("transition_marker"):
      self._add_token(self.consume())  # indent
      self._add_token(self.expect("then_kw"))
      self._consume_newlines()

    # Effects
    with self.rule("effects"):
      while self.match("indent"):
        self._add_token(self.consume())  # first indent

        # Expect another indent for double indentation
        if self.match("indent"):
          self._add_token(self.consume())  # second indent

          with self.rule("effect"):
            self._add_token(self.expect("bullet"))
            self._consume_whitespace()

            with self.rule("effect_content"):
              self._add_token(self.expect("text_line"))

            self._consume_newlines()

  def _parse_constraints(self) -> None:
    """Parse constraints section."""
    with self.rule("constraints"):
      self._add_token(self.consume())  # constraints keyword
      self._consume_newlines()

      with self.rule("constraint_list"):
        while self._is_property_start():
          self._parse_property("constraint_item")

  def _parse_guarantees(self) -> None:
    """Parse guarantees section."""
    with self.rule("guarantees"):
      self._add_token(self.consume())  # guarantees keyword
      self._consume_newlines()

      with self.rule("guarantee_list"):
        while self._is_property_start():
          self._parse_property("guarantee_item")

  def _parse_property(self, item_type: str) -> None:
    """Parse named property (constraint or guarantee)."""
    with self.rule(item_type):
      with self.rule("named_property"):
        # Property name
        with self.rule("property_name"):
          self._add_token(self.expect("identifier"))

        self._add_token(self.expect("colon"))
        self._consume_newlines()

        # Property content (indented)
        if self.match("indent"):
          self._add_token(self.consume())

          with self.rule("property_content"):
            self._add_token(self.expect("text_line"))

          self._consume_newlines()

      self._consume_newlines()

  # Helper methods

  def _add_token(self, token: Token) -> None:
    """Convert token to FrozenToken and add to current node."""
    frozen = FrozenToken.from_lex_token(token)
    self._add_element(frozen)

  def _consume_whitespace(self) -> None:
    """Consume and preserve whitespace tokens."""
    while self.match("whitespace"):
      self._add_token(self.consume())

  def _consume_newlines(self) -> None:
    """Consume and preserve newline tokens."""
    while self.match("newline"):
      self._add_token(self.consume())

  def _consume_text(self, expected: str) -> None:
    """Consume text matching expected string."""
    # This handles multi-token text like "The system maintains:"
    words = expected.split()
    for word in words:
      if self.match("the_system") and word == "The system":
        self._add_token(self.consume())
      elif self.match("uses_concepts") and word == "uses these concepts:":
        self._add_token(self.consume())
      elif self.match("maintains") and word == "maintains:":
        self._add_token(self.consume())
      else:
        # Fallback to text_line matching
        token = self.peek()
        if token and word in token.value:
          self._add_token(self.consume())
        else:
          raise SyntaxError(f"Expected '{word}'", position=self.current_position())

  def _peek_text(self, text: str) -> bool:
    """Check if upcoming tokens match text without consuming."""
    saved = self.tokens.save()
    try:
      words = text.split()
      for word in words:
        if not self._match_word(word):
          return False
        self.consume()
      return True
    finally:
      self.tokens.restore(saved)

  def _match_word(self, word: str) -> bool:
    """Check if current token matches word."""
    token = self.peek()
    return token and word in token.value

  def _at_section_start(self) -> bool:
    """Check if at the start of a new section."""
    return (
      self._peek_text("The system") or self.match("when_kw") or self.match("constraints") or self.match("guarantees")
    )

  def _is_state_start(self) -> bool:
    """Check if at state declaration start."""
    return self.match("identifier") and not self.match("when_kw")

  def _is_property_start(self) -> bool:
    """Check if at property declaration start."""
    return self.match("identifier")

  def _peek_then(self) -> bool:
    """Look ahead for 'Then:' without consuming."""
    saved = self.tokens.save()
    try:
      if self.match("text_line"):
        line = self.consume()
        return line.value.strip() == "Then:"
      return self.match("then_kw")
    finally:
      self.tokens.restore(saved)

  def current_position(self) -> Optional[Position]:
    """Get current token position for error reporting."""
    token = self.peek()
    return token.position if token else None


# Public API function


def parse(text: str, obs_context: Optional[LexicalContext] = None) -> Specification:
  """
  Parse DSL text to AST.

  Args:
      text: NSL specification text
      obs_context: Optional observability context

  Returns:
      Parsed Specification AST

  Raises:
      TypeError: If text is not a string
      LexicalError: If tokenization fails
      SyntaxError: If parsing fails
  """
  # Validate input
  if not isinstance(text, str):
    raise TypeError(f"Expected str, got {type(text).__name__}")

  # Lexical analysis
  lexer = DSLLexer(obs_context)
  tokens = list(lexer.lex(text))

  # Syntax analysis - DSLParser builds AST directly
  parser = DSLParser(tokens, obs_context)
  return parser.parse_root()
