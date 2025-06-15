#!/usr/bin/env python3
"""
BNF Grammar to CST Parser
A minimal implementation for parsing documents using BNF grammar definitions
"""

from lark import Lark, Tree
import json


def create_parser(grammar):
    """
    Create a Lark parser from a BNF grammar string.
    
    Args:
        grammar: BNF grammar definition as a string
        
    Returns:
        Lark parser instance
    """
    return Lark(grammar, parser='lalr', debug=True)


def parse_document(parser, document):
    """
    Parse a document using the provided parser.
    
    Args:
        parser: Lark parser instance
        document: Input text to parse
        
    Returns:
        Concrete Syntax Tree (CST)
    """
    return parser.parse(document)


def print_cst(tree, indent=0):
    """
    Pretty print a CST for visualization.
    
    Args:
        tree: Lark Tree object
        indent: Current indentation level
    """
    if isinstance(tree, Tree):
        print('  ' * indent + f'{tree.data}:')
        for child in tree.children:
            print_cst(child, indent + 1)
    else:
        print('  ' * indent + repr(tree))


def main():
    # Example BNF grammar for simple arithmetic expressions
    arithmetic_grammar = r"""
    ?start: expr
    
    ?expr: term
         | expr "+" term   -> add
         | expr "-" term   -> sub
    
    ?term: factor
         | term "*" factor -> mul
         | term "/" factor -> div
    
    ?factor: "(" expr ")"
           | NUMBER
    
    NUMBER: /[0-9]+(\.[0-9]+)?/
    
    %import common.WS
    %ignore WS
    """
    
    # Example with a simple language grammar
    simple_lang_grammar = r"""
    ?start: statement+
    
    ?statement: assignment
              | expression ";"
    
    assignment: IDENTIFIER "=" expression ";"
    
    ?expression: IDENTIFIER
               | NUMBER
               | expression "+" expression -> add
               | expression "*" expression -> mul
               | "(" expression ")"
    
    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
    NUMBER: /[0-9]+/
    
    %import common.WS
    %ignore WS
    """
    
    # Example 1: Parse arithmetic expression
    print("=== Arithmetic Expression Example ===")
    arith_parser = create_parser(arithmetic_grammar)
    arith_doc = "3 + 4 * 2 - 1"
    arith_cst = parse_document(arith_parser, arith_doc)
    print(f"Input: {arith_doc}")
    print("CST:")
    print_cst(arith_cst)
    
    print("\n=== Simple Language Example ===")
    lang_parser = create_parser(simple_lang_grammar)
    lang_doc = """
    x = 5;
    y = x + 3;
    x * y;
    """
    lang_cst = parse_document(lang_parser, lang_doc)
    print(f"Input: {lang_doc.strip()}")
    print("CST:")
    print_cst(lang_cst)


def parse_custom_bnf(bnf_grammar, document):
    """
    Convenience function to parse a document with a custom BNF grammar.
    
    Args:
        bnf_grammar: BNF grammar string
        document: Document to parse
        
    Returns:
        CST as a Lark Tree object
    """
    parser = create_parser(bnf_grammar)
    return parse_document(parser, document)


if __name__ == "__main__":
    main()