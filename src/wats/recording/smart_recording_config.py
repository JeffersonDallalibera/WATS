# WATS_Project/wats_app/recording/smart_recording_config.py

"""
Configuration settings for smart recording features.
Extends the base recording configuration with intelligent features.
Integrates with WATS config.json system.
"""

import logging
from typing import Dict, Any, Tuple, List

# Default smart recording configuration
SMART_RECORDING_DEFAULTS = {
    # Window tracking settings
    'window_tracking_interval': 1.0,  # Seconds between window state checks
    'window_reacquisition_attempts': 5,  # Attempts to find lost window
    'window_reacquisition_delay': 2.0,  # Delay between reacquisition attempts
    
    # Interactivity monitoring settings
    'inactivity_timeout_minutes': 10,  # Minutes of inactivity before pausing
    'activity_detection_interval': 0.5,  # Seconds between activity checks
    'mouse_sensitivity': 5,  # Minimum mouse movement in pixels
    
    # Recording behavior settings
    'pause_on_minimized': True,  # Pause when window is minimized
    'pause_on_covered': True,  # Pause when window is covered
    'pause_on_inactive': True,  # Pause on user inactivity
    'create_new_file_after_pause': True,  # Create new file after resuming
    'create_new_file_after_inactivity': True,  # Create new file after inactivity
    
    # File management settings
    'max_file_duration_minutes': 30,  # Maximum duration per file
    'max_file_size_mb': 100,  # Maximum file size before rotation
    'segment_naming_pattern': '{session_id}_seg{segment:03d}_{timestamp}',
    
    # Performance settings
    'fps': 30,  # Frames per second
    'quality': 75,  # Recording quality (0-100)
    'resolution_scale': 1.0,  # Resolution scaling factor
    'compression_enabled': True,  # Enable post-recording compression
    'compression_crf': 28,  # H.264 CRF value for compression
    'compression_preset': 'veryfast',  # ffmpeg preset for compression
    
    # Debug and logging settings
    'debug_window_tracking': False,  # Enable debug logging for window tracking
    'debug_activity_monitoring': False,  # Enable debug logging for activity
    'save_activity_log': False,  # Save activity events to file
    'save_window_state_log': False,  # Save window state changes to file
}

def get_smart_recording_config(config_dict: Dict[str, Any] = None, user_settings=None) -> Dict[str, Any]:
    """
    Get smart recording configuration from config.json and user overrides.
    
    Args:
        config_dict: Dictionary from config.json (usually config.get('recording', {}))
        user_settings: User settings object or dictionary for additional overrides
        
    Returns:
        Dictionary with smart recording configuration
    """
    config = SMART_RECORDING_DEFAULTS.copy()
    
    # First, apply config.json settings if provided
    if config_dict:
        # Map config.json keys to internal config keys
        config_mappings = {
            # Basic recording settings
            'fps': 'fps',
            'quality': 'quality',
            'resolution_scale': 'resolution_scale',
            'max_file_size_mb': 'max_file_size_mb',
            'max_duration_minutes': 'max_file_duration_minutes',
            
            # Smart recording specific settings
            'smart_recording': {
                'window_tracking_interval': 'window_tracking_interval',
                'inactivity_timeout_minutes': 'inactivity_timeout_minutes',
                'pause_on_minimized': 'pause_on_minimized',
                'pause_on_covered': 'pause_on_covered',
                'pause_on_inactive': 'pause_on_inactive',
                'create_new_file_after_pause': 'create_new_file_after_pause',
                'compression_enabled': 'compression_enabled',
                'compression_crf': 'compression_crf',
                'debug_window_tracking': 'debug_window_tracking',
                'debug_activity_monitoring': 'debug_activity_monitoring',
            }
        }
        
        # Apply basic recording settings
        for config_key, internal_key in config_mappings.items():
            if isinstance(internal_key, dict):
                continue  # Skip nested mappings for now
            if config_key in config_dict:
                config[internal_key] = config_dict[config_key]
        
        # Apply smart recording specific settings
        if 'smart_recording' in config_dict:
            smart_config = config_dict['smart_recording']
            smart_mappings = config_mappings['smart_recording']
            
            for config_key, internal_key in smart_mappings.items():
                if config_key in smart_config:
                    config[internal_key] = smart_config[config_key]
    
    # Then, apply user_settings overrides if provided
    if user_settings:
        # Map settings attributes to config keys
        setting_mappings = {
            'RECORDING_WINDOW_TRACKING_INTERVAL': 'window_tracking_interval',
            'RECORDING_INACTIVITY_TIMEOUT_MINUTES': 'inactivity_timeout_minutes',
            'RECORDING_PAUSE_ON_MINIMIZED': 'pause_on_minimized',
            'RECORDING_PAUSE_ON_COVERED': 'pause_on_covered',
            'RECORDING_PAUSE_ON_INACTIVE': 'pause_on_inactive',
            'RECORDING_CREATE_NEW_FILE_AFTER_PAUSE': 'create_new_file_after_pause',
            'RECORDING_MAX_DURATION_MINUTES': 'max_file_duration_minutes',
            'RECORDING_MAX_FILE_SIZE_MB': 'max_file_size_mb',
            'RECORDING_FPS': 'fps',
            'RECORDING_QUALITY': 'quality',
            'RECORDING_RESOLUTION_SCALE': 'resolution_scale',
            'RECORDING_COMPRESSION_ENABLED': 'compression_enabled',
            'RECORDING_COMPRESSION_CRF': 'compression_crf',
            'RECORDING_DEBUG_WINDOW_TRACKING': 'debug_window_tracking',
            'RECORDING_DEBUG_ACTIVITY_MONITORING': 'debug_activity_monitoring',
        }
        
        # Apply user settings
        for setting_attr, config_key in setting_mappings.items():
            if hasattr(user_settings, setting_attr):
                config[config_key] = getattr(user_settings, setting_attr)
            elif isinstance(user_settings, dict) and setting_attr in user_settings:
                config[config_key] = user_settings[setting_attr]
    
    return config
    """
    Get smart recording configuration with user overrides.
    
    Args:
        user_settings: User settings object or dictionary
        
    Returns:
        Dictionary with smart recording configuration
    """
    config = SMART_RECORDING_DEFAULTS.copy()
    
    if user_settings:
        # Map settings attributes to config keys
        setting_mappings = {
            'RECORDING_WINDOW_TRACKING_INTERVAL': 'window_tracking_interval',
            'RECORDING_INACTIVITY_TIMEOUT_MINUTES': 'inactivity_timeout_minutes',
            'RECORDING_PAUSE_ON_MINIMIZED': 'pause_on_minimized',
            'RECORDING_PAUSE_ON_COVERED': 'pause_on_covered',
            'RECORDING_PAUSE_ON_INACTIVE': 'pause_on_inactive',
            'RECORDING_CREATE_NEW_FILE_AFTER_PAUSE': 'create_new_file_after_pause',
            'RECORDING_MAX_DURATION_MINUTES': 'max_file_duration_minutes',
            'RECORDING_MAX_FILE_SIZE_MB': 'max_file_size_mb',
            'RECORDING_FPS': 'fps',
            'RECORDING_QUALITY': 'quality',
            'RECORDING_RESOLUTION_SCALE': 'resolution_scale',
            'RECORDING_COMPRESSION_ENABLED': 'compression_enabled',
            'RECORDING_COMPRESSION_CRF': 'compression_crf',
            'RECORDING_DEBUG_WINDOW_TRACKING': 'debug_window_tracking',
            'RECORDING_DEBUG_ACTIVITY_MONITORING': 'debug_activity_monitoring',
        }
        
        # Apply user settings
        for setting_attr, config_key in setting_mappings.items():
            if hasattr(user_settings, setting_attr):
                config[config_key] = getattr(user_settings, setting_attr)
            elif isinstance(user_settings, dict) and setting_attr in user_settings:
                config[config_key] = user_settings[setting_attr]
    
    return config

