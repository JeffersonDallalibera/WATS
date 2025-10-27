# WATS_Project/wats_app/recording/session_recorder.py

import cv2
import mss
import numpy as np
import threading
import time
import os
import logging
import psutil
import win32gui
import win32con
import win32process
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path

class SessionRecorder:
    """
    Lightweight session recorder for WATS application.
    Features:
    - Low CPU/memory usage with MSS screen capture
    - H.264 compression for efficient storage
    - File rotation based on size and time
    - Thread-safe recording operations
    """
    
    def __init__(self, output_dir: str, max_file_size_mb: int = 100, 
                 max_duration_minutes: int = 30, fps: int = 10,
                 quality: int = 23, resolution_scale: float = 1.0,
                 recording_mode: str = "full_screen"):
        """
        Initialize the session recorder.
        
        Args:
            output_dir: Directory to save recordings
            max_file_size_mb: Maximum file size before rotation (MB)
            max_duration_minutes: Maximum recording duration before rotation (minutes)
            fps: Frames per second for recording
            quality: H.264 quality (0-51, lower is better quality)
            resolution_scale: Scale factor for resolution (1.0 = full, 0.5 = half)
            recording_mode: "full_screen", "rdp_window", or "active_window"
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.max_duration = max_duration_minutes * 60  # Convert to seconds
        self.fps = fps
        self.quality = quality
        self.resolution_scale = resolution_scale
        self.recording_mode = recording_mode.lower()
        
        # Validate recording mode
        valid_modes = ["full_screen", "rdp_window", "active_window"]
        if self.recording_mode not in valid_modes:
            logging.warning(f"Invalid recording mode '{recording_mode}', using 'full_screen'")
            self.recording_mode = "full_screen"
        
        # Recording state
        self.is_recording = False
        self.recording_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Current recording info
        self.current_writer: Optional[cv2.VideoWriter] = None
        self.current_file: Optional[Path] = None
        self.recording_start_time: Optional[float] = None
        self.session_id: Optional[str] = None
        self.target_window_handle: Optional[int] = None
        self.target_process_name: Optional[str] = None
        
        # Screen capture setup
        self.sct = mss.mss()
        self.monitor = self._get_monitor_config()
        
        logging.info(f"SessionRecorder initialized - Output: {self.output_dir}, "
                    f"Max size: {max_file_size_mb}MB, Max duration: {max_duration_minutes}min, "
                    f"FPS: {fps}, Quality: {quality}, Scale: {resolution_scale}, Mode: {self.recording_mode}")

    def _get_monitor_config(self) -> Dict[str, int]:
        """Get monitor configuration based on recording mode."""
        if self.recording_mode == "full_screen":
            monitor = self.sct.monitors[0]  # Full screen (all monitors)
        else:
            # For window-specific recording, start with full screen
            # Will be updated dynamically during recording
            monitor = self.sct.monitors[1] if len(self.sct.monitors) > 1 else self.sct.monitors[0]
        
        # Apply resolution scaling
        if self.resolution_scale != 1.0:
            width = int(monitor["width"] * self.resolution_scale)
            height = int(monitor["height"] * self.resolution_scale)
            monitor = {
                "top": monitor["top"],
                "left": monitor["left"],
                "width": width,
                "height": height
            }
        
        return monitor

    def _try_restore_window(self, hwnd: int) -> bool:
        """Try to restore a minimized window."""
        try:
            # Check if window is minimized
            if win32gui.IsIconic(hwnd):
                logging.info("Window is minimized, attempting to restore")
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.5)  # Give time for window to restore
                return True
            return False
        except Exception as e:
            logging.warning(f"Failed to restore window: {e}")
            return False

    def _find_rdp_window(self, connection_info: Dict[str, Any]) -> Optional[int]:
        """Find RDP window handle based on connection information."""
        try:
            target_title = connection_info.get('name', '')
            target_ip = connection_info.get('ip', '')
            
            # Extract IP and port from connection info
            if ':' in target_ip:
                ip_part = target_ip.split(':')[0]
            else:
                ip_part = target_ip
            
            def enum_window_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd).lower()
                    
                    # Look for RDP-related window titles with specific connection info
                    rdp_indicators = [
                        'remote desktop connection',
                        'área de trabalho remota',
                        'rdp',
                        'mstsc'
                    ]
                    
                    # Check if window title contains RDP indicators
                    is_rdp_window = any(indicator in window_title for indicator in rdp_indicators)
                    
                    # Also check if title contains target info
                    title_contains_target = False
                    if target_title:
                        title_contains_target = target_title.lower() in window_title
                    if ip_part:
                        title_contains_target = title_contains_target or ip_part in window_title
                    
                    if is_rdp_window or title_contains_target:
                        try:
                            # Get process info to verify it's an RDP-related process
                            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                            process = psutil.Process(process_id)
                            process_name = process.name().lower()
                            
                            # Check if it's a known RDP process
                            rdp_processes = ['mstsc.exe', 'rdp.exe', 'rdpclip.exe']
                            if any(rdp_proc in process_name for rdp_proc in rdp_processes):
                                windows.append({
                                    'hwnd': hwnd,
                                    'title': window_title,
                                    'process_name': process_name,
                                    'process_id': process_id,
                                    'score': 2 if title_contains_target else 1  # Higher score for exact match
                                })
                            elif is_rdp_window:  # RDP indicator in title but different process
                                windows.append({
                                    'hwnd': hwnd,
                                    'title': window_title,
                                    'process_name': process_name,
                                    'process_id': process_id,
                                    'score': 1
                                })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass  # Skip this window if we can't access process info
                
                return True
            
            windows = []
            win32gui.EnumWindows(enum_window_callback, windows)
            
            if windows:
                # Sort by score (highest first) and return the best match
                windows.sort(key=lambda x: x['score'], reverse=True)
                best_match = windows[0]
                hwnd = best_match['hwnd']
                logging.info(f"Found RDP window: {best_match['title']} (PID: {best_match['process_id']}, Score: {best_match['score']})")
                
                # Try to restore if minimized
                self._try_restore_window(hwnd)
                
                return hwnd
            else:
                logging.warning("No RDP window found, falling back to full screen recording")
                return None
                
        except Exception as e:
            logging.error(f"Error finding RDP window: {e}")
            return None

    def _get_active_window(self) -> Optional[int]:
        """Get the currently active window handle."""
        try:
            return win32gui.GetForegroundWindow()
        except Exception as e:
            logging.error(f"Error getting active window: {e}")
            return None

    def _get_window_rect(self, hwnd: int) -> Optional[Dict[str, int]]:
        """Get window rectangle coordinates."""
        try:
            rect = win32gui.GetWindowRect(hwnd)
            window_rect = {
                "left": rect[0],
                "top": rect[1],
                "width": rect[2] - rect[0],
                "height": rect[3] - rect[1]
            }
            
            # Check if window is minimized or off-screen
            if (window_rect["left"] < -1000 or window_rect["top"] < -1000 or 
                window_rect["width"] < 100 or window_rect["height"] < 100):
                logging.warning(f"Window appears minimized or invalid: {window_rect}")
                return None
                
            return window_rect
        except Exception as e:
            logging.error(f"Error getting window rect: {e}")
            return None

    def _update_monitor_for_window(self, hwnd: int):
        """Update monitor configuration for specific window."""
        window_rect = self._get_window_rect(hwnd)
        if window_rect:
            # Apply resolution scaling
            if self.resolution_scale != 1.0:
                window_rect["width"] = int(window_rect["width"] * self.resolution_scale)
                window_rect["height"] = int(window_rect["height"] * self.resolution_scale)
            
            self.monitor = window_rect
            logging.info(f"Updated monitor for window: {window_rect}")
        else:
            logging.warning("Window rect invalid, switching to full screen recording")
            # Switch to full screen mode when window is not properly visible
            self.recording_mode = "full_screen"
            self.target_window_handle = None
            self.monitor = self._get_monitor_config()

    def _sanitize_connection_info(self, connection_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive information from connection_info before saving to metadata.
        Implements session protection by not storing passwords and sensitive session data.
        
        Args:
            connection_info: Original connection information dictionary
            
        Returns:
            Sanitized dictionary without passwords, usernames, or session data
        """
        if not connection_info:
            return {}
        
        # Check if session protection is enabled in config
        try:
            from ..config import get_config
            config = get_config()
            protection_config = config.get('recording', {}).get('session_protection', {})
            
            protection_enabled = protection_config.get('enabled', True)
            sanitize_metadata = protection_config.get('sanitize_metadata', True)
            remove_sensitive = protection_config.get('remove_sensitive_fields', True)
            log_actions = protection_config.get('log_protection_actions', True)
            
            if not protection_enabled or not sanitize_metadata:
                if log_actions:
                    logging.warning("Session protection is DISABLED - sensitive data may be stored in metadata")
                return connection_info.copy()
                
        except Exception as e:
            # If config loading fails, default to protection enabled
            logging.warning(f"Could not load session protection config, defaulting to enabled: {e}")
            remove_sensitive = True
            log_actions = True
        
        # Define sensitive fields that should NOT be saved to disk/database
        sensitive_fields = {
            'password', 'senha', 'pass', 'pwd', 'passwd', 'passw',
            'user', 'username', 'usuario', 'login', 'user_name', 'userid',
            'session_id', 'session_token', 'token', 'auth_token', 'access_token',
            'credentials', 'credential', 'auth', 'authentication', 'authdata',
            'private_key', 'key', 'secret', 'hash', 'cert', 'certificate',
            'domain', 'dominio', 'dn', 'distinguished_name'
        }
        
        # Create sanitized copy - only keep safe fields
        sanitized = {}
        sensitive_count = 0
        
        for key, value in connection_info.items():
            key_lower = key.lower()
            
            # Check if this field contains sensitive information
            is_sensitive = any(sensitive_field in key_lower for sensitive_field in sensitive_fields)
            
            if not is_sensitive or not remove_sensitive:
                # Keep non-sensitive fields like: name, ip, port, connection_type, etc.
                sanitized[key] = value
            else:
                # Replace sensitive data with protection placeholder
                sanitized[key] = "[PROTECTED_BY_SESSION_SECURITY]"
                sensitive_count += 1
        
        # Always include some basic metadata for identification (if available)
        safe_fields = ['name', 'ip', 'host', 'hostname', 'server', 'port', 'connection_type', 'protocol', 'connection_name']
        for field in safe_fields:
            if field in connection_info and field not in sanitized:
                sanitized[field] = connection_info[field]
        
        # Add security protection metadata
        sanitized['_session_protection'] = {
            'enabled': True,
            'sanitized_at': datetime.now().isoformat(),
            'sensitive_fields_removed': sensitive_count,
            'protection_notice': 'Authentication credentials and session data are protected and not stored'
        }
        
        if log_actions:
            logging.info(f"Session protection applied - sanitized {sensitive_count} sensitive fields from connection metadata")
        
        return sanitized

    def start_recording(self, session_id: str, connection_info: Dict[str, Any]) -> bool:
        """
        Start recording a session.
        
        Args:
            session_id: Unique identifier for this session
            connection_info: Dictionary with connection details (ip, name, user, etc.)
            
        Returns:
            True if recording started successfully, False otherwise
        """
        if self.is_recording:
            logging.warning(f"Recording already in progress for session {self.session_id}")
            return False
            
        try:
            self.session_id = session_id
            self.stop_event.clear()
            
            # Set up window tracking based on recording mode
            if self.recording_mode == "rdp_window":
                self.target_window_handle = self._find_rdp_window(connection_info)
                if self.target_window_handle:
                    # Try to get window position - if invalid, fallback to full screen
                    window_rect = self._get_window_rect(self.target_window_handle)
                    if window_rect:
                        self._update_monitor_for_window(self.target_window_handle)
                        logging.info(f"Recording RDP window for session {session_id}")
                    else:
                        logging.warning(f"RDP window found but not accessible/visible, using full screen")
                        self.recording_mode = "full_screen"
                        self.target_window_handle = None
                        self.monitor = self._get_monitor_config()
                else:
                    logging.warning(f"RDP window not found for session {session_id}, using full screen")
                    self.recording_mode = "full_screen"  # Fallback
                    
            elif self.recording_mode == "active_window":
                self.target_window_handle = self._get_active_window()
                if self.target_window_handle:
                    self._update_monitor_for_window(self.target_window_handle)
                    logging.info(f"Recording active window for session {session_id}")
                else:
                    logging.warning(f"Active window not found for session {session_id}, using full screen")
                    self.recording_mode = "full_screen"  # Fallback
            
            # Full screen mode uses the initial monitor configuration
            
            # Create metadata file with session protection - DO NOT save sensitive data
            sanitized_connection_info = self._sanitize_connection_info(connection_info)
            metadata = {
                "session_id": session_id,
                "connection_info": sanitized_connection_info,
                "start_time": datetime.now().isoformat(),
                "recorder_settings": {
                    "fps": self.fps,
                    "quality": self.quality,
                    "resolution_scale": self.resolution_scale,
                    "max_file_size_mb": self.max_file_size / (1024 * 1024),
                    "max_duration_minutes": self.max_duration / 60
                }
            }
            
            metadata_file = self.output_dir / f"{session_id}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Start recording thread
            self.recording_thread = threading.Thread(
                target=self._recording_loop,
                args=(session_id, connection_info),
                daemon=True,
                name=f"SessionRecorder-{session_id}"
            )
            
            self.is_recording = True
            self.recording_thread.start()
            
            logging.info(f"Started recording session {session_id} for {connection_info.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> bool:
        """
        Stop the current recording session.
        
        Returns:
            True if recording stopped successfully, False otherwise
        """
        if not self.is_recording:
            logging.warning("No recording in progress")
            return False
            
        try:
            self.stop_event.set()
            
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=5.0)
                
            self._cleanup_current_recording()
            
            logging.info(f"Stopped recording session {self.session_id}")
            self.session_id = None
            self.is_recording = False
            return True
            
        except Exception as e:
            logging.error(f"Error stopping recording: {e}")
            return False

    def _recording_loop(self, session_id: str, connection_info: Dict[str, Any]):
        """Main recording loop running in a separate thread."""
        # Create a new MSS instance for this thread to avoid thread-safety issues
        thread_sct = mss.mss()
        
        try:
            self._create_new_video_file(session_id, connection_info)
            
            frame_interval = 1.0 / self.fps
            last_frame_time = time.time()
            
            while not self.stop_event.is_set():
                current_time = time.time()
                
                # Check if we need to capture a frame
                if current_time - last_frame_time >= frame_interval:
                    self._capture_and_write_frame(thread_sct)
                    last_frame_time = current_time
                    
                    # Check if we need to rotate the file
                    if self._should_rotate_file():
                        self._rotate_video_file(session_id, connection_info)
                
                # Small sleep to prevent excessive CPU usage
                time.sleep(0.01)
                
        except Exception as e:
            logging.error(f"Error in recording loop: {e}")
        finally:
            # Clean up thread-specific MSS instance
            try:
                thread_sct.close()
            except Exception as e:
                logging.warning(f"Error closing MSS instance: {e}")
            self._cleanup_current_recording()

    def _capture_and_write_frame(self, sct_instance):
        """Capture a screen frame and write it to the video file."""
        try:
            # Update window position if recording specific window
            if self.recording_mode in ["rdp_window", "active_window"] and self.target_window_handle:
                try:
                    # Check if window still exists and is visible
                    if win32gui.IsWindow(self.target_window_handle) and win32gui.IsWindowVisible(self.target_window_handle):
                        # Update monitor coordinates for window movement
                        self._update_monitor_for_window(self.target_window_handle)
                    else:
                        # Window no longer exists or visible, switch to full screen
                        logging.warning("Target window no longer available, switching to full screen")
                        self.recording_mode = "full_screen"
                        self.target_window_handle = None
                        self.monitor = self._get_monitor_config()
                except Exception as e:
                    logging.error(f"Error checking window status: {e}")
                    # Continue with last known position
            
            # Capture screen/window using thread-specific MSS instance
            screenshot = sct_instance.grab(self.monitor)
            
            # Convert to numpy array
            frame = np.array(screenshot)
            
            # Convert BGRA to BGR for OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            # Resize if scaling is applied
            if self.resolution_scale != 1.0:
                height, width = frame.shape[:2]
                new_width = int(width * self.resolution_scale)
                new_height = int(height * self.resolution_scale)
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Write frame to video
            if self.current_writer:
                self.current_writer.write(frame)
                
        except Exception as e:
            logging.error(f"Error capturing frame: {e}")

    def _create_new_video_file(self, session_id: str, connection_info: Dict[str, Any]):
        """Create a new video file for recording."""
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            connection_name = connection_info.get('name', 'Unknown').replace(' ', '_')
            filename = f"{session_id}_{connection_name}_{timestamp}.mp4"
            
            self.current_file = self.output_dir / filename
            self.recording_start_time = time.time()
            
            # Get screen dimensions
            width = self.monitor["width"]
            height = self.monitor["height"]
            
            if self.resolution_scale != 1.0:
                width = int(width * self.resolution_scale)
                height = int(height * self.resolution_scale)
            
            # Create VideoWriter with H.264 codec
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or 'H264'
            self.current_writer = cv2.VideoWriter(
                str(self.current_file),
                fourcc,
                self.fps,
                (width, height)
            )
            
            if not self.current_writer.isOpened():
                raise Exception("Failed to open VideoWriter")
                
            logging.info(f"Created new video file: {self.current_file} (dimensions: {width}x{height})")
            
        except Exception as e:
            logging.error(f"Error creating video file: {e}", exc_info=True)
            raise

    def _should_rotate_file(self) -> bool:
        """Check if the current file should be rotated."""
        if not self.current_file or not self.recording_start_time:
            return False
            
        # Check file size
        try:
            if self.current_file.exists():
                file_size = self.current_file.stat().st_size
                if file_size >= self.max_file_size:
                    logging.info(f"Rotating file due to size: {file_size / (1024*1024):.1f}MB")
                    return True
        except Exception as e:
            logging.error(f"Error checking file size: {e}")
        
        # Check duration
        elapsed_time = time.time() - self.recording_start_time
        if elapsed_time >= self.max_duration:
            logging.info(f"Rotating file due to duration: {elapsed_time / 60:.1f}min")
            return True
            
        return False

    def _rotate_video_file(self, session_id: str, connection_info: Dict[str, Any]):
        """Rotate to a new video file."""
        try:
            self._cleanup_current_recording()
            self._create_new_video_file(session_id, connection_info)
        except Exception as e:
            logging.error(f"Error rotating video file: {e}")

    def _cleanup_current_recording(self):
        """Clean up the current recording resources."""
        try:
            if self.current_writer:
                self.current_writer.release()
                self.current_writer = None
                
            self.current_file = None
            self.recording_start_time = None
            
        except Exception as e:
            logging.error(f"Error cleaning up recording: {e}")

    def get_recording_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current recording."""
        if not self.is_recording:
            return None
            
        info = {
            "session_id": self.session_id,
            "is_recording": self.is_recording,
            "current_file": str(self.current_file) if self.current_file else None,
            "recording_duration": time.time() - self.recording_start_time if self.recording_start_time else 0,
            "output_directory": str(self.output_dir)
        }
        
        if self.current_file and self.current_file.exists():
            try:
                info["current_file_size"] = self.current_file.stat().st_size
            except Exception:
                info["current_file_size"] = 0
                
        return info

    def cleanup_old_recordings(self, days_to_keep: int = 30):
        """
        Clean up old recording files.
        
        Args:
            days_to_keep: Number of days to keep recordings
        """
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0
            
            for file_path in self.output_dir.glob("*.mp4"):
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        
                        # Also remove associated metadata file
                        metadata_file = file_path.with_suffix('.json')
                        if metadata_file.exists():
                            metadata_file.unlink()
                            
                except Exception as e:
                    logging.error(f"Error deleting old recording {file_path}: {e}")
            
            if deleted_count > 0:
                logging.info(f"Cleaned up {deleted_count} old recording files")
                
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        if self.is_recording:
            self.stop_recording()