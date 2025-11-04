"""Tool Validator - Validates tool actions against specifications."""

from __future__ import annotations
from typing import Optional


class ToolValidator:
    """Validates tool actions against state config and specifications."""
    
    def __init__(self, tool_manager, state_config: dict):
        self.tool_manager = tool_manager
        self.state_config = state_config
    
    def validate(self, tool_name: str, tool_args: dict, state: str) -> Optional[str]:
        """ Validate a tool action. Returns error message or None if valid. """
        
        # Check if tool exists
        spec = self.tool_manager.get_spec(tool_name)
        if not spec:
            return f"Tool '{tool_name}' not found"
        
        # Check if available in current state
        available = self.get_available_tools(state)
        if tool_name not in available:
            return f"Tool '{tool_name}' not available in state '{state}'"
        
        # Check required parameters
        required = spec.get('input_schema', {}).get('required', [])
        for param in required:
            if param not in tool_args:
                return f"Missing required parameter '{param}'"
        
        return None
    
    def get_available_tools(self, state: str) -> list[str]:
        """Get tool names available for a state."""
        return self.state_config['states'][state].get('tools', [])
