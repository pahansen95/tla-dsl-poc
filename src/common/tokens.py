#!/usr/bin/env python3
"""
Token Factory Module

Centralized token creation and manipulation utilities.
Consolidates token generation logic scattered across the codebase.
"""

from typing import List
from lark import Token


class TokenFactory:
  """Factory for creating tokens with consistent type inference."""

  @staticmethod
  def create(value: str, token_type: str = None) -> Token:
    """
    Create token with automatic type inference if not specified.

    Args:
        value: Token value
        token_type: Explicit type or None for inference

    Returns:
        Token with appropriate type
    """
    if token_type is None:
      token_type = TokenFactory.infer_type(value)
    return Token(token_type, value)

  @staticmethod
  def infer_type(value: str) -> str:
    """
    Infer token type from value content.

    Type inference rules:
    - Digits → NUMBER
    - Alphabetic/underscore → WORD
    - Single space/tab → WS
    - Newline → NEWLINE
    - Two spaces → INDENT
    - Four spaces → DOUBLE_INDENT
    - Other → SYMBOL
    """
    if value.isdigit():
      return "NUMBER"
    elif value.isalpha() or "_" in value:
      return "WORD"
    elif value in [" ", "\t"]:
      return "WS"
    elif value == "\n":
      return "NEWLINE"
    elif value == "  ":
      return "INDENT"
    elif value == "    ":
      return "DOUBLE_INDENT"
    else:
      return "SYMBOL"

  @staticmethod
  def from_text(text: str) -> List[Token]:
    """
    Convert text string to token sequence.

    Splits on whitespace and adds WS tokens between words.

    Args:
        text: Text to tokenize

    Returns:
        List of typed tokens
    """
    if not text:
      return []

    tokens = []
    words = text.split()

    for i, word in enumerate(words):
      tokens.append(TokenFactory.create(word))

      # Add space between words
      if i < len(words) - 1:
        tokens.append(TokenFactory.create(" ", "WS"))

    return tokens

  @staticmethod
  def indent(level: int = 1, size: int = 2) -> Token:
    """
    Create indentation token.

    Args:
        level: Indentation level (1 or 2)
        size: Spaces per indent level

    Returns:
        INDENT or DOUBLE_INDENT token
    """
    spaces = " " * (size * level)
    token_type = "INDENT" if level == 1 else "DOUBLE_INDENT"
    return Token(token_type, spaces)

  @staticmethod
  def newline() -> Token:
    """Create newline token."""
    return Token("NEWLINE", "\n")

  @staticmethod
  def literal(value: str) -> Token:
    """Create literal token for punctuation and symbols."""
    return Token("LITERAL", value)

  @staticmethod
  def whitespace(count: int = 1) -> Token:
    """Create whitespace token with specified count."""
    return Token("WS", " " * count)
