import subprocess
import logging
import threading
import psutil  # New import for better process handling

from typing import Dict, Optional
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import pyqtSignal, QObject
from ansi2html import Ansi2HTMLConverter

from app.models.task import Task

conv = Ansi2HTMLConverter()


class ProcessManager(QObject):
    output_received = pyqtSignal(str, QTextEdit)  # Define a signal

    def __init__(self):
        super().__init__()
        self.running_tasks: Dict[str, subprocess.Popen] = {}
        self.output_received.connect(self.update_output)  # Connect signal to slot

    def start_task(self, task: Task, output_widget: QTextEdit) -> bool:
        """Start a task and return True if successful"""
        try:
            if task.id in self.running_tasks:
                if self.check_task_status(task.id) is not None:
                    self.cleanup_task(task.id)
                else:
                    logging.info(f"Task {task.title} is already running")
                    return False

            logging.info(f"Starting task in {task.path} with command: {task.cmd}")

            process = subprocess.Popen(
                ["cmd", "/c", task.cmd],
                cwd=task.path,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # Allow process tree control
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,  # Avoid extra shell layer
            )

            def stream_output(stream, output_type):
                for line in iter(stream.readline, b""):
                    decoded_line = line.decode("utf-8")  # Decode the output
                    html_output = conv.convert(decoded_line)  # Convert ANSI to HTML
                    self.output_received.emit(
                        html_output, output_widget
                    )  # Emit the signal

            threading.Thread(
                target=stream_output, args=(process.stdout, "STDOUT"), daemon=True
            ).start()
            threading.Thread(
                target=stream_output, args=(process.stderr, "STDERR"), daemon=True
            ).start()

            self.running_tasks[task.id] = process
            return True

        except Exception as e:
            logging.error(f"Error running {task.title}: {str(e)}")
            return False

    def stop_task(self, task_id: str) -> None:
        """Ensure full process termination, including child processes"""
        if task_id not in self.running_tasks:
            logging.warning(f"Task {task_id} not found in running tasks")
            raise ValueError(f"Task {task_id} not found in running tasks")

        process = self.running_tasks[task_id]
        logging.info(f"Attempting to terminate task {task_id}")

        try:
            # Use psutil to find all children and terminate them
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            for child in children:
                logging.info(f"Terminating child process {child.pid}")
                child.terminate()

            # Terminate parent process
            process.terminate()
            process.wait(timeout=2)

            # Check if any processes are still running, force kill if needed
            for child in children:
                if child.is_running():
                    logging.warning(f"Force killing child process {child.pid}")
                    child.kill()

            if parent.is_running():
                logging.warning(f"Force killing parent process {parent.pid}")
                parent.kill()

            logging.info(f"Task {task_id} terminated successfully")

        except Exception as e:
            logging.error(f"Error terminating process {task_id}: {str(e)}")

        finally:
            self.cleanup_task(task_id)

    def check_task_status(self, task_id: str) -> Optional[int]:
        """Check if a task is still running"""
        if task_id not in self.running_tasks:
            return -1  # Task not found
        return self.running_tasks[task_id].poll()

    def cleanup_task(self, task_id: str) -> None:
        """Remove task from tracking"""
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
            logging.info(f"Cleaned up task {task_id}")

    def update_output(self, html_output: str, output_widget: QTextEdit):
        output_widget.setHtml(f"{output_widget.toHtml()}<div>{html_output}</div>")
