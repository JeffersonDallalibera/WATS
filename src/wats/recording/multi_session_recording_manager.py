# Multi-session recording manager for WATS
# Supports multiple concurrent RDP session recordings

import logging
import threading
import subprocess
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from .session_recorder import SessionRecorder
from ..config import get_config


class MultiSessionRecordingManager:
    """
    Recording manager that supports multiple concurrent recording sessions.
    Each RDP session can be recorded independently.
    """
    
    def __init__(self):
        """Initialize the multi-session recording manager."""
        self.active_recordings: Dict[str, SessionRecorder] = {}
        self.recording_configs: Dict[str, Dict[str, Any]] = {}
        self.callbacks: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        self.settings = None
        
        logging.info("MultiSessionRecordingManager initialized")
    
    def initialize(self, settings) -> bool:
        """
        Initialize the recording manager with settings.
        
        Args:
            settings: Application settings
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.settings = settings
            logging.info(f"MultiSessionRecordingManager initialized with recording enabled: {settings.RECORDING_ENABLED}")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize MultiSessionRecordingManager: {e}")
            return False
    
    def start_session_recording(self, session_id: str, connection_info: Dict[str, Any], 
                               callback: Optional[Callable] = None) -> bool:
        """
        Start recording for a specific session.
        
        Args:
            session_id: Unique identifier for the session
            connection_info: Information about the RDP connection
            callback: Optional callback when recording stops
            
        Returns:
            True if recording started successfully, False otherwise
        """
        with self._lock:
            if session_id in self.active_recordings:
                logging.warning(f"Recording already active for session {session_id}")
                return False
            
            try:
                # Get recording configuration
                config = get_config()
                recording_config = config.get('recording', {})
                
                # Override with settings if available
                if self.settings:
                    recording_config.update({
                        'enabled': self.settings.RECORDING_ENABLED,
                        'output_dir': self.settings.RECORDING_OUTPUT_DIR,
                        'fps': getattr(self.settings, 'RECORDING_FPS', recording_config.get('fps', 30)),
                        'quality': getattr(self.settings, 'RECORDING_QUALITY', recording_config.get('quality', 75)),
                        'mode': getattr(self.settings, 'RECORDING_MODE', recording_config.get('mode', 'rdp_window')),
                        'compress_enabled': getattr(self.settings, 'RECORDING_COMPRESSION_ENABLED', recording_config.get('compress_enabled', True)),
                        'compress_crf': getattr(self.settings, 'RECORDING_COMPRESSION_CRF', recording_config.get('compress_crf', 28))
                    })
                
                # Store the recording config for this session
                self.recording_configs[session_id] = recording_config
                
                # Create and start the recorder
                # Note: SessionRecorder automatically sanitizes connection_info to protect sensitive data
                recorder = SessionRecorder(connection_info, recording_config)
                if recorder.start_recording():
                    self.active_recordings[session_id] = recorder
                    if callback:
                        self.callbacks[session_id] = callback
                    logging.info(f"Started recording for session {session_id} with session protection enabled")
                    return True
                else:
                    logging.error(f"Failed to start recording for session {session_id}")
                    return False
                    
            except Exception as e:
                logging.error(f"Error starting recording for session {session_id}: {e}")
                return False
    
    def stop_session_recording(self, session_id: str) -> bool:
        """
        Stop recording for a specific session.
        
        Args:
            session_id: Session identifier to stop recording for
            
        Returns:
            True if recording stopped successfully, False otherwise
        """
        with self._lock:
            if session_id not in self.active_recordings:
                logging.warning(f"No active recording found for session {session_id}")
                return False
            
            try:
                recorder = self.active_recordings[session_id]
                video_path = recorder.stop_recording()
                
                # Remove from active recordings
                del self.active_recordings[session_id]
                
                if video_path:
                    logging.info(f"Stopped recording for session {session_id}, saved to: {video_path}")
                    
                    # Start compression in background if enabled
                    recording_config = self.recording_configs.get(session_id, {})
                    if recording_config.get('compress_enabled', False):
                        self._compress_recording_async(video_path, recording_config)
                    
                    # Call callback if provided
                    if session_id in self.callbacks:
                        try:
                            self.callbacks[session_id](video_path)
                        except Exception as e:
                            logging.error(f"Error calling callback for session {session_id}: {e}")
                        finally:
                            del self.callbacks[session_id]
                    
                    # Clean up config
                    if session_id in self.recording_configs:
                        del self.recording_configs[session_id]
                    
                    return True
                else:
                    logging.error(f"Failed to stop recording for session {session_id}")
                    return False
                    
            except Exception as e:
                logging.error(f"Error stopping recording for session {session_id}: {e}")
                return False
    
    def stop_all_recordings(self) -> List[str]:
        """
        Stop all active recordings.
        
        Returns:
            List of session IDs that were stopped
        """
        stopped_sessions = []
        with self._lock:
            session_ids = list(self.active_recordings.keys())
        
        for session_id in session_ids:
            if self.stop_session_recording(session_id):
                stopped_sessions.append(session_id)
        
        return stopped_sessions
    
    def is_recording(self, session_id: Optional[str] = None) -> bool:
        """
        Check if a specific session is recording, or if any recording is active.
        
        Args:
            session_id: Optional session ID to check specifically
            
        Returns:
            True if recording is active for the session (or any session if session_id is None)
        """
        with self._lock:
            if session_id:
                return session_id in self.active_recordings
            else:
                return len(self.active_recordings) > 0
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of all active recording session IDs.
        
        Returns:
            List of session IDs currently being recorded
        """
        with self._lock:
            return list(self.active_recordings.keys())
    
    def get_recording_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get status information for a specific recording session.
        
        Args:
            session_id: Session ID to get status for
            
        Returns:
            Dictionary with recording status information
        """
        with self._lock:
            if session_id not in self.active_recordings:
                return {'active': False, 'session_id': session_id}
            
            recorder = self.active_recordings[session_id]
            return {
                'active': True,
                'session_id': session_id,
                'duration': recorder.get_recording_duration(),
                'frame_count': getattr(recorder, 'frame_count', 0),
                'output_path': getattr(recorder, 'output_path', 'Unknown')
            }
    
    def get_all_recording_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status for all active recording sessions.
        
        Returns:
            Dictionary mapping session IDs to their status information
        """
        status = {}
        with self._lock:
            for session_id in self.active_recordings:
                status[session_id] = self.get_recording_status(session_id)
        return status
    
    def handle_connection_event(self, event_type: str, session_id: str, connection_info: Dict[str, Any]):
        """
        Handle connection events for multiple sessions.
        
        Args:
            event_type: Type of event ('connect', 'disconnect', 'heartbeat')
            session_id: Session identifier
            connection_info: Information about the connection
        """
        try:
            if not self.settings or not self.settings.RECORDING_ENABLED:
                return
                
            if event_type == 'connect':
                if getattr(self.settings, 'RECORDING_AUTO_START', False):
                    self.start_session_recording(session_id, connection_info)
                    
            elif event_type == 'disconnect':
                if self.is_recording(session_id):
                    self.stop_session_recording(session_id)
                        
            elif event_type == 'heartbeat':
                # Heartbeat events can be used to monitor active sessions
                pass
                
        except Exception as e:
            logging.error(f"Error handling connection event {event_type} for session {session_id}: {e}")
    
    def _compress_recording_async(self, video_path: str, recording_config: Dict[str, Any]):
        """
        Compress a recording file using ffmpeg in a background thread.
        
        Args:
            video_path: Path to the video file to compress
            recording_config: Recording configuration with compression settings
        """
        def compress_task():
            try:
                video_file = Path(video_path)
                if not video_file.exists():
                    logging.warning(f"Compression requested but file not found: {video_file}")
                    return

                ffmpeg_cmd = shutil.which('ffmpeg')
                if not ffmpeg_cmd:
                    logging.warning("ffmpeg not found in PATH; skipping compression")
                    return

                crf = recording_config.get('compress_crf', 28)
                tmp_file = video_file.with_suffix('.tmp.mp4')
                
                # Build ffmpeg command
                cmd = [
                    ffmpeg_cmd,
                    '-y',
                    '-i', str(video_file),
                    '-c:v', 'libx264',
                    '-preset', 'veryfast',
                    '-crf', str(crf),
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    str(tmp_file)
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
                    backup = video_file.with_suffix('.bak.mp4')
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
        
        # Start compression in background thread
        compress_thread = threading.Thread(target=compress_task, daemon=True)
        compress_thread.start()
    
    def shutdown(self):
        """Shutdown the recording manager and cleanup resources."""
        try:
            stopped_sessions = self.stop_all_recordings()
            if stopped_sessions:
                logging.info(f"Stopped recordings for sessions: {stopped_sessions}")
            
            logging.info("MultiSessionRecordingManager shutdown completed")
            
        except Exception as e:
            logging.error(f"Error during MultiSessionRecordingManager shutdown: {e}")