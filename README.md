# Experiment Tracker

## Overview
The Experiment Tracker is a PyQt5-based GUI application for managing projects and experiments. It allows users to create projects, assign dates, manage experiments, associate files, and implement version control.

## Features
- **Project Management**: Create and manage multiple projects with descriptions and team members.
- **Experiment Tracking**: Assign experiments to projects, include descriptions, and manage associated files.
- **Version Control**: Automatically assigns version numbers based on changes.
- **File Management**: Attach files and folders to experiments.

## Installation
### Prerequisites
Ensure you have Python installed. Then, install the required dependencies:
```sh
pip install PyQt5
```

## Usage
### Running the Application
Execute the following command:
```sh
python project-tracker-working.py
```

### Creating a Project
1. Click **"Choose Project Folder"** to select a directory.
2. Enter project details such as title, description, and team members.
3. Click **"Create Project"** to save the project.

### Creating an Experiment
1. Select a project from the dropdown.
2. Enter experiment details including title, description, and version.
3. Attach files/folders if necessary.
4. Click **"Save Experiment"** to store it.

## File Structure
- Project details are stored as `.json` files in the selected directory.
- Experiments are linked to their corresponding projects.

## Future Enhancements
- Cloud storage integration.
- Advanced versioning with change history.

## License
This project is open-source under the MIT License.

