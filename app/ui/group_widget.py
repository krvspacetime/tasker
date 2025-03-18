from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal
from typing import List
from ..models.task import Task
from .task_widget import TaskWidget

class GroupWidget(QWidget):
    run_group_clicked = pyqtSignal(str)
    edit_group_clicked = pyqtSignal(str)
    delete_group_clicked = pyqtSignal(str)

    def __init__(self, name: str, tasks: List[Task], parent=None):
        super().__init__(parent)
        self.name = name
        self.tasks = tasks
        self.task_widgets = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Create header with group name and buttons
        header_layout = QHBoxLayout()
        group_label = QLabel(f"Group: {self.name}")
        run_group_btn = QPushButton("Run Group")
        edit_group_btn = QPushButton("Edit Group")
        delete_group_btn = QPushButton("Delete Group")

        # Connect signals
        run_group_btn.clicked.connect(lambda: self.run_group_clicked.emit(self.name))
        edit_group_btn.clicked.connect(lambda: self.edit_group_clicked.emit(self.name))
        delete_group_btn.clicked.connect(lambda: self.delete_group_clicked.emit(self.name))

        # Add widgets to header layout
        header_layout.addWidget(group_label)
        header_layout.addWidget(run_group_btn)
        header_layout.addWidget(edit_group_btn)
        header_layout.addWidget(delete_group_btn)
        header_layout.addStretch()

        # Add header to main layout
        layout.addLayout(header_layout)

        # Add task widgets
        for task in self.tasks:
            task_widget = TaskWidget(task, self.name)
            self.task_widgets.append(task_widget)
            layout.addWidget(task_widget)

    def update_task_status(self, task_id: str, is_running: bool):
        """Update the status of a specific task"""
        for task_widget in self.task_widgets:
            if task_widget.task.id == task_id:
                task_widget.update_status(is_running)
                break
