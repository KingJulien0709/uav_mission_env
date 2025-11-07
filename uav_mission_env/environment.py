
from __future__ import annotations
import numpy as np
import yaml
import os
from pathlib import Path
from typing import Any, Dict, Optional
from .tools import Tool, Observation, Verifier, ToolManager, ToolValidator
from .missions.mission_manager import MissionManager
from .state_manager import StateManager


class MissionEnvironment():
    # Default configuration paths
    DEFAULT_DATA_CONFIG = {
        "random_seed": 42,
        "dataset_metadata_path": "uav_mission_env/data/synthetic_dataset/metadata.json",
    }
    DEFAULT_STATE_CONFIG_PATH = "uav_mission_env/configs/minimal_viable_states.yaml"
    
    def __init__(self, data_config: Optional[dict] = None, state_config: Optional[dict] = None, max_turns: int = 10):
        self.max_turns = max_turns
        
        # Load default configurations if not provided
        if data_config is None:
            data_config = self._load_default_data_config()
        
        if state_config is None:
            state_config = self._load_default_state_config()
        
        self.state_config = state_config
        self.current_state = state_config.get('initial_state', 'execution')
        self.mission_manager = MissionManager(
            dataset_metadata_path=data_config.get("dataset_metadata_path", ""),
            random_generator=np.random.RandomState(data_config.get("random_seed", 42))
        )
        self.state: dict = {}
        self.turns_performed = 0
        
        # Initialize tool manager and validator
        self.tool_manager = ToolManager()
        self.tool_validator = ToolValidator(self.tool_manager, self.state_config)
        
        # Initialize state manager for transitions
        self.state_manager = StateManager(self.state_config)
        
        self._setup_tools()
        self._setup_observations_tools()
        self._setup_verifiers()

    @classmethod
    def _load_default_data_config(cls) -> dict:
        """Load default data configuration."""
        config = cls.DEFAULT_DATA_CONFIG.copy()
        
        # Try to resolve the dataset path relative to the package location
        package_dir = Path(__file__).parent
        dataset_path = package_dir / "data" / "synthetic_dataset" / "metadata.json"
        dataset_path = dataset_path.resolve()
        
        if dataset_path.exists():
            config["dataset_metadata_path"] = str(dataset_path)
        
        return config
    
    @classmethod
    def _load_default_state_config(cls) -> dict:
        """Load default state configuration from YAML file."""
        package_dir = Path(__file__).parent
        config_path = package_dir / "configs" / "minimal_viable_states.yaml"
        config_path = config_path.resolve()
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Default state config not found at {config_path}. "
                f"Please provide a state_config parameter."
            )
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_tools(self) -> None:
        """Initialize tools with necessary dependencies."""
        # Collect unique tool names from all states
        tool_names = set()
        for state in self.state_config['states'].values():
            tool_names.update(state.get('tools', []))
        
        # Create tool instances
        self.tools = {}
        for name in tool_names:
            tool = Tool.get_tool_by_name(name, mission_manager=self.mission_manager, state_config=self.state_config)
            tool.specification = self.tool_manager.get_spec(name)
            self.tools[name] = tool

    def _setup_observations_tools(self) -> None:
        """Initialize observations with necessary dependencies."""
        observation_list = ["waypoint"]
        for state in self.state_config['states'].values():
            for observation_name in state.get('observations', []):
                if observation_name not in observation_list:
                    observation_list.append(observation_name)
        self.observations_tools = {}
        for observation_name in set(observation_list):
            self.observations_tools[observation_name] = Observation.get_observation_by_name(observation_name, mission_manager=self.mission_manager)

    def _setup_verifiers(self) -> None:
        """Initialize verifiers with necessary dependencies."""
        verifier_configs = {}
        for state in self.state_config['states'].values():
            for verifier_item in state.get('verifiers', []):
                # Handle both string and dict formats
                if isinstance(verifier_item, str):
                    verifier_name = verifier_item
                    reward_factor = 1.0
                elif isinstance(verifier_item, dict):
                    verifier_name = list(verifier_item.keys())[0]
                    reward_factor = verifier_item[verifier_name].get('reward_factor', 1.0)
                else:
                    continue
                if verifier_name not in verifier_configs:
                    verifier_configs[verifier_name] = reward_factor
        self.verifiers = {}
        #for verifier_name, reward_factor in verifier_configs.items():
        #    self.verifiers[verifier_name] = Verifier.get_verifier_by_name(verifier_name, reward_factor=reward_factor)

    def reset(self, *, seed: Optional[int] = None) -> dict:
        self.state.clear()
        if seed is not None:
            self.state["seed"] = seed
        self.mission_manager.reset(seed=seed)
        self.turns_performed = 0
        self.current_state = self.state_config.get('initial_state', 'execution')
        return self._get_observation()
    

    def step(self, action: dict = {}) -> dict:

        action_outputs = self._act_tools(action)
        self._update_state(action_outputs)
        
        # Perform state transition
        transition_context = {**self._get_observation(), **self.state}
        self.current_state = self.state_manager.get_next_state(self.current_state, transition_context)
        
        # Get observation for the new state
        observation = self._get_observation()

        reward = 0.0  # Placeholder reward 
        
        terminated = self.current_state == 'end'  # Check if we've reached the end state
        truncated = False  # Placeholder truncation condition
        info = action_outputs  # Include tool outputs in info

        self.turns_performed += 1
        if self.turns_performed >= self.max_turns:  # Example max turns
            truncated = True
        info['turns_performed'] = self.turns_performed
        info['current_state'] = self.current_state
        
        return observation, reward, terminated, truncated, info

    def close(self) -> None:
        """Clean up the environment when done."""
        pass

    def get_available_tools(self, state: Optional[str] = None) -> list[dict]:
        """Get tool specifications for available tools in a state."""
        state = state or self.current_state
        tool_names = self.tool_validator.get_available_tools(state)
        return self.tool_manager.get_specs(tool_names)

    def format_tools_for_llm(self, state: Optional[str] = None) -> list[dict]:
        """Format tools for LLM API (Claude/OpenAI format)."""
        return self.get_available_tools(state)

    def _verify_observations(self) -> float:
        return 0.0

    def _get_observation(self) -> dict:
        observation_output = {}

        inner_observations = {}
        # Return empty observation if in 'end' state
        if self.current_state == 'end':
            observation_output['current_state'] = self.current_state
            return observation_output

        for observation_name in self.state_config['states'][self.current_state].get('observations', []):
            observation_tool = self.observations_tools[observation_name]
            obs = observation_tool.execute(self.state)
            inner_observations.update(obs)
        
        #print(inner_observations)
        #print("-"*40)
        # Always include waypoint obs_payload(media and prompt)
        waypoint_obs = self.observations_tools["waypoint"].execute(self.state)
        observation_output.update(waypoint_obs)
        #print(observation_output)
        #print("-"*40)

        available_tool_names = self.tool_validator.get_available_tools(self.current_state)
        available_tools = self.tool_manager.get_specs(available_tool_names)
        observation_output['available_tools'] = available_tools

        state_prompt = self.state_config['states'][self.current_state].get('prompt', '')
        input_vars = self.state_config['states'][self.current_state]['observations']
        #print(input_vars)
        observation_output['obs_payload']['prompt'] = state_prompt.format(**{var: inner_observations[var] for var in input_vars})
        return observation_output
    
    def _act_tools(self, action: dict) -> dict:
        """Execute tools based on action, with validation."""
        outputs = {}
        errors = []
        
        for tool_name, tool_args in action.items():
            # Validate that each tool action has correct arguments
            error = self.tool_validator.validate(tool_name, {tool_name: tool_args}, self.current_state)
            if error:
                errors.append(f"{tool_name}: {error}")
                continue
            # Execute the tool
            if tool_name in self.tools:
                try:
                    outputs.update(self.tools[tool_name].use(action))
                except Exception as e:
                    errors.append(f"{tool_name}: {str(e)}")
        if errors:
            outputs['errors'] = errors
        return outputs
    
    def _update_state(self, tool_outputs: dict) -> None:
        """Update the internal state of the environment based on tool outputs."""
        for key, value in tool_outputs.items():
            self.state[key] = value