def validate_smart_recording_config(config: dict) -> tuple[bool, list]:
    """
    Validate smart recording configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate numeric ranges
    if config.get('fps', 0) <= 0 or config.get('fps', 0) > 60:
        errors.append("FPS must be between 1 and 60")
    
    if config.get('quality', 0) < 0 or config.get('quality', 0) > 100:
        errors.append("Quality must be between 0 and 100")
    
    if config.get('resolution_scale', 0) <= 0 or config.get('resolution_scale', 0) > 2.0:
        errors.append("Resolution scale must be between 0.1 and 2.0")
    
    if config.get('inactivity_timeout_minutes', 0) < 1:
        errors.append("Inactivity timeout must be at least 1 minute")
    
    if config.get('max_file_duration_minutes', 0) < 1:
        errors.append("Max file duration must be at least 1 minute")
    
    if config.get('max_file_size_mb', 0) < 10:
        errors.append("Max file size must be at least 10 MB")
    
    if config.get('window_tracking_interval', 0) < 0.1:
        errors.append("Window tracking interval must be at least 0.1 seconds")
    
    # Validate compression settings
    crf = config.get('compression_crf', 23)
    if crf < 0 or crf > 51:
        errors.append("Compression CRF must be between 0 and 51")
    
    return len(errors) == 0, errors

def create_default_config_file(file_path: str):
    """
    Create a default configuration file for smart recording.
    
    Args:
        file_path: Path where to create the config file
    """
    import json
    from pathlib import Path
    
    config_data = {
        "smart_recording": SMART_RECORDING_DEFAULTS,
        "description": "Smart Recording Configuration for WATS",
        "version": "1.0",
        "documentation": {
            "window_tracking_interval": "Seconds between window state checks",
            "inactivity_timeout_minutes": "Minutes of inactivity before pausing recording",
            "pause_on_minimized": "Pause recording when RDP window is minimized",
            "pause_on_covered": "Pause recording when RDP window is covered",
            "pause_on_inactive": "Pause recording when user is inactive",
            "create_new_file_after_pause": "Create new file when resuming after pause",
            "max_file_duration_minutes": "Maximum duration per recording file",
            "fps": "Frames per second for recording",
            "quality": "Recording quality (0-100, higher is better)",
            "resolution_scale": "Scale factor for recording resolution",
            "compression_enabled": "Enable post-recording compression",
            "compression_crf": "H.264 CRF value (0-51, lower is better quality)"
        }
    }
    
    config_file = Path(file_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    print(f"Created default smart recording config: {config_file}")

if __name__ == "__main__":
    # Create example configuration file
    create_default_config_file("smart_recording_config.json")
    
    # Validate default configuration
    config = get_smart_recording_config()
    is_valid, errors = validate_smart_recording_config(config)
    
    print(f"Default configuration valid: {is_valid}")
    if errors:
        print("Errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration validated successfully")