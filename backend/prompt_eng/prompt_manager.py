import os
import json

class PromptManager:
    def __init__(self, config_file=None):
        if config_file is None:
            # Get the directory of the current script (prompt_manager.py)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Construct the full path to prompts.json
            config_file = os.path.join(script_dir, "prompts.json")
        
        with open(config_file, "r") as file:
            self.config = json.load(file)

    def get_prompt(self, prompt_type):
        return self.config.get("prompt", {}).get(prompt_type, "Prompt not found.")

    def get_role(self, role_name):
        return self.config.get("role", {}).get(role_name, "Role not found.")
