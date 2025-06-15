#!/usr/bin/env python3
"""
BNF Grammar Test Parser
Tests Natural Language Specification DSL against documents
"""

from lark import Lark, Tree, exceptions
import sys
import argparse
from pathlib import Path


CONTEXT = Path(__file__).parent


def convert_bnf_to_lark(bnf_content):
    """
    Convert BNF notation to Lark grammar format.
    
    Handles:
    - Character ranges [a-z] → /[a-z]/
    - Epsilon rules E → ""
    - Maintains terminals and non-terminals
    """
    lines = bnf_content.split('\n')
    lark_grammar = []
    
    for line in lines:
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('/*'):
            continue
            
        # Convert character ranges
        if '[' in line and '-' in line and ']' in line:
            # Replace [a-z] with /[a-z]/
            import re
            line = re.sub(r'\[([a-zA-Z0-9]-[a-zA-Z0-9])\]', r'/[\1]/', line)
        
        # Convert epsilon E to empty string
        line = line.replace(' E ', ' "" ')
        line = line.replace(' E\n', ' ""\n')
        
        # Convert BNF ::= to Lark :
        line = line.replace('::=', ':')
        
        # Remove angle brackets from non-terminals
        line = re.sub(r'<(\w+)>', r'\1', line)
        
        lark_grammar.append(line)
    
    return '\n'.join(lark_grammar)


def load_grammar(grammar_path):
    """Load and convert BNF grammar to Lark format."""
    try:
        with open(grammar_path, 'r') as f:
            bnf_content = f.read()
        
        # Convert BNF to Lark format
        lark_grammar = convert_bnf_to_lark(bnf_content)
        
        # Add Lark-specific directives
        lark_grammar = f"""
{lark_grammar}

%import common.WS_INLINE
%ignore WS_INLINE
"""
        
        return lark_grammar
    except Exception as e:
        print(f"Error loading grammar: {e}")
        return None


def create_parser(grammar):
    """Create Lark parser from grammar string."""
    try:
        return Lark(
            grammar, 
            start='specification',
            parser='earley',  # More robust for complex grammars
            debug=True
        )
    except Exception as e:
        print(f"Error creating parser: {e}")
        print("\nGrammar that failed:")
        print("=" * 50)
        print(grammar)
        print("=" * 50)
        raise


def parse_document(parser, document_path):
    """Parse document using the grammar."""
    try:
        with open(document_path, 'r') as f:
            content = f.read()
        
        print(f"Parsing document: {document_path}")
        print(f"Document length: {len(content)} characters")
        print("-" * 50)
        
        tree = parser.parse(content)
        return tree
    except exceptions.UnexpectedCharacters as e:
        print(f"\nParse Error - Unexpected Character:")
        print(f"  Line {e.line}, Column {e.column}")
        print(f"  Expected: {e.expected}")
        print(f"  Context: {e.get_context(content)}")
        return None
    except exceptions.UnexpectedToken as e:
        print(f"\nParse Error - Unexpected Token:")
        print(f"  Token: {e.token}")
        print(f"  Expected: {e.expected}")
        print(f"  Line {e.line}, Column {e.column}")
        return None
    except Exception as e:
        print(f"\nParse Error: {type(e).__name__}: {e}")
        return None


def print_tree(tree, indent=0):
    """Pretty print parse tree."""
    if isinstance(tree, Tree):
        print('  ' * indent + f'{tree.data}')
        for child in tree.children:
            print_tree(child, indent + 1)
    else:
        # Terminal - show abbreviated version if too long
        value = str(tree)
        if len(value) > 50:
            value = value[:47] + '...'
        print('  ' * indent + f'"{value}"')


def validate_grammar(grammar_path, document_path):
    """Main validation function."""
    print(f"BNF Grammar: {grammar_path}")
    print(f"Test Document: {document_path}")
    print("=" * 70)
    
    # Load and convert grammar
    grammar = load_grammar(grammar_path)
    if not grammar:
        return False
    
    # Create parser
    try:
        parser = create_parser(grammar)
        print("✓ Grammar loaded successfully")
    except Exception as e:
        print("✗ Failed to create parser")
        return False
    
    # Parse document
    tree = parse_document(parser, document_path)
    
    if tree:
        print("\n✓ Document parsed successfully!")
        print("\nParse Tree:")
        print("-" * 50)
        print_tree(tree)
        return True
    else:
        print("\n✗ Document parsing failed")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Test BNF grammar against specification documents'
    )
    parser.add_argument(
        'grammar', 
        type=Path,
        default=(CONTEXT / 'TLA.bnf').as_posix(),
        help='Path to BNF grammar file'
    )
    parser.add_argument(
        'document',
        type=Path,
        default=(CONTEXT / 'spec.tla').as_posix(),
        help='Path to document to parse'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show debug output'
    )
    
    args = parser.parse_args()
    
    # Validate files exist
    if not args.grammar.exists():
        print(f"Error: Grammar file not found: {args.grammar}")
        sys.exit(1)
    
    if not args.document.exists():
        print(f"Error: Document file not found: {args.document}")
        sys.exit(1)
    
    # Run validation
    success = validate_grammar(args.grammar, args.document)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()