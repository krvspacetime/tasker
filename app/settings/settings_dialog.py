import os
import yaml

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 500, 100)
        self.config = self.load_config_yaml()

        layout = QVBoxLayout(self)
        default_tasks_dir_layout = QHBoxLayout()
        layout.addLayout(default_tasks_dir_layout)
        # Default Tasks Directory
        self.directory_label = QLabel("Default Tasks Directory:")
        default_tasks_dir_layout.addWidget(self.directory_label)

        self.directory_edit = QLineEdit(self)
        default_tasks_dir_layout.addWidget(self.directory_edit)

        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.browse_directory)
        default_tasks_dir_layout.addWidget(self.browse_button)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_settings)
        default_tasks_dir_layout.addWidget(self.save_button)
        self.init_settings()

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.directory_edit.setText(directory)
            self.config["settings"]["default_path"] = directory
            self.save_config_yaml()

    def save_settings(self):
        self.accept()

    def load_config_yaml(self):
        with open("config.yaml", "r") as file:
            return yaml.safe_load(file)

    def save_config_yaml(self):
        with open("config.yaml", "w") as file:
            yaml.dump(self.config, file)

    def init_settings(self):
        if self.config["settings"]["default_path"] == "":
            self.config["settings"]["default_path"] = os.path.join(
                os.path.expanduser("~"), "Documents"
            )
        else:
            self.config["settings"]["default_path"] = self.config["settings"][
                "default_path"
            ]
        self.directory_edit.setText(self.config["settings"]["default_path"])
