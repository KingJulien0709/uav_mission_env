import numpy as np
import json
import os
from typing import Optional
from .waypoint import Waypoint, WaypointManager
from .task import Task, TaskRegistry
from .mission_generator import MissionGenerator, RandomMissionGenerator

class MissionManager:
    def  __init__(self, dataset_metadata_path: str, random_generator: np.random = np.random.RandomState(), task_registry: TaskRegistry = None, mission_generator: Optional[MissionGenerator] = None):
        self.dataset_metadata_path = dataset_metadata_path
        self.random_generator = random_generator
        self.waypoint_manager = WaypointManager()
        self.task_registry = task_registry

        if mission_generator:
            self.mission_generator = mission_generator
        else:
            self.mission_generator = RandomMissionGenerator(
                dataset_metadata_path=dataset_metadata_path,
                task_registry=task_registry,
                random_generator=random_generator
            )

        self.reset()

    def visit_waypoint(self, waypoint_id: str):
        if waypoint_id in self.available_waypoints:
            self.available_waypoints.remove(waypoint_id)
            self.visited_waypoints.append(waypoint_id)
            self.current_waypoint_id = waypoint_id
        elif waypoint_id == "ground":
            self.current_waypoint_id = waypoint_id
        else:
            raise ValueError(f"Waypoint {waypoint_id} has already been visited or does not exist.")
        

    def reset(self, num_samples: int = 5, seed: int = None, custom_plan: str = None, target_criteria: dict = None):
        if seed is not None:
            self.random_generator.seed(seed)
        self.waypoint_manager.reset(seed=seed)
        
        # Generate mission using the generator
        if isinstance(self.mission_generator, RandomMissionGenerator):
             mission = self.mission_generator.generate_mission(num_samples=num_samples, custom_plan=custom_plan, target_criteria=target_criteria)
        else:
             mission = self.mission_generator.generate_mission()

        # Update internal state
        self.current_mission = mission.instruction
        self.target_waypoint = mission.target_waypoint
        
        # Add waypoints to manager
        for wp in mission.waypoints:
            self.waypoint_manager.add_waypoint(wp)
            
        self.waypoints = self.waypoint_manager.get_random_waypoint_id_list()
        self.available_waypoints = self.waypoints.copy()
        self.visited_waypoints = []
        self.current_waypoint_id = None


        