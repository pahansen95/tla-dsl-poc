"""
Observability configuration for Natural Specification Language.

Configures domain-specific event handlers and instrumentation for lexical
analysis, parsing, and transformation operations.
"""

import sys
from typing import List, Optional, Dict, Any

from observability import (
    ObservabilityConfig,
    PrintHandler,
    JsonHandler,
    TimeDeltaHandler,
    filtered,
    FanoutHandler,
    EventHandler
)
from observability.types import EventDict

from lexical.observe import (
    LEX_TOKEN_EMIT,
    PARSE_RULE_ENTER,
    PARSE_RULE_EXIT,
    PARSE_BACKTRACK,
    AST_NODE_CREATE
)


# Domain event prefixes
NSL_PREFIX = "nsl"
NSL_TRANSFORM = f"{NSL_PREFIX}.transform"
NSL_PARSE = f"{NSL_PREFIX}.parse"
NSL_ERROR = f"{NSL_PREFIX}.error"


class NSLEventFormatter:
    """Format NSL events for readable output."""
    
    def __init__(self, show_details: bool = False):
        self.show_details = show_details
        self.rule_stack: List[str] = []
    
    def format_event(self, event: EventDict) -> str:
        """Format event based on type."""
        event_type = event['type']
        
        # Track rule stack for context
        if event_type == PARSE_RULE_ENTER:
            self.rule_stack.append(event.get('rule', 'unknown'))
        elif event_type == PARSE_RULE_EXIT:
            if self.rule_stack:
                self.rule_stack.pop()
        
        # Format based on event type
        if event_type == LEX_TOKEN_EMIT:
            return self._format_token(event)
        elif event_type == PARSE_RULE_ENTER:
            return self._format_rule_enter(event)
        elif event_type == PARSE_RULE_EXIT:
            return self._format_rule_exit(event)
        elif event_type == PARSE_BACKTRACK:
            return self._format_backtrack(event)
        elif event_type == AST_NODE_CREATE:
            return self._format_ast_node(event)
        elif event_type.startswith(NSL_PREFIX):
            return self._format_nsl_event(event)
        else:
            return self._format_generic(event)
    
    def _format_token(self, event: EventDict) -> str:
        """Format token event."""
        token_type = event.get('token_type', 'unknown')
        token_value = event.get('token_value', '')
        
        # Truncate long values
        if len(token_value) > 20:
            token_value = token_value[:17] + '...'
        
        return f"TOKEN {token_type}: '{token_value}'"
    
    def _format_rule_enter(self, event: EventDict) -> str:
        """Format rule entry."""
        rule = event.get('rule', 'unknown')
        depth = event.get('parse_depth', 0)
        indent = '  ' * (depth - 1)
        return f"{indent}→ {rule}"
    
    def _format_rule_exit(self, event: EventDict) -> str:
        """Format rule exit."""
        if not self.show_details:
            return None  # Skip in non-detailed mode
        
        rule = event.get('rule', 'unknown')
        depth = event.get('parse_depth', 0)
        duration_ms = event.get('duration_ms', 0)
        indent = '  ' * depth
        return f"{indent}← {rule} ({duration_ms:.1f}ms)"
    
    def _format_backtrack(self, event: EventDict) -> str:
        """Format backtrack event."""
        rule = event.get('rule', 'unknown')
        reason = event.get('reason', 'unknown')
        return f"BACKTRACK in {rule}: {reason}"
    
    def _format_ast_node(self, event: EventDict) -> str:
        """Format AST node creation."""
        if not self.show_details:
            return None
        
        node_type = event.get('node_type', 'unknown')
        return f"AST: {node_type}"
    
    def _format_nsl_event(self, event: EventDict) -> str:
        """Format NSL-specific events."""
        event_type = event['type']
        value = event.get('value', '')
        
        if event_type == NSL_TRANSFORM:
            from_type = event.get('from_type', '?')
            to_type = event.get('to_type', '?')
            return f"TRANSFORM: {from_type} → {to_type}"
        else:
            return f"NSL: {value}"
    
    def _format_generic(self, event: EventDict) -> str:
        """Format generic event."""
        return f"{event['type']}: {event.get('value', '')}"


def create_trace_handler(detailed: bool = False) -> EventHandler:
    """Create handler for trace output."""
    formatter = NSLEventFormatter(show_details=detailed)
    
    def format_and_print(event: EventDict) -> None:
        formatted = formatter.format_event(event)
        if formatted:  # Skip None results
            # Add timing information
            timestamp_ms = event.get('timestamp_ms', 0)
            delta_us = event.get('delta_us', 0)
            print(
                f"{timestamp_ms:8.1f}ms (+{delta_us:4.0f}μs) {formatted}",
                file=sys.stderr
            )
    
    return format_and_print


def create_metrics_handler() -> EventHandler:
    """Create handler for metrics collection."""
    metrics: Dict[str, Any] = {
        'token_count': 0,
        'rule_durations': {},
        'backtrack_count': 0,
        'ast_nodes': 0
    }
    
    def collect_metrics(event: EventDict) -> None:
        event_type = event['type']
        
        if event_type == LEX_TOKEN_EMIT:
            metrics['token_count'] += 1
        elif event_type == PARSE_RULE_EXIT:
            rule = event.get('rule', 'unknown')
            duration_ms = event.get('duration_ms', 0)
            if rule not in metrics['rule_durations']:
                metrics['rule_durations'][rule] = []
            metrics['rule_durations'][rule].append(duration_ms)
        elif event_type == PARSE_BACKTRACK:
            metrics['backtrack_count'] += 1
        elif event_type == AST_NODE_CREATE:
            metrics['ast_nodes'] += 1
    
    # Store metrics for later retrieval
    collect_metrics.metrics = metrics
    return collect_metrics


def create_error_handler() -> EventHandler:
    """Create handler for error events."""
    def handle_error(event: EventDict) -> None:
        if event['type'] == 'error' or event['type'].endswith('.error'):
            error_msg = event.get('error', event.get('value', 'Unknown error'))
            position = event.get('position')
            
            if position:
                print(
                    f"ERROR at line {position.line}, column {position.column}: {error_msg}",
                    file=sys.stderr
                )
            else:
                print(f"ERROR: {error_msg}", file=sys.stderr)
    
    return handle_error


def configure_observability(
    enable_trace: bool = False,
    enable_metrics: bool = False,
    enable_errors: bool = True,
    trace_detailed: bool = False,
    json_output: bool = False
) -> ObservabilityConfig:
    """Configure observability for NSL operations."""
    handlers: List[EventHandler] = []
    
    # Always add error handler
    if enable_errors:
        handlers.append(create_error_handler())
    
    # Add trace handler
    if enable_trace:
        if json_output:
            # JSON output for machine processing
            handlers.append(JsonHandler(sys.stderr))
        else:
            # Human-readable trace output
            trace_handler = create_trace_handler(detailed=trace_detailed)
            handlers.append(TimeDeltaHandler(trace_handler))
    
    # Add metrics handler
    if enable_metrics:
        handlers.append(create_metrics_handler())
    
    # Configure sampling and filtering
    return ObservabilityConfig(
        handlers=handlers,
        sampling_rate=1.0,  # Full sampling for development
        enabled_categories={'lex', 'parse', 'ast', 'nsl'}
    )