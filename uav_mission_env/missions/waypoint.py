import numpy as np

class Waypoint:
    def __init__(
            self, waypoint_id: str, 
            gt_entities: dict = None,
            is_target: bool = False, 
            media: dict = None):
        self.waypoint_id = waypoint_id
        self.gt_entities = gt_entities if gt_entities is not None else {}  # dictionary containing information about the waypoint, for verifiable rewards
        self.is_target = is_target  # True if this waypoint is the target, False otherwise
        self.media = media if media is not None else {}  # dictionary containing media information related to the waypoint

    def to_dict(self) -> dict:
        return {
            "waypoint_id": self.waypoint_id,
            "gt_entities": self.gt_entities,
            "is_target": self.is_target,
            "media": self.media
        }
    
class GroundWaypoint(Waypoint):
    def __init__(self):
        super().__init__("ground", None, False, None)


class WaypointManager:
    def __init__(self, random_generator: np.random = None):
        self.waypoints = {}
        self.random_generator = random_generator if random_generator is not None else np.random.RandomState()

    def add_waypoint(self, waypoint: Waypoint):
        self.waypoints[waypoint.waypoint_id] = waypoint

    def get_waypoint(self, waypoint_id: str) -> Waypoint:
        if waypoint_id == "ground":
            return GroundWaypoint()
        return self.waypoints.get(waypoint_id)

    def remove_waypoint(self, waypoint_id: str):
        if waypoint_id in self.waypoints:
            del self.waypoints[waypoint_id]

    def get_random_waypoint_id_list(self):
        waypoint_ids = list(self.waypoints.keys())
        self.random_generator.shuffle(waypoint_ids)
        return waypoint_ids
    
    def reset(self, seed: int = None):
        if seed is not None:
            self.random_generator.seed(seed)
        waypoint_ids = list(self.waypoints.keys())
        self.random_generator.shuffle(waypoint_ids)
        return waypoint_ids
            

    
