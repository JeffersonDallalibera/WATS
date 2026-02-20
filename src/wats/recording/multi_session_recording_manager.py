# Multi-session recording manager for WATS
# Supports multiple concurrent RDP session recordings

import logging
import shutil
import subprocess
import threading
from typing import Iterable

from ..utils.process_monitor import RdpProcessMonitor
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..config import get_config
from .session_recorder import SessionRecorder


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
        self.process_monitor = RdpProcessMonitor()

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
            logging.info(
                f"MultiSessionRecordingManager initialized with recording enabled: {settings.RECORDING_ENABLED}"
            )
            return True
        except Exception as e:
            logging.error(f"Failed to initialize MultiSessionRecordingManager: {e}")
            return False

    def _is_rdp_process_active(self, connection_info: Dict[str, Any]) -> bool:
        """
        Validate if an RDP process is active using the shared process monitor.
        Recording only starts AFTER the [PROCESS_CHECK] log is emitted.
        """
        server_ip = connection_info.get("ip", "")
        title = connection_info.get("name", "")
        user = connection_info.get("user") or connection_info.get("username")

        try:
            return self.process_monitor.is_rdp_process_active(
                server_ip=server_ip,
                user=user,
                title=title,
                tolerance_seconds=10,
            )
        except Exception as e:
            logging.warning(f"[PROCESS_CHECK] Falha ao validar processo RDP: {e}")
            # Fail open to avoid blocking recording on monitoring errors
            return True

    def start_session_recording(
        self, session_id: str, connection_info: Dict[str, Any], callback: Optional[Callable] = None
    ) -> bool:
        """
        Start recording for a specific RDP session.
        
        Configured to:
        - Record ONLY RDP sessions (rdp_window mode)
        - Support multiple concurrent sessions (1, 2, or more)
        - Detect and follow RDP window movement
        - Exclude all other PC screen elements from recording
        - Track RDP process exclusively

        Args:
            session_id: Unique identifier for the session
            connection_info: Information about the RDP connection (must include RDP window info)
            callback: Optional callback when recording stops

        Returns:
            True if recording started successfully, False otherwise
        """
        with self._lock:
            if session_id in self.active_recordings:
                logging.warning(f"Recording already active for session {session_id}")
                return False

            # ✅ PROCESS CHECK: Only start recording if an RDP process is active
            if not self._is_rdp_process_active(connection_info):
                logging.warning(
                    f"SESSION {session_id}: Recording not started (no active RDP process)"
                )
                return False

            try:
                # Get recording configuration
                config = get_config()
                recording_config = config.get("recording", {})

                # Override with settings if available - configure for RDP-only recording
                if self.settings:
                    recording_config.update(
                        {
                            "enabled": self.settings.RECORDING_ENABLED,
                            "output_dir": self.settings.RECORDING_OUTPUT_DIR,
                            "fps": getattr(
                                self.settings, "RECORDING_FPS", recording_config.get("fps", 5)
                            ),
                            "quality": getattr(
                                self.settings,
                                "RECORDING_QUALITY",
                                recording_config.get("quality", 28),
                            ),
                            # ✅ CRITICAL: Set to rdp_window to record ONLY RDP sessions
                            "mode": "rdp_window",
                            "compress_enabled": getattr(
                                self.settings,
                                "RECORDING_COMPRESSION_ENABLED",
                                recording_config.get("compress_enabled", True),
                            ),
                            "compress_crf": getattr(
                                self.settings,
                                "RECORDING_COMPRESSION_CRF",
                                recording_config.get("compress_crf", 28),
                            ),
                        }
                    )

                # Store the recording config for this session
                self.recording_configs[session_id] = recording_config

                # Create and start the recorder with RDP-window-specific configuration
                # ✅ CONFIGURATION FOR RDP-ONLY RECORDING
                # - fps: 3 (OPTIMIZED: reduced from 5 to 3 for lower memory usage)
                # - quality: 28 CRF (good quality/size tradeoff)
                # - resolution_scale: 0.75 (75% of RDP window resolution)
                # - recording_mode: "rdp_window" (ONLY records the RDP window)
                # - track_window_movement: True (follows RDP window if it moves)
                # - exclude_other_elements: True (ignores other PC screen content)
                recorder = SessionRecorder(
                    output_dir=recording_config.get("output_dir", "./recordings"),
                    max_file_size_mb=recording_config.get("max_file_size_mb", 100),
                    max_duration_minutes=recording_config.get("max_duration_minutes", 30),
                    fps=recording_config.get("fps", 3),  # ✅ OPTIMIZED: 3 FPS (was 5) - 40% less memory
                    quality=recording_config.get("quality", 28),  # CRF 28 (better compression)
                    resolution_scale=recording_config.get("resolution_scale", 0.75),  # 75% resolution
                    recording_mode="rdp_window",  # ✅ CRITICAL: Record ONLY RDP window
                    force_window_maximized=recording_config.get("force_window_maximized", True),
                    track_window_movement=True,  # ✅ Follow RDP window if it moves
                    exclude_non_rdp_content=True,  # ✅ Exclude other PC elements
                )
                
                # Store connection info for RDP-specific tracking
                # This ensures we track the correct RDP window across all sessions
                if not hasattr(self, 'session_connections'):
                    self.session_connections = {}
                self.session_connections[session_id] = connection_info
                
                # Start recording with session_id and connection_info
                if recorder.start_recording(session_id, connection_info):
                    self.active_recordings[session_id] = recorder
                    if callback:
                        self.callbacks[session_id] = callback
                    logging.info(
                        f"✅ Started RDP-only recording for session {session_id} "
                        f"(RDP Window Tracking Enabled, Multi-session support active)"
                    )
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
                    logging.info(
                        f"Stopped recording for session {session_id}, saved to: {video_path}"
                    )

                    # ⚡ OTIMIZAÇÃO: Sempre comprime AVI -> MP4 (compress_enabled default = True)
                    recording_config = self.recording_configs.get(session_id, {})
                    if recording_config.get("compress_enabled", True):  # Default True
                        self._compress_recording_async(video_path, recording_config)
                    else:
                        logging.info(f"⚠️ Compression disabled - keeping AVI file: {video_path}")

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
                return {"active": False, "session_id": session_id}

            recorder = self.active_recordings[session_id]
            return {
                "active": True,
                "session_id": session_id,
                "duration": recorder.get_recording_duration(),
                "frame_count": getattr(recorder, "frame_count", 0),
                "output_path": getattr(recorder, "output_path", "Unknown"),
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

    def handle_connection_event(
        self, event_type: str, session_id: str, connection_info: Dict[str, Any]
    ):
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

            if event_type == "connect":
                if getattr(self.settings, "RECORDING_AUTO_START", False):
                    self.start_session_recording(session_id, connection_info)

            elif event_type == "disconnect":
                if self.is_recording(session_id):
                    self.stop_session_recording(session_id)

            elif event_type == "heartbeat":
                # Heartbeat events can be used to monitor active sessions
                pass

        except Exception as e:
            logging.error(
                f"Error handling connection event {event_type} for session {session_id}: {e}"
            )

    def _compress_recording_async(self, video_path: str, recording_config: Dict[str, Any]):
        """
        Compress a recording file using ffmpeg in a background thread.
        Converte .AVI (rápido de escrever) para .MP4 (H.264 comprimido).

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

                ffmpeg_cmd = shutil.which("ffmpeg")
                if not ffmpeg_cmd:
                    logging.warning("ffmpeg not found in PATH; skipping compression")
                    return

                crf = recording_config.get("compress_crf", 28)
                
                # ⚡ OTIMIZAÇÃO: Converte .AVI -> .MP4 (H.264)
                # Se já for .mp4, recomprime com melhor qualidade
                if video_file.suffix.lower() == ".avi":
                    output_file = video_file.with_suffix(".mp4")
                    logging.info(f"⚡ Converting AVI to MP4: {video_file.name} -> {output_file.name}")
                else:
                    output_file = video_file.with_suffix(".tmp.mp4")

                # Build ffmpeg command with optimized settings
                cmd = [
                    ffmpeg_cmd,
                    "-y",  # Overwrite output
                    "-i", str(video_file),
                    "-c:v", "libx264",  # H.264 codec
                    "-preset", "fast",  # ⚡ Mais rápido que 'veryfast' mas mantém qualidade
                    "-crf", str(crf),   # Quality (18-28 recomendado, default 28)
                    "-movflags", "+faststart",  # Permite streaming
                    "-pix_fmt", "yuv420p",  # Compatibilidade máxima
                    str(output_file),
                ]

                logging.info(f"🔄 Compressing: {video_file.name} -> CRF={crf}, preset=fast")
                proc = subprocess.run(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True,
                    timeout=600  # Timeout de 10 minutos
                )

                if proc.returncode != 0:
                    logging.error(f"❌ ffmpeg failed for {video_file.name}: {proc.stderr}")
                    if output_file.exists():
                        output_file.unlink()
                    return

                # ⚡ Se converteu de AVI -> MP4, deleta o AVI original
                if video_file.suffix.lower() == ".avi" and output_file.exists():
                    try:
                        original_size = video_file.stat().st_size / (1024 * 1024)  # MB
                        compressed_size = output_file.stat().st_size / (1024 * 1024)  # MB
                        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                        
                        video_file.unlink()  # Deleta AVI
                        logging.info(
                            f"✅ Compression completed: {output_file.name} "
                            f"({original_size:.1f}MB -> {compressed_size:.1f}MB, "
                            f"saved {ratio:.1f}%)"
                        )
                    except Exception as e:
                        logging.error(f"Failed to cleanup after compression: {e}")
                
                # Se era .mp4 original, substitui pelo comprimido
                elif output_file.suffix == ".mp4" and output_file.name.endswith(".tmp.mp4"):
                    try:
                        backup = video_file.with_suffix(".bak.mp4")
                        video_file.rename(backup)
                        output_file.rename(video_file)
                        backup.unlink()
                        logging.info(f"✅ Re-compression completed: {video_file.name}")
                    except Exception as e:
                        logging.error(f"Failed to replace original file after compression: {e}")
                        if output_file.exists():
                            output_file.unlink()

            except subprocess.TimeoutExpired:
                logging.error(f"⏱️ Compression timeout for {video_file.name}")
            except Exception as e:
                logging.error(f"❌ Unexpected error during compression: {e}")

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
