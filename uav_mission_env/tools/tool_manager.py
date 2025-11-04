"""Tool Manager - Loads and provides access to tool specifications."""

from __future__ import annotations
import yaml
from pathlib import Path
from typing import Optional


class ToolManager:
    """Manages tool specifications from all_tools.yaml."""
    
    def __init__(self, tools_config_path: Optional[Path] = None):
        if tools_config_path is None:
            tools_config_path = Path(__file__).parent.parent / "configs" / "all_tools.yaml"
        
        with open(tools_config_path, 'r') as f:
            all_tools = yaml.safe_load(f)
        
        self.registry = {tool['name']: tool for tool in all_tools.get('tools', [])}
    
    def get_spec(self, tool_name: str) -> Optional[dict]:
        """Get specification for a tool."""
        return self.registry.get(tool_name)
    
    def get_specs(self, tool_names: list[str]) -> list[dict]:
        """Get specifications for multiple tools."""
        return [self.registry[name] for name in tool_names if name in self.registry]
