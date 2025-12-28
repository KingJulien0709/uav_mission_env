from uav_mission_env.missions.mission_manager import MissionManager


class Verifier:
    def __init__(self, name: str, reward_factor: float = 1.0):
        self.name = name
        self.reward_factor = reward_factor

    def verify(self, data: str, mission_manager: MissionManager) -> float:
        # Placeholder for calculateing reward
        calculate_reward = 0.0
        return calculate_reward * self.reward_factor
        
    @classmethod
    def get_verifier_by_name(cls, name: str, reward_factor: float = 1.0):
        verifiers = {
            "formatted_verifier": FormattedVerifier,
            "conclusion_verifier": ConclusionVerifier,
        }
        verifier_class = verifiers.get(name)
        if verifier_class is None:
            raise ValueError(f"Verifier '{name}' not found.")
        return verifier_class(reward_factor=reward_factor)
    
class FormattedVerifier(Verifier):
    def __init__(self, reward_factor: float = 1.0):
        super().__init__(name="formatted_verifier", reward_factor=reward_factor)

    def verify(self, data: str, mission_manager: MissionManager) -> float:
        # the formatted verifier is done on agent side
        return 0.0
    
class ConclusionVerifier(Verifier):
    def __init__(self, reward_factor: float = 1.0):
        super().__init__(name="conclusion_verifier", reward_factor=reward_factor)

    def verify(self, data: str, mission_manager: MissionManager) -> float:
        reward = 0.0
        gt_waypoint_id = mission_manager.target_waypoint
        gt_plan_solvable = True #TODO add none solveable missions to dataset later and update this
        success_pred = data.get("mission_completed_successfully", False)
        if gt_plan_solvable and success_pred:
            reward += 1.0 # Mission was solvable and predicted as such
        predicted_waypoint_id = data.get("target_waypoint_id", None)
        if predicted_waypoint_id == gt_waypoint_id:
            reward += 1.0 # Predicted waypoint matches ground truth
        return reward * self.reward_factor

