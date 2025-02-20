# Experiment Tracking Suite

## Overview
Experiment Tracking Suite is a desktop application built with Python and PyQt5 that helps you manage and track research projects and their experiments. With an intuitive graphical interface, you can easily create projects, manage experiments, attach related files, and keep track of version changes—all while ensuring your data is safely backed up.

## Features
- **Project Management**
  - **Create Projects:** Enter project details such as title, description, team members, association (e.g., Adiuvo, Auxillium, Personal), and start/end dates.
  - **File Storage:** Save project metadata as JSON files in a chosen project folder.
  - **Backup:** Automatically backup project files to a designated tracking directory.
  
- **Experiment Management**
  - **Create Experiments:** Associate experiments with existing projects by entering experiment title, description, and version.
  - **Version Control:** Automatically generate and increment version numbers (Patch, Minor, Major) based on existing experiment files. Manual editing is also supported.
  - **File Attachments:** Add individual files or entire folders to your experiment. The app preserves the hierarchical structure of attached files.
  - **Backup:** Save experiment details as JSON files and automatically create backups in the tracking directory.

- **User-Friendly Interface**
  - **Two Main Tabs:** Switch between the **Project** and **Experiment** tabs for a clear workflow.
  - **Easy Navigation:** Intuitive dialogs for selecting project folders, tracking directories, and attaching files.
  - **Configuration Management:** Automatically load and update the tracking directory from a configuration file.

## Installation

### Prerequisites
- Python 3.x
- [PyQt5](https://pypi.org/project/PyQt5/)

### Steps
1. **Clone the Repository**
   ```bash
   git clone https://github.com/Aravind-Sridhar/project-tracker-tool.git
   cd project-tracker-tool
   ```

2. **Install Dependencies**
   Use pip to install PyQt5:
   ```bash
   pip install PyQt5
   ```

3. **Run the Application**
   Launch the app by running:
   ```bash
   python app.py
   ```

## Usage

### Initial Setup
- **Tracking Directory:**  
  On the first run, the app prompts you to select a tracking directory. This directory is used to store backup copies of your project and experiment files and is saved in `~/.experiment_tracker_config.json`.
  
- **Project Folder:**  
  In the **Project** tab, click **Choose Project Folder** to select the folder where project JSON files will be stored.

### Creating a Project
1. **Fill in Project Details:**
   - Enter a project title and description.
   - Specify team members (comma-separated) and select the project association.
   - Set the start and end dates.
2. **Create Project:**  
   Click **Create Project** to save your project. The app generates a JSON file and handles duplicate names by appending a version counter.

### Managing Experiments
1. **Select an Associated Project:**
   - In the **Experiment** tab, choose a project from the dropdown.
   - Optionally, load a previous experiment as a template.
2. **Enter Experiment Details:**
   - Provide the experiment title and description.
   - Use the version controls to generate an automatic version number or enable manual version editing by toggling the lock button.
3. **Attach Files/Folders:**
   - Use **Add Files** or **Add Folder** to include relevant files. The application preserves the folder hierarchy.
4. **Save Experiment:**
   - Set the experiment start and end dates.
   - Click **Save Experiment** to store the experiment details as a JSON file. A backup is automatically saved in the tracking directory under `backup/Experiments`.

## File Structure
- **Project Files:**  
  Saved as JSON files in your selected project folder. Backup copies are stored in `<tracking_directory>/backup/Projects/`.

- **Experiment Files:**  
  Saved in the project folder with a naming convention based on the project title, experiment title, and version number (e.g., `Project_Experiment_v1.0.0.json`). Backups are stored in `<tracking_directory>/backup/Experiments/`.

## Contributing
Contributions are welcome! If you have suggestions, bug fixes, or improvements, please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License.

## Contact
For any questions or feedback, please open an issue in the repository or contact the project maintainer.