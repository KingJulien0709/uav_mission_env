from __future__ import annotations
import numpy as np
import yaml
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..missions.mission_manager import MissionManager
from ..missions.task import TaskRegistry
from ..missions.mission_generator import MissionGenerator, ConfigMissionGenerator, PresampledMissionGenerator, RandomMissionGenerator
from ..missions.mission import Mission
from ..missions.waypoint import Waypoint

class ConfigLoader:
    # Default configuration paths
    DEFAULT_DATA_CONFIG = {
        "random_seed": 42,
        "dataset_metadata_path": "uav_mission_env/data/synthetic_dataset/metadata.json",
    }
    DEFAULT_STATE_CONFIG_PATH = "uav_mission_env/configs/minimal_viable_states.yaml"
    DEFAULT_TASK_CONFIG_PATH = "uav_mission_env/configs/tasks.yaml"

    @classmethod
    def load_config(cls, config: Optional[dict] = None) -> Tuple[dict, TaskRegistry, MissionManager]:
        if config is None:
            config = {}
        
        # 1. Resolve State Config
        if "state_config" in config:
            final_state_config = config["state_config"]
        else:
            final_state_config = cls._load_default_state_config()
            
        # 2. Resolve Task Config
        task_config_path = config.get("task_config_path")
        if task_config_path is None:
            task_config_path = cls._load_default_task_config_path()
        task_registry = TaskRegistry(task_config_path)

        # 3. Resolve Mission Generator and Data Config
        final_data_config = config.get("data_config", {})
        mission_generator = None
        
        if "mission_config" in config:
            # Presampled mission from config dict
            mission_data = config["mission_config"]
            mission = cls._create_mission_from_dict(mission_data)
            mission_generator = PresampledMissionGenerator(mission)
            
        elif "mission_config_path" in config:
            # Presampled mission from file
            mission_config_path = config["mission_config_path"]
            resolved_path = cls._resolve_mission_config_path(mission_config_path)
            mission_generator = ConfigMissionGenerator(resolved_path)
            
        else:
            # Sampling missions on the go OR mission_config_path in data_config
            # Check if mission_config_path is in data_config
            mission_config_path = final_data_config.get("mission_config_path")
            
            if mission_config_path:
                    resolved_path = cls._resolve_mission_config_path(mission_config_path)
                    mission_generator = ConfigMissionGenerator(resolved_path)
            else:
                # Ensure dataset_metadata_path is present if we are sampling
                if "dataset_metadata_path" not in final_data_config:
                        default_data = cls._load_default_data_config()
                        if "dataset_metadata_path" in default_data:
                            final_data_config.setdefault("dataset_metadata_path", default_data["dataset_metadata_path"])
                
                mission_generator = RandomMissionGenerator(
                    dataset_metadata_path=final_data_config.get("dataset_metadata_path", ""),
                    task_registry=task_registry,
                    random_generator=np.random.RandomState(final_data_config.get("random_seed", 42))
                )

        mission_manager = MissionManager(
            dataset_metadata_path=final_data_config.get("dataset_metadata_path", ""),
            random_generator=np.random.RandomState(final_data_config.get("random_seed", 42)),
            task_registry=task_registry,
            mission_generator=mission_generator
        )
        
        return final_state_config, task_registry, mission_manager

    @classmethod
    def _create_mission_from_dict(cls, mission_data: dict) -> Mission:
        waypoints = []
        target_waypoint = None
        
        for wp_data in mission_data.get("waypoints", []):
            wp = Waypoint(
                waypoint_id=wp_data["id"],
                gt_entities=wp_data.get("gt_entities", {}),
                is_target=wp_data.get("is_target", False),
                media=wp_data.get("media", [])
            )
            waypoints.append(wp)
            if wp.is_target:
                target_waypoint = wp
                
        return Mission(
            instruction=mission_data.get("instruction", ""),
            waypoints=waypoints,
            target_waypoint=target_waypoint
        )

    @classmethod
    def _load_default_data_config(cls) -> dict:
        """Load default data configuration."""
        config = cls.DEFAULT_DATA_CONFIG.copy()
        
        # Try to resolve the dataset path relative to the package location
        # Now in utils/, so package_dir is parent
        package_dir = Path(__file__).parent.parent
        dataset_path = package_dir / "data" / "synthetic_dataset" / "metadata.json"
        dataset_path = dataset_path.resolve()
        
        if dataset_path.exists():
            config["dataset_metadata_path"] = str(dataset_path)
        
        return config
    
    @classmethod
    def _load_default_state_config(cls) -> dict:
        """Load default state configuration from YAML file."""
        package_dir = Path(__file__).parent.parent
        config_path = package_dir / "configs" / "minimal_viable_states.yaml"
        config_path = config_path.resolve()
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Default state config not found at {config_path}. "
                f"Please provide a state_config parameter."
            )
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    @classmethod
    def _load_default_task_config_path(cls) -> str:
        """Load default task configuration path."""
        package_dir = Path(__file__).parent.parent
        config_path = package_dir / "configs" / "tasks.yaml"
        config_path = config_path.resolve()
        
        if not config_path.exists():
            # It's okay if it doesn't exist, we just won't have tasks
            pass
        
        return str(config_path)

    @classmethod
    def _resolve_mission_config_path(cls, config_path: str) -> str:
        """Resolve mission config path, checking default location if file not found."""
        path_obj = Path(config_path)
        if path_obj.exists():
            return str(path_obj.resolve())
            
        # Check in default configs directory
        package_dir = Path(__file__).parent.parent
        default_path = package_dir / "configs" / config_path
        if default_path.exists():
            return str(default_path.resolve())
            
        # Return original path to let ConfigMissionGenerator handle the error (or raise here)
        return config_path
