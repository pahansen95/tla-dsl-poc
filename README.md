# Natural Language Specification DSL Parser

A modular parsing framework for Natural Language Specification DSL documents. The parser transforms human-readable specifications into Concrete Syntax Trees (CST), enabling validation, transformation, and analysis workflows.

## Overview

This project provides tools for working with a domain-specific language designed to express formal specifications in natural language. The DSL bridges the gap between formal methods (like TLA+) and human-readable documentation.

### Key Features

- **Full CST Preservation**: Parse documents while preserving all formatting and structure
- **Perfect Roundtrip**: Parse → Unparse yields identical documents
- **Pipeline-Ready**: JSON serialization enables transformation workflows
- **Validation Tools**: Compare document structures and verify equivalence
- **Modular Design**: Compose parsing, transformation, and unparsing operations

## Architecture

The system follows a clean separation of concerns:

```
DSL Document → Parser → CST → Serializer → JSON → Transformer → JSON → Deserializer → CST → Unparser → DSL Document
```

### Core Modules

- **`core/parser.py`**: Converts DSL text to Concrete Syntax Trees
- **`core/unparser.py`**: Reconstructs DSL text from CST
- **`core/syntax.py`**: Serializes/deserializes CST for pipeline processing
- **`src/lex.py`**: CLI interface orchestrating all operations

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd tla-dsl-poc

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Parse and display tree structure
python src/lex.py spec/example.dsl

# Unparse (reconstruct text)
python src/lex.py spec/example.dsl --unparse

# Serialize to JSON
python src/lex.py spec/example.dsl --serialize

# Validate roundtrip
python src/lex.py spec/example.dsl --roundtrip
```

## Core Concepts

### Natural Language Specification DSL

The DSL provides structured natural language patterns for expressing system specifications:

```
System: IntegrationLib
A toy integration library that brokers request/response work.

The system uses these concepts:
- Client Identity: unique identifier from finite set
- Request: message sent to external service

The system maintains:

Client phases:
  Each client has exactly one phase
  Initially all clients are idle

When a client sends a request:
  The client must be idle
  Then:
    - The client transitions to waiting
    - The request becomes pending
```

### Concrete Syntax Tree (CST)

Unlike Abstract Syntax Trees, CSTs preserve all syntactic information including whitespace, comments, and formatting. This enables perfect document reconstruction and format-preserving transformations.

### Pipeline Model

The JSON serialization format enables Unix-style pipeline composition:

```bash
# Transform pipeline
./lex.py input.dsl -s | transform.py | ./lex.py -u > output.dsl

# Validation pipeline
./lex.py original.dsl -s | normalize.py | ./lex.py -v normalized.dsl
```

## Usage Guide

### Parsing Documents

Parse a DSL document and examine its structure:

```bash
python src/lex.py spec/integration-lib.dsl

# Debug mode shows token details
python src/lex.py spec/integration-lib.dsl --debug
```

### Document Validation

Validate that two documents have equivalent structure:

```bash
# Direct comparison
python src/lex.py doc1.dsl --validate-against doc2.dsl

# Validate transformation preserves structure
python src/lex.py original.dsl -s | ./transform.py | python src/lex.py -v expected.dsl
```

### Serialization Format

The JSON CST format preserves complete structural information:

```json
{
  "type": "tree",
  "name": "specification",
  "children": [
    {
      "type": "token",
      "value": "System:",
      "token_type": "LITERAL",
      "line": 1,
      "column": 1
    }
  ]
}
```

### Error Handling

Parse errors provide context and location:

```
✗ Parse Error - Unexpected Character:
  Line 5, Column 3
  Context: "- Request"
```

## Module Reference

### core/parser.py

Creates Lark parsers and converts DSL text to CST:

```python
from core import create_parser, parse_document

parser = create_parser(grammar_text)
tree = parse_document(parser, dsl_text)
```

### core/unparser.py

Reconstructs text from CST structures:

```python
from core import unparse_tree, extract_tokens

text = unparse_tree(tree)
tokens = extract_tokens(tree)  # Get all tokens
```

### core/syntax.py

Handles CST serialization for pipeline processing:

```python
from core import serialize_cst, deserialize_cst

json_str = serialize_cst(tree)
restored = deserialize_cst(json_str)
```

## Pipeline Patterns

### Format Normalization

Remove formatting variations while preserving structure:

```bash
#!/usr/bin/env python3
# normalize.py
import sys, json
from core import deserialize_cst, serialize_cst

tree = deserialize_cst(sys.stdin.read())
# Apply normalization transforms
print(serialize_cst(tree))
```

### CST Transformation

Modify document structure programmatically:

```python
def transform_tree(tree):
    """Example: Add default values to state declarations."""
    for node in tree.find_data("state_properties"):
        # Modify CST structure
        pass
    return tree
```

### Validation Pipeline

Create validation workflows:

```bash
# validate.sh
#!/bin/bash
python src/lex.py "$1" -s | \
  python normalize.py | \
  python src/lex.py --validate-against "$2"
```

## Grammar Specification

The DSL grammar is defined in `grammar/TLA.lark` using Lark's EBNF notation:

```lark
specification: header definitions state_section operations? constraints

header: "System:" WS* system_name NEWLINE+ description

state_block: state_name ":" NEWLINE state_properties
```

Grammar features:
- Preserves all whitespace for perfect roundtrip
- Supports multi-line descriptions and properties
- Enforces consistent indentation patterns
- Handles optional sections gracefully

## Development

### Project Structure

```
tla-dsl-poc/
├── src/
│   ├── lex.py          # CLI interface
│   └── core/           # Core modules
│       ├── parser.py   # DSL parsing
│       ├── unparser.py # Text reconstruction
│       └── syntax.py   # CST serialization
├── grammar/
│   └── TLA.lark        # DSL grammar definition
├── spec/               # Example specifications
└── tests/              # Test suite
```

### Testing

Run tests to verify functionality:

```bash
# Roundtrip validation
python src/lex.py spec/example.dsl --roundtrip

# Grammar validation
python -c "from core import validate_grammar; print(validate_grammar(open('grammar/TLA.lark').read()))"
```

### Extending the Grammar

1. Modify `grammar/TLA.lark` to add new constructs
2. Update example documents in `spec/`
3. Test roundtrip preservation
4. Document new patterns

### Contributing

1. Maintain separation of concerns between modules
2. Preserve CST completeness for roundtrip guarantee
3. Follow existing naming conventions
4. Add tests for new functionality
5. Update documentation

## License

MIT

## Acknowledgments

Built with [Lark](https://github.com/lark-parser/lark), a modern parsing library for Python.