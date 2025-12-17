from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import yaml
import os

@dataclass
class TaskConfig:
    name: str
    description: str
    template: str
    required_keys: List[str]

class Task:
    def __init__(self, config: TaskConfig, target_attributes: Dict[str, Any]):
        self.config = config
        self.target_attributes = target_attributes
        self.instruction = self._generate_instruction()

    def _generate_instruction(self) -> str:
        try:
            return self.config.template.format(**self.target_attributes)
        except KeyError as e:
            return f"Error generating instruction: missing key {e}"

    def __repr__(self):
        return f"Task(name={self.config.name}, instruction='{self.instruction}')"

class TaskRegistry:
    def __init__(self, config_path: str):
        self.tasks: Dict[str, TaskConfig] = self._load_tasks(config_path)

    def _load_tasks(self, config_path: str) -> Dict[str, TaskConfig]:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Task config file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        tasks = {}
        for name, info in data.get('tasks', {}).items():
            tasks[name] = TaskConfig(
                name=name,
                description=info.get('description', ''),
                template=info.get('template', ''),
                required_keys=info.get('required_keys', [])
            )
        return tasks

    def get_task_config(self, task_name: str) -> Optional[TaskConfig]:
        return self.tasks.get(task_name)

    def list_tasks(self) -> List[str]:
        return list(self.tasks.keys())
