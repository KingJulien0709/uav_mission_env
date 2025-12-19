# UAV Mission Environment

A Python package for UAV mission environments.

## Installation

### From Source

To install the package in development mode:

```bash
pip install -e .
```

To install the package:

```bash
pip install .
```

### From PyPI (when published)

```bash
pip install uav_mission_env
```

## Usage

### Quick Start with Default Configuration

The simplest way to get started is to use the default configuration:

```python
from uav_mission_env import MissionEnvironment

# Create environment with default configuration
env = MissionEnvironment()

# Reset and step
obs = env.reset(seed=42)
action = {
    "tool_name": "next_goal",
    "parameters": {"next_goal": "waypoint_1"}
}
obs, reward, terminated, truncated, info = env.step(action)

env.close()
```

The default configuration uses:
- **State config**: `uav_mission_env/configs/minimal_viable_states.yaml`
- **Dataset**: `uav_mission_env/data/synthetic_dataset/metadata.json`
- **Random seed**: 42

### Custom Configuration (Bring Your Own Data)

The environment is designed to be highly configurable. You can provide a single configuration dictionary to customize states, tasks, and datasets.

```python
from uav_mission_env import MissionEnvironment

# 1. Sampling missions from a custom dataset (BYOD)
config = {
    "state_config": { ... }, # Optional: custom state/tool definitions
    "data_config": {
        "dataset_metadata_path": "path/to/your/external/dataset/metadata.json",
        "random_seed": 123
    }
}
env = MissionEnvironment(config=config)

# 2. Using a specific presampled mission
config = {
    "mission_config": {
        "instruction": "Find the red box at waypoint_2",
        "waypoints": [
            {
                "id": "waypoint_1", 
                "gt_entities": {}, 
                "is_target": False, 
                "media": []
            },
            {
                "id": "waypoint_2", 
                "gt_entities": {
                  "color": "red",
                }, 
                "is_target": True, 
                "media": ["path/to/image.jpg"]
            }
        ]
    }
}
env = MissionEnvironment(config=config)

# Reset and step
obs = env.reset(seed=42)
action = {
    "tool_name": "next_goal",
    "parameters": {"next_goal": "waypoint_2"}
}
obs, reward, terminated, truncated, info = env.step(action)
```

### Configuration Structure

The `config` dictionary supports the following keys:
- `state_config`: (dict) Defines the states, available tools for each state, and transition logic.
- `data_config`: (dict) Configuration for sampling missions on the go.
    - `dataset_metadata_path`: Path to the JSON metadata file for your dataset.
    - `random_seed`: Seed for reproducibility.
- `mission_config`: (dict) A complete mission definition. If provided, the environment will use this specific mission instead of sampling.
    - `instruction`: (str) The mission goal/instruction.
    - `waypoints`: (list) List of waypoint dictionaries:
        - `id`: (str) Unique identifier (e.g., "waypoint_1").
        - `gt_entities`: (dict) Ground truth entities at this location.
        - `is_target`: (bool) Whether this is the target location.
        - `media`: (list) List of paths to images/videos for this location.
- `task_config_path`: (str) Path to a custom tasks YAML file.
- `mission_config_path`: (str) Path to a YAML file containing a presampled mission.

### State Transitions

The environment handles state transitions automatically based on conditions defined in your state configuration YAML file. After each step, the `StateManager` evaluates transition conditions using the current observations and internal state, then transitions to the appropriate next state.

**Example state configuration:**
```yaml
initial_state: execution

states:
  execution:
    prompt: "Your task instructions here..."
    observations: [current_location, plan, locations_to_be_visited]
    tools: [next_goal]
    state_transitions:
      conditions:
        - condition: "{next_goal} == 'ground'"
          next_state: end
        - condition: "{locations_to_be_visited} == []"
          next_state: end
        - condition: "else"
          next_state: execution
```

**How it works:**
1. Execute actions using available tools
2. Update internal state with tool outputs
3. Evaluate transition conditions (checked in order)
4. Transition to the next state based on first matching condition
5. Return observation for the new state
6. Set `terminated=True` when reaching the 'end' state

**Accessing state information:**
```python
obs = env.reset()
print(f"Current state: {obs['current_state']}")  # 'execution'

obs, reward, terminated, truncated, info = env.step(action)
print(f"New state: {obs['current_state']}")
print(f"Done: {terminated}")  # True if state is 'end'
```

## License

MIT