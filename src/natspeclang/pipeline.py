"""
Transformation pipeline orchestration for Natural Specification Language.

Coordinates transformations between different representations with automatic
type inference and format detection.
"""

import json
from pathlib import Path
from typing import Optional, Tuple, Any, Union
from dataclasses import dataclass

from lexical import LexicalContext

from .types import TransformResult, FormatStyle
from .errors import TransformationError
from .lex import (
    parse, format_ast, serialize_ast, deserialize_ast,
    serialize_cst, deserialize_cst, Specification, SyntaxTree
)
from lexical import FrozenNode


# Representation types
RepType = str  # 'spec', 'cst', 'ast'
Format = str   # 'text', 'json'


@dataclass(frozen=True, slots=True)
class TransformRequest:
    """Encapsulates a transformation request."""
    content: str
    from_type: Optional[RepType]
    to_type: Optional[RepType]
    format_override: Optional[Format]
    source_path: Optional[Path]
    style: Optional[FormatStyle]


class TypeInference:
    """Infers types and formats from file extensions and content."""
    
    @staticmethod
    def from_filename(path: Path) -> Tuple[Optional[RepType], Optional[Format]]:
        """Infer type and format from file extension."""
        name = path.name.lower()
        
        # Check compound extensions first
        if name.endswith('.ast.json'):
            return 'ast', 'json'
        elif name.endswith('.cst.json'):
            return 'cst', 'json'
        
        # Check simple extensions
        ext = path.suffix.lower()
        if ext == '.dsl':
            return 'spec', 'text'
        elif ext == '.json':
            # Try to infer from content structure
            return None, 'json'
        elif ext in ['.txt', '.text']:
            return None, 'text'
        
        return None, None
    
    @staticmethod
    def from_json_structure(data: dict) -> Optional[RepType]:
        """Infer type from JSON structure."""
        if '_type' not in data:
            return None
        
        # Check for AST types
        if data['_type'] == 'Specification':
            return 'ast'
        
        # Check for CST markers
        if data.get('type') in ['tree', 'token']:
            return 'cst'
        
        return None
    
    @staticmethod
    def from_content(content: str) -> RepType:
        """Infer type from content structure."""
        # Try to parse as JSON
        try:
            data = json.loads(content)
            json_type = TypeInference.from_json_structure(data)
            if json_type:
                return json_type
        except json.JSONDecodeError:
            pass
        
        # Check for DSL markers
        if content.strip().startswith('System:'):
            return 'spec'
        
        # Default to spec for text input
        return 'spec'
    
    @staticmethod
    def next_type(current: RepType) -> RepType:
        """Get next type in natural progression."""
        progression = {
            'spec': 'ast',  # Skip CST for integrated parser
            'cst': 'ast',
            'ast': 'spec'
        }
        return progression.get(current, 'ast')
    
    @staticmethod
    def default_format(rep_type: RepType, is_stdout: bool) -> Format:
        """Get default format for type and destination."""
        if rep_type == 'spec':
            return 'text'
        # Use JSON for structured data when piping
        return 'json' if is_stdout else 'text'


class TransformationPipeline:
    """Orchestrates transformations between representations."""
    
    def __init__(self, obs_context: Optional[LexicalContext] = None):
        self.obs_context = obs_context
    
    def transform(self, request: TransformRequest) -> TransformResult:
        """
        Execute transformation with intelligent defaults.
        
        Returns the transformed content as string or structured object.
        """
        # Infer input type if needed
        from_type = request.from_type
        if from_type is None:
            from_type = self._infer_input_type(request)
        
        # Load input based on type
        data = self._load_input(request.content, from_type)
        
        # Infer output type if needed
        to_type = request.to_type
        if to_type is None:
            to_type = TypeInference.next_type(from_type)
        
        # Transform data
        result = self._transform(data, from_type, to_type)
        
        # Apply formatting if string output requested
        if isinstance(result, str):
            return result
        
        # Determine output format
        output_format = self._determine_format(
            to_type,
            request.format_override,
            request.source_path
        )
        
        # Format output
        return self._format_output(result, to_type, output_format, request.style)
    
    def _infer_input_type(self, request: TransformRequest) -> RepType:
        """Infer input type from content and path."""
        # Try filename first
        if request.source_path:
            file_type, _ = TypeInference.from_filename(request.source_path)
            if file_type:
                return file_type
        
        # Infer from content
        return TypeInference.from_content(request.content)
    
    def _load_input(self, content: str, input_type: RepType) -> Any:
        """Load input based on type."""
        if input_type == 'spec':
            return parse(content, self.obs_context)
        
        elif input_type == 'cst':
            return deserialize_cst(content)
        
        elif input_type == 'ast':
            return deserialize_ast(content)
        
        raise TransformationError(
            f"Unknown input type: {input_type}",
            input_type, "unknown"
        )
    
    def _transform(self, data: Any, from_type: RepType, to_type: RepType) -> Any:
        """Transform between representations."""
        if from_type == to_type:
            return data
        
        # Define transformation paths
        if from_type == 'spec' and to_type == 'ast':
            # Already parsed to AST
            return data
        
        elif from_type == 'spec' and to_type == 'cst':
            # For integrated parser, CST is implicit
            return SyntaxTree(FrozenNode("specification", (data,)))
        
        elif from_type == 'cst' and to_type == 'ast':
            # Extract AST from CST wrapper
            return data.root.children[0]
        
        elif from_type == 'cst' and to_type == 'spec':
            # Format CST's AST content
            ast = data.root.children[0]
            return format_ast(ast)
        
        elif from_type == 'ast' and to_type == 'spec':
            return format_ast(data)
        
        elif from_type == 'ast' and to_type == 'cst':
            # Wrap AST in CST structure
            return SyntaxTree(FrozenNode("specification", (data,)))
        
        raise TransformationError(
            f"No transformation path from {from_type} to {to_type}",
            from_type, to_type,
            reason="Unsupported transformation"
        )
    
    def _determine_format(
        self,
        output_type: RepType,
        format_override: Optional[Format],
        output_path: Optional[Path]
    ) -> Format:
        """Determine output format with smart defaults."""
        # Explicit override takes precedence
        if format_override:
            return format_override
        
        # Infer from output filename
        if output_path:
            _, file_format = TypeInference.from_filename(output_path)
            if file_format:
                return file_format
        
        # Use defaults based on type and destination
        is_stdout = output_path is None
        return TypeInference.default_format(output_type, is_stdout)
    
    def _format_output(
        self,
        data: Any,
        output_type: RepType,
        format: Format,
        style: Optional[FormatStyle]
    ) -> str:
        """Format output based on type and format."""
        if output_type == 'spec':
            # Spec is always text
            return data if isinstance(data, str) else str(data)
        
        if format == 'json':
            if output_type == 'ast':
                return serialize_ast(data)
            elif output_type == 'cst':
                return serialize_cst(data)
        
        # Text representation
        if output_type == 'ast':
            return format_ast(data, style)
        elif output_type == 'cst':
            # Format CST's AST content
            ast = data.root.children[0]
            return format_ast(ast, style)
        
        raise TransformationError(
            f"Cannot format {output_type} as {format}",
            output_type, format
        )