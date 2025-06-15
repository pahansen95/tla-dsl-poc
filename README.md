# BNF to CST Parser

A minimal Python implementation for parsing documents using BNF grammar definitions and generating Concrete Syntax Trees.

## Installation

```bash
pip install lark-parser
```

## Usage

```python
from bnf_cst_parser import parse_custom_bnf

# Define BNF grammar
grammar = r"""
?start: expr
expr: term (("+" | "-") term)*
term: NUMBER | "(" expr ")"
NUMBER: /[0-9]+/
%ignore /\s+/
"""

# Parse document
cst = parse_custom_bnf(grammar, "42 + (3 - 1)")
```

## API

- `create_parser(grammar)` - Create parser from BNF grammar string
- `parse_document(parser, document)` - Generate CST from document
- `parse_custom_bnf(grammar, document)` - Convenience function combining both steps
- `print_cst(tree)` - Visualize CST structure

## Grammar Format

Uses Lark's EBNF notation:
- `?` prefix for inline rules
- `->` for named nodes
- Regular expressions for terminals
- `%import` and `%ignore` for whitespace handling

## Dependencies

- Python 3.6+
- lark-parser