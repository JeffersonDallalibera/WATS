# WATS - Windows Terminal Server Connection Manager

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://microsoft.com/windows)

**WATS V4.2** is a comprehensive Windows Terminal Server Connection Manager with advanced session recording capabilities for monitoring and auditing RDP connections.

## 🚀 Features

### Core Functionality

- **RDP Connection Management**: Centralized management of remote desktop connections
- **Database Integration**: Support for PostgreSQL and SQL Server backends
- **User Management**: Admin panel for user and connection management
- **Group Organization**: Organize connections by groups for better management

### Session Recording System _(NEW)_

- **Multiple Recording Modes**: Full screen, RDP window-specific, or active window recording
- **Lightweight Performance**: Optimized screen capture with minimal CPU/memory usage
- **H.264 Compression**: Efficient video compression for reduced file sizes
- **Automatic File Management**: Size and time-based file rotation with cleanup
- **Privacy Compliant**: Configurable recording scope for privacy requirements

### Advanced Features

- **Modern UI**: CustomTkinter-based interface with dark/light theme support
- **Real-time Monitoring**: Live connection status and heartbeat monitoring
- **Audit Trail**: Comprehensive logging and session metadata
- **Executable Build**: Standalone executable with PyInstaller

## 📋 Requirements

### System Requirements

- **OS**: Windows 10/11
- **Python**: 3.11+
- **Memory**: 4GB RAM minimum
- **Disk**: 2GB free space (more for recordings)

### Dependencies

```txt
customtkinter>=5.0.0
pyodbc>=4.0.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.0
opencv-python>=4.8.0
mss>=9.0.0
numpy>=1.24.0
pywin32>=306
psutil>=5.9.0
```

## 🛠️ Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd wats
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy sample configuration
copy .env.recording.sample .env

# Edit .env file with your database and recording settings
notepad .env
```

### 5. Run Application

```bash
python run.py
```

## ⚙️ Configuration

### Database Configuration

```env
# Database Settings
DB_TYPE=postgresql          # or sqlserver
DB_SERVER=your_server
DB_DATABASE=your_database
DB_UID=your_username
DB_PWD=your_password
DB_PORT=5432               # or 1433 for SQL Server
```

### Recording Configuration

```env
# Recording Settings
RECORDING_ENABLED=true
RECORDING_MODE=rdp_window           # full_screen, rdp_window, active_window
RECORDING_AUTO_START=true
RECORDING_FPS=10
RECORDING_QUALITY=23
RECORDING_MAX_FILE_SIZE_MB=100
RECORDING_MAX_DURATION_MINUTES=30
```

## 📚 Documentation

- **[Recording System Documentation](RECORDING_SYSTEM_DOCUMENTATION.md)** - Comprehensive guide for session recording
- **[Performance Optimization](PERFORMANCE_OPTIMIZATION.md)** - Performance tuning guide
- **[Theme Configuration](THEME_FIX_README.md)** - UI theme customization
- **[Build Instructions](BUILD_README.md)** - Creating standalone executables

## 🎯 Recording Modes

### RDP Window Recording _(Recommended)_

- Records only the RDP connection window
- 60-80% smaller file sizes
- Better privacy and performance
- Automatic window tracking

### Full Screen Recording

- Records entire desktop
- Complete audit trail
- Higher file sizes and CPU usage

### Active Window Recording

- Records currently focused window
- Dynamic recording based on user interaction

## 🔧 Building Executable

```bash
# Build standalone executable
python -m PyInstaller build_executable.spec --clean

# Executable will be created in dist/WATS_App.exe
```

## 📁 Project Structure

```
wats/
├── run.py                          # Application entry point
├── requirements.txt                # Python dependencies
├── build_executable.spec           # PyInstaller configuration
├── .env.recording.sample           # Configuration template
├── wats_app/                       # Main application package
│   ├── __init__.py
│   ├── main.py                     # Core application logic
│   ├── app_window.py               # Main UI window
│   ├── config.py                   # Configuration management
│   ├── utils.py                    # Utility functions
│   ├── dialogs.py                  # UI dialogs
│   ├── admin_panels/               # Admin interface
│   ├── db/                         # Database layer
│   │   ├── db_service.py          # Database service
│   │   ├── database_manager.py    # Connection management
│   │   └── repositories/          # Data access layer
│   └── recording/                  # Session recording system
│       ├── session_recorder.py    # Core recording functionality
│       ├── recording_manager.py   # Recording coordination
│       └── file_rotation_manager.py # File management
├── assets/                         # Application assets
│   ├── ats.ico                    # Application icon
│   └── rdp.exe                    # RDP executable
└── docs/                          # Documentation
```

## 🔒 Security Considerations

### Data Protection

- Environment variables for sensitive configuration
- Encrypted database connections
- Secure recording file storage
- Audit trail for all actions

### Recording Privacy

- Configurable recording scope
- Automatic cleanup policies
- Access control for recordings
- Privacy compliance features

## 🐛 Troubleshooting

### Common Issues

**Application won't start**

```bash
# Check Python version
python --version

# Verify dependencies
pip check

# Check environment configuration
python -c "from wats_app.config import load_environment_variables; load_environment_variables()"
```

**Recording not working**

```bash
# Check recording dependencies
pip install opencv-python mss numpy pywin32 psutil

# Verify recording configuration
python -c "from wats_app.config import Settings; s=Settings(); print(s.get_recording_config())"
```

**Database connection issues**

- Verify database server accessibility
- Check credentials in .env file
- Ensure database exists and user has permissions

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Development Team** - Initial work and ongoing maintenance

## 🙏 Acknowledgments

- CustomTkinter for modern UI components
- MSS for efficient screen capture
- OpenCV for video processing
- PyInstaller for executable creation

## 📊 Version History

- **V4.2** (2025-10-26)

  - Added comprehensive session recording system
  - Multiple recording modes (full screen, RDP window, active window)
  - Automatic file rotation and cleanup
  - Performance optimizations
  - Enhanced error handling

- **V4.1** (Previous)
  - Core RDP connection management
  - Database integration
  - Admin panel functionality
  - Basic UI framework

---

For detailed documentation and advanced configuration options, please refer to the documentation files in the project root.
