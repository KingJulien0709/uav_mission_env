from ..utils import media_utils

class Tool:
    registry = {}

    def __init__(self, name: str, logging_enabled: bool = False, arguments: dict = None, mission_manager=None):
        self.name = name
        self.logging_enabled = logging_enabled
        self.arguments = arguments or {}
        self.mission_manager = mission_manager  # Inject dependency

    def log(self, action_args: dict = None):
        if not self.logging_enabled:
            return {}
        if action_args is None:
            information = {f"{self.name}": f"no {self.name} provided"}
        else:
            default_value = f"no {self.name} provided"
            information = {f"{self.name}": f"{action_args.get(self.name, default_value)}"}
        return information

    def use(self, action_args: dict = None):
        # here can be the specific tool logic
        return self.log(action_args)

    @classmethod
    def get_tool_by_name(cls, tool_name: str, mission_manager=None, state_config: dict = {}, current_state: str = None):
        """Factory method to create tools with dependencies injected."""
        tool_class = cls.registry.get(tool_name)
        if tool_class is None:
            raise ValueError(f"Tool '{tool_name}' not found.")
        # Instantiate with dependencies (simplified - always enable logging for now)
        logging_enabled = True
        return tool_class(logging_enabled=logging_enabled, mission_manager=mission_manager)

    @classmethod
    def list_available_tools(cls):
        return list(cls.registry.keys())


class NextGoalTool(Tool):
    def __init__(self, logging_enabled: bool = False, mission_manager=None):
        super().__init__(name="next_goal", logging_enabled=logging_enabled, mission_manager=mission_manager)

    def use(self, action_args: dict = None):
        if self.mission_manager is None:
            raise RuntimeError("NextGoalTool requires a mission_manager to be injected.")
        
        waypoint_id = action_args.get("next_goal", None)
        waypoint = self.mission_manager.visit_waypoint(waypoint_id)
        obs_dict = {
            "current_location": waypoint_id,
            "locations_to_be_visited": self.mission_manager.available_waypoints,
            "past_locations": self.mission_manager.visited_waypoints,
            "plan": self.mission_manager.current_mission,
            "waypoint": waypoint,
        }
        log_args = self.log(action_args)
        obs_dict.update(log_args)
        return obs_dict


class ReportFinalConclusionTool(Tool):
    def __init__(self, logging_enabled: bool = False, mission_manager=None):
        super().__init__(name="report_final_conclusion", logging_enabled=logging_enabled, mission_manager=mission_manager)

    def use(self, action_args: dict = None):
        # Placeholder for final conclusion logic
        log_args = self.log(action_args)
        return action_args or {}

class CropZoomImageTool(Tool):
    def __init__(self, logging_enabled: bool = False, mission_manager=None):
        super().__init__(name="crop_zoom_image", logging_enabled=logging_enabled, mission_manager=mission_manager)

    def use(self, action_args: dict = None):
        image_b64 = action_args.get("image")
        bbox = action_args.get("bbox")
        
        if not image_b64 or not bbox:
                return self.log(action_args)

        try:
            img = media_utils.base64_str_to_pil_image(image_b64)
            width, height = img.size
            
            x_min = int(bbox["x_min"] * width)
            y_min = int(bbox["y_min"] * height)
            x_max = int(bbox["x_max"] * width)
            y_max = int(bbox["y_max"] * height)
            
            cropped_img = img.crop((x_min, y_min, x_max, y_max))
            cropped_b64 = media_utils.pil_image_to_base64_str(cropped_img)
            
            result = {"cropped_image": cropped_b64}
            result.update(self.log(action_args))
            return result
        except Exception as e:
            return {"error": str(e), **self.log(action_args)}

class NavigateToNewLandingZoneTool(Tool):
    def __init__(self, logging_enabled: bool = False, mission_manager=None):
        super().__init__(name="navigate_to_new_landing_zone", logging_enabled=logging_enabled, mission_manager=mission_manager)

    def use(self, action_args: dict = None):
        return self.log(action_args)

class ActivateLandingProcessTool(Tool):
    def __init__(self, logging_enabled: bool = False, mission_manager=None):
        super().__init__(name="activate_landing_process", logging_enabled=logging_enabled, mission_manager=mission_manager)

    def use(self, action_args: dict = None):
        return self.log(action_args)

class ActivateTrackingModeTool(Tool):
    def __init__(self, logging_enabled: bool = False, mission_manager=None):
        super().__init__(name="activate_tracking_mode", logging_enabled=logging_enabled, mission_manager=mission_manager)

    def use(self, action_args: dict = None):
        return self.log(action_args)


Tool.registry = {
    "next_goal": NextGoalTool,
    "report_final_conclusion": ReportFinalConclusionTool,
    "crop_zoom_image": CropZoomImageTool,
    "navigate_to_new_landing_zone": NavigateToNewLandingZoneTool,
    "activate_landing_process": ActivateLandingProcessTool,
    "activate_tracking_mode": ActivateTrackingModeTool,
}





