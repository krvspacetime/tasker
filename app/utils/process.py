import subprocess
import logging
from typing import Dict, Optional
from ..models.task import Task


class ProcessManager:
    def __init__(self):
        self.running_tasks: Dict[str, subprocess.Popen] = {}

    def start_task(self, task: Task) -> bool:
        """Start a task and return True if successful"""
        try:
            if task.id in self.running_tasks:
                # Check if the process is actually still running
                if self.check_task_status(task.id) is not None:
                    # Process has finished, clean it up
                    self.cleanup_task(task.id)
                else:
                    # Process is still running
                    logging.info(f"Task {task.title} is already running")
                    return False

            # Use subprocess to launch the command in a new window
            full_cmd = f'cmd /k "cd /d "{task.path}" && {task.cmd}"'
            logging.info(f"Executing: {full_cmd}")

            process = subprocess.Popen(
                full_cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                # text=True,
            )

            self.running_tasks[task.id] = process
            return True

        except Exception as e:
            logging.error(f"Error running {task.title}: {str(e)}")
            return False

    def check_task_status(self, task_id: str) -> Optional[int]:
        """Check if a task is still running. Returns None if running, or return code if finished"""
        if task_id not in self.running_tasks:
            return -1  # Task not found

        process = self.running_tasks[task_id]
        return process.poll()

    def cleanup_task(self, task_id: str) -> None:
        """Remove a task from running tasks"""
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
            logging.info(f"Cleaned up task {task_id}")

    def stop_task(self, task_id: str) -> None:
        """Stop a running task"""
        if task_id in self.running_tasks:
            process = self.running_tasks[task_id]
            try:
                process.terminate()
            except Exception as e:
                logging.error(f"Error terminating process: {str(e)}")
            finally:
                self.cleanup_task(task_id)

    def get_task_output(self, task_id: str) -> str:
        """Get the output of a finished task"""
        if task_id not in self.finished_tasks:
            return None
        task = self.finished_tasks[task_id]
        return {
            "return_code": task.returncode,
            "stdout": task.stdout,
            "stderr": task.stderr,
        }
