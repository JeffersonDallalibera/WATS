# Changelog

All notable changes to the WATS project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.2.0] - 2025-10-26

### Added

- **Session Recording System**

  - Multiple recording modes: full screen, RDP window-specific, active window
  - Lightweight screen capture using MSS with minimal CPU/memory usage
  - H.264 video compression for efficient storage
  - Automatic file rotation based on size and time limits
  - Storage quota management with automatic cleanup
  - Age-based deletion of old recordings
  - Real-time recording status indicators in UI

- **Recording Configuration**

  - Environment variable configuration via .env file
  - Configurable frame rate, quality, and resolution settings
  - Recording mode selection (full_screen, rdp_window, active_window)
  - Storage management settings (max size, duration, cleanup intervals)

- **Windows Integration**

  - RDP window detection and tracking
  - Automatic window following for RDP sessions
  - Process-based window identification
  - Fallback mechanisms for reliable recording

- **File Management**
  - Automatic file rotation based on configurable limits
  - Background cleanup processes
  - Metadata tracking for each recording session
  - Storage statistics and monitoring

### Enhanced

- **Performance Optimizations**

  - Deferred initialization for faster startup
  - Background database initialization
  - Optimized UI creation process
  - Reduced memory footprint

- **Error Handling**

  - Comprehensive error handling for recording operations
  - Graceful fallbacks when recording components fail
  - Detailed logging for troubleshooting
  - User-friendly error messages

- **Configuration Management**
  - Extended Settings class with recording preferences
  - Validation for all recording configuration options
  - Better environment variable handling
  - Embedded .env file support in executables

### Fixed

- Environment variable loading in PyInstaller executables
- Theme persistence across application restarts
- Database configuration validation
- Resource cleanup on application shutdown

### Dependencies

- Added `opencv-python` for video encoding
- Added `mss` for screen capture
- Added `numpy` for array processing
- Added `pywin32` for Windows API integration
- Added `psutil` for process management

## [4.1.0] - Previous Release

### Added

- Core RDP connection management
- Database integration (PostgreSQL and SQL Server)
- User management with admin panel
- Group-based connection organization
- CustomTkinter-based modern UI
- Dark/light theme support
- Real-time connection monitoring
- Heartbeat system for connection status
- PyInstaller executable creation

### Features

- Centralized RDP connection management
- Database backend support
- Admin panel for user/connection management
- Connection grouping and organization
- Modern UI with theme support
- Real-time status monitoring
- Audit logging
- Standalone executable creation

---

## Version Numbering

- **Major version** (X.0.0): Breaking changes or major feature additions
- **Minor version** (0.X.0): New features that are backward compatible
- **Patch version** (0.0.X): Bug fixes and minor improvements

## Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
