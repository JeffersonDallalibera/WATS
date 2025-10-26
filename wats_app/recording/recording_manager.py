# WATS_Project/wats_app/recording/recording_manager.py

import logging
import threading
import time
from typing import Optional, Dict, Any, Callable
from .session_recorder import SessionRecorder
from .file_rotation_manager import FileRotationManager

class RecordingManager:
    """
    Central manager for session recording in WATS application.
    Coordinates between SessionRecorder and FileRotationManager.
    Provides high-level interface for the main application.
    """
    
    def __init__(self, settings):
        """
        Initialize the recording manager.
        
        Args:
            settings: Application settings instance
        """
        self.settings = settings
        self.recorder: Optional[SessionRecorder] = None
        self.rotation_manager: Optional[FileRotationManager] = None
        
        # State tracking
        self.current_session_id: Optional[str] = None
        self.current_connection_info: Optional[Dict[str, Any]] = None
        self.is_initialized = False
        
        # Callbacks
        self.on_recording_started: Optional[Callable[[str], None]] = None
        self.on_recording_stopped: Optional[Callable[[str], None]] = None
        self.on_recording_error: Optional[Callable[[str, str], None]] = None
        
        logging.info("RecordingManager initialized")

    def initialize(self) -> bool:
        """
        Initialize recording components if recording is enabled.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not self.settings.RECORDING_ENABLED:
                logging.info("Recording is disabled in settings")
                return True
                
            if not self.settings.validate_recording_config():
                logging.error("Recording configuration validation failed")
                return False
            
            # Initialize SessionRecorder
            self.recorder = SessionRecorder(
                output_dir=self.settings.RECORDING_OUTPUT_DIR,
                max_file_size_mb=self.settings.RECORDING_MAX_FILE_SIZE_MB,
                max_duration_minutes=self.settings.RECORDING_MAX_DURATION_MINUTES,
                fps=self.settings.RECORDING_FPS,
                quality=self.settings.RECORDING_QUALITY,
                resolution_scale=self.settings.RECORDING_RESOLUTION_SCALE,
                recording_mode=self.settings.RECORDING_MODE
            )
            
            # Initialize FileRotationManager
            self.rotation_manager = FileRotationManager(
                recordings_dir=self.settings.RECORDING_OUTPUT_DIR,
                max_total_size_gb=self.settings.RECORDING_MAX_TOTAL_SIZE_GB,
                max_file_age_days=self.settings.RECORDING_MAX_FILE_AGE_DAYS,
                cleanup_interval_hours=self.settings.RECORDING_CLEANUP_INTERVAL_HOURS
            )
            
            # Start automatic cleanup
            self.rotation_manager.start_automatic_cleanup()
            
            self.is_initialized = True
            logging.info("Recording system initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize recording system: {e}")
            self.is_initialized = False
            return False

    def start_session_recording(self, session_id: str, connection_info: Dict[str, Any]) -> bool:
        """
        Start recording for a new session.
        
        Args:
            session_id: Unique identifier for the session
            connection_info: Information about the connection (ip, name, user, etc.)
            
        Returns:
            True if recording started successfully, False otherwise
        """
        try:
            if not self.is_initialized or not self.settings.RECORDING_ENABLED:
                logging.debug("Recording not initialized or disabled")
                return False
                
            if self.is_recording():
                logging.warning(f"Already recording session {self.current_session_id}")
                return False
            
            # Start recording
            if self.recorder.start_recording(session_id, connection_info):
                self.current_session_id = session_id
                self.current_connection_info = connection_info
                
                # Call callback if set
                if self.on_recording_started:
                    try:
                        self.on_recording_started(session_id)
                    except Exception as e:
                        logging.error(f"Error in recording started callback: {e}")
                
                logging.info(f"Started recording for session {session_id}")
                return True
            else:
                logging.error(f"Failed to start recording for session {session_id}")
                return False
                
        except Exception as e:
            logging.error(f"Error starting session recording: {e}")
            if self.on_recording_error:
                try:
                    self.on_recording_error(session_id, str(e))
                except Exception:
                    pass
            return False

    def stop_session_recording(self) -> bool:
        """
        Stop the current recording session.
        
        Returns:
            True if recording stopped successfully, False otherwise
        """
        try:
            if not self.is_recording():
                logging.debug("No recording in progress")
                return True
                
            session_id = self.current_session_id
            
            if self.recorder.stop_recording():
                # Call callback if set
                if self.on_recording_stopped:
                    try:
                        self.on_recording_stopped(session_id)
                    except Exception as e:
                        logging.error(f"Error in recording stopped callback: {e}")
                
                self.current_session_id = None
                self.current_connection_info = None
                
                logging.info(f"Stopped recording for session {session_id}")
                return True
            else:
                logging.error("Failed to stop recording")
                return False
                
        except Exception as e:
            logging.error(f"Error stopping session recording: {e}")
            return False

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return (self.is_initialized and 
                self.recorder is not None and 
                self.recorder.is_recording)

    def get_recording_status(self) -> Dict[str, Any]:
        """
        Get current recording status and information.
        
        Returns:
            Dictionary with recording status
        """
        try:
            status = {
                "enabled": self.settings.RECORDING_ENABLED,
                "initialized": self.is_initialized,
                "is_recording": self.is_recording(),
                "current_session_id": self.current_session_id,
                "current_connection_info": self.current_connection_info
            }
            
            if self.is_recording() and self.recorder:
                recording_info = self.recorder.get_recording_info()
                if recording_info:
                    status.update(recording_info)
            
            if self.rotation_manager:
                storage_info = self.rotation_manager.get_storage_info()
                if storage_info and "error" not in storage_info:
                    status["storage"] = storage_info
            
            return status
            
        except Exception as e:
            logging.error(f"Error getting recording status: {e}")
            return {
                "enabled": self.settings.RECORDING_ENABLED,
                "initialized": False,
                "is_recording": False,
                "error": str(e)
            }

    def handle_connection_event(self, event_type: str, connection_info: Dict[str, Any]):
        """
        Handle connection events from the main application.
        
        Args:
            event_type: Type of event ('connect', 'disconnect', 'heartbeat')
            connection_info: Information about the connection
        """
        try:
            if not self.is_initialized or not self.settings.RECORDING_ENABLED:
                return
                
            connection_id = connection_info.get('con_codigo', 'unknown')
            session_id = f"session_{connection_id}_{int(time.time())}"
            
            if event_type == 'connect':
                if self.settings.RECORDING_AUTO_START:
                    self.start_session_recording(session_id, connection_info)
                    
            elif event_type == 'disconnect':
                if self.is_recording():
                    # Check if the disconnected connection matches current recording
                    if (self.current_connection_info and 
                        self.current_connection_info.get('con_codigo') == connection_id):
                        self.stop_session_recording()
                        
            elif event_type == 'heartbeat':
                # Heartbeat events can be used to update connection status
                # without affecting recording
                pass
                
        except Exception as e:
            logging.error(f"Error handling connection event {event_type}: {e}")

    def perform_cleanup(self) -> Dict[str, Any]:
        """
        Perform manual cleanup of old recordings.
        
        Returns:
            Cleanup results
        """
        try:
            if not self.rotation_manager:
                return {"error": "Rotation manager not initialized"}
                
            return self.rotation_manager.cleanup_recordings()
            
        except Exception as e:
            logging.error(f"Error performing cleanup: {e}")
            return {"error": str(e)}

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get storage information for recordings.
        
        Returns:
            Storage information dictionary
        """
        try:
            if not self.rotation_manager:
                return {"error": "Rotation manager not initialized"}
                
            return self.rotation_manager.get_storage_info()
            
        except Exception as e:
            logging.error(f"Error getting storage info: {e}")
            return {"error": str(e)}

    def set_callbacks(self, on_started: Optional[Callable[[str], None]] = None,
                     on_stopped: Optional[Callable[[str], None]] = None,
                     on_error: Optional[Callable[[str, str], None]] = None):
        """
        Set callback functions for recording events.
        
        Args:
            on_started: Called when recording starts (session_id)
            on_stopped: Called when recording stops (session_id)
            on_error: Called on recording error (session_id, error_message)
        """
        self.on_recording_started = on_started
        self.on_recording_stopped = on_stopped
        self.on_recording_error = on_error

    def shutdown(self):
        """Shutdown the recording manager and cleanup resources."""
        try:
            if self.is_recording():
                self.stop_session_recording()
                
            if self.rotation_manager:
                self.rotation_manager.stop_automatic_cleanup()
                
            self.is_initialized = False
            logging.info("Recording manager shutdown completed")
            
        except Exception as e:
            logging.error(f"Error during recording manager shutdown: {e}")

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        self.shutdown()