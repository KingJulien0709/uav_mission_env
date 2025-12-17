from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import yaml
import os
import numpy as np
from .mission import Mission
from .waypoint import Waypoint
from .task import TaskRegistry, Task

class MissionGenerator(ABC):
    @abstractmethod
    def generate_mission(self) -> Mission:
        pass

class RandomMissionGenerator(MissionGenerator):
    def __init__(self, dataset_metadata_path: str, task_registry: Optional[TaskRegistry] = None, random_generator: np.random = np.random.RandomState()):
        self.dataset_metadata_path = dataset_metadata_path
        self.task_registry = task_registry
        self.random_generator = random_generator

    def _sample_from_metadata(self, num_samples: int):
        with open(self.dataset_metadata_path, 'r') as f:
            metadata = json.load(f)
        sampled_missions = self.random_generator.choice(metadata, size=num_samples, replace=False)
        return sampled_missions

    def generate_mission(self, num_samples: int = 5, custom_plan: str = None, target_criteria: dict = None) -> Mission:
        sampled_missions = self._sample_from_metadata(num_samples)
        
        target_index = -1
        if target_criteria:
            # Find index matching criteria
            for i, mission in enumerate(sampled_missions):
                match = True
                for k, v in target_criteria.items():
                    if mission.get("gt_entities", {}).get(k) != v:
                        match = False
                        break
                if match:
                    target_index = i
                    break
        
        if target_index == -1:
            # Randomly select which waypoint will be the target
            target_index = self.random_generator.randint(0, num_samples)

        mission_instruction = ""
        waypoints = []
        target_waypoint = None

        for i, mission_data in enumerate(sampled_missions):
            is_target = (i == target_index)
            waypoint = Waypoint(
                waypoint_id=f"waypoint_{i}",
                gt_entities=mission_data.get("gt_entities", {}),
                is_target=is_target,
                media=mission_data.get("media", [])
            )
            waypoints.append(waypoint)
            
            if is_target:
                target_waypoint = waypoint
                if custom_plan:
                    mission_instruction = custom_plan
                else:
                    # Select a random task
                    task_names = self.task_registry.list_tasks() if self.task_registry else []
                    if not task_names:
                        # Fallback if no tasks configured
                        mission_instruction = f"Find the box with number {mission_data['gt_entities'].get('number', 'unknown')}."
                    else:
                        task_name = self.random_generator.choice(task_names)
                        task_config = self.task_registry.get_task_config(task_name)
                        task = Task(task_config, mission_data.get("gt_entities", {}))
                        mission_instruction = task.instruction

        return Mission(
            instruction=mission_instruction,
            waypoints=waypoints,
            target_waypoint=target_waypoint
        )

class PresampledMissionGenerator(MissionGenerator):
    def __init__(self, mission: Mission):
        self.mission = mission

    def generate_mission(self) -> Mission:
        return self.mission

class ConfigMissionGenerator(MissionGenerator):
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.mission = self._load_mission()

    def _load_mission(self) -> Mission:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Mission config file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)
            
        return Mission.from_dict(data)

    def generate_mission(self) -> Mission:
        return self.mission
