"""Lightweight state transition manager for the mission environment."""

from typing import Dict, Any, Optional


class StateManager:
    """Handles state transitions based on conditions defined in state config."""
    
    def __init__(self, state_config: dict):
        self.state_config = state_config
    
    def get_next_state(self, current_state: str, context: Dict[str, Any]) -> str:
        """
        Determine the next state based on current state and context.
        
        Args:
            current_state: The current state name
            context: Dictionary containing observations and internal state for evaluation
            
        Returns:
            The name of the next state
        """
        state_config = self.state_config['states'].get(current_state)
        if not state_config:
            return 'end'
        
        # If no state_transitions defined, use default next_state
        if 'state_transitions' not in state_config:
            return state_config.get('next_state', 'end')
        
        transitions = state_config['state_transitions']
        
        # Evaluate conditions in order
        for transition in transitions.get('conditions', []):
            condition = transition.get('condition', '')
            
            # Handle 'else' as the default/fallback condition
            if condition == "else":
                return transition['next_state']
            
            # Evaluate the condition
            if self._evaluate_condition(condition, context):
                return transition['next_state']
        
        # If no condition matched, use default next_state
        return state_config.get('next_state', 'end')
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluate a condition string with context variables.
        
        Args:
            condition: Condition string to evaluate (e.g., "{next_goal} == 'ground'")
            context: Dictionary of variables to substitute into the condition
            
        Returns:
            Boolean result of the condition evaluation
        """
        try:
            # Format the condition with context values
            format_dict = {}
            for key, value in context.items():
                if isinstance(value, str):
                    format_dict[key] = repr(value)  # Add quotes around strings
                elif isinstance(value, list):
                    format_dict[key] = repr(value)  # Properly format lists
                else:
                    format_dict[key] = value
            
            formatted_condition = condition.format(**format_dict)
            
            # Evaluate with restricted builtins for safety
            result = eval(formatted_condition, {"__builtins__": {}}, {})
            return bool(result)
        except (KeyError, ValueError, SyntaxError, NameError) as e:
            # If evaluation fails, return False to skip this condition
            return False
