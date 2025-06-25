"""Transformation pipeline builder for Natural Specification Language.

Provides automatic pipeline construction between different representation
formats, enabling seamless transformations through intermediate stages.
"""

# Standard library imports
from collections import deque
from typing import Any, Dict, Final, List, Protocol, Tuple

# Observability imports
from observability import SharedContext
from observability.domains.logging import Logger
from lexical import LexicalContext

# Local imports
from .lex import (
  DSLLexer,
  DSLParser,
  ASTBuilder,
  ASTFormatter,
  serialize_ast,
  deserialize_ast,
  serialize_cst,
  deserialize_cst,
)
from lexical import SyntaxTree

# Module-level logger
logger = Logger(__name__, SharedContext.get())

# Module constants
DEFAULT_CACHE_SIZE: Final[int] = 100

# Format constants using strings for performance
NSL_FORMAT: Final[str] = "NSL"
CST_FORMAT: Final[str] = "CST"
CST_JSON_FORMAT: Final[str] = "CST_JSON"
AST_FORMAT: Final[str] = "AST"
AST_JSON_FORMAT: Final[str] = "AST_JSON"
AST_TEXT_FORMAT: Final[str] = "AST_TEXT"
# Future formats
# IR_FORMAT: Final[str] = "IR"
# TLA_FORMAT: Final[str] = "TLA"


# Protocol definitions
class TransformFunction(Protocol):
  """Protocol for transformation functions."""

  def __call__(self, data: Any) -> Any: ...


class Format:
  """Format constants for performance-critical comparisons."""

  NSL = NSL_FORMAT
  CST = CST_FORMAT
  CST_JSON = CST_JSON_FORMAT
  AST = AST_FORMAT
  AST_JSON = AST_JSON_FORMAT
  AST_TEXT = AST_TEXT_FORMAT

  # All formats for validation
  ALL_FORMATS = frozenset([NSL, CST, CST_JSON, AST, AST_JSON, AST_TEXT])

  @classmethod
  def validate(cls, format_str: str) -> str:
    """Validate format string."""
    if format_str not in cls.ALL_FORMATS:
      raise ValueError(f"Unknown format: {format_str}")
    return format_str


