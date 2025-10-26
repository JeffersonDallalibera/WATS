# WATS Session Recording System

## Overview

The WATS application now includes a comprehensive session recording system for monitoring and auditing remote desktop connections. This feature provides lightweight screen recording with efficient compression and automatic file management.

## Features

### Core Recording Capabilities

- **Lightweight Screen Capture**: Uses MSS (Multiple Screen Shot) for efficient screen capture with minimal CPU/memory usage
- **H.264 Compression**: Efficient video compression for reduced file sizes
- **Configurable Quality**: Adjustable frame rate, resolution, and quality settings
- **Automatic Recording**: Can automatically start recording when connections are initiated
- **Multiple Recording Modes**: Support for full screen, RDP window, or active window recording

### Recording Modes

1. **Full Screen Recording** (`RECORDING_MODE=full_screen`)

   - Records the entire desktop including all monitors
   - Captures everything visible on screen (taskbar, other windows, desktop)
   - Higher file sizes but complete visibility
   - Use when you need to see all user activities

2. **RDP Window Recording** (`RECORDING_MODE=rdp_window`) **[RECOMMENDED]**

   - Records only the RDP connection window
   - Automatically tracks and follows the RDP window
   - Significantly smaller file sizes
   - Better privacy (doesn't record other applications)
   - Ideal for session auditing and monitoring

3. **Active Window Recording** (`RECORDING_MODE=active_window`)
   - Records the currently active/focused window
   - Switches recording focus when user changes windows
   - Dynamic recording based on user interaction
   - Good for general purpose monitoring

### File Management

- **Automatic Rotation**: Files are rotated based on size and time limits
- **Storage Quotas**: Configurable maximum storage limits with automatic cleanup
- **Age-based Cleanup**: Automatic deletion of old recordings
- **Metadata Tracking**: Each recording includes metadata about the connection

### Integration

- **Connection Monitoring**: Automatically detects RDP connection start/stop events
- **Visual Indicators**: UI shows recording status with visual feedback
- **Error Handling**: Comprehensive error handling and logging

## Configuration

### Environment Variables

Add these settings to your `.env` file:

```env
# Enable recording functionality
RECORDING_ENABLED=true

# Auto-start recording for new connections
RECORDING_AUTO_START=true

# Recording mode selection
RECORDING_MODE=rdp_window               # full_screen, rdp_window, active_window

# Recording quality settings
RECORDING_FPS=10                        # Frames per second (1-60)
RECORDING_QUALITY=23                    # H.264 quality (0-51, lower = better quality)
RECORDING_RESOLUTION_SCALE=1.0          # Resolution scale (0.1-2.0)

# File rotation settings
RECORDING_MAX_FILE_SIZE_MB=100          # Max file size before rotation
RECORDING_MAX_DURATION_MINUTES=30      # Max recording duration

# Storage management
RECORDING_MAX_TOTAL_SIZE_GB=10.0        # Total storage limit
RECORDING_MAX_FILE_AGE_DAYS=30          # Auto-delete after X days
RECORDING_CLEANUP_INTERVAL_HOURS=6      # Cleanup frequency
```

### Quality Settings Guide

**Frame Rate (RECORDING_FPS)**

- Low usage: 5-10 FPS
- Standard: 10-15 FPS
- High quality: 20-30 FPS

**Quality (RECORDING_QUALITY)**

- High quality: 18-23 (recommended: 23)
- Medium quality: 24-28
- Low quality: 29-35

**Resolution Scale**

- Full resolution: 1.0
- Half resolution: 0.5 (significantly reduces file size)
- Quarter resolution: 0.25 (minimal file size)

## File Structure

### Recording Output

Recordings are stored in the configured output directory with this structure:

```
recordings/
├── session_123_ServerName_20251026_143022.mp4
├── session_123_ServerName_20251026_143022_metadata.json
├── session_124_AnotherServer_20251026_144530.mp4
├── session_124_AnotherServer_20251026_144530_metadata.json
└── cleanup_stats.json
```

### Metadata Format

Each recording includes a metadata file with connection details:

```json
{
  "session_id": "rdp_123_1729950022",
  "connection_info": {
    "con_codigo": 123,
    "ip": "192.168.1.100",
    "name": "Production Server",
    "user": "administrator",
    "connection_type": "RDP"
  },
  "start_time": "2025-10-26T14:30:22.123456",
  "recorder_settings": {
    "fps": 10,
    "quality": 23,
    "resolution_scale": 1.0,
    "max_file_size_mb": 100,
    "max_duration_minutes": 30
  }
}
```

## Dependencies

The recording system requires these additional packages:

- `opencv-python`: Video encoding and processing
- `mss`: Efficient screen capture
- `numpy`: Array processing for video frames

Install dependencies:

```bash
pip install opencv-python mss numpy
```

## Usage

### Automatic Operation

When `RECORDING_AUTO_START=true`, the system automatically:

1. Starts recording when an RDP connection is initiated
2. Stops recording when the RDP session ends
3. Manages file rotation and cleanup in the background

### Manual Control

The recording system can be controlled programmatically:

```python
# Start recording
recording_manager.start_session_recording(session_id, connection_info)

# Stop recording
recording_manager.stop_session_recording()

# Get recording status
status = recording_manager.get_recording_status()

# Perform manual cleanup
cleanup_results = recording_manager.perform_cleanup()
```

### Visual Indicators

- **Recording Active**: Window title shows 🔴 icon when recording
- **Recording Stopped**: 🔴 icon removed from window title
- **Errors**: Alert dialogs for recording failures

## Storage Management

### Automatic Cleanup

The system automatically manages storage by:

1. **Age-based deletion**: Removes recordings older than `RECORDING_MAX_FILE_AGE_DAYS`
2. **Size-based deletion**: Removes oldest recordings when total size exceeds `RECORDING_MAX_TOTAL_SIZE_GB`
3. **Scheduled cleanup**: Runs every `RECORDING_CLEANUP_INTERVAL_HOURS`

### Manual Cleanup

Force cleanup operations:

```python
# Clean files older than X days
recording_manager.rotation_manager.force_cleanup_by_age(days=7)

# Clean to achieve target size
recording_manager.rotation_manager.force_cleanup_by_size(target_size_gb=5.0)
```

## Performance Considerations

### System Requirements

- **CPU**: Minimal impact with optimized settings (5-10% usage at 10 FPS)
- **Memory**: ~50-100 MB for recording buffer
- **Disk**: Depends on quality settings and duration

### Optimization Tips

1. **Lower FPS**: Reduce from 30 to 10 FPS for 70% smaller files
2. **Reduce Resolution**: Scale to 0.5 for 75% smaller files
3. **Adjust Quality**: Increase CRF from 23 to 28 for 40% smaller files
4. **Enable Cleanup**: Set appropriate age limits to manage disk usage

### File Size Estimates

For a 1920x1080 display at different settings:

| FPS | Quality | Scale | MB/hour | GB/day (8h) |
| --- | ------- | ----- | ------- | ----------- |
| 10  | 23      | 1.0   | 180     | 1.4         |
| 10  | 23      | 0.5   | 45      | 0.36        |
| 5   | 28      | 0.5   | 15      | 0.12        |

## Troubleshooting

### Common Issues

**Recording won't start**

- Check `RECORDING_ENABLED=true` in .env
- Verify output directory permissions
- Check log files for error messages

**High CPU usage**

- Reduce FPS (try 5-10 instead of 30)
- Lower resolution scale (try 0.5)
- Increase quality value (try 28-30)

**Large file sizes**

- Increase quality value (higher = smaller files)
- Reduce resolution scale
- Enable automatic rotation

**Recording stops unexpectedly**

- Check disk space in output directory
- Verify file size limits aren't too low
- Check system logs for errors

### Log Analysis

Recording activities are logged with these patterns:

```
[INFO] Recording started for session: rdp_123_1729950022
[INFO] Recording stopped for session: rdp_123_1729950022
[ERROR] Recording error for session rdp_123_1729950022: Disk full
[INFO] Cleanup completed: deleted 5 files, freed 1.2 GB
```

## Security Considerations

### Data Protection

- Recordings contain sensitive information and should be secured
- Consider encryption for stored recordings
- Implement access controls for recording directories
- Regular cleanup prevents indefinite data retention

### Privacy Compliance

- Inform users about recording activities
- Implement retention policies
- Consider data minimization (lower quality/resolution)
- Regular audits of stored recordings

### Access Control

- Restrict access to recording output directory
- Use appropriate file system permissions
- Consider separate storage for recordings
- Implement audit trails for recording access

## API Reference

### RecordingManager Class

Main interface for recording operations:

```python
class RecordingManager:
    def initialize() -> bool
    def start_session_recording(session_id: str, connection_info: dict) -> bool
    def stop_session_recording() -> bool
    def is_recording() -> bool
    def get_recording_status() -> dict
    def perform_cleanup() -> dict
    def get_storage_info() -> dict
    def shutdown()
```

### Configuration Methods

```python
# Get recording configuration
config = settings.get_recording_config()

# Validate configuration
is_valid = settings.validate_recording_config()
```

## Integration Examples

### Custom Recording Triggers

```python
# Start recording for specific connection types
def on_connection_start(connection_info):
    if connection_info.get('connection_type') == 'RDP':
        if connection_info.get('ip').startswith('192.168.'):
            # Only record internal connections
            recording_manager.start_session_recording(session_id, connection_info)
```

### Custom Cleanup Policies

```python
# Advanced cleanup based on connection type
def custom_cleanup():
    storage_info = recording_manager.get_storage_info()
    if storage_info['size_usage_percent'] > 80:
        # More aggressive cleanup when storage is high
        recording_manager.rotation_manager.force_cleanup_by_age(days=7)
```

This recording system provides comprehensive session monitoring capabilities while maintaining excellent performance and efficient storage management.
