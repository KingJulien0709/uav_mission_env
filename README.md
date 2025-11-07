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
action = {"next_goal": "waypoint_1"}
obs, reward, terminated, truncated, info = env.step(action)

env.close()
```

The default configuration uses:
- **State config**: `uav_mission_env/configs/minimal_viable_states.yaml`
- **Dataset**: `uav_mission_env/data/synthetic_dataset/metadata.json`
- **Random seed**: 42

### Custom Configuration

You can also provide custom configurations:

```python
from uav_mission_env import MissionEnvironment
import yaml

# Load state configuration
with open('path/to/your/config.yaml', 'r') as f:
    state_config = yaml.safe_load(f)

# Configure data
data_config = {
    "dataset_metadata_path": "path/to/metadata.json",
    "random_seed": 123
}

# Create environment with custom configuration
env = MissionEnvironment(
    data_config=data_config,
    state_config=state_config,
    max_turns=10
)

# Reset and step
obs = env.reset(seed=42)
action = {"next_goal": "waypoint_1"}
obs, reward, terminated, truncated, info = env.step(action)

env.close()
```

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