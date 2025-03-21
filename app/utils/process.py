import subprocess
import logging
import psutil
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import pyqtSignal, QObject
from ansi2html import Ansi2HTMLConverter

from app.models.task import Task

conv = Ansi2HTMLConverter()


class ProcessManager(QObject):
    output_received = pyqtSignal(str, QTextEdit)  # Signal for UI updates

    def __init__(self):
        super().__init__()
        self.running_tasks: Dict[str, subprocess.Popen] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)  # Limit concurrent tasks
        self.output_received.connect(self.update_output)  # Connect signal to UI slot

    def start_task(self, task: Task, output_widget: QTextEdit) -> bool:
        """Start a new task in a separate thread."""
        if task.id in self.running_tasks:
            if self.check_task_status(task.id) is not None:
                self.cleanup_task(task.id)
            else:
                logging.info(f"Task {task.title} is already running")
                return False

        logging.info(f"Starting task in {task.path} with command: {task.cmd}")

        try:
            process = subprocess.Popen(
                ["cmd", "/c", task.cmd],
                cwd=task.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                shell=False,  # Avoid unnecessary shell overhead
            )

            self.running_tasks[task.id] = process

            # Run output streaming in background threads
            self.executor.submit(self._stream_output, process.stdout, output_widget)
            self.executor.submit(self._stream_output, process.stderr, output_widget)

            return True

        except Exception as e:
            logging.error(f"Error running {task.title}: {str(e)}")
            return False

    def _stream_output(self, stream, output_widget):
        """Reads process output in real-time and updates UI in batches."""
        batch_size = 5
        output_buffer = []

        for line in iter(stream.readline, b""):
            decoded_line = line.decode("utf-8", errors="replace").strip()
            html_output = conv.convert(decoded_line)
            output_buffer.append(html_output)

            if len(output_buffer) >= batch_size:
                self.output_received.emit("".join(output_buffer), output_widget)
                output_buffer.clear()

        # Send remaining output
        if output_buffer:
            self.output_received.emit("".join(output_buffer), output_widget)

    def stop_task(self, task_id: str) -> None:
        """Ensure full process termination, including child processes."""
        if task_id not in self.running_tasks:
            logging.warning(f"Task {task_id} not found in running tasks")
            raise ValueError(f"Task {task_id} not found in running tasks")

        process = self.running_tasks[task_id]
        logging.info(f"Attempting to terminate task {task_id}")

        try:
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)

            for child in children:
                logging.info(f"Terminating child process {child.pid}")
                child.terminate()

            process.terminate()
            process.wait(timeout=2)

            # Ensure all processes are fully stopped
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
        """Check if a task is still running."""
        return (
            self.running_tasks.get(task_id, None).poll()
            if task_id in self.running_tasks
            else -1
        )

    def cleanup_task(self, task_id: str) -> None:
        """Remove task from tracking."""
        self.running_tasks.pop(task_id, None)
        logging.info(f"Cleaned up task {task_id}")

    def update_output(self, html_output: str, output_widget: QTextEdit):
        """Update the UI with new output."""
        output_widget.setHtml(f"{output_widget.toHtml()}<div>{html_output}</div>")
