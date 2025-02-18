import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLineEdit, QTextEdit, QDateEdit, QComboBox, QPushButton,
                            QFileDialog, QListWidget, QLabel, QTabWidget, QMessageBox)
from PyQt5.QtCore import QDate, QDateTime

class ExperimentTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_folder = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Experiment Tracker")
        self.setGeometry(100, 100, 900, 700)
        
        main_widget = QWidget()
        self.tabs = QTabWidget()
        
        self.tabs.addTab(self.create_project_tab(), "Project")
        self.tabs.addTab(self.create_experiment_tab(), "Experiment")
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def create_project_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Folder selection
        folder_btn = QPushButton("Choose Project Folder")
        folder_btn.clicked.connect(self.choose_base_folder)
        self.folder_label = QLabel("No folder selected")
        
        # Project fields
        self.project_title = QLineEdit()
        self.project_description = QTextEdit()
        self.usernames = QLineEdit()
        self.project_association = QComboBox()
        self.project_association.addItems(["Adiuvo", "Auxillium", "Others"])
        
        # Date fields with calendar popup
        self.project_start_date = QDateEdit(calendarPopup=True)
        self.project_start_date.setDate(QDate.currentDate())
        self.project_end_date = QDateEdit(calendarPopup=True)
        self.project_end_date.setDate(QDate.currentDate())
        
        create_btn = QPushButton("Create Project")
        create_btn.clicked.connect(self.save_project)
        
        layout.addWidget(folder_btn)
        layout.addWidget(self.folder_label)
        layout.addWidget(QLabel("Project Title:"))
        layout.addWidget(self.project_title)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.project_description)
        layout.addWidget(QLabel("Team Members (comma-separated):"))
        layout.addWidget(self.usernames)
        layout.addWidget(QLabel("Association:"))
        layout.addWidget(self.project_association)
        layout.addWidget(QLabel("Start Date:"))
        layout.addWidget(self.project_start_date)
        layout.addWidget(QLabel("End Date:"))
        layout.addWidget(self.project_end_date)
        layout.addWidget(create_btn)
        
        tab.setLayout(layout)
        return tab

    def create_experiment_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.projects_combo = QComboBox()
        self.experiment_title = QLineEdit()
        self.experiment_description = QTextEdit()
        self.version = QLineEdit()
        self.file_list = QListWidget()
        
        file_btn = QPushButton("Add Files")
        file_btn.clicked.connect(self.select_files)
        folder_btn = QPushButton("Add Folder")
        folder_btn.clicked.connect(self.select_folder)
        
        self.experiment_start_date = QDateEdit(calendarPopup=True)
        self.experiment_start_date.setDate(QDate.currentDate())
        self.experiment_end_date = QDateEdit(calendarPopup=True)
        
        create_btn = QPushButton("Save Experiment")
        create_btn.clicked.connect(self.save_experiment)
        
        layout.addWidget(QLabel("Associated Project:"))
        layout.addWidget(self.projects_combo)
        layout.addWidget(QLabel("Experiment Title:"))
        layout.addWidget(self.experiment_title)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.experiment_description)
        layout.addWidget(QLabel("Version:"))
        layout.addWidget(self.version)
        layout.addWidget(QLabel("Associated Files/Folders:"))
        layout.addWidget(self.file_list)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(file_btn)
        btn_layout.addWidget(folder_btn)
        layout.addLayout(btn_layout)
        
        layout.addWidget(QLabel("Start Date:"))
        layout.addWidget(self.experiment_start_date)
        layout.addWidget(QLabel("End Date:"))
        layout.addWidget(self.experiment_end_date)
        layout.addWidget(create_btn)
        
        tab.setLayout(layout)
        return tab

    def choose_base_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Directory",
            options=QFileDialog.ShowDirsOnly
        )
        if folder:
            self.base_folder = folder
            self.folder_label.setText(f"Selected Folder: {folder}")
            self.load_existing_projects()

    def load_existing_projects(self):
        self.projects_combo.clear()
        if self.base_folder:
            for f in os.listdir(self.base_folder):
                if f.endswith('.json'):
                    try:
                        with open(os.path.join(self.base_folder, f), 'r') as file:
                            data = json.load(file)
                            if 'project' in data:  # Only load project files
                                self.projects_combo.addItem(data['project']['title'], f)
                    except:
                        continue

    def select_files(self):
        if not self.base_folder:
            self.show_warning("Please select a project folder first!")
            return
            
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Experiment Files",
            self.base_folder
        )
        if files:
            for file in files:
                rel_path = os.path.relpath(file, self.base_folder)
                self.file_list.addItem(rel_path)

    def select_folder(self):
        if not self.base_folder:
            self.show_warning("Please select a project folder first!")
            return
            
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Experiment Folder",
            self.base_folder,
            QFileDialog.ShowDirsOnly
        )
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, self.base_folder)
                    self.file_list.addItem(rel_path)

    def save_project(self):
        if not self.base_folder:
            self.show_warning("Please select a project folder first!")
            return
            
        project_title = self.project_title.text().strip()
        if not project_title:
            self.show_warning("Project title is required!")
            return

        timestamp = QDateTime.currentDateTime().toString("yyyyMMddhhmmss")
        filename = f"{self.sanitize_filename(project_title)}_{timestamp}.json"
        filepath = os.path.join(self.base_folder, filename)
        
        metadata = {
            "project": {
                "title": project_title,
                "description": self.project_description.toPlainText(),
                "usernames": [u.strip() for u in self.usernames.text().split(',')],
                "association": self.project_association.currentText(),
                "dates": {
                    "start": self.project_start_date.date().toString("yyyy-MM-dd"),
                    "end": self.project_end_date.date().toString("yyyy-MM-dd")
                }
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=4)
            
        self.load_existing_projects()
        QMessageBox.information(self, "Success", "Project created successfully!")

    def save_experiment(self):
        if not self.base_folder:
            self.show_warning("Please select a project folder first!")
            return
            
        if self.projects_combo.currentIndex() == -1:
            self.show_warning("Please select a project!")
            return
            
        project_file = self.projects_combo.currentData()
        experiment_title = self.experiment_title.text().strip()
        version = self.version.text().strip()
        
        if not experiment_title:
            self.show_warning("Experiment title is required!")
            return
        if not version:
            self.show_warning("Version number is required!")
            return
            
        try:
            with open(os.path.join(self.base_folder, project_file), 'r') as f:
                project_data = json.load(f)
                project_title = project_data['project']['title']
        except Exception as e:
            self.show_warning(f"Error reading project file: {str(e)}")
            return

        # Build hierarchical file structure
        file_paths = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        file_hierarchy = self.build_hierarchy(file_paths)

        # Create experiment filename
        safe_project = self.sanitize_filename(project_title)
        safe_experiment = self.sanitize_filename(experiment_title)
        safe_version = self.sanitize_filename(version)
        experiment_filename = f"{safe_project}_{safe_experiment}_v{safe_version}.json"
        experiment_path = os.path.join(self.base_folder, experiment_filename)

        experiment_data = {
            "project_reference": project_file,
            "experiment": {
                "title": experiment_title,
                "description": self.experiment_description.toPlainText(),
                "version": version,
                "file_structure": file_hierarchy,
                "dates": {
                    "start": self.experiment_start_date.date().toString("yyyy-MM-dd"),
                    "end": self.experiment_end_date.date().toString("yyyy-MM-dd")
                }
            }
        }

        try:
            with open(experiment_path, 'w') as f:
                json.dump(experiment_data, f, indent=4)
            self.file_list.clear()
            QMessageBox.information(self, "Success", "Experiment saved successfully!")
        except Exception as e:
            self.show_warning(f"Error saving experiment: {str(e)}")

    def build_hierarchy(self, file_paths):
        hierarchy = {}
        for path in file_paths:
            parts = path.split(os.sep)
            current_level = hierarchy
            for part in parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            filename = parts[-1]
            current_level[filename] = path
        return hierarchy

    def sanitize_filename(self, name):
        return "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in name)

    def show_warning(self, message):
        QMessageBox.warning(self, "Warning", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExperimentTracker()
    window.show()
    sys.exit(app.exec_())
