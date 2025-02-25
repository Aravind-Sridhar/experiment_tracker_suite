import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QTextEdit, QDateEdit, QComboBox, QPushButton,
                             QFileDialog, QListWidget, QLabel, QTabWidget, QMessageBox,
                             QDialog, QDialogButtonBox, QTreeWidget, QTreeWidgetItem, QTreeView,
                             QAbstractItemView)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont

CONFIG_FILE = os.path.expanduser("~/.experiment_tracker_config.json")

class ExperimentTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_folder = None
        self.tracking_dir = self.load_tracking_dir()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Experiment Tracking Suite")
        self.setGeometry(100, 100, 500, 300)
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Tracking Directory Section
        tracking_layout = QHBoxLayout()
        self.tracking_dir_btn = QPushButton("Set Tracking Directory")
        self.tracking_dir_btn.clicked.connect(self.change_tracking_dir)
        self.tracking_dir_label = QLabel("No tracking directory selected")
        self.tracking_dir_label.setWordWrap(True)
        self.tracking_dir_label.setStyleSheet("color: #666; border: 1px solid #ddd; padding: 5px;")
        tracking_layout.addWidget(self.tracking_dir_btn)
        tracking_layout.addWidget(self.tracking_dir_label)
        main_layout.addLayout(tracking_layout)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_project_tab(), "Project")
        self.tabs.addTab(self.create_experiment_tab(), "Experiment")
        main_layout.addWidget(self.tabs)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        if self.tracking_dir:
            self.update_tracking_display()
            
        if not self.tracking_dir:
            self.change_tracking_dir(initial_setup=True)

    def create_project_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Folder selection
        folder_btn = QPushButton("Choose Project Folder")
        folder_btn.clicked.connect(self.choose_base_folder)
        self.folder_label = QLabel("No project folder selected")
        self.folder_label.setWordWrap(True)

        # Project fields
        self.project_title = QLineEdit()
        self.project_description = QTextEdit()
        self.usernames = QLineEdit("Aravind Sridhar")
        self.project_association = QComboBox()
        self.project_association.addItems(["Adiuvo", "Auxillium", "Personal", "Others (Add in Description)"])

        # Date fields
        self.project_start_date = QDateEdit(calendarPopup=True)
        self.project_start_date.setDate(QDate.currentDate())
        self.project_end_date = QDateEdit(calendarPopup=True)
        self.project_end_date.setDate(QDate.currentDate())

        create_btn = QPushButton("Create Project")
        create_btn.clicked.connect(self.save_project)

        # Layout
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

        # Previous experiments
        self.previous_experiments_combo = QComboBox()
        load_template_btn = QPushButton("Load Selected Experiment")
        load_template_btn.clicked.connect(self.load_selected_experiment)

        # Project selection
        self.projects_combo = QComboBox()

        # Experiment fields
        self.experiment_title = QLineEdit()
        self.experiment_title.textChanged.connect(self.update_version)
        self.experiment_description = QTextEdit()

        # Version controls
        version_layout = QHBoxLayout()
        self.version = QLineEdit()
        self.version.setReadOnly(True)
        self.version_type_combo = QComboBox()
        self.version_type_combo.addItems(["Patch", "Minor", "Major"])
        self.version_type_combo.currentIndexChanged.connect(self.update_version)
        self.version_lock = QPushButton("Lock Version")
        self.version_lock.setCheckable(True)
        self.version_lock.clicked.connect(self.toggle_version_lock)
        version_layout.addWidget(self.version)
        version_layout.addWidget(self.version_type_combo)
        version_layout.addWidget(self.version_lock)

        # File selection
        self.file_list = QListWidget()
        file_btn = QPushButton("Add Files")
        file_btn.clicked.connect(self.select_files)
        folder_btn = QPushButton("Add Folder")
        folder_btn.clicked.connect(self.select_folder)
        remove_btn = QPushButton("Remove Files/Folders")
        remove_btn.clicked.connect(self.open_remove_dialog)

        # Date fields
        self.experiment_start_date = QDateEdit(calendarPopup=True)
        self.experiment_start_date.setDate(QDate.currentDate())
        self.experiment_end_date = QDateEdit(calendarPopup=True)
        self.experiment_end_date.setDate(QDate.currentDate())

        # Save button
        create_btn = QPushButton("Save Experiment")
        create_btn.clicked.connect(self.save_experiment)

        # Layout
        layout.addWidget(QLabel("Associated Project:"))
        layout.addWidget(self.projects_combo)
        layout.addWidget(QLabel("Load Previous Experiment:"))
        layout.addWidget(self.previous_experiments_combo)
        layout.addWidget(load_template_btn)
        layout.addWidget(QLabel("Experiment Title:"))
        layout.addWidget(self.experiment_title)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.experiment_description)
        layout.addWidget(QLabel("Version:"))
        layout.addLayout(version_layout)
        layout.addWidget(QLabel("Associated Files/Folders:"))
        layout.addWidget(self.file_list)
        
        file_btn_layout = QHBoxLayout()
        file_btn_layout.addWidget(file_btn)
        file_btn_layout.addWidget(folder_btn)
        file_btn_layout.addWidget(remove_btn)
        layout.addLayout(file_btn_layout)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Start Date:"))
        date_layout.addWidget(self.experiment_start_date)
        date_layout.addWidget(QLabel("End Date:"))
        date_layout.addWidget(self.experiment_end_date)
        layout.addLayout(date_layout)
        layout.addWidget(create_btn)

        tab.setLayout(layout)
        return tab

    def toggle_version_lock(self):
        if self.version_lock.isChecked():
            self.version.setReadOnly(False)
            self.version_lock.setText("Manual versioning enabled")
            self.version.setStyleSheet("background-color: white;")
        else:
            self.version.setReadOnly(True)
            self.version_lock.setText("Automatic Versioning Enabled")
            self.version.setStyleSheet("")

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
            self.load_experiment_templates()

    def load_tracking_dir(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    if os.path.isdir(config['tracking_dir']):
                        return config['tracking_dir']
        except:
            return None

    def save_tracking_dir(self, path):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'tracking_dir': path}, f, indent=4)
            return True
        except Exception as e:
            self.show_warning(f"Failed to save config: {str(e)}")
            return False

    def change_tracking_dir(self, initial_setup=False):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Tracking Directory" if initial_setup else "Change Tracking Directory",
            options=QFileDialog.ShowDirsOnly
        )
        if path:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except Exception as e:
                    self.show_warning(f"Error creating directory: {str(e)}")
                    return
            if self.save_tracking_dir(path):
                self.tracking_dir = path
                self.update_tracking_display()
                if not initial_setup:
                    QMessageBox.information(self, "Success", "Tracking directory updated!")
            else:
                self.show_warning("Failed to save tracking directory configuration")
        elif initial_setup:
            self.show_warning("Tracking directory is required to use this application")
            sys.exit(1)

    def update_tracking_display(self):
        if self.tracking_dir:
            self.tracking_dir_label.setText(f"Tracking Directory: {self.tracking_dir}")
            self.tracking_dir_label.setStyleSheet("color: #333; border: 1px solid #ddd; padding: 5px;")

    def load_existing_projects(self):
        self.projects_combo.clear()
        if self.base_folder:
            for f in os.listdir(self.base_folder):
                if f.endswith('.json'):
                    try:
                        with open(os.path.join(self.base_folder, f), 'r') as file:
                            data = json.load(file)
                            if 'project' in data:
                                self.projects_combo.addItem(data['project']['title'], f)
                    except:
                        continue
        self.projects_combo.currentIndexChanged.connect(self.load_experiment_templates)

    def load_experiment_templates(self):
        self.previous_experiments_combo.clear()
        if not self.base_folder or self.projects_combo.currentIndex() == -1:
            return
        project_file = self.projects_combo.currentData()
        for fname in os.listdir(self.base_folder):
            if fname.endswith('.json') and fname != project_file:
                try:
                    with open(os.path.join(self.base_folder, fname), 'r') as f:
                        data = json.load(f)
                        if 'experiment' in data and data.get('project_reference') == project_file:
                            exp_title = data['experiment']['title']
                            version = data['experiment']['version']
                            self.previous_experiments_combo.addItem(
                                f"{exp_title} (v{version})", fname
                            )
                except:
                    continue

    def load_selected_experiment(self):
        if self.previous_experiments_combo.currentIndex() == -1:
            return
        experiment_file = self.previous_experiments_combo.currentData()
        try:
            with open(os.path.join(self.base_folder, experiment_file), 'r') as f:
                data = json.load(f)
                exp_data = data['experiment']
                self.experiment_title.setText(exp_data['title'])
                self.experiment_description.setPlainText(exp_data['description'])
                self.file_list.clear()
                self.populate_file_list(exp_data['file_structure'])
                self.version_type_combo.setCurrentText('Patch')
                self.update_version()
                self.version.setStyleSheet("background-color: #e0ffe0;")
        except Exception as e:
            self.show_warning(f"Error loading experiment: {str(e)}")

    def populate_file_list(self, file_structure, current_path=""):
        for name, value in file_structure.items():
            if isinstance(value, dict):
                self.populate_file_list(value, os.path.join(current_path, name))
            else:
                self.file_list.addItem(os.path.join(current_path, name))

    def update_version(self):
        if not self.base_folder or self.projects_combo.currentIndex() == -1:
            return
        project_file = self.projects_combo.currentData()
        experiment_title = self.experiment_title.text().strip()
        version_type = self.version_type_combo.currentText().lower()

        try:
            with open(os.path.join(self.base_folder, project_file), 'r') as f:
                project_data = json.load(f)
                project_title = project_data['project']['title']
        except:
            return

        safe_project = self.sanitize_filename(project_title)
        safe_experiment = self.sanitize_filename(experiment_title)
        if not safe_experiment:
            self.version.clear()
            return

        existing_versions = []
        for fname in os.listdir(self.base_folder):
            if fname.startswith(f"{safe_project}_{safe_experiment}_v") and fname.endswith(".json"):
                try:
                    version_part = fname.split('_v')[1].split('.json')[0]
                    parts = list(map(int, version_part.split('.')))
                    if len(parts) == 3:
                        existing_versions.append(tuple(parts))
                except:
                    continue

        if existing_versions:
            latest = max(existing_versions)
            if version_type == 'major':
                new_version = (latest[0] + 1, 0, 0)
            elif version_type == 'minor':
                new_version = (latest[0], latest[1] + 1, 0)
            else:
                new_version = (latest[0], latest[1], latest[2] + 1)
            new_version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
        else:
            new_version_str = "1.0.0"

        self.version.setText(new_version_str)

    def select_files(self):
        if not self.base_folder:
            self.show_warning("Please select a project folder first!")
            return
        
        # Allow multiple file selection with preview
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files/Folders",
            self.base_folder,
            options=QFileDialog.DontUseNativeDialog | QFileDialog.ReadOnly
        )
        
        if files:
            self.process_paths(files)

    def select_folder(self):
        if not self.base_folder:
            self.show_warning("Please select a project folder first!")
            return

        # Create custom dialog for multiple folder selection
        dialog = QFileDialog()
        dialog.setWindowTitle("Select Multiple Folders")
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        dialog.setViewMode(QFileDialog.Detail)
        
        # Enable multiple selection
        tree_view = dialog.findChild(QTreeView, "treeView")
        if tree_view:
            tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        if dialog.exec_() == QDialog.Accepted:
            folders = dialog.selectedFiles()
            if folders:
                self.process_paths(folders)

    def process_paths(self, paths):
        base_drive = os.path.splitdrive(self.base_folder)[0].upper()
        existing_items = {self.file_list.item(i).text() for i in range(self.file_list.count())}
        
        for path in paths:
            if os.path.isfile(path):
                self.add_single_file(path, base_drive, existing_items)
            elif os.path.isdir(path):
                self.add_directory_contents(path, base_drive, existing_items)

    def add_single_file(self, file_path, base_drive, existing_items):
        file_drive = os.path.splitdrive(file_path)[0].upper()
        if file_drive == base_drive:
            rel_path = os.path.relpath(file_path, self.base_folder)
        else:
            rel_path = os.path.abspath(file_path)
        
        if rel_path not in existing_items:
            self.file_list.addItem(rel_path)
            existing_items.add(rel_path)

    def add_directory_contents(self, folder_path, base_drive, existing_items):
        folder_drive = os.path.splitdrive(folder_path)[0].upper()
        same_drive = (folder_drive == base_drive)
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                if same_drive:
                    rel_path = os.path.relpath(abs_path, self.base_folder)
                else:
                    rel_path = os.path.abspath(abs_path)
                
                if rel_path not in existing_items:
                    self.file_list.addItem(rel_path)
                    existing_items.add(rel_path)

    def save_project(self):
        if not self.base_folder:
            self.show_warning("Please select a project folder first!")
            return
        project_title = self.project_title.text().strip()
        if not project_title:
            self.show_warning("Project title is required!")
            return
        
        safe_title = self.sanitize_filename(project_title)
        filename = f"{safe_title}.json"
        counter = 1
        while os.path.exists(os.path.join(self.base_folder, filename)):
            filename = f"{safe_title}_v{counter}.json"
            counter += 1

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

        try:
            with open(filepath, 'w') as f:
                json.dump(metadata, f, indent=4)
            if self.tracking_dir:
                backup_dir = os.path.join(self.tracking_dir, "backup", "Projects")
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, filename)
                with open(backup_path, 'w') as f:
                    json.dump(metadata, f, indent=4)
            self.load_existing_projects()
            QMessageBox.information(self, "Success", "Project created successfully!")
        except Exception as e:
            self.show_warning(f"Error saving project: {str(e)}")

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

        # Create unique filename
        safe_project = self.sanitize_filename(project_title)
        safe_experiment = self.sanitize_filename(experiment_title)
        base_name = f"{safe_project}_{safe_experiment}_v{version}"
        experiment_filename = f"{base_name}.json"
        counter = 1
        while os.path.exists(os.path.join(self.base_folder, experiment_filename)):
            experiment_filename = f"{base_name}({counter}).json"
            counter += 1

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
            if self.tracking_dir:
                backup_dir = os.path.join(self.tracking_dir, "backup", "Experiments")
                os.makedirs(backup_dir, exist_ok=True)
                backup_filename = os.path.basename(experiment_path)
                backup_path = os.path.join(backup_dir, backup_filename)
                with open(backup_path, 'w') as f:
                    json.dump(experiment_data, f, indent=4)
            self.file_list.clear()
            self.version.setStyleSheet("")
            self.previous_experiments_combo.setCurrentIndex(-1)
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

    def open_remove_dialog(self):
        if self.file_list.count() == 0:
            self.show_warning("No files to remove!")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Remove Files/Folders")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        tree = QTreeWidget()
        tree.setHeaderLabel("Select files/folders to remove")
        tree.setStyleSheet("QTreeWidget::item { height: 25px; }")
        
        # Build hierarchy from existing files
        root = tree.invisibleRootItem()
        path_map = {}
        
        for i in range(self.file_list.count()):
            path = self.file_list.item(i).text()
            parts = path.split(os.sep)
            parent = root
            
            for part in parts:
                if part not in path_map:
                    node = QTreeWidgetItem([part])
                    node.setFlags(node.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
                    node.setCheckState(0, Qt.Unchecked)
                    parent.addChild(node)
                    path_map[part] = node
                parent = path_map[part]

        # Configure dialog buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)

        layout.addWidget(tree)
        layout.addWidget(btn_box)
        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            self.remove_selected_items(tree)

    def remove_selected_items(self, tree):
        selected_paths = set()
        
        def collect_paths(item, current_path):
            full_path = os.path.join(current_path, item.text(0))
            if item.checkState(0) == Qt.Checked:
                selected_paths.add(full_path)
            for i in range(item.childCount()):
                collect_paths(item.child(i), full_path)
        
        for i in range(tree.topLevelItemCount()):
            collect_paths(tree.topLevelItem(i), "")
        
        # Remove items matching selected paths
        for i in reversed(range(self.file_list.count())):
            item_path = self.file_list.item(i).text()
            for sp in selected_paths:
                if item_path == sp or item_path.startswith(sp + os.sep):
                    self.file_list.takeItem(i)
                    break

    def show_warning(self, message):
        QMessageBox.warning(self, "Warning", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExperimentTracker()
    window.show()
    sys.exit(app.exec_())
