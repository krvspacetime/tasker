import os
import json
import uuid

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QComboBox,
    QWidget,
)
from app.utils.utils import load_config_yaml
from app.models.task import Task

COMMANDS_JSON_PATH = os.path.join(os.getcwd(), "commands.json")


class TaskEditDialog(QDialog):
    def __init__(self, task: Task = None, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("Edit Task" if task else "New Task")
        self.commands_list = self.load_commands()
        self.init_ui()
        if task:
            self.path_input.setText(task.path)
            self.cmd_input.setCurrentText(task.cmd)
            self.title_input.setText(task.title)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Path input with browse button
        path_container = QWidget(self)
        path_layout = QHBoxLayout(path_container)
        path_layout.setContentsMargins(0, 0, 0, 0)

        path_label = QLabel("Path:", self)
        self.path_input = QLineEdit(self)
        self.path_input.setPlaceholderText("Enter folder path (e.g., C:\\code\\myrepo)")
        browse_btn = QPushButton("Browse...", self)
        browse_btn.clicked.connect(self.browse_directory)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)

        # Command input
        cmd_label = QLabel("Command:", self)
        self.cmd_input = QComboBox(self)
        self.cmd_input.setEditable(True)
        self.cmd_input.addItems(self.commands_list)

        # Title input
        title_label = QLabel("Title:", self)
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Enter title (defaults to command)")

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save", self)
        cancel_btn = QPushButton("Cancel", self)

        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        # Add all widgets to main layout
        layout.addWidget(path_container)
        layout.addWidget(cmd_label)
        layout.addWidget(self.cmd_input)
        layout.addWidget(title_label)
        layout.addWidget(self.title_input)
        layout.addLayout(button_layout)

    def browse_directory(self):
        """Open file dialog to select a directory"""
        config = load_config_yaml()
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            config["settings"]["default_path"],
            QFileDialog.Option.ShowDirsOnly,
        )
        if directory:
            self.path_input.setText(directory)

    def get_values(self) -> tuple:
        """Return the input values"""
        return (
            self.path_input.text().strip(),
            self.cmd_input.currentText().strip(),
            self.title_input.text().strip(),
        )

    def accept(self):
        command = self.cmd_input.currentText()
        self.add_command(command)
        super().accept()

    def add_command(self, command):
        if command and command not in self.commands_list:
            self.commands_list.append(command)
            self.save_commands()
            self.cmd_input.clear()
            self.cmd_input.addItems(self.commands_list)

    def load_commands(self):
        try:
            with open(COMMANDS_JSON_PATH, "r") as f:
                data = json.load(f)
                return [task["cmd"] for task in data["tasks"]]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_commands(self):
        tasks = []
        for cmd in self.commands_list:
            tasks.append({"id": str(uuid.uuid4()), "cmd": cmd})
        with open(COMMANDS_JSON_PATH, "w") as f:
            json.dump({"tasks": tasks}, f, indent=4)
