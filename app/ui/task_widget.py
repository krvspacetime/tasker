from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal
from ..models.task import Task


class TaskWidget(QWidget):
    run_clicked = pyqtSignal(Task)
    edit_clicked = pyqtSignal(Task, str)
    delete_clicked = pyqtSignal(Task, str)
    add_to_group_clicked = pyqtSignal(Task)

    def __init__(self, task: Task, group_name: str = None, parent=None):
        super().__init__(parent)
        self.task = task
        self.group_name = group_name
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Create status indicator
        self.status_label = QLabel("●", objectName="status")
        self.status_label.setStyleSheet("color: gray;")
        self.status_label.setProperty("taskId", self.task.id)

        # Create title label
        title_label = QLabel(self.task.title)

        # Create buttons
        run_btn = QPushButton("Run")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")

        # Connect signals
        run_btn.clicked.connect(lambda: self.run_clicked.emit(self.task))
        edit_btn.clicked.connect(
            lambda: self.edit_clicked.emit(self.task, self.group_name)
        )
        delete_btn.clicked.connect(
            lambda: self.delete_clicked.emit(self.task, self.group_name)
        )

        # Add widgets to layout
        layout.addWidget(self.status_label)
        layout.addWidget(title_label)
        layout.addWidget(run_btn)
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)

        # Add "Add to Group" button for ungrouped tasks
        if not self.group_name:
            add_to_group_btn = QPushButton("Add to Group")
            add_to_group_btn.clicked.connect(
                lambda: self.add_to_group_clicked.emit(self.task)
            )
            layout.addWidget(add_to_group_btn)

        layout.addStretch()

    def update_status(self, is_running: bool):
        """Update the status indicator"""
        self.status_label.setStyleSheet(
            "color: green;" if is_running else "color: gray;"
        )
