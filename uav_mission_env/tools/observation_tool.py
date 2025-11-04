from ..missions.mission_manager import MissionManager
from ..missions.waypoint import Waypoint

class Observation:
    def __init__(self, name: str, mission_manager: MissionManager = None):
        self.name = name
        self.mission_manager = mission_manager

    def execute(self, state: dict) -> str:
        return {f"{self.name}" :  f"{state.get(self.name, 'empty observation')}"}
    
    @classmethod
    def get_observation_by_name(cls, observation_name: str, mission_manager=None):
        observation_classes = {
            "current_location": CurrentLocationObservation,
            "plan": PlanObservation,
            "locations_to_be_visited": LocationsToBeVisitedObservation,
            "past_locations": PastLocationsObservation,
            "waypoint": CurrentWaypointObservation,
        }
        observation_class = observation_classes.get(observation_name)
        if observation_class is None:
            raise ValueError(f"Observation '{observation_name}' not found.")
        return observation_class(mission_manager=mission_manager)
    
class CurrentLocationObservation(Observation):
    def __init__(self, mission_manager: MissionManager = None):
        super().__init__(name="current_location", mission_manager=mission_manager)

    def execute(self, state: dict) -> str:
        location = self.mission_manager.current_waypoint_id if self.mission_manager else "unknown"
        return {self.name: location}
    
class PlanObservation(Observation):
    def __init__(self, mission_manager: MissionManager = None):
        super().__init__(name="plan", mission_manager=mission_manager)

    def execute(self, state: dict) -> str:
        plan = self.mission_manager.current_mission if self.mission_manager else "no plan available"
        return {self.name: plan}

class LocationsToBeVisitedObservation(Observation):
    def __init__(self, mission_manager: MissionManager = None):
        super().__init__(name="locations_to_be_visited", mission_manager=mission_manager)

    def execute(self, state: dict) -> str:
        locations = self.mission_manager.available_waypoints if self.mission_manager else []
        return {self.name: locations}

class PastLocationsObservation(Observation):
    def __init__(self, mission_manager: MissionManager = None):
        super().__init__(name="past_locations", mission_manager=mission_manager)

    def execute(self, state: dict) -> str:
        past_locations = self.mission_manager.visited_waypoints if self.mission_manager else []
        return {self.name: past_locations}
    
class CurrentWaypointObservation(Observation):
    def __init__(self, mission_manager: MissionManager = None):
        super().__init__(name="waypoint", mission_manager=mission_manager)

    def execute(self, state: dict):
        waypoint = self.mission_manager.waypoint_manager.get_waypoint(self.mission_manager.current_waypoint_id) if self.mission_manager else {}
        return {self.name: waypoint.to_dict() if waypoint else {}}
