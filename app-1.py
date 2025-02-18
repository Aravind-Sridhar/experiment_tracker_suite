import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLineEdit, QTextEdit, QDateEdit, QComboBox, QPushButton,
                            QFileDialog, QListWidget, QLabel, QTabWidget, QMessageBox)
from PyQt5.QtCore import QDate

class ExperimentTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_folder = None
        self.metadata = {"project": {}, "experiments": []}
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Experiment Tracker")
        self.setGeometry(100, 100, 800, 600)
        
        main_widget = QWidget()
        self.tabs = QTabWidget()
        
        # Setup tabs
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
        
        # Date fields
        self.project_start_date = QDateEdit()
        self.project_start_date.setDate(QDate.currentDate())
        self.project_end_date = QDateEdit()
        
        # Create project button
        create_btn = QPushButton("Create Project")
        create_btn.clicked.connect(self.save_project)
        
        # Add elements to layout
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
        
        # Experiment fields
        self.experiment_title = QLineEdit()
        self.experiment_description = QTextEdit()
        self.version = QLineEdit()
        self.file_list = QListWidget()
        
        # File selection buttons
        file_btn = QPushButton("Add Files")
        file_btn.clicked.connect(self.select_files)
        folder_btn = QPushButton("Add Folder")
        folder_btn.clicked.connect(self.select_folder)
        
        # Date fields
        self.experiment_start_date = QDateEdit()
        self.experiment_start_date.setDate(QDate.currentDate())
        self.experiment_end_date = QDateEdit()
        
        # Create experiment button
        create_btn = QPushButton("Save Experiment")
        create_btn.clicked.connect(self.save_experiment)
        
        # Add elements to layout
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
            self.file_list.addItems(files)
            
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
                    self.file_list.addItem(os.path.join(root, file))
                    
    def save_project(self):
        if not self.base_folder:
            self.show_warning("Please select a project folder first!")
            return
            
        if not self.project_title.text().strip():
            self.show_warning("Project title is required!")
            return
            
        self.metadata["project"] = {
            "title": self.project_title.text(),
            "description": self.project_description.toPlainText(),
            "usernames": [u.strip() for u in self.usernames.text().split(',')],
            "association": self.project_association.currentText(),
            "dates": {
                "start": self.project_start_date.date().toString("yyyy-MM-dd"),
                "end": self.project_end_date.date().toString("yyyy-MM-dd")
            }
        }
        
        self.save_metadata()
        QMessageBox.information(self, "Success", "Project created successfully!")
        
    def save_experiment(self):
        if not self.metadata.get("project"):
            self.show_warning("Please create a project first!")
            return
            
        if not self.experiment_title.text().strip():
            self.show_warning("Experiment title is required!")
            return
            
        experiment = {
            "title": self.experiment_title.text(),
            "description": self.experiment_description.toPlainText(),
            "version": self.version.text(),
            "files": [self.file_list.item(i).text() for i in range(self.file_list.count())],
            "dates": {
                "start": self.experiment_start_date.date().toString("yyyy-MM-dd"),
                "end": self.experiment_end_date.date().toString("yyyy-MM-dd")
            }
        }
        
        self.metadata["experiments"].append(experiment)
        self.save_metadata()
        self.file_list.clear()
        QMessageBox.information(self, "Success", "Experiment saved successfully!")
        
    def save_metadata(self):
        if not self.base_folder:
            return
            
        json_path = os.path.join(self.base_folder, "project_metadata.json")
        with open(json_path, 'w') as f:
            json.dump(self.metadata, f, indent=4)
            
    def show_warning(self, message):
        QMessageBox.warning(self, "Warning", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExperimentTracker()
    window.show()
    sys.exit(app.exec_())
