import numpy as np
import json
from .waypoint import Waypoint, WaypointManager

class MissionManager:
    def  __init__(self, dataset_metadata_path: str, random_generator: np.random = np.random.RandomState()):
        self.dataset_metadata_path = dataset_metadata_path
        self.random_generator = random_generator
        self.waypoint_manager = WaypointManager()
        
        self.current_mission, self.waypoints = self._sample_mission(num_samples=5)
        self.available_waypoints = self.waypoints.copy()
        self.current_waypoint_id: str = "None"
        self.visited_waypoints = []

    def _sample_from_metadata(self, num_samples: int):
        with open(self.dataset_metadata_path, 'r') as f:
            metadata = json.load(f)
        
        sampled_missions = self.random_generator.choice(metadata, size=num_samples, replace=False)
        return sampled_missions

    def _sample_mission(self, num_samples: int) -> str:
        sampled_missions = self._sample_from_metadata(num_samples)
        mission_instruction = ""
        for i, mission in enumerate(sampled_missions):
            media = {}
            # Handle both 'media' list and 'image_path' single image
            if "media" in mission:
                for j, m in enumerate(mission["media"]):
                    if m.endswith(('.png', '.jpg', '.jpeg')):
                        m_type = 'image'
                    elif m.endswith(('.mp4', '.avi', '.mov')):
                        m_type = 'video'
                    else:
                        m_type = 'unknown'
                    media[f'media_{j}'] = {
                        'type': m_type,
                        'path': m
                    }
            elif "image_path" in mission:
                media['media_0'] = {
                    'type': 'image',
                    'path': mission["image_path"]
                }

            waypoint = Waypoint(
                waypoint_id=f"waypoint_{i}",
                payload=mission.get("payload", {}),
                is_target=i == 0,  # First sampled mission is the target
                media=media
            )
            self.waypoint_manager.add_waypoint(waypoint)
            if i == 0:
                mission_instruction = f"Find the box with number {mission['payload']['number']}."

        return mission_instruction, self.waypoint_manager.get_random_waypoint_id_list()
    
    def visit_waypoint(self, waypoint_id: str):
        if waypoint_id in self.available_waypoints:
            self.available_waypoints.remove(waypoint_id)
            self.visited_waypoints.append(waypoint_id)
            self.current_waypoint_id = waypoint_id
        elif waypoint_id == "ground":
            self.current_waypoint_id = waypoint_id
        else:
            raise ValueError(f"Waypoint {waypoint_id} has already been visited or does not exist.")
        

    def reset(self, num_samples: int = 5, seed: int = None):
        if seed is not None:
            self.random_generator.seed(seed)
        self.waypoint_manager.reset(seed=seed)
        self.current_mission, self.waypoints = self._sample_mission(num_samples=num_samples)
        self.available_waypoints = self.waypoints.copy()
        self.visited_waypoints = []


        