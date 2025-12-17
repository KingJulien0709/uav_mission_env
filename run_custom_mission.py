import os
import sys
from pathlib import Path

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from uav_mission_env.environment import MissionEnvironment

def run_custom_mission():
    # 1. Define the configuration for the demo data
    package_dir = Path("uav_mission_env").resolve()
    demo_metadata_path = package_dir / "data" / "demo" / "metadata.json"
    
    data_config = {
        "random_seed": 42,
        "dataset_metadata_path": str(demo_metadata_path)
    }

    # 2. Initialize the environment
    print(f"Initializing environment with metadata: {demo_metadata_path}")
    env = MissionEnvironment(data_config=data_config)

    # 3. Reset the environment with the custom mission plan AND target criteria
    custom_question = "How many 'h' are in the streetname of house number 12?"
    target_criteria = {"number": 12}
    
    print(f"Setting custom mission: {custom_question}")
    print(f"Target criteria: {target_criteria}")
    
    observation = env.reset(custom_plan=custom_question, target_criteria=target_criteria)

    # 4. Verify the mission and target
    current_mission = env.mission_manager.current_mission
    target_waypoint = env.mission_manager.target_waypoint
    
    print(f"\nCurrent Mission: {current_mission}")
    print(f"Target Waypoint ID: {target_waypoint.waypoint_id}")
    print(f"Target Waypoint Entities: {target_waypoint.gt_entities}")
    
    if target_waypoint.gt_entities.get("number") == 12:
        print("\nSUCCESS: Target waypoint correctly identified based on criteria.")
    else:
        print("\nFAILURE: Target waypoint does not match criteria.")

if __name__ == "__main__":
    run_custom_mission()
