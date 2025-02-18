from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QMenu, QListWidget, QListWidgetItem, QInputDialog,
    QApplication, QMainWindow, QWidget, QTableWidget, QTableWidgetItem, QComboBox, QHBoxLayout,
    QAbstractItemView, QCalendarWidget, QDateEdit, QGridLayout, QFormLayout, QCheckBox,
    QScrollArea
)
import hashlib
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
import os
import json
from datetime import datetime
import tempfile
import shutil
import platform
import subprocess
from PyQt5.QtCore import QDate
import copy

# Supported image extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}

def is_image_file(filename):
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS

def strip_timestamp(file_name):
    """Strip any existing timestamp from the filename."""
    base, ext = os.path.splitext(file_name)  # Split the file name into base and extension
    parts = base.split("_")  # Split the base name into parts using underscores
    if len(parts) > 1 and parts[-1].isdigit():  # Check if the last part is a numeric timestamp
        base = "_".join(parts[:-1])  # Remove the timestamp
    return base + ext  # Reconstruct the file name

#The following is the code for the home screen functionality. It lets you open 
# Projects, Prototypes, Users, and Experiments
class HomeDialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_folder = None
        self.init_ui()

    def init_ui(self):
        """Set up the main UI layout."""
        self.setWindowTitle("R&D Tool - Home Screen")

        # Central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Label to display selected base folder path
        self.folder_label = QLabel("No base folder selected", self)
        layout.addWidget(self.folder_label)

        # Button to select base folder
        select_folder_btn = QPushButton("Select Base Folder", self)
        select_folder_btn.clicked.connect(self.select_base_folder)
        layout.addWidget(select_folder_btn)

        # Placeholder for main buttons
        self.buttons = {}
        sections = ["Experiments", "Prototypes", "Users", "Projects"]
        for section in sections:
            button = QPushButton(section, self)
            button.clicked.connect(lambda _, sec=section: self.handle_section_click(sec))
            button.setEnabled(False)  # Disabled until a base folder is selected
            layout.addWidget(button)
            self.buttons[section] = button

        self.show()

    def select_base_folder(self):
        """Prompt the user to select a base folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Base Folder")
        if folder:
            self.base_folder = folder
            # Check if metadata.json exists, create if not
            self.check_or_create_metadata()
            # Update the folder label
            self.folder_label.setText(f"Base Folder: {folder}")
            QMessageBox.information(self, "Base Folder Selected", f"Base folder set to: {folder}")
            # Enable the main buttons
            for button in self.buttons.values():
                button.setEnabled(True)
        else:
            QMessageBox.warning(self, "No Folder Selected", "Please select a base folder to proceed.")

    def check_or_create_metadata(self):
        """Check if metadata.json exists in the base folder, and create it with high-level entry types if not."""
        metadata_path = os.path.join(self.base_folder, "metadata.json")
        if not os.path.exists(metadata_path):
            # Create metadata.json with high-level entry types
            initial_data = {
                "Projects": [],
                "Prototypes": [],
                "Experiments": [],
                "Users": []
            }
            with open(metadata_path, "w") as f:
                json.dump(initial_data, f, indent=4)
            QMessageBox.information(self, "Metadata File Created", f"'metadata.json' created in {self.base_folder}")
        else:
            QMessageBox.information(self, "Metadata File Found", f"'metadata.json' already exists in {self.base_folder}")

    def handle_section_click(self, section):
        """Handle clicks on the main buttons."""
        if self.base_folder:
            if section == "Projects":
                self.open_projects_dialog()
            elif section == "Prototypes":
                self.open_prototypes_dialog()
            elif section == "Users":
                self.open_users_dialog()
            elif section == "Experiments":
                self.open_experiments_dialog()
            else:
                QMessageBox.information(self, "Not Implemented", f"{section} section is not yet implemented.")
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Please select a base folder before accessing this section."
            )

    def open_projects_dialog(self):
        """Open the Projects dialog."""
        dialog = ProjectsDialog(self.base_folder)
        dialog.exec_()
        
    def open_prototypes_dialog(self):
        """Open the Projects dialog."""
        dialog = PrototypesDialog(self.base_folder)
        dialog.exec_()
        
    def open_users_dialog(self):
        """Open the Projects dialog."""
        dialog = UsersDialog(self.base_folder)
        dialog.exec_()
        
    def open_experiments_dialog(self):
        """Open the Projects dialog."""
        dialog = ExperimentsDialog(self.base_folder)
        dialog.exec_()

#Create and manage experiments using the following classes (each corresponding to a separate window)
# ExperimentsDialog() - opens a dialog to create or browse prototypes
# CreateExperimentDialog() - allows you to create a new prototype
# BrowseExperimentsDialog() - allows you to view the list of existing prototype. 
#                           It also also allows you to edit a selected prototype
#                           version
# EditExperimentDialog() - It allows you to edit a selected prototype and save
#                         changes as a new version automatically. 
class ExperimentsDialog(QDialog):
    """Main Projects dialog with Create and Browse options."""
    def __init__(self, base_folder):
        super().__init__()
        self.base_folder = base_folder
        self.metadata_path = os.path.join(self.base_folder, "metadata.json")
        self.metadata = self.load_metadata()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Experiments")
        layout = QVBoxLayout()

        # Create Project Button
        create_button = QPushButton("Create Experiment", self)
        create_button.clicked.connect(self.open_create_experiment_dialog)
        layout.addWidget(create_button)

        # Browse Projects Button
        browse_button = QPushButton("Browse Experiments", self)
        browse_button.clicked.connect(self.browse_experiments)
        layout.addWidget(browse_button)

        # Close Button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def load_metadata(self):
        """Load metadata from metadata.json."""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        return {"Projects": [], "Prototypes": [], "Experiments": [], "Users": []}

    def save_metadata(self):
        """Save metadata back to metadata.json."""
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=4)

    def open_create_experiment_dialog(self):
        """Open the Create Prototype dialog."""
        dialog = CreateExperimentDialog(self.base_folder, self.metadata)
        if dialog.exec_():  # If the dialog is successfully completed
            self.save_metadata()

    def browse_experiments(self):
        """Open the Browse Projects dialog to view and edit existing prototypes."""
        if not self.metadata.get("Prototypes"):
            QMessageBox.information(self, "No Prototypes", "There are no prototypes to browse.")
            return
    
        # Open the Browse experiments dialog
        dialog = BrowseExperimentsDialog(self.base_folder, self.metadata)
        if dialog.exec_():  # If changes were made
            print('Done browsing')
            # Save updated metadata directly
            self.save_metadata()
            
            # Debugging: Print metadata after returning from the dialog
            print("Updated Metadata After Browsing:")
            print(json.dumps(self.metadata, indent=4))

class CreateExperimentDialog(QDialog):
    """Dialog for creating a new project."""
    def __init__(self, base_folder, metadata):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.experiment_files_folder = os.path.join(self.base_folder, "Experiment Files")
        os.makedirs(self.experiment_files_folder, exist_ok=True)
        self.uploaded_items = []  # To store uploaded files and folders
        self.selected_node = None  # Track the selected node in the project tree
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("Create Experiment")
        main_layout = QHBoxLayout()  # Main horizontal layout for two columns

        # Left Column
        left_column = QVBoxLayout()

        # Experiment Name
        self.name_label = QLabel("Experiment Title:")
        left_column.addWidget(self.name_label)
        self.name_input = QLineEdit()
        left_column.addWidget(self.name_input)

        # Experiment Description
        self.description_label = QLabel("Experiment Description:")
        left_column.addWidget(self.description_label)
        self.description_input = QTextEdit()
        left_column.addWidget(self.description_input)

        # Associated Project
        self.project_label = QLabel("Select Associated Project:")
        left_column.addWidget(self.project_label)
        self.project_dropdown = QComboBox()
        self.project_dropdown.addItems([p["name"] for p in self.metadata.get("Projects", [])])
        self.project_dropdown.currentIndexChanged.connect(self.display_project_tree)  # Trigger tree display on selection
        print("Connected project_dropdown to display_project_tree.")
        left_column.addWidget(self.project_dropdown)
    
        # Project Tree View
        self.project_tree_label = QLabel("Select Node in Project:")
        self.project_tree_label.setVisible(True)
        left_column.addWidget(self.project_tree_label)
        self.project_tree_widget = QTreeWidget()
        self.project_tree_widget.setHeaderLabel("Project Structure")
        self.project_tree_widget.setVisible(True)
        left_column.addWidget(self.project_tree_widget)
        if self.project_dropdown.count() > 0:
            self.display_project_tree()  # Call manually to handle the first item
        self.project_tree_widget.itemClicked.connect(self.node_selected)


        # Associated Users
        self.users_label = QLabel("Select Users:")
        left_column.addWidget(self.users_label)
        self.users_list = QListWidget()
        self.users_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for user in self.metadata.get("Users", []):
            item = QListWidgetItem(user["name"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, user)
            self.users_list.addItem(item)
        left_column.addWidget(self.users_list)

        # Associated Prototypes
        self.prototypes_label = QLabel("Select Prototypes:")
        left_column.addWidget(self.prototypes_label)
        self.prototypes_list = QListWidget()
        self.prototypes_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for prototype in self.metadata.get("Prototypes", []):
            item = QListWidgetItem(prototype["name"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, prototype)
            self.prototypes_list.addItem(item)
        left_column.addWidget(self.prototypes_list)

        main_layout.addLayout(left_column)

        # Right Column
        right_column = QVBoxLayout()

        # Experiment Type
        self.type_label = QLabel("Experiment Type:")
        right_column.addWidget(self.type_label)
        self.type_dropdown = QComboBox()
        self.type_dropdown.addItems([
            "Prototype: Pre-assembly",
            "Prototype: Inspection",
            "Prototype: Full system",
            "Non-prototype"
        ])
        right_column.addWidget(self.type_dropdown)

        # Start and End Dates
        self.dates_label = QLabel("Set Start and End Dates:")
        right_column.addWidget(self.dates_label)
        self.dates_layout = QHBoxLayout()
        self.start_date_label = QLabel("Start Date:")
        self.start_date_picker = QDateEdit()
        self.start_date_picker.setDate(QDate.currentDate())
        self.start_date_picker.setCalendarPopup(True)
        self.dates_layout.addWidget(self.start_date_label)
        self.dates_layout.addWidget(self.start_date_picker)
        self.end_date_label = QLabel("End Date:")
        self.end_date_picker = QDateEdit()
        self.end_date_picker.setDate(QDate.currentDate())
        self.end_date_picker.setCalendarPopup(True)
        self.dates_layout.addWidget(self.end_date_label)
        self.dates_layout.addWidget(self.end_date_picker)
        right_column.addLayout(self.dates_layout)

        # File and Folder Upload
        self.upload_files_button = QPushButton("Upload Files")
        self.upload_files_button.clicked.connect(self.upload_files)
        right_column.addWidget(self.upload_files_button)

        self.upload_folder_button = QPushButton("Upload Folder")
        self.upload_folder_button.clicked.connect(self.upload_folder)
        right_column.addWidget(self.upload_folder_button)

        # Uploaded Items Display
        self.uploaded_items_tree = QTreeWidget()
        self.uploaded_items_tree.setHeaderLabel("Uploaded Files/Folders")
        right_column.addWidget(self.uploaded_items_tree)

        # Save Button
        self.save_button = QPushButton("Save Experiment")
        self.save_button.clicked.connect(self.save_experiment)
        right_column.addWidget(self.save_button)

        # Add Image Folder Upload Button
        self.upload_image_folder_btn = QPushButton("Upload Image Folder", self)
        self.upload_image_folder_btn.clicked.connect(self.upload_image_folder)
        main_layout.addWidget(self.upload_image_folder_btn)

        main_layout.addLayout(right_column)
        self.setLayout(main_layout)

    def upload_image_folder(self):
        """Handle image folder uploads with special processing"""
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            folder_name = os.path.basename(folder)
            dest_folder = os.path.join(self.project_files_folder, folder_name)
            
            # Process folder and get metadata
            folder_metadata = self.process_image_folder(folder, dest_folder)
            
            # Add to uploaded items
            self.uploaded_items.append(folder_metadata)
            
            # Add to tree view with special display
            folder_item = QTreeWidgetItem([f"Image Folder: {folder_name}"])
            for img in folder_metadata["images"]:
                file_item = QTreeWidgetItem([img])
                folder_item.addChild(file_item)
            self.uploaded_items_tree.addTopLevelItem(folder_item)
            
            QMessageBox.information(self, "Success", 
                                  f"Image folder '{folder_name}' uploaded with {len(folder_metadata['images'])} images")
        
    ### Supporting methods ###
    def load_projects(self):
        """Load existing projects into the dropdown."""
        self.project_dropdown.addItem("Select a Project")
        projects = self.metadata.get("Projects", [])
        for project in projects:
            self.project_dropdown.addItem(project["name"])
    
    def load_users(self):
        """Load existing users into the multi-selection list."""
        users = self.metadata.get("Users", [])
        for user in users:
            item = QListWidgetItem(user["name"])
            item.setCheckState(Qt.Unchecked)
            self.users_list.addItem(item)
    
    def load_prototypes(self):
        """Load existing prototypes into the multi-selection list."""
        prototypes = self.metadata.get("Prototypes", [])
        for prototype in prototypes:
            item = QListWidgetItem(prototype["name"])
            item.setCheckState(Qt.Unchecked)
            self.prototypes_list.addItem(item)
            
    def process_folder(self, source_folder, dest_folder):
        """Recursively copy a folder and its contents while preserving the structure."""
        folder_metadata = {"name": os.path.basename(source_folder), "children": []}
        os.makedirs(dest_folder, exist_ok=True)
    
        for entry in os.listdir(source_folder):
            source_entry_path = os.path.join(source_folder, entry)
            dest_entry_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(source_entry_path):
                # Process subfolders recursively
                subfolder_metadata = self.process_folder(source_entry_path, dest_entry_path)
                folder_metadata["children"].append(subfolder_metadata)
            else:
                # Process files
                shutil.copy(source_entry_path, dest_entry_path)
                folder_metadata["children"].append({"name": entry, "path": dest_entry_path})
    
        return folder_metadata

    def process_image_folder(self, source_folder, dest_folder):
        """Special processing for image folders"""
        folder_metadata = {
            "name": os.path.basename(source_folder),
            "type": "image_folder",
            "images": [],
            "children": []
        }
        
        os.makedirs(dest_folder, exist_ok=True)
        
        for entry in os.listdir(source_folder):
            source_path = os.path.join(source_folder, entry)
            dest_path = os.path.join(dest_folder, entry)
            
            if os.path.isdir(source_path):
                # Process subdirectories recursively
                sub_metadata = self.process_image_folder(source_path, dest_path)
                folder_metadata["children"].append(sub_metadata)
            elif is_image_file(entry):
                # Copy image file and record metadata
                shutil.copy(source_path, dest_path)
                folder_metadata["images"].append(entry)
        
        return folder_metadata


    def display_project_tree(self):
        """Display the tree structure of the selected project."""
        self.project_tree_widget.clear()  # Clear previous nodes
        # print('Entering DIsplay project tree')
    
        # Get the selected project
        project_name = self.project_dropdown.currentText()
        project = next((p for p in self.metadata.get("Projects", []) if p["name"] == project_name), None)
    
        if project and "versions" in project:
            # Get the latest version key
            latest_version_key = str(max(map(int, project["versions"].keys())))
            latest_version = project["versions"].get(latest_version_key, {})
            # print('Latest Project vesion: ', latest_version)
            
            # Check if the tree_structure exists in the latest version
            tree_structure = latest_version.get("tree_structure", [])
            # print(tree_structure)
            if tree_structure:
                # Populate the tree structure
                self.add_tree_nodes(self.project_tree_widget, tree_structure)
            else:
                QMessageBox.warning(self, "Tree Structure Missing", f"Tree structure not found in the latest version of project: {project_name}")
        else:
            QMessageBox.warning(self, "Project Not Found", f"Project '{project_name}' not found in metadata.")
    
    def add_tree_nodes(self, parent, nodes):
        """Recursively add nodes to the tree widget."""
        for node in nodes:
            item = QTreeWidgetItem([node["name"]])
            parent.addTopLevelItem(item) if isinstance(parent, QTreeWidget) else parent.addChild(item)
            if "children" in node:
                self.add_tree_nodes(item, node["children"])

                
    def node_selected(self, item):
        """Track the selected node in the project tree."""
        self.selected_node = item.text(0)  # Get the name of the selected node
        print(f"Node selected: {self.selected_node}")  # Debugging

    ### File and Folder Upload ###
    def upload_files(self):
        """Upload files and copy them to the experiment files folder."""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            for file in files:
                file_name = os.path.basename(file)
                dest_path = os.path.join(self.experiment_files_folder, file_name)
                shutil.copy(file, dest_path)

                # Update metadata
                self.uploaded_items.append({"name": file_name, "path": dest_path})

                # Add to display tree
                file_item = QTreeWidgetItem([f"File: {file_name}"])
                file_item.setToolTip(0, dest_path)
                self.uploaded_items_tree.addTopLevelItem(file_item)

            QMessageBox.information(self, "Files Uploaded", "Files have been uploaded successfully.")
    
    def upload_folder(self):
        """Upload a folder and preserve its hierarchy."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            folder_name = os.path.basename(folder)
            dest_folder = os.path.join(self.experiment_files_folder, folder_name)
    
            # Use process_folder to copy the folder and generate metadata
            folder_metadata = self.process_folder(folder, dest_folder)
    
            # Update metadata
            self.uploaded_items.append({"name": folder_name, "children": folder_metadata["children"]})
    
            # Add to display tree
            folder_item = QTreeWidgetItem([f"Folder: {folder_name}"])
            self.add_folder_to_tree(folder_item, folder_metadata["children"])
            self.uploaded_items_tree.addTopLevelItem(folder_item)
    
            QMessageBox.information(self, "Folder Uploaded", f"Folder '{folder_name}' has been uploaded.")

    def copy_folder_contents(self, source_folder, dest_folder):
        """Recursively copy folder and its contents while preserving structure."""
        folder_metadata = {"name": os.path.basename(source_folder), "children": []}
        os.makedirs(dest_folder, exist_ok=True)
    
        for entry in os.listdir(source_folder):
            entry_path = os.path.join(source_folder, entry)
            dest_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(entry_path):
                # Process subfolders recursively
                subfolder_metadata = self.copy_folder_contents(entry_path, dest_path)
                folder_metadata["children"].append(subfolder_metadata)
            else:
                # Process files
                shutil.copy(entry_path, dest_path)
                folder_metadata["children"].append({"name": entry, "path": dest_path})
    
        return folder_metadata


    def add_folder_to_tree(self, parent_item, children):
        """Recursively add folder and file structure to the tree widget."""
        for child in children:
            if isinstance(child, dict):  # Ensure child is a dictionary
                if "children" in child:  # It's a folder
                    folder_item = QTreeWidgetItem([child["name"]])
                    self.add_folder_to_tree(folder_item, child["children"])  # Recurse into folder
                    parent_item.addChild(folder_item)
                elif "path" in child:  # It's a file
                    file_item = QTreeWidgetItem([child["name"]])
                    file_item.setToolTip(0, child["path"])  # Set path as tooltip
                    parent_item.addChild(file_item)
            else:
                print(f"Unexpected child format: {child}")  # Debugging


    ### Save Experiment ###
    def save_experiment(self):
        """Save experiment metadata to the JSON file."""
        experiment_name = self.name_input.text().strip()
        if not experiment_name:
            QMessageBox.critical(self, "Error", "Experiment name cannot be empty.")
            return
    
        description = self.description_input.toPlainText().strip()
        associated_project = self.project_dropdown.currentText()
        if not self.selected_node:
            QMessageBox.warning(self, "Node Selection Missing", "Please select a node in the project tree.")
            return
        
        # Save the selected node in the metadata
        selected_node = self.selected_node
        print(f"Saving with selected node: {selected_node}")

        selected_users = [
            self.users_list.item(i).data(Qt.UserRole)["name"]
            for i in range(self.users_list.count())
            if self.users_list.item(i).checkState() == Qt.Checked
        ]
        selected_prototypes = [
            self.prototypes_list.item(i).data(Qt.UserRole)["name"]
            for i in range(self.prototypes_list.count())
            if self.prototypes_list.item(i).checkState() == Qt.Checked
        ]
        selected_category = self.type_dropdown.currentText()  # Corrected this line
        start_date = self.start_date_picker.date().toString("yyyy-MM-dd")
        end_date = self.end_date_picker.date().toString("yyyy-MM-dd")
    
        # Prompt for a version summary
        version_summary, ok = QInputDialog.getText(self, "Version Summary", "Enter a summary for this version:")
        if not ok or not version_summary:
            QMessageBox.warning(self, "Version Summary Required", "You must provide a summary for this version.")
            return
    
        version_data = {
            "description": description,
            "associated_project": associated_project,
            "associated_node": selected_node,  # Save selected node
            "associated_users": selected_users, #Jagdish
            "associated_prototypes": selected_prototypes, #Jagdish
            "category": selected_category,
            "start_date": start_date,
            "end_date": end_date,
            "uploaded_items": self.uploaded_items,
            "version_summary": version_summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        }
    
        # Save to metadata
        experiment = next((p for p in self.metadata.get("Experiments", []) if p["name"] == experiment_name), None)
        if experiment:
            versions = experiment.setdefault("versions", {})
            versions[str(len(versions) + 1)] = version_data
        else:
            self.metadata.setdefault("Experiments", []).append({
                "name": experiment_name,
                "versions": {"1": version_data}
            })
    
        # Save metadata
        with open(os.path.join(self.base_folder, "metadata.json"), "w") as f:
            json.dump(self.metadata, f, indent=4)
    
        QMessageBox.information(self, "Experiment Saved", "Experiment created successfully.")
        self.accept()
    
        def process_folder(self, source_folder, dest_folder):
            """Recursively copy a folder and its contents while preserving the structure."""
            folder_metadata = {"name": os.path.basename(source_folder), "children": []}
            os.makedirs(dest_folder, exist_ok=True)
        
            for entry in os.listdir(source_folder):
                entry_path = os.path.join(source_folder, entry)
                dest_path = os.path.join(dest_folder, entry)
        
                if os.path.isdir(entry_path):
                    # Process subfolders recursively
                    subfolder_metadata = self.process_folder(entry_path, dest_path)
                    folder_metadata["children"].append(subfolder_metadata)
                else:
                    # Process files
                    shutil.copy(entry_path, dest_path)
                    folder_metadata["children"].append({"name": entry, "path": dest_path})
        
            return folder_metadata

