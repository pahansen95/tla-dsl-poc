"""
Unified lexical analysis for Natural Specification Language.

Consolidates all lexical components including token patterns, parsing,
AST definitions, transformations, and serialization into a cohesive module
leveraging the Lexical framework.
"""

import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager

from lexical import (
    Lexer, Parser, Token, pattern, token, rule,
    SyntaxTree, FrozenNode, FrozenToken,
    LexicalContext, Position, Match
)

from .types import TokenType, TokenValue, FormatStyle
from .errors import LexicalError, SyntaxError, SemanticError, SerializationError


# ===== DSL Token Patterns =====

class DSLLexer(Lexer):
    """Lexer for Natural Specification Language."""
    
    # Keywords (high priority)
    system_kw = pattern.literal("System:", priority=10)
    the_system = pattern.literal("The system", priority=10)
    when_kw = pattern.literal("When", priority=10)
    then_kw = pattern.literal("Then:", priority=10)
    initially = pattern.literal("Initially", priority=10)
    
    # Section headers
    uses_concepts = pattern.literal("uses these concepts:", priority=9)
    maintains = pattern.literal("maintains:", priority=9)
    constraints = pattern.literal("System Constraints:", priority=9)
    guarantees = pattern.literal("System Guarantees:", priority=9)
    
    # Structural tokens
    bullet = pattern.literal("-", priority=5)
    colon = pattern.literal(":", priority=5)
    must = pattern.literal("must", priority=5)
    
    # Content patterns
    identifier = pattern.regex(r'[a-zA-Z][a-zA-Z0-9_]*(?:\s+[a-zA-Z][a-zA-Z0-9_]*)*')
    
    # Text until end of line
    text_line = pattern.regex(r'[^\n]+')
    
    # Whitespace handling
    newline = pattern.literal("\n", skip=True)
    whitespace = pattern.regex(r'[ \t]+', skip=True)
    
    # Indentation tracking
    @token(priority=8)
    def indent(self, nav):
        if nav.at_line_start and nav.match_literal("  "):
            nav.advance(2)
            return Match("  ", 2)
        return None


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
            properties=tuple(properties)
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
            
            states.append(StateDeclaration(
                name=name,
                properties=tuple(properties),
                initial_condition=initial
            ))
        
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
            trigger=trigger,
            preconditions=tuple(preconditions),
            effects=tuple(effects),
            unchanged=tuple(unchanged)
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
        self.style = style or {
            "indent_size": 2,
            "bullet_char": "-",
            "section_spacing": 1
        }
    
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
        if hasattr(obj, '__dict__'):
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