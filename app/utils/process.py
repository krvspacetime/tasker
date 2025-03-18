import subprocess
import logging
import threading

from typing import Dict, Optional

from colorama import init
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import pyqtSignal, QObject
from ansi2html import Ansi2HTMLConverter

from ..models.task import Task


# Initialize colorama
init()
conv = Ansi2HTMLConverter()


class ProcessManager(QObject):
    output_received = pyqtSignal(str, QTextEdit)  # Define a signal

    def __init__(self):
        super().__init__()
        self.running_tasks: Dict[str, subprocess.Popen] = {}
        self.output_received.connect(self.update_output)  # Connect signal to slot
        self.running_tasks: Dict[str, subprocess.Popen] = {}

    def start_task(self, task: Task, output_widget: QTextEdit) -> bool:
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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            def stream_output(stream, output_type):
                for line in iter(stream.readline, b""):
                    decoded_line = line.decode("utf-8")  # Decode the output
                    html_output = conv.convert(decoded_line)  # Convert ANSI to HTML
                    self.output_received.emit(
                        html_output, output_widget
                    )  # Emit the signal
                stream.close()

            threading.Thread(
                target=stream_output, args=(process.stdout, "STDOUT")
            ).start()
            threading.Thread(
                target=stream_output, args=(process.stderr, "STDERR")
            ).start()

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

    def update_output(self, html_output: str, output_widget: QTextEdit):
        output_widget.setHtml(f"{output_widget.toHtml()}<div>{html_output}</div>")