class BrowseExperimentsDialog(QDialog):
    """Dialog for browsing and selecting experiments and their versions."""
    def __init__(self, base_folder, metadata):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.selected_experiment = None
        self.selected_version = None
        self.init_ui()

    def init_ui(self):
        """Set up the UI for browsing experiments."""
        self.setWindowTitle("Browse Experiments")
        
        # Main Layout
        main_layout = QHBoxLayout()  # Two-column layout
        
        # Left Column Layout (Filters and Tree)
        left_column = QVBoxLayout()
        
        # Filter Section
        filter_layout = QFormLayout()
        
        # Project Filter
        self.project_filter_label = QLabel("Select Project:")
        self.project_filter = QComboBox()
        self.project_filter.addItem("Select a Project")
        self.project_filter.addItems([project["name"] for project in self.metadata.get("Projects", [])])
        self.project_filter.currentIndexChanged.connect(self.load_project_nodes)  # Load tree nodes on project selection
        filter_layout.addRow(self.project_filter_label, self.project_filter)
        
        # Project Tree View
        self.project_tree_label = QLabel("Select Node in Project:")
        self.project_tree_widget = QTreeWidget()
        self.project_tree_widget.setHeaderLabel("Project Structure")
        self.project_tree_widget.itemClicked.connect(self.node_selected)  # Track node selection
        filter_layout.addRow(self.project_tree_label, self.project_tree_widget)
        
        # Prototype Filter
        self.prototype_filter = QComboBox()
        self.prototype_filter.addItem("All Prototypes")
        self.prototype_filter.addItems([prototype["name"] for prototype in self.metadata.get("Prototypes", [])])
        filter_layout.addRow("Filter by Prototype:", self.prototype_filter)
        
        # User Filter
        self.user_filter = QComboBox()
        self.user_filter.addItem("All Users")
        self.user_filter.addItems([user["name"] for user in self.metadata.get("Users", [])])
        filter_layout.addRow("Filter by User:", self.user_filter)
        
        # Experiment Type Filter
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        self.type_filter.addItems(["Prototype: Pre-assembly", "Prototype: Inspection", "Prototype: Full system", "Non-prototype"])
        filter_layout.addRow("Filter by Type:", self.type_filter)
        
        # Date Filters
        self.date_filter_checkbox = QCheckBox("Enable Date Filtering")
        self.date_filter_checkbox.setChecked(False)  # Default is unchecked
        filter_layout.addRow(self.date_filter_checkbox)
        
        self.start_date_filter = QDateEdit()
        self.start_date_filter.setCalendarPopup(True)
        self.start_date_filter.setDate(QDate.currentDate())
        self.start_date_filter.setEnabled(False)
        filter_layout.addRow("Start Date:", self.start_date_filter)
        
        self.end_date_filter = QDateEdit()
        self.end_date_filter.setCalendarPopup(True)
        self.end_date_filter.setDate(QDate.currentDate())
        self.end_date_filter.setEnabled(False)
        filter_layout.addRow("End Date:", self.end_date_filter)
        
        # Enable/Disable date filters based on checkbox state
        self.date_filter_checkbox.stateChanged.connect(self.toggle_date_filters)
        
        left_column.addLayout(filter_layout)
        
        # Filter and Reset Buttons
        button_layout = QHBoxLayout()
        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.apply_filter)
        button_layout.addWidget(self.apply_filter_button)
        
        self.reset_filter_button = QPushButton("Reset Filters")
        self.reset_filter_button.clicked.connect(self.reset_filters)
        button_layout.addWidget(self.reset_filter_button)
        
        left_column.addLayout(button_layout)
        
        main_layout.addLayout(left_column)  # Add left column to the main layout
        
        # Right Column Layout (Experiments Table)
        right_column = QVBoxLayout()
        
        # Table to display experiments
        self.experiments_table = QTableWidget(0, 3)
        self.experiments_table.setHorizontalHeaderLabels(["Experiment Name", "Latest Version", "Version Summary"])
        self.experiments_table.horizontalHeader().setStretchLastSection(True)
        right_column.addWidget(self.experiments_table)
        
        self.load_experiments()  # Load all experiments by default
        self.experiments_table.cellClicked.connect(self.row_selected)
        
        self.open_button = QPushButton("Open Selected Experiments Version")
        self.open_button.clicked.connect(self.open_selected_experiment)
        right_column.addWidget(self.open_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        right_column.addWidget(close_button)
        
        main_layout.addLayout(right_column)  # Add right column to the main layout
        
        self.setLayout(main_layout)


    
    def load_projects(self):
        """Load projects and their tree structures into the tree widget."""
        self.project_tree_widget.clear()
        for project in self.metadata.get("Projects", []):
            latest_version_key = str(max(map(int, project["versions"].keys())))
            latest_version = project["versions"][latest_version_key]
    
            if "tree_structure" in latest_version:
                project_item = QTreeWidgetItem([project["name"]])
                self.add_tree_items(project_item, latest_version["tree_structure"])
                self.project_tree_widget.addTopLevelItem(project_item)


    def add_tree_items(self, parent, children):
        """Add nodes to the project tree."""
        for child in children:
            node_item = QTreeWidgetItem([child["name"]])
            parent.addChild(node_item)
            self.add_tree_items(node_item, child.get("children", []))

    def node_selected(self, item, column):
        """Track the selected project node."""
        self.selected_node = item.text(0)
        print(f"Node selected: {self.selected_node}")

    def toggle_date_filters(self, state):
        """Enable or disable date filters based on checkbox state."""
        self.start_date_filter.setEnabled(state == Qt.Checked)
        self.end_date_filter.setEnabled(state == Qt.Checked)
    
    def load_project_nodes(self):
        """Load the tree structure of the selected project."""
        self.project_tree_widget.clear()  # Clear the tree view
        selected_project = self.project_filter.currentText()
    
        # Skip if no valid project is selected
        if selected_project == "Select a Project":
            return
    
        # Find the selected project in metadata
        project = next((p for p in self.metadata.get("Projects", []) if p["name"] == selected_project), None)
        if not project:
            return
    
        # Load the latest version's tree structure
        latest_version_key = str(max(map(int, project["versions"].keys())))
        latest_version = project["versions"][latest_version_key]
        tree_structure = latest_version.get("tree_structure", [])
    
        # Populate the tree widget
        for root in tree_structure:
            root_item = QTreeWidgetItem([root["name"]])
            self.add_tree_items(root_item, root.get("children", []))
            self.project_tree_widget.addTopLevelItem(root_item)


    def reset_filters(self):
        """Reset all filters and display all experiments."""
        self.project_filter.setCurrentIndex(0)
        self.prototype_filter.setCurrentIndex(0)
        self.user_filter.setCurrentIndex(0)
        self.type_filter.setCurrentIndex(0)
        self.date_filter_checkbox.setChecked(False)
        self.load_experiments()  # Load all experiments without filtering

    def load_experiments(self, filter_params=None):
        """Load experiments and their latest versions into the table."""
        self.experiments_table.setRowCount(0)  # Clear the table
    
        # Iterate through experiments in metadata
        for experiment in self.metadata.get("Experiments", []):
            # Get the latest version key and metadata
            latest_version_key = str(max(map(int, experiment["versions"].keys())))
            latest_version = experiment["versions"][latest_version_key]
    
            # Apply filters
            if filter_params:
                # Check project
                if filter_params.get("project") and filter_params["project"] != latest_version.get("associated_project"):
                    continue
                
                # Check node
                if filter_params.get("node") and filter_params["node"] != latest_version.get("associated_node"):
                    continue
    
                # Check prototypes
                if filter_params.get("prototypes"):
                    associated_prototypes = set(latest_version.get("associated_prototypes", [])) #Jagdish
                    if not associated_prototypes.intersection(set(filter_params["prototypes"])):
                        continue
    
                # Check users
                if filter_params.get("users"):
                    associated_users = set(latest_version.get("associated_users", [])) #Jagdish
                    if not associated_users.intersection(set(filter_params["users"])):
                        continue
    
                # Check type
                if filter_params.get("type") and filter_params["type"] != latest_version.get("category"):
                    continue
    
                # Check dates
                if filter_params.get("start_date"):
                    experiment_start_date = QDate.fromString(latest_version.get("start_date", ""), "yyyy-MM-dd")
                    if experiment_start_date < filter_params["start_date"]:
                        continue
    
                if filter_params.get("end_date"):
                    experiment_end_date = QDate.fromString(latest_version.get("end_date", ""), "yyyy-MM-dd")
                    if experiment_end_date > filter_params["end_date"]:
                        continue
    
            # Add experiment to the table
            row = self.experiments_table.rowCount()
            self.experiments_table.insertRow(row)
    
            # Experiment Name
            self.experiments_table.setItem(row, 0, QTableWidgetItem(experiment["name"]))
    
            # Version Dropdown
            version_dropdown = QComboBox()
            version_dropdown.addItems(sorted(experiment["versions"].keys(), key=int, reverse=True))
            version_dropdown.setCurrentText(latest_version_key)
            version_dropdown.currentIndexChanged.connect(lambda _, r=row: self.version_selected(r))
            self.experiments_table.setCellWidget(row, 1, version_dropdown)
    
            # Version Summary
            version_summary = latest_version.get("version_summary", "No Summary")
            self.experiments_table.setItem(row, 2, QTableWidgetItem(version_summary))
    
        # Automatically select the first row, if present
        if self.experiments_table.rowCount() > 0:
            self.row_selected(0, 0)  # Select the first row by default

    def apply_filter(self):
        """Apply the filter and display only matching experiments."""
        selected_node = self.project_tree_widget.currentItem().text(0) if self.project_tree_widget.currentItem() else None
        filter_params = {
            "project": self.project_filter.currentText() if self.project_filter.currentIndex() > 0 else None,
            "node": selected_node,
            "prototype": self.prototype_filter.currentText() if self.prototype_filter.currentIndex() > 0 else None,
            "user": self.user_filter.currentText() if self.user_filter.currentIndex() > 0 else None,
            "type": self.type_filter.currentText() if self.type_filter.currentIndex() > 0 else None,
            "start_date": self.start_date_filter.date() if self.date_filter_checkbox.isChecked() else None,
            "end_date": self.end_date_filter.date() if self.date_filter_checkbox.isChecked() else None,
        }
        self.load_experiments(filter_params)


    def load_users(self):
        """Load all users and pre-select the ones associated with this version."""
        selected_users = set(self.latest_version.get("associateed_users", [])) #Jagdish
        for user in self.metadata.get("Users", []):
            checkbox = QCheckBox(user["name"])
            checkbox.setChecked(user["name"] in selected_users)  # Pre-select if already associated
            self.users_checkboxes.append(checkbox)
            self.users_scroll_layout.addWidget(checkbox)

    def load_prototypes(self):
        """Load all prototypes and pre-select the ones associated with this version."""
        selected_prototypes = set(self.latest_version.get("associated_prototypes", [])) #Jagdish
        for prototype in self.metadata.get("Prototypes", []):
            checkbox = QCheckBox(prototype["name"])
            checkbox.setChecked(prototype["name"] in selected_prototypes)  # Pre-select if already associated
            self.prototypes_checkboxes.append(checkbox)
            self.prototypes_scroll_layout.addWidget(checkbox)


    def version_selected(self, row):
        """Handle version selection and update summary."""
        version_dropdown = self.experiments_table.cellWidget(row, 1)
        selected_version = version_dropdown.currentText()
        experiment = self.metadata["Experiments"][row]
        version_summary = experiment["versions"][selected_version].get("version_summary", "No Summary")
        self.experiments_table.setItem(row, 2, QTableWidgetItem(version_summary))

    def row_selected(self, row, column):
        """Handle row selection in the table."""
        if row < 0 or row >= self.experiments_table.rowCount():
            self.selected_experiment = None
            self.selected_version = None
            return

        self.selected_experiment = self.metadata["Experiments"][row]
        version_dropdown = self.experiments_table.cellWidget(row, 1)
        self.selected_version = version_dropdown.currentText() if version_dropdown else None

    def open_selected_experiment(self):
        """Open the selected experiment and version."""
        if not self.selected_experiment or not self.selected_version:
            QMessageBox.warning(self, "No Selection", "Please select an experiment and a version to open.")
            return

        experiment_versions = self.selected_experiment.get("versions", {})
        selected_version_data = experiment_versions.get(self.selected_version)

        if not selected_version_data:
            QMessageBox.critical(self, "Error", f"Version {self.selected_version} not found for experiment {self.selected_experiment['name']}.")
            return

        dialog = EditExperimentDialog(self.base_folder, self.metadata, self.selected_experiment, self.selected_version)
        dialog.exec_()
        self.load_experiments()  # Reload experiments to reflect changes


class EditExperimentDialog(QDialog):
    """Dialog for editing a selected experiment."""
    def __init__(self, base_folder, metadata, experiment, selected_version=None):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.experiment = experiment
        self.selected_version = selected_version or self.get_latest_version()
        self.latest_version = self.experiment["versions"].get(self.selected_version, {})
        
        # Snapshot of the original data for change detection
        self.previous_uploaded_items = json.loads(
            json.dumps(self.latest_version.get("uploaded_items", []))
        )
        self.uploaded_items = copy.deepcopy(self.latest_version.get("uploaded_items", []))
        self.associated_project = self.latest_version.get("associated_project", None)
        self.initial_associated_node = self.latest_version.get("associated_node", None)
        self.selected_node = self.initial_associated_node  # Default to the initially associated node

        self.associated_users = self.latest_version.get("associated_users", [])
        self.associated_prototypes = self.latest_version.get("associated_prototypes", [])
        self.category = self.latest_version.get("category", None)
        self.start_date = self.latest_version.get("start_date", None)
        self.end_date = self.latest_version.get("end_date", None)
        self.temp_files = {}  # Track temporary files for edits
        self.init_ui()

    def get_latest_version(self):
        """Retrieve the latest version of the experiment."""
        versions = self.experiment["versions"]
        return str(max(map(int, versions.keys())))

    def init_ui(self):
        """Set up the UI for editing the experiment."""
        self.setWindowTitle(f"Edit Experiment - {self.experiment['name']} (Version {self.selected_version})")
        
        # Main Layout
        main_layout = QHBoxLayout()  # Horizontal layout for three sections
        
        # First Column Layout (Details and Project)
        first_column = QVBoxLayout()
        
        # Experiment Description
        self.description_label = QLabel("Experiment Description:")
        first_column.addWidget(self.description_label)
        self.description_input = QTextEdit(self.latest_version.get("description", ""))
        first_column.addWidget(self.description_input)
        
        # Project Dropdown with Search Box
        self.project_label = QLabel("Associated Project:")
        first_column.addWidget(self.project_label)
    
        self.project_search = QLineEdit()
        self.project_search.setPlaceholderText("Search Project...")
        self.project_search.textChanged.connect(self.filter_projects)
        first_column.addWidget(self.project_search)
    
        self.project_dropdown = QComboBox()
        self.all_projects = [project["name"] for project in self.metadata.get("Projects", [])]
        self.project_dropdown.addItems(self.all_projects)
        if self.latest_version.get("associated_project"):
            self.project_dropdown.setCurrentText(self.latest_version["associated_project"])
        self.project_dropdown.currentIndexChanged.connect(self.display_project_tree)
        first_column.addWidget(self.project_dropdown)
        
        # Project Tree View
        self.project_tree_label = QLabel("Project Tree Structure:")
        first_column.addWidget(self.project_tree_label)
    
        self.project_tree_widget = QTreeWidget()
        self.project_tree_widget.setHeaderLabel("Project Nodes")
        self.project_tree_widget.itemClicked.connect(self.node_selected)  # Track node selection
        first_column.addWidget(self.project_tree_widget)
    
        # Initial Display of the Project Tree
        self.display_project_tree()
        
        # Start and End Dates
        self.start_date_label = QLabel("Start Date:")
        first_column.addWidget(self.start_date_label)
        self.start_date_picker = QDateEdit()
        self.start_date_picker.setCalendarPopup(True)
        self.start_date_picker.setDate(QDate.fromString(self.latest_version.get("start_date", QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
        first_column.addWidget(self.start_date_picker)
    
        self.end_date_label = QLabel("End Date:")
        first_column.addWidget(self.end_date_label)
        self.end_date_picker = QDateEdit()
        self.end_date_picker.setCalendarPopup(True)
        self.end_date_picker.setDate(QDate.fromString(self.latest_version.get("end_date", QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
        first_column.addWidget(self.end_date_picker)
    
        main_layout.addLayout(first_column)  # Add the first column to the main layout
        
        # Second Column Layout (Prototypes and Users)
        second_column = QVBoxLayout()
    
        # Prototypes Section
        self.prototypes_label = QLabel("Associated Prototypes:")
        second_column.addWidget(self.prototypes_label)
    
        self.prototypes_search = QLineEdit()
        self.prototypes_search.setPlaceholderText("Search Prototypes...")
        self.prototypes_search.textChanged.connect(self.filter_prototypes)
        second_column.addWidget(self.prototypes_search)
    
        self.prototypes_scroll_area = QScrollArea()
        self.prototypes_scroll_area.setWidgetResizable(True)
        self.prototypes_widget = QWidget()
        self.prototypes_layout = QVBoxLayout(self.prototypes_widget)
    
        associated_prototypes = set(self.latest_version.get("associated_prototypes", []))
        self.prototypes_checkboxes = []
        for prototype in self.metadata.get("Prototypes", []):
            checkbox = QCheckBox(prototype["name"])
            checkbox.setChecked(prototype["name"] in associated_prototypes)
            self.prototypes_checkboxes.append(checkbox)
            self.prototypes_layout.addWidget(checkbox)
    
        self.prototypes_scroll_area.setWidget(self.prototypes_widget)
        second_column.addWidget(self.prototypes_scroll_area)
    
        # Users Section
        self.users_label = QLabel("Associated Users:")
        second_column.addWidget(self.users_label)
    
        self.users_search = QLineEdit()
        self.users_search.setPlaceholderText("Search Users...")
        self.users_search.textChanged.connect(self.filter_users)
        second_column.addWidget(self.users_search)
    
        self.users_scroll_area = QScrollArea()
        self.users_scroll_area.setWidgetResizable(True)
        self.users_widget = QWidget()
        self.users_layout = QVBoxLayout(self.users_widget)
    
        associated_users = set(self.latest_version.get("associated_users", []))
        self.users_checkboxes = []
        for user in self.metadata.get("Users", []):
            checkbox = QCheckBox(user["name"])
            checkbox.setChecked(user["name"] in associated_users)
            self.users_checkboxes.append(checkbox)
            self.users_layout.addWidget(checkbox)
    
        self.users_scroll_area.setWidget(self.users_widget)
        second_column.addWidget(self.users_scroll_area)
    
        # Category Dropdown
        self.category_label = QLabel("Experiment Type:")
        second_column.addWidget(self.category_label)
        self.category_dropdown = QComboBox()
        categories = ["Prototype: Pre-assembly", "Prototype: Inspection", "Prototype: Full system", "Non-prototype"]
        self.category_dropdown.addItems(categories)
        if self.latest_version.get("category"):
            self.category_dropdown.setCurrentText(self.latest_version["category"])
        second_column.addWidget(self.category_dropdown)
    
        main_layout.addLayout(second_column)  # Add the second column to the main layout
    
        # Third Column Layout (Files and Folders)
        third_column = QVBoxLayout()
    
        # Uploaded Files and Folders
        self.files_label = QLabel("Uploaded Files and Folders:")
        third_column.addWidget(self.files_label)
        self.files_tree_widget = QTreeWidget()
        self.files_tree_widget.setHeaderLabel("Uploaded Items")
        self.load_uploaded_items(self.uploaded_items)
        self.files_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.files_tree_widget.customContextMenuRequested.connect(self.show_file_context_menu)
        third_column.addWidget(self.files_tree_widget)
    
        # Save Changes Button
        save_layout = QVBoxLayout()
        self.upload_file_button = QPushButton("Add Files")
        self.upload_file_button.clicked.connect(self.upload_files)
        save_layout.addWidget(self.upload_file_button)
    
        self.upload_folder_button = QPushButton("Add Folder")
        self.upload_folder_button.clicked.connect(self.upload_folder)
        save_layout.addWidget(self.upload_folder_button)
    
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        save_layout.addWidget(self.save_button)
    
        third_column.addLayout(save_layout)
        main_layout.addLayout(third_column)  # Add the third column to the main layout
    
        self.setLayout(main_layout)


    def display_project_tree(self):
        """Display the tree structure of the currently selected project."""
        self.project_tree_widget.clear()  # Clear the current tree view
    
        # Get the selected project name
        selected_project_name = self.project_dropdown.currentText()
    
        # Find the metadata for the selected project
        selected_project = next(
            (project for project in self.metadata.get("Projects", [])
             if project["name"] == selected_project_name), None)
    
        if not selected_project:
            return  # No project selected or project not found
    
        # Get the latest version of the selected project
        latest_version_key = str(max(map(int, selected_project["versions"].keys())))
        latest_version = selected_project["versions"][latest_version_key]
    
        # Get the tree structure from the latest version
        tree_structure = latest_version.get("tree_structure", [])
    
        # Populate the tree widget
        def add_items(parent, children):
            for child in children:
                item = QTreeWidgetItem([child["name"]])
                parent.addChild(item)
                add_items(item, child.get("children", []))
    
        for root in tree_structure:
            root_item = QTreeWidgetItem([root["name"]])
            self.project_tree_widget.addTopLevelItem(root_item)
            add_items(root_item, root.get("children", []))
    
        # Highlight the associated node, if any
        associated_node = self.latest_version.get("associated_node")
        if associated_node:
            self.highlight_node(self.project_tree_widget, associated_node)
    
    def highlight_node(self, tree_widget, node_name):
        """Highlight the specified node in the tree widget."""
        def search_and_highlight(item):
            if item.text(0) == node_name:
                tree_widget.setCurrentItem(item)  # Highlight the item
                item.setSelected(True)
                tree_widget.scrollToItem(item)  # Ensure it is visible
                return True
            for i in range(item.childCount()):
                if search_and_highlight(item.child(i)):
                    return True
            return False
    
        for i in range(tree_widget.topLevelItemCount()):
            top_level_item = tree_widget.topLevelItem(i)
            if search_and_highlight(top_level_item):
                break
    
    def node_selected(self, item, column):
        """Track the selected node in the project tree."""
        self.selected_node = item.text(0)  # Store the name of the selected node
        print(f"Selected Node: {self.selected_node}")
    
        
    def filter_projects(self, query):
        """Filter the projects in the dropdown based on the search query."""
        query = query.lower()
        self.project_dropdown.clear()
        filtered_projects = [project for project in self.all_projects if query in project.lower()]
        self.project_dropdown.addItems(filtered_projects)

    
    def filter_prototypes(self, query):
        """Filter the prototype checkboxes based on the search query."""
        query = query.lower()
        for checkbox in self.prototypes_checkboxes:
            checkbox.setVisible(query in checkbox.text().lower())
    
    def filter_users(self, query):
        """Filter the user checkboxes based on the search query."""
        query = query.lower()
        for checkbox in self.users_checkboxes:
            checkbox.setVisible(query in checkbox.text().lower())
                
    # ---- Tree Structure Methods ----

    def show_tree_context_menu(self, position):
        """Show context menu for the project tree structure."""
        item = self.tree_widget.itemAt(position)
        menu = QMenu(self)

        add_action = menu.addAction("Add Child")
        edit_action = menu.addAction("Edit Node")
        delete_action = menu.addAction("Delete Node")

        add_action.triggered.connect(lambda: self.add_child(item))
        edit_action.triggered.connect(lambda: self.edit_node(item))
        delete_action.triggered.connect(lambda: self.delete_node(item))

        menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    # ---- File/Folder Context Menu ----
    def get_tree_structure(self):
        """Convert the tree widget into a dictionary format."""
        def item_to_dict(item):
            return {"name": item.text(0), "children": [item_to_dict(item.child(i)) for i in range(item.childCount())]}

        return [item_to_dict(self.tree_widget.topLevelItem(i)) for i in range(self.tree_widget.topLevelItemCount())]
    
    def show_file_context_menu(self, position):
        """Show context menu for files and folders."""
        item = self.files_tree_widget.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        # Add "Edit" and "Delete" options to the context menu
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")

        # Assign signals for the options (no functionality assigned yet)
        edit_action.triggered.connect(lambda: self.edit_file_or_folder(item))
        delete_action.triggered.connect(lambda: self.delete_file_or_folder(item))

        menu.exec_(self.files_tree_widget.viewport().mapToGlobal(position))
    
    def edit_file_or_folder(self, item):
        """Edit the selected file or folder."""
        if item.childCount() == 0:  # File
            print(f"Editing file: {item.text(0)}")
            self.open_file_as_temp(item, 0)  # Open file as a temporary copy for editing
        else:  # Folder
            print(f"Editing folder: {item.text(0)}")
            self.upload_folder_to_selected_folder(item)  # Add new folder to this folder

    
    def get_folder_metadata(self, tree_item):
        """Retrieve metadata for the selected folder."""
        def traverse_metadata(metadata_list, target_name):
            for entry in metadata_list:
                if entry["name"] == target_name:
                    return entry
                if "children" in entry:
                    result = traverse_metadata(entry["children"], target_name)
                    if result:
                        return result
            return None
    
        folder_path = []
        while tree_item:
            folder_path.insert(0, tree_item.text(0))
            tree_item = tree_item.parent()
    
        current_metadata = self.uploaded_items
        for part in folder_path:
            current_metadata = traverse_metadata(current_metadata, part)
    
        return current_metadata

    def add_folder_to_tree(self, parent_item, children):
        """Recursively add a folder and its contents to the tree widget."""
        for child in children:
            if "children" in child:  # Folder
                folder_item = QTreeWidgetItem([child["name"]])
                self.add_folder_to_tree(folder_item, child["children"])
                parent_item.addChild(folder_item)
            elif "path" in child:  # File
                file_item = QTreeWidgetItem([child["name"]])
                file_item.setToolTip(0, child["path"])
                parent_item.addChild(file_item)


    def delete_file_or_folder(self, item):
        """Delete the selected file or folder."""
        if not item:
            QMessageBox.warning(self, "Error", "No item selected to delete.")
            return
    
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion", f"Are you sure you want to delete '{item.text(0)}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
    
        # Perform deletion but defer saving until save_changes()
        def remove_from_metadata(metadata_list, target_name):
            """Recursively remove the target from metadata."""
            for index, entry in enumerate(metadata_list):
                if entry["name"] == target_name:
                    del metadata_list[index]
                    return True
                if "children" in entry:
                    if remove_from_metadata(entry["children"], target_name):
                        return True
            return False
    
        # Remove the selected item from metadata
        target_name = item.text(0)
        removed = remove_from_metadata(self.uploaded_items, target_name)
    
        if removed:
            # Update the tree view without saving
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.files_tree_widget.indexOfTopLevelItem(item)
                self.files_tree_widget.takeTopLevelItem(index)
    
            print(f"Deleted: {target_name}. Changes deferred to save_changes().")
        else:
            QMessageBox.warning(self, "Error", f"Could not find '{target_name}' in the metadata.")

     # ---- Tree Structure Methods ----
    
    def load_tree_structure(self, tree_structure):
         """Load the experiment tree structure into the widget."""
         def add_items(parent, children):
             for child in children:
                 item = QTreeWidgetItem([child["name"]])
                 add_items(item, child.get("children", []))
                 parent.addChild(item)
    
         self.tree_widget.clear()
         for root in tree_structure:
             root_item = QTreeWidgetItem([root["name"]])
             add_items(root_item, root.get("children", []))
             self.tree_widget.addTopLevelItem(root_item)
    
    
     # ---- Uploaded Items ----
    
    def load_uploaded_items(self, uploaded_items):
         """Load uploaded files and folders into the tree widget."""
         def add_items(parent, children):
             for child in children:
                 if "children" in child:  # Folder
                     folder_item = QTreeWidgetItem([child["name"]])
                     add_items(folder_item, child["children"])
                     parent.addChild(folder_item)
                 elif "path" in child:  # File
                     file_item = QTreeWidgetItem([child["name"]])
                     file_item.setToolTip(0, child["path"])
                     parent.addChild(file_item)
    
         self.files_tree_widget.clear()
         for item in uploaded_items:
             if "children" in item:  # Folder
                 folder_item = QTreeWidgetItem([item["name"]])
                 add_items(folder_item, item["children"])
                 self.files_tree_widget.addTopLevelItem(folder_item)
             elif "path" in item:  # File
                 file_item = QTreeWidgetItem([item["name"]])
                 file_item.setToolTip(0, item["path"])
                 self.files_tree_widget.addTopLevelItem(file_item)
    
    def open_file_as_temp(self, item, column):
         """Open a file as a temporary copy."""
         file_path = item.toolTip(0)
         if not file_path or not os.path.isfile(file_path):
             QMessageBox.warning(self, "Error", "File path is invalid or does not exist.")
             return
    
         try:
             with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[-1]) as temp_file:
                 temp_file_path = temp_file.name
                 shutil.copy(file_path, temp_file_path)
             QDesktopServices.openUrl(QUrl.fromLocalFile(temp_file_path))
             self.temp_files[file_path] = temp_file_path
         except Exception as e:
             QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
    
     # ---- File Uploads and Save ----
     
    def upload_files(self):
         """Upload files and append them to the uploaded items."""
         files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
         if files:
             for file in files:
                 file_name = os.path.basename(file)
                 dest_path = os.path.join(self.base_folder, "Experiment Files", file_name)
                 shutil.copy(file, dest_path)
     
                 # Add the new file to uploaded_items
                 self.uploaded_items.append({"name": file_name, "path": dest_path})
             self.load_uploaded_items(self.uploaded_items)  # Refresh the tree view
    
    
    def upload_folder(self):
         """Upload a folder and append it to the uploaded items."""
         folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
         if folder_path:
             folder_name = os.path.basename(folder_path)
             dest_folder = os.path.join(self.base_folder, "Experiment Files", folder_name)
             folder_metadata = self.scan_folder(folder_path, dest_folder)
     
             # Add the new folder to uploaded_items
             self.uploaded_items.append({"name": folder_name, "children": folder_metadata})
             self.load_uploaded_items(self.uploaded_items)  # Refresh the tree view
    
    def upload_folder_to_selected_folder(self, selected_folder_item):
        """Upload a folder and append its structure to a selected folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            folder_name = os.path.basename(folder_path)
    
            # Get the destination path for the selected folder
            parent_metadata = self.get_folder_metadata(selected_folder_item)
            dest_folder_path = os.path.join(self.base_folder, "Experiment Files", folder_name)
            folder_content = self.scan_folder(folder_path, dest_folder_path)
    
            # Update the metadata of the selected folder
            parent_metadata["children"].append({
                "name": folder_name,
                "children": folder_content
            })
    
            # Add the folder and its contents to the tree widget
            new_folder_item = QTreeWidgetItem([folder_name])
            self.add_folder_to_tree(new_folder_item, folder_content)
            selected_folder_item.addChild(new_folder_item)
    
            print(f"Added folder '{folder_name}' into '{selected_folder_item.text(0)}'.")

    def scan_folder(self, source_folder, dest_folder):
        """Recursively scan a folder, copy its contents, and return its structure."""
        os.makedirs(dest_folder, exist_ok=True)
        children = []
    
        for entry in os.listdir(source_folder):
            source_entry_path = os.path.join(source_folder, entry)
            dest_entry_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(source_entry_path):
                subfolder_metadata = self.scan_folder(source_entry_path, dest_entry_path)
                children.append({"name": entry, "children": subfolder_metadata})
            else:
                shutil.copy(source_entry_path, dest_entry_path)
                children.append({"name": entry, "path": dest_entry_path})
    
        return children

    def save_changes(self):
        """Save changes to the experiment while preserving folder structure and detecting all changes."""
        # Helper functions (compute_file_hash, strip_timestamp, process_uploaded_items, etc.) remain unchanged
    
        def collect_checked_items(checkboxes):
            """Collect items from the checkboxes that are checked."""
            return [checkbox.text().strip() for checkbox in checkboxes if checkbox.isChecked()]

        def compute_file_hash(file_path):
            """Compute SHA256 hash of the file."""
            sha256 = hashlib.sha256()
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        sha256.update(chunk)
                return sha256.hexdigest()
            except Exception as e:
                print(f"Error computing hash for {file_path}: {e}")
                return None

        def collect_tree_items(tree_widget):
            """Collect items from the tree widget into a list."""
            def traverse_tree(item):
                if item.childCount() == 0:  # File
                    return {"name": item.text(0), "path": item.toolTip(0)}
                else:  # Folder
                    return {
                        "name": item.text(0),
                        "children": [traverse_tree(item.child(i)) for i in range(item.childCount())]
                    }
    
            items = []
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                items.append(traverse_tree(item))
            return items

        def process_uploaded_items(previous_items, current_items):
            """Recursively process uploaded items, detect changes, and handle new versions."""
            updated_items = []
            changes_detected = False
    
            # Create a lookup for previous items by name for easy comparison
            prev_lookup = {item["name"]: item for item in previous_items}
    
            for item in current_items:
                if "children" in item:  # Folder
                    previous_folder = prev_lookup.get(item["name"], {}).get("children", [])
                    updated_folder, folder_changes = process_uploaded_items(previous_folder, item["children"])
                    updated_items.append({
                        "name": item["name"],
                        "children": updated_folder
                    })
                    if item["name"] not in prev_lookup:  # New folder
                        print(f"New folder detected: {item['name']}")
                        changes_detected = True
                    changes_detected |= folder_changes
                elif "path" in item:  # File
                    previous_file = prev_lookup.get(item["name"])
                    temp_file_path = self.temp_files.get(item["path"])
    
                    if previous_file is None:  # New file added
                        print(f"New file detected: {item['name']}")
                        updated_items.append(item)
                        changes_detected = True
                    elif temp_file_path:  # File was opened/edited
                        temp_file_hash = compute_file_hash(temp_file_path)
                        original_hash = compute_file_hash(item["path"])
    
                        if original_hash != temp_file_hash:  # File content has changed
                            # Create a new versioned filename
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            original_file_name = strip_timestamp(item["name"])
                            new_file_name = f"{os.path.splitext(original_file_name)[0]}_{timestamp}{os.path.splitext(original_file_name)[1]}"
                            new_file_path = os.path.join(self.base_folder, "Experiment Files", new_file_name)
                            shutil.copy(temp_file_path, new_file_path)
    
                            updated_items.append({
                                "name": new_file_name,
                                "path": new_file_path
                            })
                            print(f"File updated: {new_file_path}")
                            changes_detected = True
                        else:  # File content unchanged
                            updated_items.append(item)
                    else:  # File unchanged
                        updated_items.append(item)
    
            # Detect deleted items
            current_item_names = {item["name"] for item in current_items}
            for item in previous_items:
                if item["name"] not in current_item_names:
                    print(f"Item deleted: {item['name']}")
                    changes_detected = True
    
            return updated_items, changes_detected
    
        # --- Gather New Data ---
        new_description = self.description_input.toPlainText().strip()
        current_project = self.project_dropdown.currentText().strip()
        current_users = sorted(collect_checked_items(self.users_checkboxes))
        current_prototypes = sorted(collect_checked_items(self.prototypes_checkboxes))
        current_category = self.category_dropdown.currentText().strip()
        current_start_date = self.start_date_picker.date().toString("yyyy-MM-dd").strip()
        current_end_date = self.end_date_picker.date().toString("yyyy-MM-dd").strip()
        current_uploaded_items = collect_tree_items(self.files_tree_widget)
    
        # Detect changes in the associated node
        node_changed = self.selected_node != self.initial_associated_node
    
        # Compare previous and current items
        new_uploaded_items, file_changes_detected = process_uploaded_items(self.previous_uploaded_items, current_uploaded_items)
        description_changed = new_description != self.latest_version.get("description", "").strip()
        project_changed = current_project != self.latest_version.get("associated_project", "").strip()
        users_changed = sorted(self.latest_version.get("associated_users", [])) != current_users
        prototypes_changed = sorted(self.latest_version.get("associated_prototypes", [])) != current_prototypes
        category_changed = current_category != self.latest_version.get("category", "").strip()
        start_date_changed = current_start_date != self.latest_version.get("start_date", "").strip()
        end_date_changed = current_end_date != self.latest_version.get("end_date", "").strip()
    
        # Detect overall changes
        changes_detected = (
            file_changes_detected or
            description_changed or
            project_changed or
            users_changed or
            prototypes_changed or
            category_changed or
            start_date_changed or
            end_date_changed or
            node_changed
        )
    
        if not changes_detected:
            QMessageBox.information(self, "No Changes", "No changes detected. Nothing to save.")
            return
    
        # --- Prompt for Version Summary ---
        version_summary, ok = QInputDialog.getText(self, "Version Summary", "Enter a summary for this version:")
        if not ok or not version_summary:
            QMessageBox.warning(self, "Version Summary Required", "You must provide a summary for the new version.")
            return
    
        # --- Prepare New Version Data ---
        new_version_data = {
            "description": new_description,
            "uploaded_items": new_uploaded_items,
            "associated_project": current_project,
            "associated_node": self.selected_node,  # Save the selected node
            "associated_users": current_users,
            "associated_prototypes": current_prototypes,
            "category": current_category,
            "start_date": current_start_date,
            "end_date": current_end_date,
            "version_summary": version_summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        }
    
        # --- Save the New Version ---
        versions = self.experiment.setdefault("versions", {})
        new_version_number = str(len(versions) + 1)
        versions[new_version_number] = new_version_data
    
        # Save updated metadata
        metadata_path = os.path.join(self.base_folder, "metadata.json")
        try:
            with open(metadata_path, "w") as f:
                json.dump(self.metadata, f, indent=4)
            QMessageBox.information(self, "Saved", f"Experiment changes saved successfully as version {new_version_number}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save metadata: {e}")
    
        # Cleanup temporary files
        self.cleanup_temp_files()
        self.accept()


 
    def cleanup_temp_files(self):
        """Delete temporary files created for editing."""
        for temp_file in self.temp_files.values():
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"Temporary file deleted: {temp_file}")
            except Exception as e:
                print(f"Error deleting temporary file {temp_file}: {e}")
        self.temp_files.clear()



#Create and manage prototypes using the following classes (each corresponding to a separate window)
# PrototypesDialog() - opens a dialog to create or browse prototypes
# CreateProtypeDialog() - allows you to create a new prototype
# BrowsePrototypeDialog() - allows you to view the list of existing prototype. 
#                           It also also allows you to edit a selected prototype
#                           version
# EditPrototypeDialog() - It allows you to edit a selected prototype and save
#                         changes as a new version automatically. 

class PrototypesDialog(QDialog):
    """Main Projects dialog with Create and Browse options."""
    def __init__(self, base_folder):
        super().__init__()
        self.base_folder = base_folder
        self.metadata_path = os.path.join(self.base_folder, "metadata.json")
        self.metadata = self.load_metadata()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Prototypes")
        layout = QVBoxLayout()

        # Create Project Button
        create_button = QPushButton("Create Prototype", self)
        create_button.clicked.connect(self.open_create_prototype_dialog)
        layout.addWidget(create_button)

        # Browse Projects Button
        browse_button = QPushButton("Browse Prototypes", self)
        browse_button.clicked.connect(self.browse_prototypes)
        layout.addWidget(browse_button)

        # Close Button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def load_metadata(self):
        """Load metadata from metadata.json."""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        return {"Projects": [], "Prototypes": [], "Experiments": [], "Users": []}

    def save_metadata(self):
        """Save metadata back to metadata.json."""
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=4)

    def open_create_prototype_dialog(self):
        """Open the Create Prototype dialog."""
        dialog = CreatePrototypeDialog(self.base_folder, self.metadata)
        if dialog.exec_():  # If the dialog is successfully completed
            self.save_metadata()

    def browse_prototypes(self):
        """Open the Browse Projects dialog to view and edit existing prototypes."""
        if not self.metadata.get("Prototypes"):
            QMessageBox.information(self, "No Prototypes", "There are no prototypes to browse.")
            return
    
        # Open the Browse Projects dialog
        dialog = BrowsePrototypesDialog(self.base_folder, self.metadata)
        if dialog.exec_():  # If changes were made
            print('Done browsing')
            # Save updated metadata directly
            self.save_metadata()
            
            # Debugging: Print metadata after returning from the dialog
            print("Updated Metadata After Browsing:")
            print(json.dumps(self.metadata, indent=4))

class CreatePrototypeDialog(QDialog):
    """Dialog for creating a new project."""
    def __init__(self, base_folder, metadata):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.prototype_files_folder = os.path.join(self.base_folder, "Prototype Files")
        os.makedirs(self.prototype_files_folder, exist_ok=True)
        self.uploaded_items = []  # To store uploaded files and folders
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("Create Prototype")
        layout = QVBoxLayout()

        # Prototype Name
        self.name_label = QLabel("Prototype Title:")
        layout.addWidget(self.name_label)
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # Prototype Description
        self.description_label = QLabel("Prototype Description:")
        layout.addWidget(self.description_label)
        self.description_input = QTextEdit()
        layout.addWidget(self.description_input)

        # File and Folder Upload
        self.upload_files_button = QPushButton("Upload Files")
        self.upload_files_button.clicked.connect(self.upload_files)
        layout.addWidget(self.upload_files_button)

        self.upload_folder_button = QPushButton("Upload Folder")
        self.upload_folder_button.clicked.connect(self.upload_folder)
        layout.addWidget(self.upload_folder_button)

        # Uploaded Items Display
        self.uploaded_items_tree = QTreeWidget()
        self.uploaded_items_tree.setHeaderLabel("Uploaded Files/Folders")
        layout.addWidget(self.uploaded_items_tree)

        # Save Button
        self.save_button = QPushButton("Save Prototype")
        self.save_button.clicked.connect(self.save_prototype)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    ### File and Folder Upload ###
    def upload_files(self):
        """Upload files and copy them to the prototype files folder."""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            for file in files:
                file_name = os.path.basename(file)
                dest_path = os.path.join(self.prototype_files_folder, file_name)
                shutil.copy(file, dest_path)

                # Update metadata
                self.uploaded_items.append({"name": file_name, "path": dest_path})

                # Add to display tree
                file_item = QTreeWidgetItem([f"File: {file_name}"])
                file_item.setToolTip(0, dest_path)
                self.uploaded_items_tree.addTopLevelItem(file_item)

            QMessageBox.information(self, "Files Uploaded", "Files have been uploaded successfully.")
    
    def upload_folder(self):
        """Upload a folder and preserve its hierarchy."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            folder_name = os.path.basename(folder)
            dest_folder = os.path.join(self.prototype_files_folder, folder_name)
    
            # Use process_folder to copy the folder and generate metadata
            folder_metadata = self.process_folder(folder, dest_folder)
    
            # Update metadata
            self.uploaded_items.append({"name": folder_name, "children": folder_metadata["children"]})
    
            # Add to display tree
            folder_item = QTreeWidgetItem([f"Folder: {folder_name}"])
            self.add_folder_to_tree(folder_item, folder_metadata["children"])
            self.uploaded_items_tree.addTopLevelItem(folder_item)
    
            QMessageBox.information(self, "Folder Uploaded", f"Folder '{folder_name}' has been uploaded.")

    def copy_folder_contents(self, source_folder, dest_folder):
        """Recursively copy folder and its contents while preserving structure."""
        folder_metadata = {"name": os.path.basename(source_folder), "children": []}
        os.makedirs(dest_folder, exist_ok=True)
    
        for entry in os.listdir(source_folder):
            entry_path = os.path.join(source_folder, entry)
            dest_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(entry_path):
                # Process subfolders recursively
                subfolder_metadata = self.copy_folder_contents(entry_path, dest_path)
                folder_metadata["children"].append(subfolder_metadata)
            else:
                # Process files
                shutil.copy(entry_path, dest_path)
                folder_metadata["children"].append({"name": entry, "path": dest_path})
    
        return folder_metadata


    def add_folder_to_tree(self, parent_item, children):
        """Recursively add folder and file structure to the tree widget."""
        for child in children:
            if isinstance(child, dict):  # Ensure child is a dictionary
                if "children" in child:  # It's a folder
                    folder_item = QTreeWidgetItem([child["name"]])
                    self.add_folder_to_tree(folder_item, child["children"])  # Recurse into folder
                    parent_item.addChild(folder_item)
                elif "path" in child:  # It's a file
                    file_item = QTreeWidgetItem([child["name"]])
                    file_item.setToolTip(0, child["path"])  # Set path as tooltip
                    parent_item.addChild(file_item)
            else:
                print(f"Unexpected child format: {child}")  # Debugging


    ### Save Prototype ###
    def save_prototype(self):
        """Save prototype metadata to the JSON file."""
        prototype_name = self.name_input.text().strip()
        if not prototype_name:
            QMessageBox.critical(self, "Error", "Prototype name cannot be empty.")
            return
    
        description = self.description_input.toPlainText().strip()
        # tree_structure = self.get_tree_structure()
    
        # Prompt for a version summary
        version_summary, ok = QInputDialog.getText(self, "Version Summary", "Enter a summary for this version:")
        if not ok or not version_summary:
            QMessageBox.warning(self, "Version Summary Required", "You must provide a summary for this version.")
            return
    
        version_data = {
            "description": description,
            "uploaded_items": self.uploaded_items,
            "version_summary": version_summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        }
    
        # Save to metadata
        prototype = next((p for p in self.metadata.get("Prototypes", []) if p["name"] == prototype_name), None)
        if prototype:
            versions = prototype.setdefault("versions", {})
            versions[str(len(versions) + 1)] = version_data
        else:
            self.metadata.setdefault("Prototypes", []).append({
                "name": prototype_name,
                "versions": {"1": version_data}
            })
    
        # Save metadata
        with open(os.path.join(self.base_folder, "metadata.json"), "w") as f:
            json.dump(self.metadata, f, indent=4)
    
        QMessageBox.information(self, "Prototype Saved", "Prototype created successfully.")
        self.accept()
    
    def process_folder(self, source_folder, dest_folder):
        """Recursively copy a folder and its contents while preserving the structure."""
        folder_metadata = {"name": os.path.basename(source_folder), "children": []}
        os.makedirs(dest_folder, exist_ok=True)
    
        for entry in os.listdir(source_folder):
            entry_path = os.path.join(source_folder, entry)
            dest_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(entry_path):
                # Process subfolders recursively
                subfolder_metadata = self.process_folder(entry_path, dest_path)
                folder_metadata["children"].append(subfolder_metadata)
            else:
                # Process files
                shutil.copy(entry_path, dest_path)
                folder_metadata["children"].append({"name": entry, "path": dest_path})
    
        return folder_metadata

class BrowsePrototypesDialog(QDialog):
    """Dialog for browsing and selecting prototypes and their versions."""
    def __init__(self, base_folder, metadata):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.selected_prototype = None
        self.selected_version = None
        self.init_ui()
    
    def init_ui(self):
        """Set up the UI for browsing prototypes."""
        self.setWindowTitle("Browse Prototypes")
        layout = QVBoxLayout()
    
        # Table to display prototypes, versions, and version summary
        self.prototypes_table = QTableWidget(0, 3)
        self.prototypes_table.setHorizontalHeaderLabels(["Prototype Name", "Latest Version", "Version Summary"])
        self.prototypes_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.prototypes_table)
    
        self.load_prototypes()
        self.prototypes_table.cellClicked.connect(self.row_selected)
    
        self.open_button = QPushButton("Open Selected Prototype Version")
        self.open_button.clicked.connect(self.open_selected_prototype)
        layout.addWidget(self.open_button)
    
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
    
        self.setLayout(layout)
    
    def load_prototypes(self):
        """Load prototypes and their latest versions into the table."""
        self.prototypes_table.setRowCount(0)
        for row, prototype in enumerate(self.metadata.get("Prototypes", [])):
            prototype_name = prototype["name"]
            latest_version = str(max(map(int, prototype["versions"].keys())))
            version_summary = prototype["versions"][latest_version].get("version_summary", "No Summary")
    
            # Populate table
            self.prototypes_table.insertRow(row)
            self.prototypes_table.setItem(row, 0, QTableWidgetItem(prototype_name))
            
            version_dropdown = QComboBox()
            version_dropdown.addItems(sorted(prototype["versions"].keys(), key=int, reverse=True))
            version_dropdown.setCurrentText(latest_version)
            version_dropdown.currentIndexChanged.connect(lambda _, r=row: self.version_selected(r))
            self.prototypes_table.setCellWidget(row, 1, version_dropdown)
    
            # Add the version summary
            self.prototypes_table.setItem(row, 2, QTableWidgetItem(version_summary))
    
        self.row_selected(0, 0)
    
    def version_selected(self, row):
        """Handle version selection and update summary."""
        version_dropdown = self.prototypes_table.cellWidget(row, 1)
        selected_version = version_dropdown.currentText()
        prototype = self.metadata["Prototypes"][row]
        version_summary = prototype["versions"][selected_version].get("version_summary", "No Summary")
    
        # Update summary column
        self.prototypes_table.setItem(row, 2, QTableWidgetItem(version_summary))


    def row_selected(self, row, column):
        """Handle row selection in the table."""
        if row < 0 or row >= self.prototypes_table.rowCount():
            self.selected_prototype = None
            self.selected_version = None
            return

        # Update the selected prototype based on the clicked row
        self.selected_prototype = self.metadata["Prototypes"][row]

        # Update the selected version based on the dropdown in the selected row
        version_dropdown = self.prototypes_table.cellWidget(row, 1)
        if version_dropdown:
            self.selected_version = version_dropdown.currentText()
        else:
            self.selected_version = None

        print(f"Row Selected: {row}, Prototype: {self.selected_prototype['name']}, Version: {self.selected_version}")

    def open_selected_prototype(self):
        """Open the selected prototype and version."""
        print(f"Selected Prototype: {self.selected_prototype}, Selected Version: {self.selected_version}")
        if not self.selected_prototype or not self.selected_version:
            QMessageBox.warning(self, "No Selection", "Please select a prototype and a version to open.")
            return

        # Load the selected version's metadata
        prototype_name = self.selected_prototype["name"]
        prototype_versions = self.selected_prototype.get("versions", {})
        selected_version_data = prototype_versions.get(self.selected_version)

        if not selected_version_data:
            QMessageBox.critical(self, "Error", f"Version {self.selected_version} not found for prototype {prototype_name}.")
            return

        # Open EditPrototypeDialog for the selected prototype version
        dialog = EditPrototypeDialog(self.base_folder, self.metadata, self.selected_prototype, self.selected_version)
        dialog.exec_()

        # Reload prototypes to reflect changes
        self.load_prototypes()

class EditPrototypeDialog(QDialog):
    """Dialog for editing a selected project."""
    def __init__(self, base_folder, metadata, prototype, selected_version=None):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.prototype = prototype
        self.selected_version = selected_version or self.get_latest_version()
        self.latest_version = self.prototype["versions"].get(self.selected_version, {})
        
        # Take a static snapshot of uploaded items when the dialog opens
        self.previous_uploaded_items = json.loads(
            json.dumps(self.latest_version.get("uploaded_items", []))
        )
        
        self.uploaded_items = copy.deepcopy(self.latest_version.get("uploaded_items", []))
        self.tree_structure = self.latest_version.get("tree_structure", [])
        self.temp_files = {}  # To track temporary files
        self.init_ui()

    def get_latest_version(self):
        """Retrieve the latest version of the prototype."""
        versions = self.prototype["versions"]
        return str(max(map(int, versions.keys())))

    def init_ui(self):
        """Set up the UI for editing the prototype."""
        self.setWindowTitle(f"Edit Prototype - {self.prototype['name']} (Version {self.selected_version})")
        layout = QVBoxLayout()

        # Prototype Description
        self.description_label = QLabel("Prototype Description:")
        layout.addWidget(self.description_label)
        self.description_input = QTextEdit(self.latest_version.get("description", ""))
        layout.addWidget(self.description_input)

        # Uploaded Files and Folders
        self.files_label = QLabel("Uploaded Files and Folders:")
        layout.addWidget(self.files_label)
        self.files_tree_widget = QTreeWidget()
        self.files_tree_widget.setHeaderLabel("Uploaded Items")
        self.load_uploaded_items(self.uploaded_items)
        self.files_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.files_tree_widget.customContextMenuRequested.connect(self.show_file_context_menu)
        layout.addWidget(self.files_tree_widget)

        # Save Changes Button
        save_layout = QHBoxLayout()
        self.upload_file_button = QPushButton("Add Files")
        self.upload_file_button.clicked.connect(self.upload_files)
        save_layout.addWidget(self.upload_file_button)

        self.upload_folder_button = QPushButton("Add Folder")
        self.upload_folder_button.clicked.connect(self.upload_folder)
        save_layout.addWidget(self.upload_folder_button)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        save_layout.addWidget(self.save_button)

        layout.addLayout(save_layout)
        self.setLayout(layout)

    # ---- Tree Structure Methods ----

    def show_tree_context_menu(self, position):
        """Show context menu for the project tree structure."""
        item = self.tree_widget.itemAt(position)
        menu = QMenu(self)

        add_action = menu.addAction("Add Child")
        edit_action = menu.addAction("Edit Node")
        delete_action = menu.addAction("Delete Node")

        add_action.triggered.connect(lambda: self.add_child(item))
        edit_action.triggered.connect(lambda: self.edit_node(item))
        delete_action.triggered.connect(lambda: self.delete_node(item))

        menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    # ---- File/Folder Context Menu ----
    def get_tree_structure(self):
        """Convert the tree widget into a dictionary format."""
        def item_to_dict(item):
            return {"name": item.text(0), "children": [item_to_dict(item.child(i)) for i in range(item.childCount())]}

        return [item_to_dict(self.tree_widget.topLevelItem(i)) for i in range(self.tree_widget.topLevelItemCount())]
    
    def show_file_context_menu(self, position):
        """Show context menu for files and folders."""
        item = self.files_tree_widget.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        # Add "Edit" and "Delete" options to the context menu
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")

        # Assign signals for the options (no functionality assigned yet)
        edit_action.triggered.connect(lambda: self.edit_file_or_folder(item))
        delete_action.triggered.connect(lambda: self.delete_file_or_folder(item))

        menu.exec_(self.files_tree_widget.viewport().mapToGlobal(position))
    
    def edit_file_or_folder(self, item):
        """Edit the selected file or folder."""
        if item.childCount() == 0:  # File
            print(f"Editing file: {item.text(0)}")
            self.open_file_as_temp(item, 0)  # Open file as a temporary copy for editing
        else:  # Folder
            print(f"Editing folder: {item.text(0)}")
            self.upload_folder_to_selected_folder(item)  # Add new folder to this folder

    
    def get_folder_metadata(self, tree_item):
        """Retrieve metadata for the selected folder."""
        def traverse_metadata(metadata_list, target_name):
            for entry in metadata_list:
                if entry["name"] == target_name:
                    return entry
                if "children" in entry:
                    result = traverse_metadata(entry["children"], target_name)
                    if result:
                        return result
            return None
    
        folder_path = []
        while tree_item:
            folder_path.insert(0, tree_item.text(0))
            tree_item = tree_item.parent()
    
        current_metadata = self.uploaded_items
        for part in folder_path:
            current_metadata = traverse_metadata(current_metadata, part)
    
        return current_metadata

    def add_folder_to_tree(self, parent_item, children):
        """Recursively add a folder and its contents to the tree widget."""
        for child in children:
            if "children" in child:  # Folder
                folder_item = QTreeWidgetItem([child["name"]])
                self.add_folder_to_tree(folder_item, child["children"])
                parent_item.addChild(folder_item)
            elif "path" in child:  # File
                file_item = QTreeWidgetItem([child["name"]])
                file_item.setToolTip(0, child["path"])
                parent_item.addChild(file_item)


    def delete_file_or_folder(self, item):
        """Delete the selected file or folder."""
        if not item:
            QMessageBox.warning(self, "Error", "No item selected to delete.")
            return
    
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion", f"Are you sure you want to delete '{item.text(0)}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
    
        # Perform deletion but defer saving until save_changes()
        def remove_from_metadata(metadata_list, target_name):
            """Recursively remove the target from metadata."""
            for index, entry in enumerate(metadata_list):
                if entry["name"] == target_name:
                    del metadata_list[index]
                    return True
                if "children" in entry:
                    if remove_from_metadata(entry["children"], target_name):
                        return True
            return False
    
        # Remove the selected item from metadata
        target_name = item.text(0)
        removed = remove_from_metadata(self.uploaded_items, target_name)
    
        if removed:
            # Update the tree view without saving
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.files_tree_widget.indexOfTopLevelItem(item)
                self.files_tree_widget.takeTopLevelItem(index)
    
            print(f"Deleted: {target_name}. Changes deferred to save_changes().")
        else:
            QMessageBox.warning(self, "Error", f"Could not find '{target_name}' in the metadata.")

     # ---- Tree Structure Methods ----
    
    def load_tree_structure(self, tree_structure):
         """Load the prototype tree structure into the widget."""
         def add_items(parent, children):
             for child in children:
                 item = QTreeWidgetItem([child["name"]])
                 add_items(item, child.get("children", []))
                 parent.addChild(item)
    
         self.tree_widget.clear()
         for root in tree_structure:
             root_item = QTreeWidgetItem([root["name"]])
             add_items(root_item, root.get("children", []))
             self.tree_widget.addTopLevelItem(root_item)
    
    
     # ---- Uploaded Items ----
    
    def load_uploaded_items(self, uploaded_items):
         """Load uploaded files and folders into the tree widget."""
         def add_items(parent, children):
             for child in children:
                 if "children" in child:  # Folder
                     folder_item = QTreeWidgetItem([child["name"]])
                     add_items(folder_item, child["children"])
                     parent.addChild(folder_item)
                 elif "path" in child:  # File
                     file_item = QTreeWidgetItem([child["name"]])
                     file_item.setToolTip(0, child["path"])
                     parent.addChild(file_item)
    
         self.files_tree_widget.clear()
         for item in uploaded_items:
             if "children" in item:  # Folder
                 folder_item = QTreeWidgetItem([item["name"]])
                 add_items(folder_item, item["children"])
                 self.files_tree_widget.addTopLevelItem(folder_item)
             elif "path" in item:  # File
                 file_item = QTreeWidgetItem([item["name"]])
                 file_item.setToolTip(0, item["path"])
                 self.files_tree_widget.addTopLevelItem(file_item)
    
    def open_file_as_temp(self, item, column):
         """Open a file as a temporary copy."""
         file_path = item.toolTip(0)
         if not file_path or not os.path.isfile(file_path):
             QMessageBox.warning(self, "Error", "File path is invalid or does not exist.")
             return
    
         try:
             with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[-1]) as temp_file:
                 temp_file_path = temp_file.name
                 shutil.copy(file_path, temp_file_path)
             QDesktopServices.openUrl(QUrl.fromLocalFile(temp_file_path))
             self.temp_files[file_path] = temp_file_path
         except Exception as e:
             QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
    
     # ---- File Uploads and Save ----
     
    def upload_files(self):
         """Upload files and append them to the uploaded items."""
         files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
         if files:
             for file in files:
                 file_name = os.path.basename(file)
                 dest_path = os.path.join(self.base_folder, "Prototype Files", file_name)
                 shutil.copy(file, dest_path)
     
                 # Add the new file to uploaded_items
                 self.uploaded_items.append({"name": file_name, "path": dest_path})
             self.load_uploaded_items(self.uploaded_items)  # Refresh the tree view
    
    
    def upload_folder(self):
         """Upload a folder and append it to the uploaded items."""
         folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
         if folder_path:
             folder_name = os.path.basename(folder_path)
             dest_folder = os.path.join(self.base_folder, "Prototype Files", folder_name)
             folder_metadata = self.scan_folder(folder_path, dest_folder)
     
             # Add the new folder to uploaded_items
             self.uploaded_items.append({"name": folder_name, "children": folder_metadata})
             self.load_uploaded_items(self.uploaded_items)  # Refresh the tree view
    
    def upload_folder_to_selected_folder(self, selected_folder_item):
        """Upload a folder and append its structure to a selected folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            folder_name = os.path.basename(folder_path)
    
            # Get the destination path for the selected folder
            parent_metadata = self.get_folder_metadata(selected_folder_item)
            dest_folder_path = os.path.join(self.base_folder, "Prototype Files", folder_name)
            folder_content = self.scan_folder(folder_path, dest_folder_path)
    
            # Update the metadata of the selected folder
            parent_metadata["children"].append({
                "name": folder_name,
                "children": folder_content
            })
    
            # Add the folder and its contents to the tree widget
            new_folder_item = QTreeWidgetItem([folder_name])
            self.add_folder_to_tree(new_folder_item, folder_content)
            selected_folder_item.addChild(new_folder_item)
    
            print(f"Added folder '{folder_name}' into '{selected_folder_item.text(0)}'.")

    def scan_folder(self, source_folder, dest_folder):
        """Recursively scan a folder, copy its contents, and return its structure."""
        os.makedirs(dest_folder, exist_ok=True)
        children = []
    
        for entry in os.listdir(source_folder):
            source_entry_path = os.path.join(source_folder, entry)
            dest_entry_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(source_entry_path):
                subfolder_metadata = self.scan_folder(source_entry_path, dest_entry_path)
                children.append({"name": entry, "children": subfolder_metadata})
            else:
                shutil.copy(source_entry_path, dest_entry_path)
                children.append({"name": entry, "path": dest_entry_path})
    
        return children

    
    def save_changes(self):
        """Save changes to the prototype while preserving folder structure and requesting summary only for changes."""
        def compute_file_hash(file_path):
            """Compute SHA256 hash of the file."""
            sha256 = hashlib.sha256()
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        sha256.update(chunk)
                    return sha256.hexdigest()
            except Exception as e:
                print(f"Error computing hash for {file_path}: {e}")
                return None
    
        def strip_timestamp(file_name):
            """Strip any existing timestamp from the filename."""
            base, ext = os.path.splitext(file_name)
            parts = base.split("_")
            if len(parts) > 1 and parts[-1].isdigit():  # Check if last part is a numeric timestamp
                base = "_".join(parts[:-1])  # Remove the timestamp
            return base + ext
    
        def process_uploaded_items(previous_items, current_items):
            """Recursively process uploaded items, detect changes, and handle new versions."""
            updated_items = []
            changes_detected = False
    
            # Create a lookup for previous items by name for easy comparison
            prev_lookup = {item["name"]: item for item in previous_items}
    
            for item in current_items:
                if "children" in item:  # Folder
                    previous_folder = prev_lookup.get(item["name"], {}).get("children", [])
                    updated_folder, folder_changes = process_uploaded_items(previous_folder, item["children"])
                    updated_items.append({
                        "name": item["name"],
                        "children": updated_folder
                    })
    
                    if item["name"] not in prev_lookup:  # New folder
                        print(f"New folder detected: {item['name']}")
                        changes_detected = True
                    changes_detected |= folder_changes
                elif "path" in item:  # File
                    previous_file = prev_lookup.get(item["name"])
                    temp_file_path = self.temp_files.get(item["path"])
    
                    if previous_file is None:  # New file added
                        print(f"New file detected: {item['name']}")
                        updated_items.append(item)
                        changes_detected = True
                    elif temp_file_path:  # File was opened/edited
                        temp_file_hash = compute_file_hash(temp_file_path)
                        original_hash = compute_file_hash(item["path"])
    
                        if original_hash != temp_file_hash:  # File content has changed
                            # Create a new versioned filename
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            original_file_name = strip_timestamp(item["name"])
                            new_file_name = f"{os.path.splitext(original_file_name)[0]}_{timestamp}{os.path.splitext(original_file_name)[1]}"
                            new_file_path = os.path.join(self.base_folder, "Prototype Files", new_file_name)
                            shutil.copy(temp_file_path, new_file_path)
    
                            updated_items.append({
                                "name": new_file_name,
                                "path": new_file_path
                            })
                            print(f"File updated: {new_file_path}")
                            changes_detected = True
                        else:  # File content unchanged
                            updated_items.append(item)
                    else:  # File unchanged
                        updated_items.append(item)
    
            # Detect deleted items
            current_item_names = {item["name"] for item in current_items}
            for item in previous_items:
                if item["name"] not in current_item_names:
                    print(f"Item deleted: {item['name']}")
                    changes_detected = True
    
            return updated_items, changes_detected
    
        def collect_tree_items(tree_widget):
            """Collect items from the tree widget into a list."""
            def traverse_tree(item):
                if item.childCount() == 0:  # File
                    return {"name": item.text(0), "path": item.toolTip(0)}
                else:  # Folder
                    return {
                        "name": item.text(0),
                        "children": [traverse_tree(item.child(i)) for i in range(item.childCount())]
                    }
    
            items = []
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                items.append(traverse_tree(item))
            return items
    
        # --- Gather New Data ---
        new_description = self.description_input.toPlainText().strip()
        # new_tree_structure = self.get_tree_structure()
        current_uploaded_items = collect_tree_items(self.files_tree_widget)
    
        # Compare previous and current items
        print("\nPrevious uploaded items:", self.previous_uploaded_items)
        print("\nCurrent uploaded items:", current_uploaded_items)
    
        new_uploaded_items, file_changes_detected = process_uploaded_items(self.previous_uploaded_items, current_uploaded_items)
        description_changed = new_description != self.latest_version.get("description", "")
        # tree_structure_changed = new_tree_structure != self.latest_version.get("tree_structure", [])
    
        changes_detected = file_changes_detected or description_changed #or tree_structure_changed
    
        if not changes_detected:
            QMessageBox.information(self, "No Changes", "No changes detected. Nothing to save.")
            return
    
        # --- Prompt for Version Summary ---
        version_summary, ok = QInputDialog.getText(self, "Version Summary", "Enter a summary for this version:")
        if not ok or not version_summary:
            QMessageBox.warning(self, "Version Summary Required", "You must provide a summary for the new version.")
            return
    
        # --- Prepare New Version Data ---
        new_version_data = {
            "description": new_description,
            # "tree_structure": new_tree_structure,
            "uploaded_items": new_uploaded_items,
            "version_summary": version_summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        }
    
        # --- Save the New Version ---
        versions = self.prototype.setdefault("versions", {})
        new_version_number = str(len(versions) + 1)
        versions[new_version_number] = new_version_data
    
        # Save updated metadata
        metadata_path = os.path.join(self.base_folder, "metadata.json")
        try:
            with open(metadata_path, "w") as f:
                json.dump(self.metadata, f, indent=4)
            QMessageBox.information(self, "Saved", f"Prototype changes saved successfully as version {new_version_number}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save metadata: {e}")
    
        # Cleanup temporary files
        self.cleanup_temp_files()
        self.accept()

     
    def cleanup_temp_files(self):
        """Delete temporary files created for editing."""
        for temp_file in self.temp_files.values():
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"Temporary file deleted: {temp_file}")
            except Exception as e:
                print(f"Error deleting temporary file {temp_file}: {e}")
        self.temp_files.clear()

#Create and manage users using the following classes (each corresponding to a separate window)
# usersDialog() - opens a dialog to create or browse users
# CreateProtypeDialog() - allows you to create a new user
# BrowseuserDialog() - allows you to view the list of existing user. 
#                           It also also allows you to edit a selected user
#                           version
# EdituserDialog() - It allows you to edit a selected user and save
#                         changes as a new version automatically. 

class UsersDialog(QDialog):
    """Main Users dialog with Create and Browse options."""
    def __init__(self, base_folder):
        super().__init__()
        self.base_folder = base_folder
        self.metadata_path = os.path.join(self.base_folder, "metadata.json")
        self.metadata = self.load_metadata()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Users")
        layout = QVBoxLayout()

        # Create Project Button
        create_button = QPushButton("Create User", self)
        create_button.clicked.connect(self.open_create_user_dialog)
        layout.addWidget(create_button)

        # Browse Projects Button
        browse_button = QPushButton("Browse Users", self)
        browse_button.clicked.connect(self.browse_users)
        layout.addWidget(browse_button)

        # Close Button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def load_metadata(self):
        """Load metadata from metadata.json."""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        return {"Projects": [], "Prototypes": [], "Experiments": [], "Users": []}

    def save_metadata(self):
        """Save metadata back to metadata.json."""
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=4)

    def open_create_user_dialog(self):
        """Open the Create User dialog."""
        dialog = CreateUserDialog(self.base_folder, self.metadata)
        if dialog.exec_():  # If the dialog is successfully completed
            self.save_metadata()

    def browse_users(self):
        """Open the Browse Projects dialog to view and edit existing users."""
        if not self.metadata.get("Users"):
            QMessageBox.information(self, "No Users", "There are no users to browse.")
            return
    
        # Open the Browse Projects dialog
        dialog = BrowseUsersDialog(self.base_folder, self.metadata)
        if dialog.exec_():  # If changes were made
            print('Done browsing')
            # Save updated metadata directly
            self.save_metadata()
            
            # Debugging: Print metadata after returning from the dialog
            print("Updated Metadata After Browsing:")
            print(json.dumps(self.metadata, indent=4))

class CreateUserDialog(QDialog):
    """Dialog for creating a new user."""
    def __init__(self, base_folder, metadata):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.user_files_folder = os.path.join(self.base_folder, "User Files")
        os.makedirs(self.user_files_folder, exist_ok=True)
        self.uploaded_items = []  # To store uploaded files and folders
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("Create User")
        layout = QVBoxLayout()

        # USer Name
        self.name_label = QLabel("User Title:")
        layout.addWidget(self.name_label)
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # User Description
        self.description_label = QLabel("User Description:")
        layout.addWidget(self.description_label)
        self.description_input = QTextEdit()
        layout.addWidget(self.description_input)

        # File and Folder Upload
        self.upload_files_button = QPushButton("Upload Files")
        self.upload_files_button.clicked.connect(self.upload_files)
        layout.addWidget(self.upload_files_button)

        self.upload_folder_button = QPushButton("Upload Folder")
        self.upload_folder_button.clicked.connect(self.upload_folder)
        layout.addWidget(self.upload_folder_button)

        # Uploaded Items Display
        self.uploaded_items_tree = QTreeWidget()
        self.uploaded_items_tree.setHeaderLabel("Uploaded Files/Folders")
        layout.addWidget(self.uploaded_items_tree)

        # Save Button
        self.save_button = QPushButton("Save User")
        self.save_button.clicked.connect(self.save_user)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    ### File and Folder Upload ###
    def upload_files(self):
        """Upload files and copy them to the user files folder."""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            for file in files:
                file_name = os.path.basename(file)
                dest_path = os.path.join(self.user_files_folder, file_name)
                shutil.copy(file, dest_path)

                # Update metadata
                self.uploaded_items.append({"name": file_name, "path": dest_path})

                # Add to display tree
                file_item = QTreeWidgetItem([f"File: {file_name}"])
                file_item.setToolTip(0, dest_path)
                self.uploaded_items_tree.addTopLevelItem(file_item)

            QMessageBox.information(self, "Files Uploaded", "Files have been uploaded successfully.")
    
    def upload_folder(self):
        """Upload a folder and preserve its hierarchy."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            folder_name = os.path.basename(folder)
            dest_folder = os.path.join(self.user_files_folder, folder_name)
    
            # Use process_folder to copy the folder and generate metadata
            folder_metadata = self.process_folder(folder, dest_folder)
    
            # Update metadata
            self.uploaded_items.append({"name": folder_name, "children": folder_metadata["children"]})
    
            # Add to display tree
            folder_item = QTreeWidgetItem([f"Folder: {folder_name}"])
            self.add_folder_to_tree(folder_item, folder_metadata["children"])
            self.uploaded_items_tree.addTopLevelItem(folder_item)
    
            QMessageBox.information(self, "Folder Uploaded", f"Folder '{folder_name}' has been uploaded.")

    def copy_folder_contents(self, source_folder, dest_folder):
        """Recursively copy folder and its contents while preserving structure."""
        folder_metadata = {"name": os.path.basename(source_folder), "children": []}
        os.makedirs(dest_folder, exist_ok=True)
    
        for entry in os.listdir(source_folder):
            entry_path = os.path.join(source_folder, entry)
            dest_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(entry_path):
                # Process subfolders recursively
                subfolder_metadata = self.copy_folder_contents(entry_path, dest_path)
                folder_metadata["children"].append(subfolder_metadata)
            else:
                # Process files
                shutil.copy(entry_path, dest_path)
                folder_metadata["children"].append({"name": entry, "path": dest_path})
    
        return folder_metadata


    def add_folder_to_tree(self, parent_item, children):
        """Recursively add folder and file structure to the tree widget."""
        for child in children:
            if isinstance(child, dict):  # Ensure child is a dictionary
                if "children" in child:  # It's a folder
                    folder_item = QTreeWidgetItem([child["name"]])
                    self.add_folder_to_tree(folder_item, child["children"])  # Recurse into folder
                    parent_item.addChild(folder_item)
                elif "path" in child:  # It's a file
                    file_item = QTreeWidgetItem([child["name"]])
                    file_item.setToolTip(0, child["path"])  # Set path as tooltip
                    parent_item.addChild(file_item)
            else:
                print(f"Unexpected child format: {child}")  # Debugging


    ### Save User ###
    def save_user(self):
        """Save user metadata to the JSON file."""
        user_name = self.name_input.text().strip()
        if not user_name:
            QMessageBox.critical(self, "Error", "User name cannot be empty.")
            return
    
        description = self.description_input.toPlainText().strip()
        # tree_structure = self.get_tree_structure()
    
        # Prompt for a version summary
        version_summary, ok = QInputDialog.getText(self, "Version Summary", "Enter a summary for this version:")
        if not ok or not version_summary:
            QMessageBox.warning(self, "Version Summary Required", "You must provide a summary for this version.")
            return
    
        version_data = {
            "description": description,
            "uploaded_items": self.uploaded_items,
            "version_summary": version_summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        }
    
        # Save to metadata
        user = next((p for p in self.metadata.get("Users", []) if p["name"] == user_name), None)
        if user:
            versions = user.setdefault("versions", {})
            versions[str(len(versions) + 1)] = version_data
        else:
            self.metadata.setdefault("Users", []).append({
                "name": user_name,
                "versions": {"1": version_data}
            })
    
        # Save metadata
        with open(os.path.join(self.base_folder, "metadata.json"), "w") as f:
            json.dump(self.metadata, f, indent=4)
    
        QMessageBox.information(self, "User Saved", "User created successfully.")
        self.accept()
    
    def process_folder(self, source_folder, dest_folder):
        """Recursively copy a folder and its contents while preserving the structure."""
        folder_metadata = {"name": os.path.basename(source_folder), "children": []}
        os.makedirs(dest_folder, exist_ok=True)
    
        for entry in os.listdir(source_folder):
            entry_path = os.path.join(source_folder, entry)
            dest_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(entry_path):
                # Process subfolders recursively
                subfolder_metadata = self.process_folder(entry_path, dest_path)
                folder_metadata["children"].append(subfolder_metadata)
            else:
                # Process files
                shutil.copy(entry_path, dest_path)
                folder_metadata["children"].append({"name": entry, "path": dest_path})
    
        return folder_metadata

class BrowseUsersDialog(QDialog):
    """Dialog for browsing and selecting users and their versions."""
    def __init__(self, base_folder, metadata):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.selected_user = None
        self.selected_version = None
        self.init_ui()
    
    def init_ui(self):
        """Set up the UI for browsing users."""
        self.setWindowTitle("Browse Users")
        layout = QVBoxLayout()
    
        # Table to display users, versions, and version summary
        self.users_table = QTableWidget(0, 3)
        self.users_table.setHorizontalHeaderLabels(["User Name", "Latest Version", "Version Summary"])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.users_table)
    
        self.load_users()
        self.users_table.cellClicked.connect(self.row_selected)
    
        self.open_button = QPushButton("Open Selected User Version")
        self.open_button.clicked.connect(self.open_selected_user)
        layout.addWidget(self.open_button)
    
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
    
        self.setLayout(layout)
    
    def load_users(self):
        """Load users and their latest versions into the table."""
        self.users_table.setRowCount(0)
        for row, user in enumerate(self.metadata.get("Users", [])):
            user_name = user["name"]
            latest_version = str(max(map(int, user["versions"].keys())))
            version_summary = user["versions"][latest_version].get("version_summary", "No Summary")
    
            # Populate table
            self.users_table.insertRow(row)
            self.users_table.setItem(row, 0, QTableWidgetItem(user_name))
            
            version_dropdown = QComboBox()
            version_dropdown.addItems(sorted(user["versions"].keys(), key=int, reverse=True))
            version_dropdown.setCurrentText(latest_version)
            version_dropdown.currentIndexChanged.connect(lambda _, r=row: self.version_selected(r))
            self.users_table.setCellWidget(row, 1, version_dropdown)
    
            # Add the version summary
            self.users_table.setItem(row, 2, QTableWidgetItem(version_summary))
    
        self.row_selected(0, 0)
    
    def version_selected(self, row):
        """Handle version selection and update summary."""
        version_dropdown = self.users_table.cellWidget(row, 1)
        selected_version = version_dropdown.currentText()
        user = self.metadata["Users"][row]
        version_summary = user["versions"][selected_version].get("version_summary", "No Summary")
    
        # Update summary column
        self.users_table.setItem(row, 2, QTableWidgetItem(version_summary))


    def row_selected(self, row, column):
        """Handle row selection in the table."""
        if row < 0 or row >= self.users_table.rowCount():
            self.selected_users = None
            self.selected_version = None
            return

        # Update the selected user based on the clicked row
        self.selected_user = self.metadata["Users"][row]

        # Update the selected version based on the dropdown in the selected row
        version_dropdown = self.users_table.cellWidget(row, 1)
        if version_dropdown:
            self.selected_version = version_dropdown.currentText()
        else:
            self.selected_version = None

        print(f"Row Selected: {row}, User: {self.selected_user['name']}, Version: {self.selected_version}")

    def open_selected_user(self):
        """Open the selected user and version."""
        print(f"Selected User: {self.selected_user}, Selected Version: {self.selected_version}")
        if not self.selected_user or not self.selected_version:
            QMessageBox.warning(self, "No Selection", "Please select a user and a version to open.")
            return

        # Load the selected version's metadata
        user_name = self.selected_user["name"]
        user_versions = self.selected_user.get("versions", {})
        selected_version_data = user_versions.get(self.selected_version)

        if not selected_version_data:
            QMessageBox.critical(self, "Error", f"Version {self.selected_version} not found for user {user_name}.")
            return

        # Open EditUserDialog for the selected prototype version
        dialog = EditUserDialog(self.base_folder, self.metadata, self.selected_user, self.selected_version)
        dialog.exec_()

        # Reload prototypes to reflect changes
        self.load_users()

class EditUserDialog(QDialog):
    """Dialog for editing a selected projeuserct."""
    def __init__(self, base_folder, metadata, user, selected_version=None):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.user = user
        self.selected_version = selected_version or self.get_latest_version()
        self.latest_version = self.user["versions"].get(self.selected_version, {})
        
        # Take a static snapshot of uploaded items when the dialog opens
        self.previous_uploaded_items = json.loads(
            json.dumps(self.latest_version.get("uploaded_items", []))
        )
        
        self.uploaded_items = copy.deepcopy(self.latest_version.get("uploaded_items", []))
        self.tree_structure = self.latest_version.get("tree_structure", [])
        self.temp_files = {}  # To track temporary files
        self.init_ui()

    def get_latest_version(self):
        """Retrieve the latest version of the user."""
        versions = self.user["versions"]
        return str(max(map(int, versions.keys())))

    def init_ui(self):
        """Set up the UI for editing the user."""
        self.setWindowTitle(f"Edit User - {self.user['name']} (Version {self.selected_version})")
        layout = QVBoxLayout()

        # User Description
        self.description_label = QLabel("User Description:")
        layout.addWidget(self.description_label)
        self.description_input = QTextEdit(self.latest_version.get("description", ""))
        layout.addWidget(self.description_input)

        # Uploaded Files and Folders
        self.files_label = QLabel("Uploaded Files and Folders:")
        layout.addWidget(self.files_label)
        self.files_tree_widget = QTreeWidget()
        self.files_tree_widget.setHeaderLabel("Uploaded Items")
        self.load_uploaded_items(self.uploaded_items)
        self.files_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.files_tree_widget.customContextMenuRequested.connect(self.show_file_context_menu)
        layout.addWidget(self.files_tree_widget)

        # Save Changes Button
        save_layout = QHBoxLayout()
        self.upload_file_button = QPushButton("Add Files")
        self.upload_file_button.clicked.connect(self.upload_files)
        save_layout.addWidget(self.upload_file_button)

        self.upload_folder_button = QPushButton("Add Folder")
        self.upload_folder_button.clicked.connect(self.upload_folder)
        save_layout.addWidget(self.upload_folder_button)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        save_layout.addWidget(self.save_button)

        layout.addLayout(save_layout)
        self.setLayout(layout)

    # ---- Tree Structure Methods ----

    def show_tree_context_menu(self, position):
        """Show context menu for the project tree structure."""
        item = self.tree_widget.itemAt(position)
        menu = QMenu(self)

        add_action = menu.addAction("Add Child")
        edit_action = menu.addAction("Edit Node")
        delete_action = menu.addAction("Delete Node")

        add_action.triggered.connect(lambda: self.add_child(item))
        edit_action.triggered.connect(lambda: self.edit_node(item))
        delete_action.triggered.connect(lambda: self.delete_node(item))

        menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    # ---- File/Folder Context Menu ----
    def get_tree_structure(self):
        """Convert the tree widget into a dictionary format."""
        def item_to_dict(item):
            return {"name": item.text(0), "children": [item_to_dict(item.child(i)) for i in range(item.childCount())]}

        return [item_to_dict(self.tree_widget.topLevelItem(i)) for i in range(self.tree_widget.topLevelItemCount())]
    
    def show_file_context_menu(self, position):
        """Show context menu for files and folders."""
        item = self.files_tree_widget.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        # Add "Edit" and "Delete" options to the context menu
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")

        # Assign signals for the options (no functionality assigned yet)
        edit_action.triggered.connect(lambda: self.edit_file_or_folder(item))
        delete_action.triggered.connect(lambda: self.delete_file_or_folder(item))

        menu.exec_(self.files_tree_widget.viewport().mapToGlobal(position))
    
    def edit_file_or_folder(self, item):
        """Edit the selected file or folder."""
        if item.childCount() == 0:  # File
            print(f"Editing file: {item.text(0)}")
            self.open_file_as_temp(item, 0)  # Open file as a temporary copy for editing
        else:  # Folder
            print(f"Editing folder: {item.text(0)}")
            self.upload_folder_to_selected_folder(item)  # Add new folder to this folder

    
    def get_folder_metadata(self, tree_item):
        """Retrieve metadata for the selected folder."""
        def traverse_metadata(metadata_list, target_name):
            for entry in metadata_list:
                if entry["name"] == target_name:
                    return entry
                if "children" in entry:
                    result = traverse_metadata(entry["children"], target_name)
                    if result:
                        return result
            return None
    
        folder_path = []
        while tree_item:
            folder_path.insert(0, tree_item.text(0))
            tree_item = tree_item.parent()
    
        current_metadata = self.uploaded_items
        for part in folder_path:
            current_metadata = traverse_metadata(current_metadata, part)
    
        return current_metadata

    def add_folder_to_tree(self, parent_item, children):
        """Recursively add a folder and its contents to the tree widget."""
        for child in children:
            if "children" in child:  # Folder
                folder_item = QTreeWidgetItem([child["name"]])
                self.add_folder_to_tree(folder_item, child["children"])
                parent_item.addChild(folder_item)
            elif "path" in child:  # File
                file_item = QTreeWidgetItem([child["name"]])
                file_item.setToolTip(0, child["path"])
                parent_item.addChild(file_item)


    def delete_file_or_folder(self, item):
        """Delete the selected file or folder."""
        if not item:
            QMessageBox.warning(self, "Error", "No item selected to delete.")
            return
    
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion", f"Are you sure you want to delete '{item.text(0)}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
    
        # Perform deletion but defer saving until save_changes()
        def remove_from_metadata(metadata_list, target_name):
            """Recursively remove the target from metadata."""
            for index, entry in enumerate(metadata_list):
                if entry["name"] == target_name:
                    del metadata_list[index]
                    return True
                if "children" in entry:
                    if remove_from_metadata(entry["children"], target_name):
                        return True
            return False
    
        # Remove the selected item from metadata
        target_name = item.text(0)
        removed = remove_from_metadata(self.uploaded_items, target_name)
    
        if removed:
            # Update the tree view without saving
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.files_tree_widget.indexOfTopLevelItem(item)
                self.files_tree_widget.takeTopLevelItem(index)
    
            print(f"Deleted: {target_name}. Changes deferred to save_changes().")
        else:
            QMessageBox.warning(self, "Error", f"Could not find '{target_name}' in the metadata.")

     # ---- Tree Structure Methods ----
    
    def load_tree_structure(self, tree_structure):
         """Load the user tree structure into the widget."""
         def add_items(parent, children):
             for child in children:
                 item = QTreeWidgetItem([child["name"]])
                 add_items(item, child.get("children", []))
                 parent.addChild(item)
    
         self.tree_widget.clear()
         for root in tree_structure:
             root_item = QTreeWidgetItem([root["name"]])
             add_items(root_item, root.get("children", []))
             self.tree_widget.addTopLevelItem(root_item)
    
    
     # ---- Uploaded Items ----
    
    def load_uploaded_items(self, uploaded_items):
         """Load uploaded files and folders into the tree widget."""
         def add_items(parent, children):
             for child in children:
                 if "children" in child:  # Folder
                     folder_item = QTreeWidgetItem([child["name"]])
                     add_items(folder_item, child["children"])
                     parent.addChild(folder_item)
                 elif "path" in child:  # File
                     file_item = QTreeWidgetItem([child["name"]])
                     file_item.setToolTip(0, child["path"])
                     parent.addChild(file_item)
    
         self.files_tree_widget.clear()
         for item in uploaded_items:
             if "children" in item:  # Folder
                 folder_item = QTreeWidgetItem([item["name"]])
                 add_items(folder_item, item["children"])
                 self.files_tree_widget.addTopLevelItem(folder_item)
             elif "path" in item:  # File
                 file_item = QTreeWidgetItem([item["name"]])
                 file_item.setToolTip(0, item["path"])
                 self.files_tree_widget.addTopLevelItem(file_item)
    
    def open_file_as_temp(self, item, column):
         """Open a file as a temporary copy."""
         file_path = item.toolTip(0)
         if not file_path or not os.path.isfile(file_path):
             QMessageBox.warning(self, "Error", "File path is invalid or does not exist.")
             return
    
         try:
             with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[-1]) as temp_file:
                 temp_file_path = temp_file.name
                 shutil.copy(file_path, temp_file_path)
             QDesktopServices.openUrl(QUrl.fromLocalFile(temp_file_path))
             self.temp_files[file_path] = temp_file_path
         except Exception as e:
             QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
    
     # ---- File Uploads and Save ----
     
    def upload_files(self):
         """Upload files and append them to the uploaded items."""
         files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
         if files:
             for file in files:
                 file_name = os.path.basename(file)
                 dest_path = os.path.join(self.base_folder, "User Files", file_name)
                 shutil.copy(file, dest_path)
     
                 # Add the new file to uploaded_items
                 self.uploaded_items.append({"name": file_name, "path": dest_path})
             self.load_uploaded_items(self.uploaded_items)  # Refresh the tree view
    
    
    def upload_folder(self):
         """Upload a folder and append it to the uploaded items."""
         folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
         if folder_path:
             folder_name = os.path.basename(folder_path)
             dest_folder = os.path.join(self.base_folder, "User Files", folder_name)
             folder_metadata = self.scan_folder(folder_path, dest_folder)
     
             # Add the new folder to uploaded_items
             self.uploaded_items.append({"name": folder_name, "children": folder_metadata})
             self.load_uploaded_items(self.uploaded_items)  # Refresh the tree view
    
    def upload_folder_to_selected_folder(self, selected_folder_item):
        """Upload a folder and append its structure to a selected folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            folder_name = os.path.basename(folder_path)
    
            # Get the destination path for the selected folder
            parent_metadata = self.get_folder_metadata(selected_folder_item)
            dest_folder_path = os.path.join(self.base_folder, "User Files", folder_name)
            folder_content = self.scan_folder(folder_path, dest_folder_path)
    
            # Update the metadata of the selected folder
            parent_metadata["children"].append({
                "name": folder_name,
                "children": folder_content
            })
    
            # Add the folder and its contents to the tree widget
            new_folder_item = QTreeWidgetItem([folder_name])
            self.add_folder_to_tree(new_folder_item, folder_content)
            selected_folder_item.addChild(new_folder_item)
    
            print(f"Added folder '{folder_name}' into '{selected_folder_item.text(0)}'.")

    def scan_folder(self, source_folder, dest_folder):
        """Recursively scan a folder, copy its contents, and return its structure."""
        os.makedirs(dest_folder, exist_ok=True)
        children = []
    
        for entry in os.listdir(source_folder):
            source_entry_path = os.path.join(source_folder, entry)
            dest_entry_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(source_entry_path):
                subfolder_metadata = self.scan_folder(source_entry_path, dest_entry_path)
                children.append({"name": entry, "children": subfolder_metadata})
            else:
                shutil.copy(source_entry_path, dest_entry_path)
                children.append({"name": entry, "path": dest_entry_path})
    
        return children

    
    def save_changes(self):
        """Save changes to the user while preserving folder structure and requesting summary only for changes."""
        def compute_file_hash(file_path):
            """Compute SHA256 hash of the file."""
            sha256 = hashlib.sha256()
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        sha256.update(chunk)
                    return sha256.hexdigest()
            except Exception as e:
                print(f"Error computing hash for {file_path}: {e}")
                return None
    
        def strip_timestamp(file_name):
            """Strip any existing timestamp from the filename."""
            base, ext = os.path.splitext(file_name)
            parts = base.split("_")
            if len(parts) > 1 and parts[-1].isdigit():  # Check if last part is a numeric timestamp
                base = "_".join(parts[:-1])  # Remove the timestamp
            return base + ext
    
        def process_uploaded_items(previous_items, current_items):
            """Recursively process uploaded items, detect changes, and handle new versions."""
            updated_items = []
            changes_detected = False
    
            # Create a lookup for previous items by name for easy comparison
            prev_lookup = {item["name"]: item for item in previous_items}
    
            for item in current_items:
                if "children" in item:  # Folder
                    previous_folder = prev_lookup.get(item["name"], {}).get("children", [])
                    updated_folder, folder_changes = process_uploaded_items(previous_folder, item["children"])
                    updated_items.append({
                        "name": item["name"],
                        "children": updated_folder
                    })
    
                    if item["name"] not in prev_lookup:  # New folder
                        print(f"New folder detected: {item['name']}")
                        changes_detected = True
                    changes_detected |= folder_changes
                elif "path" in item:  # File
                    previous_file = prev_lookup.get(item["name"])
                    temp_file_path = self.temp_files.get(item["path"])
    
                    if previous_file is None:  # New file added
                        print(f"New file detected: {item['name']}")
                        updated_items.append(item)
                        changes_detected = True
                    elif temp_file_path:  # File was opened/edited
                        temp_file_hash = compute_file_hash(temp_file_path)
                        original_hash = compute_file_hash(item["path"])
    
                        if original_hash != temp_file_hash:  # File content has changed
                            # Create a new versioned filename
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            original_file_name = strip_timestamp(item["name"])
                            new_file_name = f"{os.path.splitext(original_file_name)[0]}_{timestamp}{os.path.splitext(original_file_name)[1]}"
                            new_file_path = os.path.join(self.base_folder, "User Files", new_file_name)
                            shutil.copy(temp_file_path, new_file_path)
    
                            updated_items.append({
                                "name": new_file_name,
                                "path": new_file_path
                            })
                            print(f"File updated: {new_file_path}")
                            changes_detected = True
                        else:  # File content unchanged
                            updated_items.append(item)
                    else:  # File unchanged
                        updated_items.append(item)
    
            # Detect deleted items
            current_item_names = {item["name"] for item in current_items}
            for item in previous_items:
                if item["name"] not in current_item_names:
                    print(f"Item deleted: {item['name']}")
                    changes_detected = True
    
            return updated_items, changes_detected
    
        def collect_tree_items(tree_widget):
            """Collect items from the tree widget into a list."""
            def traverse_tree(item):
                if item.childCount() == 0:  # File
                    return {"name": item.text(0), "path": item.toolTip(0)}
                else:  # Folder
                    return {
                        "name": item.text(0),
                        "children": [traverse_tree(item.child(i)) for i in range(item.childCount())]
                    }
    
            items = []
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                items.append(traverse_tree(item))
            return items
    
        # --- Gather New Data ---
        new_description = self.description_input.toPlainText().strip()
        # new_tree_structure = self.get_tree_structure()
        current_uploaded_items = collect_tree_items(self.files_tree_widget)
    
        # Compare previous and current items
        print("\nPrevious uploaded items:", self.previous_uploaded_items)
        print("\nCurrent uploaded items:", current_uploaded_items)
    
        new_uploaded_items, file_changes_detected = process_uploaded_items(self.previous_uploaded_items, current_uploaded_items)
        description_changed = new_description != self.latest_version.get("description", "")
        # tree_structure_changed = new_tree_structure != self.latest_version.get("tree_structure", [])
    
        changes_detected = file_changes_detected or description_changed #or tree_structure_changed
    
        if not changes_detected:
            QMessageBox.information(self, "No Changes", "No changes detected. Nothing to save.")
            return
    
        # --- Prompt for Version Summary ---
        version_summary, ok = QInputDialog.getText(self, "Version Summary", "Enter a summary for this version:")
        if not ok or not version_summary:
            QMessageBox.warning(self, "Version Summary Required", "You must provide a summary for the new version.")
            return
    
        # --- Prepare New Version Data ---
        new_version_data = {
            "description": new_description,
            # "tree_structure": new_tree_structure,
            "uploaded_items": new_uploaded_items,
            "version_summary": version_summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        }
    
        # --- Save the New Version ---
        versions = self.user.setdefault("versions", {})
        new_version_number = str(len(versions) + 1)
        versions[new_version_number] = new_version_data
    
        # Save updated metadata
        metadata_path = os.path.join(self.base_folder, "metadata.json")
        try:
            with open(metadata_path, "w") as f:
                json.dump(self.metadata, f, indent=4)
            QMessageBox.information(self, "Saved", f"User changes saved successfully as version {new_version_number}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save metadata: {e}")
    
        # Cleanup temporary files
        self.cleanup_temp_files()
        self.accept()

     
    def cleanup_temp_files(self):
        """Delete temporary files created for editing."""
        for temp_file in self.temp_files.values():
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"Temporary file deleted: {temp_file}")
            except Exception as e:
                print(f"Error deleting temporary file {temp_file}: {e}")
        self.temp_files.clear()

#Create and manage projects using the following classes (each corresponding to a separate window)
# projectsDialog() - opens a dialog to create or browse projects
# CreateProtypeDialog() - allows you to create a new project
# BrowseprojectDialog() - allows you to view the list of existing project. 
#                           It also also allows you to edit a selected project
#                           version
# EditprojectDialog() - It allows you to edit a selected project and save
#                         changes as a new version automatically. 
class ProjectsDialog(QDialog):
    """Main Projects dialog with Create and Browse options."""
    def __init__(self, base_folder):
        super().__init__()
        self.base_folder = base_folder
        self.metadata_path = os.path.join(self.base_folder, "metadata.json")
        self.metadata = self.load_metadata()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Projects")
        layout = QVBoxLayout()

        # Create Project Button
        create_button = QPushButton("Create Project", self)
        create_button.clicked.connect(self.open_create_project_dialog)
        layout.addWidget(create_button)

        # Browse Projects Button
        browse_button = QPushButton("Browse Projects", self)
        browse_button.clicked.connect(self.browse_projects)
        layout.addWidget(browse_button)

        # Close Button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def load_metadata(self):
        """Load metadata from metadata.json."""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        return {"Projects": [], "Prototypes": [], "Experiments": [], "Users": []}

    def save_metadata(self):
        """Save metadata back to metadata.json."""
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=4)

    def open_create_project_dialog(self):
        """Open the Create Project dialog."""
        dialog = CreateProjectDialog(self.base_folder, self.metadata)
        if dialog.exec_():  # If the dialog is successfully completed
            self.save_metadata()

    def browse_projects(self):
        """Open the Browse Projects dialog to view and edit existing projects."""
        if not self.metadata.get("Projects"):
            QMessageBox.information(self, "No Projects", "There are no projects to browse.")
            return
    
        # Open the Browse Projects dialog
        dialog = BrowseProjectsDialog(self.base_folder, self.metadata)
        if dialog.exec_():  # If changes were made
            print('Done browsing')
            # Save updated metadata directly
            self.save_metadata()
            
            # Debugging: Print metadata after returning from the dialog
            print("Updated Metadata After Browsing:")
            print(json.dumps(self.metadata, indent=4))

class CreateProjectDialog(QDialog):
    """Dialog for creating a new project."""
    def __init__(self, base_folder, metadata):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.project_files_folder = os.path.join(self.base_folder, "Project Files")
        os.makedirs(self.project_files_folder, exist_ok=True)
        self.uploaded_items = []  # To store uploaded files and folders
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("Create Project")
        layout = QVBoxLayout()

        # Project Name
        self.name_label = QLabel("Project Title:")
        layout.addWidget(self.name_label)
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # Project Description
        self.description_label = QLabel("Project Description:")
        layout.addWidget(self.description_label)
        self.description_input = QTextEdit()
        layout.addWidget(self.description_input)

        # Tree Structure
        self.tree_label = QLabel("Project Tree Structure:")
        layout.addWidget(self.tree_label)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Project Structure")
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.tree_widget)

        # File and Folder Upload
        self.upload_files_button = QPushButton("Upload Files")
        self.upload_files_button.clicked.connect(self.upload_files)
        layout.addWidget(self.upload_files_button)

        self.upload_folder_button = QPushButton("Upload Folder")
        self.upload_folder_button.clicked.connect(self.upload_folder)
        layout.addWidget(self.upload_folder_button)

        # Uploaded Items Display
        self.uploaded_items_tree = QTreeWidget()
        self.uploaded_items_tree.setHeaderLabel("Uploaded Files/Folders")
        layout.addWidget(self.uploaded_items_tree)

        # Save Button
        self.save_button = QPushButton("Save Project")
        self.save_button.clicked.connect(self.save_project)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    ### File and Folder Upload ###
    def upload_files(self):
        """Upload files and copy them to the project files folder."""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            for file in files:
                file_name = os.path.basename(file)
                dest_path = os.path.join(self.project_files_folder, file_name)
                shutil.copy(file, dest_path)

                # Update metadata
                self.uploaded_items.append({"name": file_name, "path": dest_path})

                # Add to display tree
                file_item = QTreeWidgetItem([f"File: {file_name}"])
                file_item.setToolTip(0, dest_path)
                self.uploaded_items_tree.addTopLevelItem(file_item)

            QMessageBox.information(self, "Files Uploaded", "Files have been uploaded successfully.")
    
    def upload_folder(self):
        """Upload a folder and preserve its hierarchy."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            folder_name = os.path.basename(folder)
            dest_folder = os.path.join(self.project_files_folder, folder_name)
    
            # Use process_folder to copy the folder and generate metadata
            folder_metadata = self.process_folder(folder, dest_folder)
    
            # Update metadata
            self.uploaded_items.append({"name": folder_name, "children": folder_metadata["children"]})
    
            # Add to display tree
            folder_item = QTreeWidgetItem([f"Folder: {folder_name}"])
            self.add_folder_to_tree(folder_item, folder_metadata["children"])
            self.uploaded_items_tree.addTopLevelItem(folder_item)
    
            QMessageBox.information(self, "Folder Uploaded", f"Folder '{folder_name}' has been uploaded.")

    def copy_folder_contents(self, source_folder, dest_folder):
        """Recursively copy folder and its contents while preserving structure."""
        folder_metadata = {"name": os.path.basename(source_folder), "children": []}
        os.makedirs(dest_folder, exist_ok=True)
    
        for entry in os.listdir(source_folder):
            entry_path = os.path.join(source_folder, entry)
            dest_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(entry_path):
                # Process subfolders recursively
                subfolder_metadata = self.copy_folder_contents(entry_path, dest_path)
                folder_metadata["children"].append(subfolder_metadata)
            else:
                # Process files
                shutil.copy(entry_path, dest_path)
                folder_metadata["children"].append({"name": entry, "path": dest_path})
    
        return folder_metadata


    def add_folder_to_tree(self, parent_item, children):
        """Recursively add folder and file structure to the tree widget."""
        for child in children:
            if isinstance(child, dict):  # Ensure child is a dictionary
                if "children" in child:  # It's a folder
                    folder_item = QTreeWidgetItem([child["name"]])
                    self.add_folder_to_tree(folder_item, child["children"])  # Recurse into folder
                    parent_item.addChild(folder_item)
                elif "path" in child:  # It's a file
                    file_item = QTreeWidgetItem([child["name"]])
                    file_item.setToolTip(0, child["path"])  # Set path as tooltip
                    parent_item.addChild(file_item)
            else:
                print(f"Unexpected child format: {child}")  # Debugging

    ### Project Tree Widget Context Menu ###
    def show_context_menu(self, position):
        """Show a context menu for adding, editing, or deleting nodes."""
        item = self.tree_widget.itemAt(position)
        menu = QMenu(self)

        add_action = menu.addAction("Add Child")
        edit_action = menu.addAction("Edit Node")
        delete_action = menu.addAction("Delete Node")

        add_action.triggered.connect(lambda: self.add_child(item))
        edit_action.triggered.connect(lambda: self.edit_node(item))
        delete_action.triggered.connect(lambda: self.delete_node(item))

        menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    def add_child(self, parent_item):
        """Add a child node to the tree widget."""
        name, ok = QInputDialog.getText(self, "Add Child", "Enter name:")
        if ok and name:
            child_item = QTreeWidgetItem([name])
            if parent_item:
                parent_item.addChild(child_item)
            else:
                self.tree_widget.addTopLevelItem(child_item)

    def edit_node(self, item):
        """Edit the name of a tree node."""
        if item:
            name, ok = QInputDialog.getText(self, "Edit Node", "Enter new name:", text=item.text(0))
            if ok and name:
                item.setText(0, name)

    def delete_node(self, item):
        """Delete a node from the tree."""
        if item:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.tree_widget.takeTopLevelItem(self.tree_widget.indexOfTopLevelItem(item))

    ### Save Project ###
    def save_project(self):
        """Save project metadata with image folder information"""
        project_name = self.name_input.text().strip()
        if not project_name:
            QMessageBox.critical(self, "Error", "Project name cannot be empty.")
            return

        version_summary, ok = QInputDialog.getText(self, "Version Summary", 
                                                  "Enter a summary for this version:")
        if not ok or not version_summary:
            QMessageBox.warning(self, "Version Summary Required", 
                              "You must provide a summary for this version.")
            return

        version_data = {
            "description": self.description_input.toPlainText().strip(),
            "uploaded_items": self.uploaded_items,
            "version_summary": version_summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        }

        # Save to metadata
        project = next((p for p in self.metadata.get("Projects", []) 
                      if p["name"] == project_name), None)
        if project:
            versions = project.setdefault("versions", {})
            versions[str(len(versions) + 1)] = version_data
        else:
            self.metadata.setdefault("Projects", []).append({
                "name": project_name,
                "versions": {"1": version_data}
            })

        with open(os.path.join(self.base_folder, "metadata.json"), "w") as f:
            json.dump(self.metadata, f, indent=4)
        
        QMessageBox.information(self, "Saved", "Project created successfully.")
        self.accept()

    def get_tree_structure(self):
        """Convert the tree widget into a dictionary format."""
        def item_to_dict(item):
            return {"name": item.text(0), "children": [item_to_dict(item.child(i)) for i in range(item.childCount())]}

        return [item_to_dict(self.tree_widget.topLevelItem(i)) for i in range(self.tree_widget.topLevelItemCount())]
    
    def process_folder(self, source_folder, dest_folder):
        """Recursively copy a folder and its contents while preserving the structure."""
        folder_metadata = {"name": os.path.basename(source_folder), "children": []}
        os.makedirs(dest_folder, exist_ok=True)
    
        for entry in os.listdir(source_folder):
            entry_path = os.path.join(source_folder, entry)
            dest_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(entry_path):
                # Process subfolders recursively
                subfolder_metadata = self.process_folder(entry_path, dest_path)
                folder_metadata["children"].append(subfolder_metadata)
            else:
                # Process files
                shutil.copy(entry_path, dest_path)
                folder_metadata["children"].append({"name": entry, "path": dest_path})
    
        return folder_metadata

class BrowseProjectsDialog(QDialog):
    """Dialog for browsing and selecting projects and their versions."""
    def __init__(self, base_folder, metadata):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        self.selected_project = None
        self.selected_version = None
        self.init_ui()
    
    def init_ui(self):
        """Set up the UI for browsing projects."""
        self.setWindowTitle("Browse Projects")
        layout = QVBoxLayout()
    
        # Table to display projects, versions, and version summary
        self.projects_table = QTableWidget(0, 3)
        self.projects_table.setHorizontalHeaderLabels(["Project Name", "Latest Version", "Version Summary"])
        self.projects_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.projects_table)
    
        self.load_projects()
        self.projects_table.cellClicked.connect(self.row_selected)
    
        self.open_button = QPushButton("Open Selected Project Version")
        self.open_button.clicked.connect(self.open_selected_project)
        layout.addWidget(self.open_button)
    
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
    
        self.setLayout(layout)
    
    def load_projects(self):
        """Load projects with image folder support"""
        self.project_tree_widget.clear()
        for project in self.metadata.get("Projects", []):
            latest_version_key = str(max(map(int, project["versions"].keys())))
            latest_version = project["versions"][latest_version_key]
            tree_structure = latest_version.get("uploaded_items", [])
            
            project_item = QTreeWidgetItem([project["name"]])
            self.add_tree_items(project_item, tree_structure)
            self.project_tree_widget.addTopLevelItem(project_item)
    
    def version_selected(self, row):
        """Handle version selection and update summary."""
        version_dropdown = self.projects_table.cellWidget(row, 1)
        selected_version = version_dropdown.currentText()
        project = self.metadata["Projects"][row]
        version_summary = project["versions"][selected_version].get("version_summary", "No Summary")
    
        # Update summary column
        self.projects_table.setItem(row, 2, QTableWidgetItem(version_summary))


    def row_selected(self, row, column):
        """Handle row selection in the table."""
        if row < 0 or row >= self.projects_table.rowCount():
            self.selected_project = None
            self.selected_version = None
            return

        # Update the selected project based on the clicked row
        self.selected_project = self.metadata["Projects"][row]

        # Update the selected version based on the dropdown in the selected row
        version_dropdown = self.projects_table.cellWidget(row, 1)
        if version_dropdown:
            self.selected_version = version_dropdown.currentText()
        else:
            self.selected_version = None

        print(f"Row Selected: {row}, Project: {self.selected_project['name']}, Version: {self.selected_version}")

    def open_selected_project(self):
        """Open the selected project and version."""
        print(f"Selected Project: {self.selected_project}, Selected Version: {self.selected_version}")
        if not self.selected_project or not self.selected_version:
            QMessageBox.warning(self, "No Selection", "Please select a project and a version to open.")
            return

        # Load the selected version's metadata
        project_name = self.selected_project["name"]
        project_versions = self.selected_project.get("versions", {})
        selected_version_data = project_versions.get(self.selected_version)

        if not selected_version_data:
            QMessageBox.critical(self, "Error", f"Version {self.selected_version} not found for project {project_name}.")
            return

        # Open EditProjectDialog for the selected project version
        dialog = EditProjectDialog(self.base_folder, self.metadata, self.selected_project, self.selected_version)
        dialog.exec_()

        # Reload projects to reflect changes
        self.load_projects()

class EditProjectDialog(QDialog):
    """Dialog for editing a selected project."""
    def __init__(self, base_folder, metadata, project, selected_version=None):
        super().__init__()
        self.base_folder = base_folder
        self.metadata = metadata
        # print("\nMeta data at Dialog init: ", self.metadata)
        self.project = project
        self.selected_version = selected_version or self.get_latest_version()
        self.latest_version = self.project["versions"].get(self.selected_version, {})
        
        # Take a static snapshot of uploaded items when the dialog opens
        self.previous_uploaded_items = json.loads(
            json.dumps(self.latest_version.get("uploaded_items", []))
        )
        
        self.uploaded_items = copy.deepcopy(self.latest_version.get("uploaded_items", []))
        self.tree_structure = self.latest_version.get("tree_structure", [])
        self.temp_files = {}  # To track temporary files
        self.init_ui()

    def get_latest_version(self):
        """Retrieve the latest version of the project."""
        versions = self.project["versions"]
        return str(max(map(int, versions.keys())))

    def init_ui(self):
        """Set up the UI for editing the project."""
        self.setWindowTitle(f"Edit Project - {self.project['name']} (Version {self.selected_version})")
        layout = QVBoxLayout()

        # Project Description
        self.description_label = QLabel("Project Description:")
        layout.addWidget(self.description_label)
        self.description_input = QTextEdit(self.latest_version.get("description", ""))
        layout.addWidget(self.description_input)

        # Project Tree Structure
        self.tree_label = QLabel("Project Tree Structure:")
        layout.addWidget(self.tree_label)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Project Structure")
        self.load_tree_structure(self.tree_structure)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_tree_context_menu)
        layout.addWidget(self.tree_widget)

        # Uploaded Files and Folders
        self.files_label = QLabel("Uploaded Files and Folders:")
        layout.addWidget(self.files_label)
        self.files_tree_widget = QTreeWidget()
        self.files_tree_widget.setHeaderLabel("Uploaded Items")
        self.load_uploaded_items(self.uploaded_items)
        self.files_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.files_tree_widget.customContextMenuRequested.connect(self.show_file_context_menu)
        layout.addWidget(self.files_tree_widget)

        # Save Changes Button
        save_layout = QHBoxLayout()
        self.upload_file_button = QPushButton("Add Files")
        self.upload_file_button.clicked.connect(self.upload_files)
        save_layout.addWidget(self.upload_file_button)

        self.upload_folder_button = QPushButton("Add Folder")
        self.upload_folder_button.clicked.connect(self.upload_folder)
        save_layout.addWidget(self.upload_folder_button)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        save_layout.addWidget(self.save_button)

        layout.addLayout(save_layout)
        self.setLayout(layout)

    # ---- Tree Context Menu ----

    def show_tree_context_menu(self, position):
        """Show context menu for the project tree structure."""
        item = self.tree_widget.itemAt(position)
        menu = QMenu(self)

        add_action = menu.addAction("Add Child")
        edit_action = menu.addAction("Edit Node")
        delete_action = menu.addAction("Delete Node")

        add_action.triggered.connect(lambda: self.add_child(item))
        edit_action.triggered.connect(lambda: self.edit_node(item))
        delete_action.triggered.connect(lambda: self.delete_node(item))

        menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    # ---- File/Folder Context Menu ----

    def show_file_context_menu(self, position):
        """Show context menu for files and folders."""
        item = self.files_tree_widget.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        # Add "Edit" and "Delete" options to the context menu
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")

        # Assign signals for the options (no functionality assigned yet)
        edit_action.triggered.connect(lambda: self.edit_file_or_folder(item))
        delete_action.triggered.connect(lambda: self.delete_file_or_folder(item))

        menu.exec_(self.files_tree_widget.viewport().mapToGlobal(position))

    def edit_file_or_folder(self, item):
        """Edit the selected file or folder."""
        if item.childCount() == 0:  # File
            print(f"Editing file: {item.text(0)}")
            self.open_file_as_temp(item, 0)  # Open file as a temporary copy for editing
        else:  # Folder
            print(f"Editing folder: {item.text(0)}")
            self.upload_folder_to_selected_folder(item)  # Add new folder to this folder

    
    def get_folder_metadata(self, tree_item):
        """Retrieve metadata for the selected folder."""
        def traverse_metadata(metadata_list, target_name):
            for entry in metadata_list:
                if entry["name"] == target_name:
                    return entry
                if "children" in entry:
                    result = traverse_metadata(entry["children"], target_name)
                    if result:
                        return result
            return None
    
        folder_path = []
        while tree_item:
            folder_path.insert(0, tree_item.text(0))
            tree_item = tree_item.parent()
    
        current_metadata = self.uploaded_items
        for part in folder_path:
            current_metadata = traverse_metadata(current_metadata, part)
    
        return current_metadata

    
    def add_tree_items(self, parent, children):
        """Add nodes with image folder support"""
        for child in children:
            if child.get("type") == "image_folder":
                # Create special item for image folders
                item = QTreeWidgetItem([f"📷 {child['name']} ({len(child['images'])} images)"])
                # Add image files as children
                for img in child["images"]:
                    img_item = QTreeWidgetItem([img])
                    item.addChild(img_item)
            elif "children" in child:
                # Regular folder
                item = QTreeWidgetItem([child["name"]])
                self.add_tree_items(item, child.get("children", []))
            else:
                # Regular file
                item = QTreeWidgetItem([child["name"]])
            parent.addChild(item)


    def delete_file_or_folder(self, item):
        """Delete the selected file or folder."""
        if not item:
            QMessageBox.warning(self, "Error", "No item selected to delete.")
            return
    
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion", f"Are you sure you want to delete '{item.text(0)}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
    
        # Perform deletion but defer saving until save_changes()
        def remove_from_metadata(metadata_list, target_name):
            """Recursively remove the target from metadata."""
            for index, entry in enumerate(metadata_list):
                if entry["name"] == target_name:
                    del metadata_list[index]
                    return True
                if "children" in entry:
                    if remove_from_metadata(entry["children"], target_name):
                        return True
            return False
    
        # Remove the selected item from metadata
        target_name = item.text(0)
        removed = remove_from_metadata(self.uploaded_items, target_name)
    
        if removed:
            # Update the tree view without saving
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.files_tree_widget.indexOfTopLevelItem(item)
                self.files_tree_widget.takeTopLevelItem(index)
    
            print(f"Deleted: {target_name}. Changes deferred to save_changes().")
        else:
            QMessageBox.warning(self, "Error", f"Could not find '{target_name}' in the metadata.")


     # ---- Tree Structure Methods ----
    
    def load_tree_structure(self, tree_structure):
         """Load the project tree structure into the widget."""
         def add_items(parent, children):
             for child in children:
                 item = QTreeWidgetItem([child["name"]])
                 add_items(item, child.get("children", []))
                 parent.addChild(item)
    
         self.tree_widget.clear()
         for root in tree_structure:
             root_item = QTreeWidgetItem([root["name"]])
             add_items(root_item, root.get("children", []))
             self.tree_widget.addTopLevelItem(root_item)
    
    def get_tree_structure(self):
         """Convert the tree widget structure into a dictionary."""
         def item_to_dict(item):
             return {"name": item.text(0), "children": [item_to_dict(item.child(i)) for i in range(item.childCount())]}
    
         root_items = [self.tree_widget.topLevelItem(i) for i in range(self.tree_widget.topLevelItemCount())]
         return [item_to_dict(item) for item in root_items]
    
    def show_tree_context_menu(self, position):
         """Show context menu for tree structure."""
         item = self.tree_widget.itemAt(position)
         menu = QMenu(self)
    
         add_action = menu.addAction("Add Child")
         edit_action = menu.addAction("Edit Node")
         delete_action = menu.addAction("Delete Node")
    
         add_action.triggered.connect(lambda: self.add_child(item))
         edit_action.triggered.connect(lambda: self.edit_node(item))
         delete_action.triggered.connect(lambda: self.delete_node(item))
    
         menu.exec_(self.tree_widget.viewport().mapToGlobal(position))
    
    def add_child(self, parent_item):
         """Add a child node."""
         name, ok = QInputDialog.getText(self, "Add Child", "Enter name for the new child node:")
         if ok and name:
             child_item = QTreeWidgetItem([name])
             if parent_item:
                 parent_item.addChild(child_item)
             else:
                 self.tree_widget.addTopLevelItem(child_item)
    
    def edit_node(self, item):
         """Edit a tree node's name."""
         if item:
             name, ok = QInputDialog.getText(self, "Edit Node", "Edit node name:", text=item.text(0))
             if ok and name:
                 item.setText(0, name)
    
    def delete_node(self, item):
         """Delete a tree node."""
         parent = item.parent()
         if parent:
             parent.removeChild(item)
         else:
             index = self.tree_widget.indexOfTopLevelItem(item)
             self.tree_widget.takeTopLevelItem(index)
    
     # ---- Uploaded Items ----
    
    def load_uploaded_items(self, uploaded_items):
         """Load uploaded files and folders into the tree widget."""
         def add_items(parent, children):
             for child in children:
                 if "children" in child:  # Folder
                     folder_item = QTreeWidgetItem([child["name"]])
                     add_items(folder_item, child["children"])
                     parent.addChild(folder_item)
                 elif "path" in child:  # File
                     file_item = QTreeWidgetItem([child["name"]])
                     file_item.setToolTip(0, child["path"])
                     parent.addChild(file_item)
    
         self.files_tree_widget.clear()
         for item in uploaded_items:
             if "children" in item:  # Folder
                 folder_item = QTreeWidgetItem([item["name"]])
                 add_items(folder_item, item["children"])
                 self.files_tree_widget.addTopLevelItem(folder_item)
             elif "path" in item:  # File
                 file_item = QTreeWidgetItem([item["name"]])
                 file_item.setToolTip(0, item["path"])
                 self.files_tree_widget.addTopLevelItem(file_item)
    
    def open_file_as_temp(self, item, column):
         """Open a file as a temporary copy."""
         file_path = item.toolTip(0)
         if not file_path or not os.path.isfile(file_path):
             QMessageBox.warning(self, "Error", "File path is invalid or does not exist.")
             return
    
         try:
             with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[-1]) as temp_file:
                 temp_file_path = temp_file.name
                 shutil.copy(file_path, temp_file_path)
             QDesktopServices.openUrl(QUrl.fromLocalFile(temp_file_path))
             self.temp_files[file_path] = temp_file_path
         except Exception as e:
             QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
    
     # ---- File Uploads and Save ----
    def upload_files(self):
        """Upload files and append them to the uploaded items."""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            for file in files:
                file_name = os.path.basename(file)
                dest_path = os.path.join(self.base_folder, "Project Files", file_name)
                shutil.copy(file, dest_path)
    
                # Avoid adding duplicates
                if not any(item.get("name") == file_name and item.get("path") == dest_path for item in self.uploaded_items):
                    self.uploaded_items.append({"name": file_name, "path": dest_path})
    
            # Debugging: Check uploaded_items state
            print("Uploaded Items after file upload:")
            print(json.dumps(self.uploaded_items, indent=4))
    
            self.load_uploaded_items(self.uploaded_items)  # Refresh the tree view

    
    def upload_folder(self):
         """Upload a folder and append it to the uploaded items."""
         folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
         if folder_path:
             folder_name = os.path.basename(folder_path)
             dest_folder = os.path.join(self.base_folder, "Project Files", folder_name)
             folder_metadata = self.scan_folder(folder_path, dest_folder)
     
             # Add the new folder to uploaded_items
             self.uploaded_items.append({"name": folder_name, "children": folder_metadata})
             self.load_uploaded_items(self.uploaded_items)  # Refresh the tree view
    
    def upload_folder_to_selected_folder(self, selected_folder_item):
        """Upload a folder and append its structure to a selected folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            folder_name = os.path.basename(folder_path)
    
            # Get the destination path for the selected folder
            parent_metadata = self.get_folder_metadata(selected_folder_item)
            dest_folder_path = os.path.join(self.base_folder, "Project Files", folder_name)
            folder_content = self.scan_folder(folder_path, dest_folder_path)
    
            # Update the metadata of the selected folder
            parent_metadata["children"].append({
                "name": folder_name,
                "children": folder_content
            })
    
            # Add the folder and its contents to the tree widget
            new_folder_item = QTreeWidgetItem([folder_name])
            self.add_folder_to_tree(new_folder_item, folder_content)
            selected_folder_item.addChild(new_folder_item)
    
            print(f"Added folder '{folder_name}' into '{selected_folder_item.text(0)}'.")

    def scan_folder(self, source_folder, dest_folder):
        """Recursively scan a folder, copy its contents, and return its structure."""
        os.makedirs(dest_folder, exist_ok=True)
        children = []
    
        for entry in os.listdir(source_folder):
            source_entry_path = os.path.join(source_folder, entry)
            dest_entry_path = os.path.join(dest_folder, entry)
    
            if os.path.isdir(source_entry_path):
                subfolder_metadata = self.scan_folder(source_entry_path, dest_entry_path)
                children.append({"name": entry, "children": subfolder_metadata})
            else:
                shutil.copy(source_entry_path, dest_entry_path)
                children.append({"name": entry, "path": dest_entry_path})
    
        return children

    
    def save_changes(self):
        """Save changes to the project while preserving folder structure and requesting summary only for changes."""
        def compute_file_hash(file_path):
            """Compute SHA256 hash of the file."""
            sha256 = hashlib.sha256()
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        sha256.update(chunk)
                    return sha256.hexdigest()
            except Exception as e:
                print(f"Error computing hash for {file_path}: {e}")
                return None
    
        def strip_timestamp(file_name):
            """Strip any existing timestamp from the filename."""
            base, ext = os.path.splitext(file_name)
            parts = base.split("_")
            if len(parts) > 1 and parts[-1].isdigit():  # Check if last part is a numeric timestamp
                base = "_".join(parts[:-1])  # Remove the timestamp
            return base + ext
    
        def process_uploaded_items(previous_items, current_items):
            """Recursively process uploaded items, detect changes, and handle new versions."""
            updated_items = []
            changes_detected = False
    
            # Create a lookup for previous items by name for easy comparison
            prev_lookup = {item["name"]: item for item in previous_items}
    
            for item in current_items:
                if "children" in item:  # Folder
                    previous_folder = prev_lookup.get(item["name"], {}).get("children", [])
                    updated_folder, folder_changes = process_uploaded_items(previous_folder, item["children"])
                    updated_items.append({
                        "name": item["name"],
                        "children": updated_folder
                    })
    
                    if item["name"] not in prev_lookup:  # New folder
                        print(f"New folder detected: {item['name']}")
                        changes_detected = True
                    changes_detected |= folder_changes
                elif "path" in item:  # File
                    previous_file = prev_lookup.get(item["name"])
                    temp_file_path = self.temp_files.get(item["path"])
    
                    if previous_file is None:  # New file added
                        print(f"New file detected: {item['name']}")
                        updated_items.append(item)
                        changes_detected = True
                    elif temp_file_path:  # File was opened/edited
                        temp_file_hash = compute_file_hash(temp_file_path)
                        original_hash = compute_file_hash(item["path"])
    
                        if original_hash != temp_file_hash:  # File content has changed
                            # Create a new versioned filename
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            original_file_name = strip_timestamp(item["name"])
                            new_file_name = f"{os.path.splitext(original_file_name)[0]}_{timestamp}{os.path.splitext(original_file_name)[1]}"
                            new_file_path = os.path.join(self.base_folder, "Project Files", new_file_name)
                            shutil.copy(temp_file_path, new_file_path)
    
                            updated_items.append({
                                "name": new_file_name,
                                "path": new_file_path
                            })
                            print(f"File updated: {new_file_path}")
                            changes_detected = True
                        else:  # File content unchanged
                            updated_items.append(item)
                    else:  # File unchanged
                        updated_items.append(item)
    
            # Detect deleted items
            current_item_names = {item["name"] for item in current_items}
            for item in previous_items:
                if item["name"] not in current_item_names:
                    print(f"Item deleted: {item['name']}")
                    changes_detected = True
    
            return updated_items, changes_detected
    
        def collect_tree_items(tree_widget):
            """Collect items from the tree widget into a list."""
            def traverse_tree(item):
                if item.childCount() == 0:  # File
                    return {"name": item.text(0), "path": item.toolTip(0)}
                else:  # Folder
                    return {
                        "name": item.text(0),
                        "children": [traverse_tree(item.child(i)) for i in range(item.childCount())]
                    }
    
            items = []
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                items.append(traverse_tree(item))
            return items
    
        # --- Gather New Data ---
        new_description = self.description_input.toPlainText().strip()
        new_tree_structure = self.get_tree_structure()
        current_uploaded_items = collect_tree_items(self.files_tree_widget)
    
        # Compare previous and current items
        print("\nPrevious uploaded items:", self.previous_uploaded_items)
        print("\nCurrent uploaded items:", current_uploaded_items)
    
        new_uploaded_items, file_changes_detected = process_uploaded_items(self.previous_uploaded_items, current_uploaded_items)
        description_changed = new_description != self.latest_version.get("description", "")
        tree_structure_changed = new_tree_structure != self.latest_version.get("tree_structure", [])
    
        changes_detected = file_changes_detected or description_changed or tree_structure_changed
    
        if not changes_detected:
            QMessageBox.information(self, "No Changes", "No changes detected. Nothing to save.")
            return
    
        # --- Prompt for Version Summary ---
        version_summary, ok = QInputDialog.getText(self, "Version Summary", "Enter a summary for this version:")
        if not ok or not version_summary:
            QMessageBox.warning(self, "Version Summary Required", "You must provide a summary for the new version.")
            return
    
        # --- Prepare New Version Data ---
        new_version_data = {
            "description": new_description,
            "tree_structure": new_tree_structure,
            "uploaded_items": new_uploaded_items,
            "version_summary": version_summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        }
        
        print('\nNew Version Data: ', new_version_data)
    
        # --- Save the New Version ---
        versions = self.project.setdefault("versions", {})
        new_version_number = str(len(versions) + 1)
        versions[new_version_number] = new_version_data
    
        # Save updated metadata
        metadata_path = os.path.join(self.base_folder, "metadata.json")
        try:
            with open(metadata_path, "w") as f:
                json.dump(self.metadata, f, indent=4)
            QMessageBox.information(self, "Saved", f"Project changes saved successfully as version {new_version_number}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save metadata: {e}")
        
        # Cleanup temporary files
        self.cleanup_temp_files()
        self.accept()

     
    def cleanup_temp_files(self):
        """Delete temporary files created for editing."""
        for temp_file in self.temp_files.values():
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"Temporary file deleted: {temp_file}")
            except Exception as e:
                print(f"Error deleting temporary file {temp_file}: {e}")
        self.temp_files.clear()

     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    home_dialog = HomeDialog()
    sys.exit(app.exec_())
