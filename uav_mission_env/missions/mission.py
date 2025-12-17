from dataclasses import dataclass
from typing import List, Optional
from .waypoint import Waypoint

@dataclass
class Mission:
    instruction: str
    waypoints: List[Waypoint]
    target_waypoint: Waypoint
    id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Mission':
        waypoints = []
        target_waypoint = None
        
        for wp_data in data.get('waypoints', []):
            wp = Waypoint(
                waypoint_id=wp_data['waypoint_id'],
                gt_entities=wp_data.get('gt_entities', {}),
                is_target=wp_data.get('is_target', False),
                media=wp_data.get('media', {})
            )
            waypoints.append(wp)
            if wp.is_target:
                target_waypoint = wp
                
        return cls(
            instruction=data['instruction'],
            waypoints=waypoints,
            target_waypoint=target_waypoint,
            id=data.get('id')
        )