class PipelineBuilder:
  """Constructs transformation pipelines between formats.

  The builder maintains a registry of direct transformations and uses
  graph traversal to find multi-step transformation paths when needed.
  Integrates observability for debugging transformation flows.
  """

  __slots__ = ("transforms", "_obs", "_cache", "_cache_size")

  def __init__(self, obs_context: LexicalContext = None):
    """Initialize pipeline builder with optional observability."""
    # Use SharedContext if no explicit context provided
    if obs_context is None:
      try:
        shared_ctx = SharedContext.get()
        obs_context = LexicalContext(shared_ctx)
      except RuntimeError:
        # SharedContext not initialized, use null context
        obs_context = LexicalContext.null()

    self.transforms: Dict[Tuple[str, str], TransformFunction] = {}
    self._obs = obs_context
    self._cache: Dict[Tuple[str, str], List[TransformFunction]] = {}
    self._cache_size = DEFAULT_CACHE_SIZE
    self._register_transforms()

  def _register_transforms(self) -> None:
    """Register all available transformations."""
    # NSL → CST transformations
    self.register(Format.NSL, Format.CST, self._nsl_to_cst)
    self.register(Format.NSL, Format.CST_JSON, self._nsl_to_cst_json)

    # CST → AST transformations
    self.register(Format.CST, Format.AST, self._cst_to_ast)
    self.register(Format.CST_JSON, Format.AST, self._cst_json_to_ast)

    # AST output transformations
    self.register(Format.AST, Format.AST_TEXT, self._ast_to_text)
    self.register(Format.AST, Format.AST_JSON, self._ast_to_json)
    self.register(Format.AST, Format.NSL, self._ast_to_nsl)

    # Deserialization transformations
    self.register(Format.AST_JSON, Format.AST, self._ast_json_to_ast)
    self.register(Format.CST_JSON, Format.CST, self._cst_json_to_cst)

  def register(self, source: str, target: str, transform: TransformFunction) -> None:
    """Register a transformation between formats."""
    # Validate formats
    Format.validate(source)
    Format.validate(target)

    self.transforms[(source, target)] = transform
    # Clear cache when registry changes
    self._cache.clear()

  def find_pipeline(self, source: str, target: str) -> List[TransformFunction]:
    """Find transformation path from source to target format.

    Uses breadth-first search to find the shortest transformation path.
    Results are cached for repeated lookups.

    Returns:
        List of transformation functions to execute in order

    Raises:
        ValueError: If no transformation path exists
    """
    if source == target:
      return []

    # Check cache first
    cache_key = (source, target)
    if cache_key in self._cache:
      return self._cache[cache_key]

    # Emit search start
    if self._obs.has_handlers():
      self._obs.emit_event("pipeline.search.start", source=source, target=target)

    # Check for direct transformation
    if (source, target) in self.transforms:
      pipeline = [self.transforms[(source, target)]]
      self._cache_pipeline(cache_key, pipeline)
      return pipeline

    # Find path using BFS
    queue = deque([(source, [])])
    visited = {source}

    while queue:
      current, path = queue.popleft()

      # Explore all transformations from current format
      for (src, dst), transform in self.transforms.items():
        if src == current and dst not in visited:
          new_path = path + [transform]

          if dst == target:
            self._cache_pipeline(cache_key, new_path)
            return new_path

          visited.add(dst)
          queue.append((dst, new_path))

    raise ValueError(f"No transformation path from {source} to {target}")

  def _cache_pipeline(self, key: Tuple[str, str], pipeline: List[TransformFunction]) -> None:
    """Cache pipeline with size limit."""
    if len(self._cache) >= self._cache_size:
      # Simple FIFO eviction
      first_key = next(iter(self._cache))
      del self._cache[first_key]
    self._cache[key] = pipeline

  def transform(self, data: Any, source: str, target: str) -> Any:
    """Execute transformation pipeline from source to target format."""
    logger.info(f"Transforming {source} to {target}")

    # Emit transform start
    if self._obs.has_handlers():
      self._obs.emit_event("pipeline.transform.start", source=source, target=target)

    pipeline = self.find_pipeline(source, target)

    result = data
    for i, transform in enumerate(pipeline):
      if self._obs.has_handlers():
        self._obs.emit_event("pipeline.step.start", step=i, transform=transform.__name__)

      logger.debug(f"Pipeline step {i}: {transform.__name__}")
      result = transform(result)

      if self._obs.has_handlers():
        self._obs.emit_event("pipeline.step.complete", step=i, transform=transform.__name__)

    if self._obs.has_handlers():
      self._obs.emit_event("pipeline.transform.complete", source=source, target=target)

    logger.info(f"Transformation complete: {source} → {target}")
    return result

  def describe_pipeline(self, source: str, target: str) -> List[str]:
    """Get human-readable description of transformation steps."""
    pipeline = self.find_pipeline(source, target)
    return [transform.__name__ for transform in pipeline]

  # Transformation implementations

  def _nsl_to_cst(self, text: str) -> SyntaxTree:
    """Parse NSL text to CST."""
    lexer = DSLLexer(self._obs)
    tokens = list(lexer.lex(text))
    parser = DSLParser(tokens, self._obs)
    return parser.parse()

  def _nsl_to_cst_json(self, text: str) -> str:
    """Parse NSL text directly to CST JSON."""
    tree = self._nsl_to_cst(text)
    return serialize_cst(tree)

  def _cst_to_ast(self, tree: SyntaxTree):
    """Transform CST to AST."""
    builder = ASTBuilder()
    return builder.build(tree)

  def _cst_json_to_ast(self, json_str: str):
    """Transform CST JSON to AST."""
    tree = deserialize_cst(json_str)
    return self._cst_to_ast(tree)

  def _ast_to_text(self, spec):
    """Format AST as human-readable text."""
    formatter = ASTFormatter()
    return formatter.format(spec)

  def _ast_to_nsl(self, spec):
    """Convert AST back to NSL format."""
    formatter = ASTFormatter()
    return formatter.format(spec)

  def _ast_to_json(self, spec) -> str:
    """Serialize AST to JSON."""
    return serialize_ast(spec)

  def _ast_json_to_ast(self, json_str: str):
    """Deserialize AST from JSON."""
    return deserialize_ast(json_str)

  def _cst_json_to_cst(self, json_str: str) -> SyntaxTree:
    """Deserialize CST from JSON."""
    return deserialize_cst(json_str)


# Module-level instances
_pipeline_builder: PipelineBuilder = None


# Public functions
def get_pipeline_builder() -> PipelineBuilder:
  """Get the global pipeline builder instance."""
  global _pipeline_builder
  if _pipeline_builder is None:
    _pipeline_builder = PipelineBuilder()
  return _pipeline_builder


def transform(data: Any, source: str, target: str) -> Any:
  """Convenience function for one-off transformations."""
  return _pipeline_builder.transform(data, source, target)


def describe_pipeline(source: str, target: str) -> List[str]:
  """Describe the transformation pipeline between formats."""
  return _pipeline_builder.describe_pipeline(source, target)


# Explicit exports
__all__ = [
  # Format constants
  "Format",
  # Main class
  "PipelineBuilder",
  # Functions
  "get_pipeline_builder",
  "transform",
  "describe_pipeline",
  # Protocols
  "TransformFunction",
]
