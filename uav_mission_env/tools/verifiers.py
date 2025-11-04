class Verifier:
    def __init__(self, name: str, reward_factor: float = 1.0):
        self.name = name
        self.reward_factor = reward_factor

    def verify(self, data: str) -> bool:
        # Placeholder for calculateing reward
        calculate_reward = 0.0
        return calculate_reward * self.reward_factor
        
    @classmethod
    def get_verifier_by_name(cls, name: str, reward_factor: float = 1.0):
        verifiers = {
            "formatted_verifier": FormattedVerifier,
            "content_verifier": ContentVerifier,
        }
        verifier_class = verifiers.get(name)
        if verifier_class is None:
            raise ValueError(f"Verifier '{name}' not found.")
        return verifier_class(name=name, reward_factor=reward_factor)
    
class FormattedVerifier(Verifier):
    def __init__(self, name: str, reward_factor: float = 1.0):
        super().__init__(name, reward_factor)

    def verify(self, data: str) -> bool:
        # Placeholder for formatted verification logic
        is_formatted_correctly = True
        return (1.0 if is_formatted_correctly else 0.0) * self.reward_factor
    
class ContentVerifier(Verifier):
    def __init__(self, name: str, reward_factor: float = 1.0):
        super().__init__(name, reward_factor)

    def verify(self, data: str) -> bool:
        # Placeholder for content verification logic
        is_content_valid = True
        return (1.0 if is_content_valid else 0.0) * self.reward_factor

