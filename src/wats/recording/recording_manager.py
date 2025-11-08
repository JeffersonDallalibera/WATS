# WATS_Project/wats_app/recording/recording_manager.py

import logging
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .file_rotation_manager import FileRotationManager
from .smart_session_recorder import SmartSessionRecorder

# ============================================================================
# API INTEGRATION DESABILITADA (não está sendo usada no momento)
# ============================================================================
# Import API components if available
# try:
#     from ..api import ApiIntegrationManager
#     API_AVAILABLE = True
# except ImportError:
#     logging.warning("API upload system not available")
#     API_AVAILABLE = False
#     ApiIntegrationManager = None

# Forçar API como indisponível
API_AVAILABLE = False
ApiIntegrationManager = None


class RecordingManager:
    """
    Central manager for session recording in WATS application.
    Coordinates between SmartSessionRecorder, FileRotationManager, and API upload.
    Provides high-level interface for the main application with intelligent recording features.
    """

    def __init__(self, settings):
        """
        Initialize the recording manager.

        Args:
            settings: Application settings instance
        """
        self.settings = settings
        self.smart_recorder: Optional[SmartSessionRecorder] = None
        self.rotation_manager: Optional[FileRotationManager] = None
        self.api_manager = None  # Optional[ApiIntegrationManager]

        # State tracking
        self.current_session_id: Optional[str] = None
        self.current_connection_info: Optional[Dict[str, Any]] = None
        self.is_initialized = False

        # Callbacks
        self.on_recording_started: Optional[Callable[[str], None]] = None
        self.on_recording_stopped: Optional[Callable[[str], None]] = None
        self.on_recording_paused: Optional[Callable[[str], None]] = None
        self.on_recording_resumed: Optional[Callable[[str], None]] = None
        self.on_recording_error: Optional[Callable[[str, str], None]] = None
        self.on_upload_started: Optional[Callable[[str, str], None]] = None  # (task_id, filename)
        self.on_upload_completed: Optional[Callable[[str], None]] = None  # (task_id)
        self.on_upload_failed: Optional[Callable[[str, str], None]] = None  # (task_id, error)

        logging.info("RecordingManager initialized with smart recording capabilities")

    def initialize(self) -> bool:
        """
        Initialize recording components if recording is enabled.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logging.info(
                f"RecordingManager.initialize() called - RECORDING_ENABLED={getattr(self.settings, 'RECORDING_ENABLED', None)}, OUTPUT_DIR={getattr(self.settings, 'RECORDING_OUTPUT_DIR', None)}"
            )
            if not self.settings.RECORDING_ENABLED:
                logging.info("Recording is disabled in settings")
                return True

            if not self.settings.validate_recording_config():
                logging.error("Recording configuration validation failed")
                return False

            # Note: SmartSessionRecorder will be created per session, not globally
            # This allows each session to have its own intelligent recording instance

            # Initialize FileRotationManager
            self.rotation_manager = FileRotationManager(
                recordings_dir=self.settings.RECORDING_OUTPUT_DIR,
                max_total_size_gb=self.settings.RECORDING_MAX_TOTAL_SIZE_GB,
                max_file_age_days=self.settings.RECORDING_MAX_FILE_AGE_DAYS,
                cleanup_interval_hours=self.settings.RECORDING_CLEANUP_INTERVAL_HOURS,
            )

            # Start automatic cleanup
            self.rotation_manager.start_automatic_cleanup()

            # Initialize API upload manager if available and enabled
            if (
                API_AVAILABLE
                and hasattr(self.settings, "API_ENABLED")
                and self.settings.API_ENABLED
            ):
                try:
                    self.api_manager = ApiIntegrationManager(self.settings)
                    if self.api_manager.is_initialized:
                        # Set up callbacks for upload events
                        self.api_manager.on_upload_started = self._on_api_upload_started
                        self.api_manager.on_upload_completed = self._on_api_upload_completed
                        self.api_manager.on_upload_failed = self._on_api_upload_failed

                        logging.info("API upload system initialized successfully")

                        # Upload any older recordings if configured
                        if (
                            hasattr(self.settings, "API_UPLOAD_OLDER_RECORDINGS")
                            and self.settings.API_UPLOAD_OLDER_RECORDINGS
                        ):
                            self._upload_older_recordings_async()
                    else:
                        logging.warning("API upload system failed to initialize")
                        self.api_manager = None
                except Exception as e:
                    logging.error(f"Failed to initialize API upload system: {e}")
                    self.api_manager = None
            elif hasattr(self.settings, "API_ENABLED") and self.settings.API_ENABLED:
                logging.warning("API upload is enabled but API system is not available")

            self.is_initialized = True
            logging.info("Recording system initialized successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to initialize recording system: {e}", exc_info=True)
            self.is_initialized = False
            return False

    def start_session_recording(self, session_id: str, connection_info: Dict[str, Any]) -> bool:
        """
        Start intelligent recording for a new session.

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

            # Create recording configuration
            recording_config = self._create_recording_config()

            # Create smart recorder for this session
            self.smart_recorder = SmartSessionRecorder(
                output_dir=self.settings.RECORDING_OUTPUT_DIR,
                connection_info=connection_info,
                recording_config=recording_config,
            )

            # Set callbacks for smart recorder
            self.smart_recorder.set_callbacks(
                on_started=self._on_smart_recording_started,
                on_stopped=self._on_smart_recording_stopped,
                on_paused=self._on_smart_recording_paused,
                on_resumed=self._on_smart_recording_resumed,
                on_new_segment=self._on_new_segment_created,
            )

            # Start intelligent recording
            if self.smart_recorder.start_recording(session_id):
                self.current_session_id = session_id
                self.current_connection_info = connection_info

                # Call callback if set
                if self.on_recording_started:
                    try:
                        self.on_recording_started(session_id)
                    except Exception as e:
                        logging.error(f"Error in recording started callback: {e}")

                logging.info(f"Started intelligent recording for session {session_id}")
                return True
            else:
                logging.error(f"Failed to start intelligent recording for session {session_id}")
                self.smart_recorder = None
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
        Stop the current intelligent recording session.

        Returns:
            True if recording stopped successfully, False otherwise
        """
        try:
            if not self.is_recording():
                logging.debug("No recording in progress")
                return True

            session_id = self.current_session_id

            # Stop smart recorder and get created files
            created_files = []
            if self.smart_recorder:
                created_files = self.smart_recorder.stop_recording()

            # Process created files for compression and upload
            if created_files:
                # Optionally compress recordings before upload
                try:
                    compression_enabled = getattr(
                        self.settings, "RECORDING_COMPRESSION_ENABLED", True
                    )
                    compression_crf = getattr(self.settings, "RECORDING_COMPRESSION_CRF", 28)
                except Exception:
                    compression_enabled = True
                    compression_crf = 28

                if compression_enabled:
                    # Compress in background to avoid blocking shutdown
                    for file_path in created_files:
                        try:
                            Thread = threading.Thread
                            t = Thread(
                                target=self._compress_recording_async,
                                args=(Path(file_path), compression_crf),
                                daemon=True,
                            )
                            t.start()
                            logging.info(
                                f"Started background compression for {Path(file_path).name}"
                            )
                        except Exception as e:
                            logging.warning(f"Failed to start compression thread: {e}")

                # Trigger upload if API is available and auto_upload is enabled
                if (
                    self.api_manager
                    and hasattr(self.settings, "API_AUTO_UPLOAD")
                    and self.settings.API_AUTO_UPLOAD
                ):
                    for file_path in created_files:
                        self._queue_recording_upload(session_id, file_path)

                # Call callback if set
                if self.on_recording_stopped:
                    try:
                        self.on_recording_stopped(session_id)
                    except Exception as e:
                        logging.error(f"Error in recording stopped callback: {e}")

                self.current_session_id = None
                self.current_connection_info = None
                self.smart_recorder = None

                logging.info(
                    f"Stopped intelligent recording for session {session_id}, created {len(created_files)} files"
                )
                return True
            else:
                logging.error("Failed to stop recording - no files created")
                self.smart_recorder = None
                return False

        except Exception as e:
            logging.error(f"Error stopping session recording: {e}")
            return False

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return (
            self.is_initialized
            and self.smart_recorder is not None
            and self.current_session_id is not None
        )

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
                "current_connection_info": self.current_connection_info,
            }

            if self.is_recording() and self.smart_recorder:
                recording_info = self.smart_recorder.get_recording_info()
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
                "error": str(e),
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

            connection_id = connection_info.get("con_codigo", "unknown")
            session_id = f"session_{connection_id}_{int(time.time())}"

            if event_type == "connect":
                if self.settings.RECORDING_AUTO_START:
                    self.start_session_recording(session_id, connection_info)

            elif event_type == "disconnect":
                if self.is_recording():
                    # Check if the disconnected connection matches current recording
                    if (
                        self.current_connection_info
                        and self.current_connection_info.get("con_codigo") == connection_id
                    ):
                        self.stop_session_recording()

            elif event_type == "heartbeat":
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

    def set_callbacks(
        self,
        on_started: Optional[Callable[[str], None]] = None,
        on_stopped: Optional[Callable[[str], None]] = None,
        on_paused: Optional[Callable[[str], None]] = None,
        on_resumed: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None,
    ):
        """
        Set callback functions for recording events.

        Args:
            on_started: Called when recording starts (session_id)
            on_stopped: Called when recording stops (session_id)
            on_paused: Called when recording is paused (reason)
            on_resumed: Called when recording is resumed (reason)
            on_error: Called on recording error (session_id, error_message)
        """
        self.on_recording_started = on_started
        self.on_recording_stopped = on_stopped
        self.on_recording_paused = on_paused
        self.on_recording_resumed = on_resumed
        self.on_recording_error = on_error

    def _create_recording_config(self) -> Dict[str, Any]:
        """Create recording configuration from config.json and settings."""
        try:
            # Import WATS config system
            from ..config import get_config

            # Get config from config.json
            wats_config = get_config()
            recording_config_dict = wats_config.get("recording", {})

            # Import smart recording config
            from .smart_recording_config import get_smart_recording_config

            # Combine config.json + settings
            config = get_smart_recording_config(recording_config_dict, self.settings)

            logging.info("Smart recording config loaded from config.json and settings")
            return config

        except ImportError as e:
            logging.warning(f"Could not load WATS config system: {e}")
            # Fallback to settings-only configuration
            return self._create_fallback_recording_config()
        except Exception as e:
            logging.error(f"Error loading smart recording config: {e}")
            # Fallback to settings-only configuration
            return self._create_fallback_recording_config()

    def _create_fallback_recording_config(self) -> Dict[str, Any]:
        """Create fallback recording configuration from settings only."""
        return {
            "fps": getattr(self.settings, "RECORDING_FPS", 30),
            "quality": getattr(self.settings, "RECORDING_QUALITY", 75),
            "resolution_scale": getattr(self.settings, "RECORDING_RESOLUTION_SCALE", 1.0),
            "inactivity_timeout_minutes": getattr(
                self.settings, "RECORDING_INACTIVITY_TIMEOUT_MINUTES", 10
            ),
            "create_new_file_after_pause": getattr(
                self.settings, "RECORDING_CREATE_NEW_FILE_AFTER_PAUSE", True
            ),
            "pause_on_minimized": getattr(self.settings, "RECORDING_PAUSE_ON_MINIMIZED", True),
            "pause_on_covered": getattr(self.settings, "RECORDING_PAUSE_ON_COVERED", True),
            "max_file_duration_minutes": getattr(
                self.settings, "RECORDING_MAX_DURATION_MINUTES", 30
            ),
            "max_file_size_mb": getattr(self.settings, "RECORDING_MAX_FILE_SIZE_MB", 100),
            "window_tracking_interval": getattr(
                self.settings, "RECORDING_WINDOW_TRACKING_INTERVAL", 1.0
            ),
            "compression_enabled": getattr(self.settings, "RECORDING_COMPRESSION_ENABLED", True),
            "compression_cr": getattr(self.settings, "RECORDING_COMPRESSION_CRF", 28),
            "debug_window_tracking": getattr(
                self.settings, "RECORDING_DEBUG_WINDOW_TRACKING", False
            ),
            "debug_activity_monitoring": getattr(
                self.settings, "RECORDING_DEBUG_ACTIVITY_MONITORING", False
            ),
        }

    # Smart recorder callbacks
    def _on_smart_recording_started(self, session_id: str):
        """Callback when smart recording starts."""
        logging.info(f"Smart recording started for session {session_id}")

    def _on_smart_recording_stopped(self, session_id: str):
        """Callback when smart recording stops."""
        logging.info(f"Smart recording stopped for session {session_id}")

    def _on_smart_recording_paused(self, reason: str):
        """Callback when smart recording is paused."""
        logging.info(f"Smart recording paused: {reason}")
        if self.on_recording_paused:
            try:
                self.on_recording_paused(reason)
            except Exception as e:
                logging.error(f"Error in recording paused callback: {e}")

    def _on_smart_recording_resumed(self, reason: str):
        """Callback when smart recording is resumed."""
        logging.info(f"Smart recording resumed: {reason}")
        if self.on_recording_resumed:
            try:
                self.on_recording_resumed(reason)
            except Exception as e:
                logging.error(f"Error in recording resumed callback: {e}")

    def _on_new_segment_created(self, segment):
        """Callback when a new recording segment is created."""
        logging.info(
            f"New recording segment created: {segment.file_path.name} (reason: {segment.reason})"
        )

    def _queue_recording_upload_legacy(self, session_id: str, file_path: str):
        """Queue a recording file for upload (versão antiga)."""
        if self.api_manager:
            try:
                self.api_manager.queue_upload(file_path, session_id)
                logging.info(f"Queued recording for upload: {Path(file_path).name}")
            except Exception as e:
                logging.error(f"Failed to queue upload for {file_path}: {e}")

    def _compress_recording_async_legacy(self, video_file: Path, crf: int):
        """Compress a recording file asynchronously (versão antiga)."""
        try:
            if not video_file.exists():
                logging.warning(f"Compression requested but file not found: {video_file}")
                return

            ffmpeg_cmd = shutil.which("ffmpeg")
            if not ffmpeg_cmd:
                logging.warning("ffmpeg not found in PATH; skipping compression")
                return

            tmp_file = video_file.with_suffix(".tmp.mp4")

            # Build ffmpeg command
            cmd = [
                ffmpeg_cmd,
                "-y",
                "-i",
                str(video_file),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                str(crf),
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                str(tmp_file),
            ]

            logging.info(f"Compressing {video_file.name} -> CRF={crf}")
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if proc.returncode != 0:
                logging.error(f"ffmpeg failed for {video_file.name}: {proc.stderr}")
                if tmp_file.exists():
                    tmp_file.unlink()
                return

            # Replace original with compressed file
            try:
                backup = video_file.with_suffix(".bak.mp4")
                video_file.rename(backup)
                tmp_file.rename(video_file)
                backup.unlink()
                logging.info(f"Compression completed and replaced original: {video_file.name}")
            except Exception as e:
                logging.error(f"Failed to replace original file after compression: {e}")
                if tmp_file.exists():
                    tmp_file.unlink()

        except Exception as e:
            logging.error(f"Unexpected error during compression: {e}")

    def shutdown(self):
        """Shutdown the recording manager and cleanup resources."""
        try:
            if self.is_recording():
                self.stop_session_recording()

            if self.rotation_manager:
                self.rotation_manager.stop_automatic_cleanup()

            if self.api_manager:
                self.api_manager.shutdown()

            self.is_initialized = False
            logging.info("Recording manager shutdown completed")

        except Exception as e:
            logging.error(f"Error during recording manager shutdown: {e}")

    # API Upload Integration Methods

    def _queue_recording_upload(self, session_id: str):
        """Queue the completed recording for upload."""
        if not self.api_manager:
            return

        try:
            # Find the recording files
            recordings_dir = Path(self.settings.RECORDING_OUTPUT_DIR)

            # Look for video file
            video_files = list(recordings_dir.glob(f"{session_id}_*.mp4"))
            if not video_files:
                logging.warning(f"No video file found for session {session_id}")
                return

            video_file = video_files[0]  # Take the first matching file

            # Look for metadata file
            metadata_file = recordings_dir / f"{session_id}_metadata.json"
            if not metadata_file.exists():
                logging.warning(f"No metadata file found for session {session_id}")
                return

            # Queue the upload
            task_id = self.api_manager.upload_recording(video_file, metadata_file)
            if task_id:
                logging.info(f"Queued recording upload: {video_file.name} (task: {task_id})")
            else:
                logging.error(f"Failed to queue recording upload for session {session_id}")

        except Exception as e:
            logging.error(f"Error queuing recording upload for {session_id}: {e}")

    def _compress_recording_async(self, video_file: Path, crf: int = 28):
        """Compress a recording file using ffmpeg in a background thread.

        Replaces the original file on success (keeps original on failure).
        """
        try:
            if not video_file.exists():
                logging.warning(f"Compression requested but file not found: {video_file}")
                return

            ffmpeg_cmd = shutil.which("ffmpeg")
            if not ffmpeg_cmd:
                logging.warning("ffmpeg not found in PATH; skipping compression")
                return

            tmp_file = video_file.with_suffix(".tmp.mp4")
            # Build ffmpeg command: re-encode with libx264 and CRF
            cmd = [
                ffmpeg_cmd,
                "-y",
                "-i",
                str(video_file),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                str(crf),
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                str(tmp_file),
            ]

            logging.info(f"Compressing {video_file.name} -> CRF={crf}")
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                logging.error(f"ffmpeg failed for {video_file.name}: {proc.stderr}")
                if tmp_file.exists():
                    try:
                        tmp_file.unlink()
                    except Exception:
                        pass
                return

            # Replace original with compressed file
            try:
                backup = video_file.with_suffix(".bak.mp4")
                video_file.rename(backup)
                tmp_file.rename(video_file)
                try:
                    backup.unlink()
                except Exception:
                    logging.debug(f"Could not remove backup {backup}")
                logging.info(f"Compression completed and replaced original: {video_file.name}")
            except Exception as e:
                logging.error(f"Failed to replace original file after compression: {e}")
                # Cleanup tmp
                if tmp_file.exists():
                    try:
                        tmp_file.unlink()
                    except Exception:
                        pass

        except Exception as e:
            logging.error(f"Unexpected error during compression: {e}", exc_info=True)

    def _upload_older_recordings_async(self):
        """Upload older recordings in a background thread."""

        def upload_task():
            try:
                recordings_dir = Path(self.settings.RECORDING_OUTPUT_DIR)
                task_ids = self.api_manager.upload_older_recordings(recordings_dir)
                if task_ids:
                    logging.info(f"Queued {len(task_ids)} older recordings for upload")
            except Exception as e:
                logging.error(f"Error uploading older recordings: {e}")

        upload_thread = threading.Thread(target=upload_task, daemon=True)
        upload_thread.start()

    def _on_api_upload_started(self, task_id: str, filename: str):
        """Internal callback for API upload started."""
        logging.info(f"Upload started: {filename} (task: {task_id})")
        if self.on_upload_started:
            try:
                self.on_upload_started(task_id, filename)
            except Exception as e:
                logging.error(f"Error in upload started callback: {e}")

    def _on_api_upload_completed(self, task_id: str, server_file_id: str):
        """Internal callback for API upload completed."""
        logging.info(f"Upload completed: {task_id} -> {server_file_id}")
        if self.on_upload_completed:
            try:
                self.on_upload_completed(task_id)
            except Exception as e:
                logging.error(f"Error in upload completed callback: {e}")

    def _on_api_upload_failed(self, task_id: str, error: str):
        """Internal callback for API upload failed."""
        logging.warning(f"Upload failed: {task_id} - {error}")
        if self.on_upload_failed:
            try:
                self.on_upload_failed(task_id, error)
            except Exception as e:
                logging.error(f"Error in upload failed callback: {e}")

    # Public API Upload Methods

    def manual_upload_recording(self, session_id: str) -> Optional[str]:
        """
        Manually trigger upload of a specific recording.

        Args:
            session_id: Session ID of the recording to upload

        Returns:
            Upload task ID if successful, None otherwise
        """
        if not self.api_manager:
            logging.warning("API upload not available")
            return None

        try:
            recordings_dir = Path(self.settings.RECORDING_OUTPUT_DIR)

            # Find video file
            video_files = list(recordings_dir.glob(f"{session_id}_*.mp4"))
            if not video_files:
                logging.error(f"No video file found for session {session_id}")
                return None

            video_file = video_files[0]
            metadata_file = recordings_dir / f"{session_id}_metadata.json"

            if not metadata_file.exists():
                logging.error(f"No metadata file found for session {session_id}")
                return None

            return self.api_manager.upload_recording(video_file, metadata_file)

        except Exception as e:
            logging.error(f"Error in manual upload for {session_id}: {e}")
            return None

    def get_upload_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an upload task."""
        if not self.api_manager:
            return None

        return self.api_manager.get_upload_status(task_id)

    def get_upload_queue_status(self) -> Dict[str, Any]:
        """Get the status of the upload queue."""
        if not self.api_manager:
            return {
                "queue_size": 0,
                "active_uploads": 0,
                "completed_uploads": 0,
                "failed_uploads": 0,
                "is_running": False,
            }

        return self.api_manager.get_queue_status()

    def retry_failed_upload(self, task_id: str) -> bool:
        """Retry a failed upload."""
        if not self.api_manager:
            return False

        return self.api_manager.retry_failed_upload(task_id)

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        self.shutdown()
