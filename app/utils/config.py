import json
import logging
from typing import Dict, List
from ..models.task import Task

CONFIG_FILE = "commands.json"

class ConfigManager:
    def __init__(self):
        self.tasks: List[Task] = []
        self.groups: Dict[str, List[Task]] = {}

    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            config = {
                'tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'path': task.path,
                        'cmd': task.cmd
                    } for task in self.tasks
                ],
                'groups': {
                    name: [
                        {
                            'id': task.id,
                            'title': task.title,
                            'path': task.path,
                            'cmd': task.cmd
                        } for task in tasks
                    ] for name, tasks in self.groups.items()
                }
            }
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
                
            logging.info("Configuration saved successfully")
            
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")

    def load_config(self) -> None:
        """Load configuration from file"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                
            self.tasks = [
                Task(**task_data)
                for task_data in config.get('tasks', [])
            ]
            
            self.groups = {
                name: [Task(**task_data) for task_data in tasks]
                for name, tasks in config.get('groups', {}).items()
            }
            
            logging.info("Configuration loaded successfully")
            
        except FileNotFoundError:
            logging.info("No configuration file found, starting with empty state")
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            # Start with empty state on error
            self.tasks = []
            self.groups = {}
