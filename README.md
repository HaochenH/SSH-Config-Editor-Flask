# SSH-Config-Editor-Flask
### Provides a web-based interface for editing the ssh config file, with support for Windows, macOS, and Linux.

A Flask-based SSH configuration file management tool that provides a visual interface for editing and managing SSH configuration files.

## Features

- Visual editing of SSH configuration files
- Add, delete, and modify SSH host configurations
- Drag-and-drop sorting of host configurations
- Support for common SSH options (HostName, User, Port, etc.)
- Raw file editing mode

## Installation

Install the required dependencies:

```bash
pip install flask
```

On Windows systems, you also need to install Waitress:

```bash
pip install waitress
```

## Running the Application

```bash
python app.py
```

Once running, open a browser and navigate to `http://localhost:5000` to use the application.

## License

MIT License