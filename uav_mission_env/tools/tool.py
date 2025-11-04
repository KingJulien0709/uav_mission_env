

class Tool:
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
        tool_classes = {
            "next_goal": NextGoalTool,
            "reasoning": ReasoningTool,
            "information": InformationTool,
        }
        tool_class = tool_classes.get(tool_name)
        if tool_class is None:
            raise ValueError(f"Tool '{tool_name}' not found.")
        # Instantiate with dependencies (simplified - always enable logging for now)
        logging_enabled = True
        return tool_class(logging_enabled=logging_enabled, mission_manager=mission_manager)


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


class ReasoningTool(Tool):
    def __init__(self, logging_enabled: bool = False, mission_manager=None):
        super().__init__(name="reasoning", logging_enabled=logging_enabled, mission_manager=mission_manager)
    
class InformationTool(Tool):
    def __init__(self, logging_enabled: bool = False, mission_manager=None):
        super().__init__(name="information", logging_enabled=logging_enabled, mission_manager=mission_manager)

    