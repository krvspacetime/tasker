from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QMessageBox,
    QInputDialog,
    QTabWidget,
    QFileDialog,
    QDialog,
    QHBoxLayout,
)
from PyQt6.QtCore import QTimer
from ..models.task import Task
from ..utils.config import ConfigManager
from ..utils.process import ProcessManager
from .task_widget import TaskWidget
from .group_widget import GroupWidget
from .task_dialog import TaskEditDialog

import logging
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tasker")
        self.setGeometry(100, 100, 800, 600)

        # Initialize managers
        self.config_manager = ConfigManager()
        self.process_manager = ProcessManager()

        # Create timer for checking process status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_running_tasks)
        self.status_timer.start(1000)  # Check every second

        self.init_ui()
        self.config_manager.load_config()
        self.update_displays()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Main controls layout
        main_controls = QHBoxLayout()
        layout.addLayout(main_controls)

        # Add Task button
        add_btn = QPushButton("Create Task")
        add_btn.clicked.connect(self.add_task)
        main_controls.addWidget(add_btn)

        # Create Group button
        group_btn = QPushButton("Create Group")
        main_controls.addWidget(group_btn)

        # Tabs for Tasks and Groups
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tasks Tab
        self.task_tab = QWidget()
        task_layout = QVBoxLayout(self.task_tab)
        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        task_layout.addWidget(self.task_list)

        # Add group button
        group_btn = QPushButton("Group Selected Tasks")
        group_btn.clicked.connect(self.group_tasks)
        task_layout.addWidget(group_btn)

        self.tabs.addTab(self.task_tab, "Tasks")

        # Groups Tab
        self.group_tab = QWidget()
        group_layout = QVBoxLayout(self.group_tab)
        self.group_list = QListWidget()
        group_layout.addWidget(self.group_list)
        self.tabs.addTab(self.group_tab, "Groups")

        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

    def add_task(self):
        dialog = TaskEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            path, cmd, title = dialog.get_values()

            if not (path and cmd):
                self.show_error("Please fill in path and command.")
                return

            if not os.path.isdir(path):
                self.show_error(f"Invalid directory: {path}")
                return

            task = Task.create(path=path, cmd=cmd, title=title or cmd)
            self.config_manager.tasks.append(task)
            self.update_displays()
            self.config_manager.save_config()
            logging.info(f"Added task: {task.title} (ID: {task.id})")

    def run_task(self, task: Task):
        """Run a specific task"""
        if self.process_manager.start_task(task):
            self.update_task_status(task.id, True)
            self.status_label.setText(f"Started: {task.title}")

    def run_group(self, group_name: str):
        """Run all tasks in a group"""
        if group_name not in self.config_manager.groups:
            return

        for task in self.config_manager.groups[group_name]:
            self.run_task(task)

    def check_running_tasks(self):
        """Check status of running tasks"""
        for task_id in list(self.process_manager.running_tasks.keys()):
            if self.process_manager.check_task_status(task_id) is not None:
                # Process has finished or was terminated
                self.update_task_status(task_id, False)
                self.process_manager.cleanup_task(task_id)
                logging.info(f"Task {task_id} is no longer running")

    def update_task_status(self, task_id: str, is_running: bool):
        """Update the status of a task in both task list and group list"""
        # Update in task list
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            widget = self.task_list.itemWidget(item)
            if isinstance(widget, TaskWidget) and widget.task.id == task_id:
                widget.update_status(is_running)

        # Update in group list
        for i in range(self.group_list.count()):
            item = self.group_list.item(i)
            widget = self.group_list.itemWidget(item)
            if isinstance(widget, GroupWidget):
                widget.update_task_status(task_id, is_running)

    def update_displays(self):
        """Update both task and group displays"""
        self.update_task_display()
        self.update_group_display()

    def update_task_display(self):
        """Update the task list display"""
        self.task_list.clear()
        for task in self.config_manager.tasks:
            task_widget = TaskWidget(task)
            item = QListWidgetItem(self.task_list)
            item.setSizeHint(task_widget.sizeHint())
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, task_widget)

            # Connect signals
            task_widget.run_clicked.connect(self.run_task)
            task_widget.edit_clicked.connect(self.edit_task)
            task_widget.delete_clicked.connect(self.delete_task)
            task_widget.add_to_group_clicked.connect(self.add_to_existing_group)

    def update_group_display(self):
        """Update the group list display"""
        self.group_list.clear()
        for group_name, tasks in self.config_manager.groups.items():
            group_widget = GroupWidget(group_name, tasks)
            item = QListWidgetItem(self.group_list)
            item.setSizeHint(group_widget.sizeHint())
            self.group_list.addItem(item)
            self.group_list.setItemWidget(item, group_widget)

            # Connect signals
            group_widget.run_group_clicked.connect(self.run_group)
            group_widget.edit_group_clicked.connect(self.edit_group)
            group_widget.delete_group_clicked.connect(self.delete_group)

    def show_error(self, message: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
        self.status_label.setText(f"Error: {message}")

    def group_tasks(self):
        """Create a new group from selected tasks"""
        selected_items = self.task_list.selectedItems()
        if len(selected_items) < 2:
            self.show_error("Select at least two tasks to group.")
            return

        group_name, ok = QInputDialog.getText(self, "Create Group", "Enter group name:")
        if not ok or not group_name:
            return

        if group_name in self.config_manager.groups:
            self.show_error(f"Group {group_name} already exists.")
            return

        # Create a new group with selected tasks
        group_tasks = []
        for item in selected_items:
            task = self.task_list.itemWidget(item).task
            if task in self.config_manager.tasks:
                # Remove task from main list and add to group
                self.config_manager.tasks.remove(task)
                group_tasks.append(task)

        self.config_manager.groups[group_name] = group_tasks
        self.update_displays()
        self.config_manager.save_config()
        logging.info(f"Created group: {group_name} with {len(group_tasks)} tasks")

    def edit_task(self, task: Task, group_name: str = None):
        """Edit an existing task"""
        dialog = TaskEditDialog(task, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            path, cmd, title = dialog.get_values()

            if not (path and cmd):
                self.show_error("Please fill in path and command.")
                return

            if not os.path.isdir(path):
                self.show_error(f"Invalid directory: {path}")
                return

            # Update task properties
            task.path = path
            task.cmd = cmd
            task.title = title or cmd

            self.update_displays()
            self.config_manager.save_config()
            logging.info(f"Updated task: {task.title} (ID: {task.id})")

    def delete_task(self, task: Task, group_name: str = None):
        """Delete a task from either ungrouped tasks or a group"""
        if task in self.config_manager.tasks:
            self.config_manager.tasks.remove(task)
        elif group_name and task in self.config_manager.groups.get(group_name, []):
            self.config_manager.groups[group_name].remove(task)
            if not self.config_manager.groups[group_name]:
                del self.config_manager.groups[group_name]

        self.update_displays()
        self.config_manager.save_config()
        logging.info(f"Deleted task: {task.title} (ID: {task.id})")

    def edit_group(self, group_name: str):
        """Edit a group's name"""
        new_name, ok = QInputDialog.getText(
            self, "Edit Group", "Enter new group name:", text=group_name
        )
        if ok and new_name and new_name != group_name:
            if new_name in self.config_manager.groups:
                self.show_error(f"Group '{new_name}' already exists.")
                return
            self.config_manager.groups[new_name] = self.config_manager.groups.pop(
                group_name
            )
            self.update_displays()
            self.config_manager.save_config()
            logging.info(f"Renamed group from {group_name} to {new_name}")

    def delete_group(self, group_name: str):
        """Delete a group and move its tasks to ungrouped tasks"""
        reply = QMessageBox.question(
            self,
            "Delete Group",
            f"Delete group '{group_name}'? Tasks will be moved to ungrouped tasks.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Move tasks back to ungrouped tasks
            self.config_manager.tasks.extend(self.config_manager.groups[group_name])
            del self.config_manager.groups[group_name]
            self.update_displays()
            self.config_manager.save_config()
            logging.info(f"Deleted group: {group_name}")

    def add_to_existing_group(self, task: Task):
        """Add a task to an existing group"""
        group_names = list(self.config_manager.groups.keys())
        if not group_names:
            self.show_error("No existing groups. Create a group first.")
            return

        group_name, ok = QInputDialog.getItem(
            self, "Add to Group", "Select group:", group_names, 0, False
        )
        if ok and group_name:
            if task in self.config_manager.tasks:
                self.config_manager.tasks.remove(task)
            self.config_manager.groups[group_name].append(task)
            self.update_displays()
            self.config_manager.save_config()
            logging.info(f"Added task {task.title} to group {group_name}")

    def browse_directory(self):
        """Open file dialog to select a directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            "",  # Start from default directory since we removed path_input
            QFileDialog.Option.ShowDirsOnly,
        )
        if directory:
            self.path_input.setText(directory)
