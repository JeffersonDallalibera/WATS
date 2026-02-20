# WATS_Project/wats_app/recording/session_recorder.py

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import mss
import numpy as np
import psutil
import win32con
import win32gui
import win32process
import win32ui


class SessionRecorder:
    """
    Lightweight session recorder for WATS application.
    Features:
    - Low CPU/memory usage with MSS screen capture
    - H.264 compression for efficient storage
    - File rotation based on size and time
    - Thread-safe recording operations
    """

    def __init__(
        self,
        output_dir: str,
        max_file_size_mb: int = 100,
        max_duration_minutes: int = 30,
        fps: int = 10,
        quality: int = 23,
        resolution_scale: float = 1.0,
        recording_mode: str = "full_screen",
        force_window_maximized: bool = True,
        track_window_movement: bool = True,
        exclude_non_rdp_content: bool = True,
    ):
        """
        Initialize the session recorder optimized for RDP recording.

        Args:
            output_dir: Directory to save recordings
            max_file_size_mb: Maximum file size before rotation (MB)
            max_duration_minutes: Maximum recording duration before rotation (minutes)
            fps: Frames per second for recording
            quality: H.264 quality (0-51, lower is better quality)
            resolution_scale: Scale factor for resolution (1.0 = full, 0.5 = half)
            recording_mode: "full_screen", "rdp_window", or "active_window"
            force_window_maximized: Force RDP window to be maximized (prevents FFmpeg errors)
            track_window_movement: ✅ Track and follow RDP window if it moves
            exclude_non_rdp_content: ✅ Exclude non-RDP content from recording
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.max_duration = max_duration_minutes * 60  # Convert to seconds
        self.fps = fps
        self.quality = quality  # H.264 CRF (23-35 recomendado, maior = menor arquivo)
        self.resolution_scale = resolution_scale
        self.recording_mode = recording_mode.lower()
        self.force_window_maximized = force_window_maximized
        self.track_window_movement = track_window_movement  # ✅ NEW: Follow RDP window
        self.exclude_non_rdp_content = exclude_non_rdp_content  # ✅ NEW: Only record RDP

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
        
        # ✅ Window tracking for RDP movement detection
        self.rdp_window_tracking_enabled = track_window_movement and recording_mode == "rdp_window"
        self.last_rdp_window_position: Optional[Dict[str, int]] = None
        self.rdp_window_moves_count: int = 0
        
        # Rastreamento de dimensões para detectar mudanças
        self.last_frame_width: Optional[int] = None
        self.last_frame_height: Optional[int] = None
        self.dimension_change_count: int = 0
        self.force_window_maximized: bool = True  # Força janela maximizada para evitar problemas

        # Minimum capture size to consider the RDP window "established"
        self.min_capture_width: int = 320
        self.min_capture_height: int = 200

        # FFmpeg fallback (when OpenCV VideoWriter is unavailable)
        self.ffmpeg_process = None
        self.ffmpeg_stdin = None
        
        # Frame capture statistics
        self.frames_captured: int = 0
        self.frames_failed: int = 0

        # Screen capture setup
        self.sct = mss.mss()
        self.monitor = self._get_monitor_config()

        logging.info(
            f"✅ SessionRecorder initialized - Output: {self.output_dir}, "
            f"Max size: {max_file_size_mb}MB, Max duration: {max_duration_minutes}min, "
            f"FPS: {fps}, Quality: {quality}, Scale: {resolution_scale}, Mode: {self.recording_mode}, "
            f"RDP Tracking: {self.rdp_window_tracking_enabled}, "
            f"Exclude Non-RDP: {self.exclude_non_rdp_content}")

    def _get_monitor_config(self) -> Dict[str, int]:
        """Get monitor configuration based on recording mode."""
        if self.recording_mode == "full_screen":
            monitor = self.sct.monitors[0]  # Full screen (all monitors)
        else:
            # For window-specific recording, start with primary monitor
            # Will be updated dynamically during recording when RDP window is found
            # DO NOT apply scaling here - MSS needs real screen coordinates
            monitor = self.sct.monitors[1] if len(self.sct.monitors) > 1 else self.sct.monitors[0]

        # ⚠️ CRITICAL: DO NOT apply resolution_scale here!
        # MSS needs EXACT screen coordinates to capture properly
        # Scaling will be applied to the FRAME AFTER capture, not the capture region
        
        return {
            "top": monitor["top"],
            "left": monitor["left"],
            "width": monitor["width"],
            "height": monitor["height"],
        }

    def _is_valid_capture_size(self, width: int, height: int) -> bool:
        """Validate capture size to avoid tiny/invalid windows before starting recording."""
        return width >= self.min_capture_width and height >= self.min_capture_height

    def _normalize_dimensions(self, width: int, height: int) -> tuple[int, int]:
        """Ensure dimensions are even (required by some codecs) and >= minimum size."""
        width = int(width)
        height = int(height)
        if width % 2 != 0:
            width -= 1
        if height % 2 != 0:
            height -= 1
        return max(width, self.min_capture_width), max(height, self.min_capture_height)

    def _try_open_video_writer(
        self,
        file_path: Path,
        fps: int,
        size: tuple[int, int],
        codecs: tuple[str, ...],
        api_prefs: tuple[int, ...],
    ) -> tuple[Optional[cv2.VideoWriter], list[str]]:
        """Try to open VideoWriter with multiple APIs/codecs and return writer + tried list."""
        tried = []
        for api in api_prefs:
            for codec in codecs:
                tried.append(codec)
                fourcc = cv2.VideoWriter_fourcc(*codec)
                writer = cv2.VideoWriter(str(file_path), api, fourcc, fps, size)
                if writer.isOpened():
                    return writer, tried
        return None, tried

    def _start_ffmpeg_writer(
        self,
        width: int,
        height: int,
        session_id: str,
        connection_info: Dict[str, Any],
        timestamp: str,
    ) -> bool:
        """Start ffmpeg fallback writer using raw frames piped to stdin."""
        try:
            import shutil
            import subprocess

            ffmpeg_path = shutil.which("ffmpeg")
            if not ffmpeg_path:
                logging.error("FFmpeg not found in PATH - cannot fallback to ffmpeg writer")
                return False

            connection_name = connection_info.get("name", "Unknown").replace(" ", "_")
            filename = f"{session_id}_{connection_name}_{timestamp}_ffmpeg.avi"
            self.current_file = self.output_dir / filename

            # Use MPEG-4 encoder (built-in) to avoid OpenH264 dependency
            cmd = [
                ffmpeg_path,
                "-y",
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "-s", f"{width}x{height}",
                "-r", str(self.fps),
                "-i", "-",
                "-an",
                "-vcodec", "mpeg4",
                "-q:v", "5",
                str(self.current_file),
            ]

            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.ffmpeg_stdin = self.ffmpeg_process.stdin
            logging.info(f"⚡ FFmpeg fallback writer started: {self.current_file}")
            return True

        except Exception as e:
            logging.error(f"Failed to start FFmpeg fallback writer: {e}")
            return False

    def _try_restore_window(self, hwnd: int) -> bool:
        """
        Try to restore a minimized window (but don't force maximize).
        
        Args:
            hwnd: Window handle
            
        Returns:
            True if window was restored successfully
        """
        try:
            # Check if window is minimized - only restore, don't force maximize
            if win32gui.IsIconic(hwnd):
                logging.info("Window is minimized, attempting to restore to normal size")
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)  # Give time for window to restore
                logging.info("✅ Window restored to normal size")
                
            return True
        except Exception as e:
            logging.warning(f"Failed to restore window: {e}")
            return False
    
    def _check_window_dimension_change(self, current_width: int, current_height: int) -> bool:
        """
        Verifica se as dimensões da janela mudaram significativamente.
        
        Args:
            current_width: Largura atual
            current_height: Altura atual
            
        Returns:
            True se houve mudança significativa
        """
        # ✅ CRITICAL FIX: These are now initialized in _create_new_video_file()
        # so we should NEVER have None values here. But keep check for safety.
        if self.last_frame_width is None or self.last_frame_height is None:
            logging.warning(
                f"⚠️ Dimension tracking not initialized (should have been in _create_new_video_file). "
                f"Initializing now: {current_width}x{current_height}"
            )
            self.last_frame_width = current_width
            self.last_frame_height = current_height
            return False
        
        # Calcula diferença percentual
        width_diff = abs(current_width - self.last_frame_width)
        height_diff = abs(current_height - self.last_frame_height)
        
        # Considera mudança significativa se diferença > 5%
        width_change_pct = (width_diff / self.last_frame_width) * 100 if self.last_frame_width > 0 else 0
        height_change_pct = (height_diff / self.last_frame_height) * 100 if self.last_frame_height > 0 else 0
        
        if width_change_pct > 5 or height_change_pct > 5:
            self.dimension_change_count += 1
            logging.warning(
                f"⚠️ DIMENSÕES DA JANELA MUDARAM: {self.last_frame_width}x{self.last_frame_height} → "
                f"{current_width}x{current_height} (Δ: {width_change_pct:.1f}%, {height_change_pct:.1f}%) "
                f"[Mudanças: {self.dimension_change_count}]"
            )
            
            # Atualiza dimensões armazenadas
            self.last_frame_width = current_width
            self.last_frame_height = current_height
            
            return True
        
        return False
    
    def _recreate_video_writer(self, width: int, height: int, session_id: str, connection_info: Dict[str, Any]):
        """
        Recria o VideoWriter com novas dimensões.
        Necessário quando a janela é redimensionada ou movida.
        
        Args:
            width: Nova largura
            height: Nova altura
            session_id: ID da sessão
            connection_info: Informações da conexão
        """
        try:
            logging.info(f"🔄 Recriando VideoWriter com novas dimensões: {width}x{height}")
            
            # Fecha writer atual
            if self.current_writer:
                self.current_writer.release()
                logging.info(f"VideoWriter anterior liberado")
            
            # Cria novo arquivo de vídeo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            connection_name = connection_info.get("name", "Unknown").replace(" ", "_")
            # ⚡ OTIMIZAÇÃO: Grava em .AVI (mais rápido) - será comprimido depois
            filename = f"{session_id}_{connection_name}_{timestamp}_resized.avi"
            
            self.current_file = self.output_dir / filename
            
            # Normalize dimensions for codec compatibility
            width, height = self._normalize_dimensions(width, height)

            # ⚡ OTIMIZAÇÃO: Cria VideoWriter com codecs rápidos (MJPEG primeiro)
            api_candidates = []
            for api_name in ("CAP_FFMPEG", "CAP_MSMF", "CAP_DSHOW", "CAP_ANY"):
                api_val = getattr(cv2, api_name, None)
                if api_val is not None:
                    api_candidates.append(api_val)
            api_prefs = tuple(api_candidates) if api_candidates else (0,)

            self.current_writer, tried_codecs = self._try_open_video_writer(
                self.current_file,
                self.fps,
                (width, height),
                ("MJPG", "XVID", "mp4v", "I420", "DIB "),
                api_prefs,
            )

            if self.current_writer and self.current_writer.isOpened():
                logging.info(f"✅ Novo VideoWriter AVI criado: {self.current_file}")

            if not self.current_writer or not self.current_writer.isOpened():
                raise Exception(f"Failed to open new VideoWriter (tried: {tried_codecs})")

            # Reseta tempo de início do arquivo atual
            self.recording_start_time = time.time()

            # Atualiza dimensões conhecidas para evitar mismatch entre writer e frames
            try:
                self.last_frame_width = int(width)
                self.last_frame_height = int(height)
            except Exception:
                pass
            
        except Exception as e:
            logging.error(f"❌ Erro ao recriar VideoWriter: {e}", exc_info=True)
            raise

    def _find_rdp_window(self, connection_info: Dict[str, Any]) -> Optional[int]:
        """
        Find RDP window handle based on connection information.
        ✅ IMPROVED: More flexible detection for all RDP clients
        """
        try:
            target_title = connection_info.get("name", "")
            target_ip = connection_info.get("ip", "")

            # Extract IP (remove port if present)
            if ":" in target_ip:
                ip_part = target_ip.split(":")[0]
            else:
                ip_part = target_ip

            def enum_window_callback(hwnd, windows):
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                
                window_title = win32gui.GetWindowText(hwnd)
                window_title_lower = window_title.lower()

                # ✅ EXPANDED: Support more RDP clients
                rdp_indicators = [
                    "remote desktop",
                    "área de trabalho remota",
                    "rdp",
                    "mstsc",
                    "royalts",
                    "teamviewer",
                    "anydesk",
                    "connectwise",
                    "vncviewer",
                    "freerdp",
                    "connection",
                    "servidor",
                    "server",
                ]

                # ✅ IMPROVED: Check for RDP indicator in window title
                is_rdp_window = any(indicator in window_title_lower for indicator in rdp_indicators)

                # Check if window title contains target connection info
                title_contains_target = False
                if target_title:
                    title_contains_target = target_title.lower() in window_title_lower
                if ip_part and ip_part.strip():
                    title_contains_target = title_contains_target or ip_part in window_title_lower

                # ✅ CRITICAL: Accept window if it has RDP indicator OR target info
                if is_rdp_window or title_contains_target:
                    try:
                        # Get process info to verify
                        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(process_id)
                        process_name = process.name().lower()

                        # ✅ EXPANDED: Support all common RDP processes
                        rdp_processes = [
                            "mstsc.exe",           # Windows RDP
                            "rdp.exe",
                            "royalts.exe",         # Royal TS
                            "teamviewer.exe",      # TeamViewer
                            "anydesk.exe",         # AnyDesk
                            "connectwise.exe",     # ConnectWise
                            "vncviewer.exe",       # VNC
                            "freerdp.exe",         # FreeRDP
                            "chrome.exe",          # Chrome RDP extension
                            "firefox.exe",         # Firefox RDP
                        ]

                        is_known_rdp = any(rdp_proc in process_name for rdp_proc in rdp_processes)

                        # Score: Higher for exact connection match, lower for generic RDP
                        if is_known_rdp and title_contains_target:
                            score = 3  # Highest: Known RDP process with target match
                        elif is_known_rdp:
                            score = 2  # Known RDP process
                        elif title_contains_target:
                            score = 2  # Has target connection info
                        else:
                            score = 1  # Generic RDP indicator

                        # ✅ IMPORTANT: Add window to candidates
                        windows.append(
                            {
                                "hwnd": hwnd,
                                "title": window_title,
                                "process_name": process_name,
                                "process_id": process_id,
                                "score": score,
                                "is_known_rdp": is_known_rdp,
                            }
                        )
                        logging.debug(
                            f"🔍 Found RDP candidate: '{window_title}' (PID: {process_id}, Score: {score})"
                        )

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass  # Skip this window if we can't access process info

                return True

            windows = []
            win32gui.EnumWindows(enum_window_callback, windows)

            if windows:
                # ✅ Sort by score (highest first) and return the best match
                windows.sort(key=lambda x: x["score"], reverse=True)
                best_match = windows[0]
                hwnd = best_match["hwnd"]
                
                # 🔍 Log window details
                try:
                    rect = win32gui.GetClientRect(hwnd)
                    left_top = win32gui.ClientToScreen(hwnd, (rect[0], rect[1]))
                    right_bottom = win32gui.ClientToScreen(hwnd, (rect[2], rect[3]))
                    window_width = right_bottom[0] - left_top[0]
                    window_height = right_bottom[1] - left_top[1]
                    
                    logging.info(
                        f"✅ RDP Window FOUND: '{best_match['title']}' "
                        f"(Process: {best_match['process_name']}, PID: {best_match['process_id']}, Score: {best_match['score']}) | "
                        f"📍 Position: ({left_top[0]}, {left_top[1]}) | "
                        f"📏 Size: {window_width}x{window_height}"
                    )
                except Exception as e:
                    logging.info(
                        f"✅ RDP Window FOUND: '{best_match['title']}' "
                        f"(PID: {best_match['process_id']}, Score: {best_match['score']})"
                    )

                # Don't force restore - user can minimize if they want
                # PrintWindow works even with minimized windows
                return hwnd
            else:
                logging.warning(
                    f"❌ RDP window NOT found for: {target_title or target_ip} | "
                    f"RDP-only mode: will wait and retry"
                )
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
        """
        Get window CLIENT AREA rectangle coordinates (conteúdo interno sem bordas).
        Essencial para RDP: captura apenas a sessão remota, não a janela do cliente.
        """
        try:
            # ✅ ALLOW MINIMIZED: Don't force restore - PrintWindow can capture minimized windows
            # Just log if minimized but continue recording
            if win32gui.IsIconic(hwnd):
                logging.debug(f"Window is minimized - continuing recording with PrintWindow")
                # Don't restore - let user keep window minimized
            
            # ⚡ CORREÇÃO CRÍTICA: Usa GetClientRect + ClientToScreen para pegar apenas conteúdo
            # GetWindowRect pega a janela inteira (bordas, barra de título, etc.)
            # GetClientRect pega APENAS a área de conteúdo (o que está dentro da janela)
            
            # Pega retângulo do CLIENT AREA (conteúdo interno)
            rect = win32gui.GetClientRect(hwnd)
            
            # Converte coordenadas locais (client) para coordenadas de tela
            left_top = win32gui.ClientToScreen(hwnd, (rect[0], rect[1]))
            right_bottom = win32gui.ClientToScreen(hwnd, (rect[2], rect[3]))
            
            window_rect = {
                "left": left_top[0],
                "top": left_top[1],
                "width": right_bottom[0] - left_top[0],
                "height": right_bottom[1] - left_top[1],
            }

            # ✅ ALLOW MINIMIZED: Handle special minimized coordinates
            # Windows uses -32000 coordinates for minimized windows - this is OK
            if window_rect["left"] <= -32000 or window_rect["top"] <= -32000:
                logging.debug(f"Window is minimized (coordinates: {window_rect['left']}, {window_rect['top']}) - PrintWindow will capture it")
                # Keep the window rect as-is for PrintWindow to handle

            # Check if window is invalid by size only
            # (allow negative coordinates for multi-monitor setups)
            if window_rect["width"] < 100 or window_rect["height"] < 100:
                logging.warning(f"Window appears invalid (too small): {window_rect}")
                return None

            logging.debug(
                f"🎬 CLIENT AREA: {window_rect['width']}x{window_rect['height']} "
                f"at ({window_rect['left']}, {window_rect['top']})"
            )
            return window_rect
        except Exception as e:
            logging.error(f"Error getting window client rect: {e}")
            return None

    def _update_monitor_for_window(self, hwnd: int) -> bool:
        """
        Update monitor configuration for specific window.
        ✅ DETECTS RDP WINDOW MOVEMENT and continues recording
        ⚠️ CRITICAL: Must provide correct MSS monitor dict format
        
        IMPORTANTE: MSS precisa das coordenadas EXATAS da tela, sem scaling.
        O scaling é aplicado depois no resize do frame capturado.
        """
        window_rect = self._get_window_rect(hwnd)
        if window_rect:
            # ✅ Track RDP window movement
            if self.rdp_window_tracking_enabled and self.last_rdp_window_position:
                position_changed = (
                    window_rect['left'] != self.last_rdp_window_position.get('left') or
                    window_rect['top'] != self.last_rdp_window_position.get('top')
                )
                
                if position_changed:
                    self.rdp_window_moves_count += 1
                    logging.info(
                        f"🎬 SESSION {self.session_id}: RDP Window MOVED: "
                        f"({self.last_rdp_window_position.get('left')}, {self.last_rdp_window_position.get('top')}) → "
                        f"({window_rect['left']}, {window_rect['top']}) [Move #{self.rdp_window_moves_count}] - "
                        f"✅ CONTINUING RECORDING"
                    )
            
            # Store current position for next check
            self.last_rdp_window_position = window_rect.copy()
            
            # ⚠️ CRÍTICO: Construir dict correto para MSS
            # MSS espera: {'left': int, 'top': int, 'width': int, 'height': int}
            mss_monitor = {
                "left": window_rect["left"],
                "top": window_rect["top"],
                "width": window_rect["width"],
                "height": window_rect["height"],
            }
            
            # Validate monitor dict
            if mss_monitor["width"] < 100 or mss_monitor["height"] < 100:
                logging.warning(
                    f"⚠️ Invalid monitor config for session {self.session_id}: {mss_monitor} | "
                    f"RDP-only mode: keeping last valid region"
                )
                return False
            
            self.monitor = mss_monitor
            logging.debug(
                f"📍 SESSION {self.session_id}: Monitor updated - RDP window: "
                f"{mss_monitor['width']}x{mss_monitor['height']} "
                f"at ({mss_monitor['left']}, {mss_monitor['top']})"
            )
            return True
        else:
            logging.warning(
                f"⚠️ SESSION {self.session_id}: Window rect invalid - RDP-only mode will wait"
            )
            return False

    def _capture_rdp_window_frame(self, hwnd: int) -> Optional[np.ndarray]:
        """
        Capture ONLY the RDP window content using PrintWindow.
        This avoids recording any overlaying windows on top of the RDP session.
        Returns a BGR frame or None if capture fails.
        ✅ MEMORY OPTIMIZED: Proper GDI cleanup with try-finally
        """
        hwnd_dc = None
        mfc_dc = None
        save_dc = None
        save_bitmap = None
        
        try:
            # Ensure valid window
            if not win32gui.IsWindow(hwnd):
                return None

            # Try to get window rect - but be lenient about sizes
            try:
                rect = win32gui.GetClientRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
            except Exception as e:
                logging.debug(f"SESSION {self.session_id}: GetClientRect failed: {e}")
                return None

            # Allow smaller windows - better to record something than nothing
            if width < 50 or height < 50:
                logging.debug(f"SESSION {self.session_id}: RDP window too small: {width}x{height}")
                return None

            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)

            # ✅ IMPROVED: Try different PrintWindow flags
            # First try: PW_RENDERFULLCONTENT alone (works better for some windows)
            PW_RENDERFULLCONTENT = 2
            result = win32gui.PrintWindow(hwnd, save_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)

            if result != 1:
                # Second try: No flags (default behavior)
                result = win32gui.PrintWindow(hwnd, save_dc.GetSafeHdc(), 0)
                
            if result != 1:
                # Third try: PW_CLIENTONLY
                PW_CLIENTONLY = 1
                result = win32gui.PrintWindow(hwnd, save_dc.GetSafeHdc(), PW_CLIENTONLY)

            if result != 1:
                # PrintWindow failed with all attempts
                logging.debug(f"SESSION {self.session_id}: PrintWindow failed with all flag combinations")
                return None

            bmp_info = save_bitmap.GetInfo()
            bmp_str = save_bitmap.GetBitmapBits(True)
            img = np.frombuffer(bmp_str, dtype=np.uint8)
            img = img.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 4))

            # Convert BGRA to BGR for OpenCV - COPY data before cleanup
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR).copy()
            
            return frame
            
        except Exception as e:
            logging.debug(f"SESSION {self.session_id}: PrintWindow exception: {e}")
            return None
        
        finally:
            # ✅ CRITICAL: ALWAYS cleanup GDI objects, even if exception occurs
            try:
                if save_bitmap:
                    win32gui.DeleteObject(save_bitmap.GetHandle())
            except Exception:
                pass
            
            try:
                if save_dc:
                    save_dc.DeleteDC()
            except Exception:
                pass
                
            try:
                if mfc_dc:
                    mfc_dc.DeleteDC()
            except Exception:
                pass
                
            try:
                if hwnd_dc is not None:
                    win32gui.ReleaseDC(hwnd, hwnd_dc)
            except Exception:
                pass

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
            protection_config = config.get("recording", {}).get("session_protection", {})

            protection_enabled = protection_config.get("enabled", True)
            sanitize_metadata = protection_config.get("sanitize_metadata", True)
            remove_sensitive = protection_config.get("remove_sensitive_fields", True)
            log_actions = protection_config.get("log_protection_actions", True)

            if not protection_enabled or not sanitize_metadata:
                if log_actions:
                    logging.warning(
                        "Session protection is DISABLED - sensitive data may be stored in metadata"
                    )
                return connection_info.copy()

        except Exception as e:
            # If config loading fails, default to protection enabled
            logging.warning(f"Could not load session protection config, defaulting to enabled: {e}")
            remove_sensitive = True
            log_actions = True

        # Define safe fields that should ALWAYS be kept (for identification)
        safe_fields = {
            "name",
            "ip",
            "host",
            "hostname",
            "server",
            "port",
            "connection_type",
            "protocol",
            "connection_name",
            "server_name",
        }

        # Define sensitive fields that should NOT be saved to disk/database
        # IMPORTANT: Only exact field names, not partial matches!
        sensitive_fields = {
            "password",
            "senha",
            "pass",
            "pwd",
            "passwd",
            "passw",
            "username",
            "usuario",
            "login",
            "user_name",
            "userid",
            "session_id",
            "session_token",
            "token",
            "auth_token",
            "access_token",
            "credentials",
            "credential",
            "auth",
            "authentication",
            "authdata",
            "private_key",
            "key",
            "secret",
            "hash",
            "cert",
            "certificate",
            "domain",
            "dominio",
            "dn",
            "distinguished_name",
        }

        # Create sanitized copy - only keep safe fields
        sanitized = {}
        sensitive_count = 0

        for key, value in connection_info.items():
            key_lower = key.lower()

            # PRIORITY 1: If it's in safe_fields, always keep it ✓
            if key_lower in safe_fields:
                sanitized[key] = value
            # PRIORITY 2: Check if it's a sensitive field (exact match or key contains it)
            elif key_lower in sensitive_fields or any(sensitive_field in key_lower for sensitive_field in sensitive_fields):
                if remove_sensitive:
                    # Replace sensitive data with protection placeholder
                    sanitized[key] = "[PROTECTED_BY_SESSION_SECURITY]"
                    sensitive_count += 1
                else:
                    # Keep it if removal is disabled
                    sanitized[key] = value
            else:
                # Keep other fields as they are not sensitive
                sanitized[key] = value

        # Add security protection metadata
        sanitized["_session_protection"] = {
            "enabled": True,
            "sanitized_at": datetime.now().isoformat(),
            "sensitive_fields_removed": sensitive_count,
            "protection_notice": "Authentication credentials and session data are protected and not stored",
        }

        if log_actions:
            logging.info(
                f"Session protection applied - sanitized {sensitive_count} sensitive fields from connection metadata"
            )

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
            
            # Armazena informações da conexão para uso posterior
            self.current_connection_name = connection_info.get("name", "Unknown")
            self.current_connection_ip = connection_info.get("ip", "Unknown")

            # Set up window tracking based on recording mode
            if self.recording_mode == "rdp_window":
                # ⚡ RETRY LOGIC: RDP window may take time to appear (up to 5s)
                max_attempts = 10  # 10 attempts × 0.5s = 5 seconds
                self.target_window_handle = None
                
                logging.info(f"🔍 SESSION {session_id}: Searching for RDP window: {connection_info.get('name', 'Unknown')} ({connection_info.get('ip', 'N/A')})")
                
                for attempt in range(max_attempts):
                    self.target_window_handle = self._find_rdp_window(connection_info)
                    if self.target_window_handle:
                        logging.info(f"✅ SESSION {session_id}: RDP window found on attempt {attempt + 1}/{max_attempts}")
                        break
                    if attempt < max_attempts - 1:
                        logging.info(f"⏳ SESSION {session_id}: Waiting for RDP window (attempt {attempt + 1}/{max_attempts})...")
                        time.sleep(0.5)
                
                if self.target_window_handle:
                    # Try to get window position - if invalid, fallback to full screen
                    window_rect = self._get_window_rect(self.target_window_handle)
                    if window_rect:
                        self._update_monitor_for_window(self.target_window_handle)
                        logging.info(
                            f"✅ SESSION {session_id}: RDP-ONLY RECORDING CONFIGURED "
                            f"📺 Window Size: {window_rect['width']}x{window_rect['height']} | "
                            f"📍 Screen Position: ({window_rect['left']}, {window_rect['top']}) | "
                            f"🔄 Window Tracking: ENABLED | "
                            f"🚫 Non-RDP Exclusion: ENABLED | "
                            f"🔢 Handle: {self.target_window_handle}"
                        )
                    else:
                        logging.warning(
                            f"⚠️ SESSION {session_id}: RDP window found but rect is invalid - RDP-only mode will wait"
                        )
                        self.target_window_handle = None
                else:
                    logging.warning(
                        f"❌ SESSION {session_id}: RDP window NOT found after {max_attempts} attempts - RDP-only mode will wait"
                    )
                    self.target_window_handle = None

            elif self.recording_mode == "active_window":
                self.target_window_handle = self._get_active_window()
                if self.target_window_handle:
                    self._update_monitor_for_window(self.target_window_handle)
                    logging.info(f"Recording active window for session {session_id}")
                else:
                    logging.warning(
                        f"Active window not found for session {session_id}, using full screen"
                    )
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
                    "max_duration_minutes": self.max_duration / 60,
                },
            }

            metadata_file = self.output_dir / f"{session_id}_metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                import json

                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # Start recording thread
            self.recording_thread = threading.Thread(
                target=self._recording_loop,
                args=(session_id, connection_info),
                daemon=True,
                name=f"SessionRecorder-{session_id}",
            )

            self.is_recording = True
            self.recording_thread.start()

            logging.info(
                f"Started recording session {session_id} for {connection_info.get('name', 'Unknown')}"
            )
            return True

        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> Optional[str]:
        """
        Stop the current recording session.

        Returns:
            Path to the recorded video file if successful, None otherwise
        """
        if not self.is_recording:
            logging.warning("No recording in progress")
            return None

        try:
            # Store the current file path before cleanup
            video_path = str(self.current_file) if self.current_file else None
            
            self.stop_event.set()

            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=5.0)

            self._cleanup_current_recording()

            logging.info(f"Stopped recording session {self.session_id} - Frames captured: {self.frames_captured}, Failed: {self.frames_failed}")
            self.session_id = None
            self.is_recording = False
            
            return video_path

        except Exception as e:
            logging.error(f"Error stopping recording: {e}")
            return None

    def _recording_loop(self, session_id: str, connection_info: Dict[str, Any]):
        """
        Main recording loop running in a separate thread.
        ✅ MEMORY OPTIMIZED: Periodic garbage collection and efficient frame handling
        """
        import gc
        
        # Create a new MSS instance for this thread to avoid thread-safety issues
        thread_sct = mss.mss()

        try:
            # RDP-only: wait for a valid RDP window before starting capture
            if self.recording_mode == "rdp_window":
                # ✅ Wait for a VALID RDP window size before starting recording
                while not self.stop_event.is_set():
                    if self.target_window_handle and win32gui.IsWindow(self.target_window_handle):
                        if self._update_monitor_for_window(self.target_window_handle):
                            if self._is_valid_capture_size(
                                self.monitor["width"], self.monitor["height"]
                            ):
                                break
                    self.target_window_handle = self._find_rdp_window(connection_info)
                    if self.target_window_handle:
                        if self._update_monitor_for_window(self.target_window_handle):
                            if self._is_valid_capture_size(
                                self.monitor["width"], self.monitor["height"]
                            ):
                                break
                        self.target_window_handle = None
                    time.sleep(0.2)

            if self.stop_event.is_set():
                return

            # ✅ Only create VideoWriter after a valid capture region exists
            max_writer_attempts = 5
            created = False
            for attempt in range(1, max_writer_attempts + 1):
                if self._create_new_video_file(session_id, connection_info):
                    created = True
                    break
                logging.error(
                    f"Error creating video file (attempt {attempt}/{max_writer_attempts})"
                )
                if attempt < max_writer_attempts:
                    time.sleep(1.0)

            if not created:
                logging.error("Recording aborted: no available VideoWriter/FFmpeg backend")
                return

            frame_interval = 1.0 / self.fps
            last_frame_time = time.time()
            frames_since_gc = 0  # ✅ NEW: Track frames for periodic GC
            gc_interval = 30  # Run GC every 30 frames
            
            while not self.stop_event.is_set():
                current_time = time.time()

                # Check if we need to capture a frame
                if current_time - last_frame_time >= frame_interval:
                    self._capture_and_write_frame(thread_sct)
                    last_frame_time = current_time
                    frames_since_gc += 1
                    
                    # ✅ MEMORY: Periodic garbage collection to free Python objects
                    if frames_since_gc >= gc_interval:
                        gc.collect(generation=0)  # Fast collection of youngest generation
                        frames_since_gc = 0

                    # Check if we need to rotate the file
                    if self._should_rotate_file():
                        self._rotate_video_file(session_id, connection_info)

                # Small sleep to prevent excessive CPU usage
                time.sleep(0.01)

        except Exception as e:
            logging.error(f"Error in recording loop: {e}")
        finally:
            # ✅ FINAL CLEANUP: Force garbage collection
            gc.collect()
            
            # Clean up thread-specific MSS instance
            try:
                thread_sct.close()
            except Exception as e:
                logging.warning(f"Error closing MSS instance: {e}")
            self._cleanup_current_recording()

    def _capture_and_write_frame(self, sct_instance):
        """
        Capture a screen frame and write it to the video file.
        
        ✅ FEATURES FOR RDP-ONLY RECORDING:
        - Records ONLY the RDP window (not other PC content)
        - Tracks RDP window movement and continues recording
        - Ignores non-RDP elements
        ✅ MEMORY OPTIMIZED: Explicit memory cleanup after each frame
        """
        frame = None  # Initialize for cleanup
        
        try:
            # Update window position if recording specific window
            if self.recording_mode in ["rdp_window", "active_window"]:
                try:
                    if self.target_window_handle and win32gui.IsWindow(self.target_window_handle) and win32gui.IsWindowVisible(
                        self.target_window_handle
                    ):
                        if not self._update_monitor_for_window(self.target_window_handle):
                            return
                    else:
                        # RDP-only: try to re-find window, do not fall back to full screen
                        self.target_window_handle = self._find_rdp_window(
                            {
                                "name": getattr(self, "current_connection_name", "Unknown"),
                                "ip": getattr(self, "current_connection_ip", "Unknown"),
                            }
                        )
                        if not self.target_window_handle:
                            return
                        if not self._update_monitor_for_window(self.target_window_handle):
                            return
                except Exception as e:
                    logging.error(f"Error checking RDP window status: {e}")
                    return

            # Capture frame
            if self.recording_mode == "rdp_window" and self.exclude_non_rdp_content:
                frame = self._capture_rdp_window_frame(self.target_window_handle)
                if frame is None:
                    # ⚠️ HYBRID APPROACH: Use MSS as fallback (may capture overlays)
                    # PrintWindow doesn't work with all RDP clients
                    # Better to record with overlays than not record at all
                    try:
                        screenshot = sct_instance.grab(self.monitor)
                        frame = np.array(screenshot)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                        self.frames_failed += 1  # Count as "failed" PrintWindow
                        if self.frames_failed == 10:  # Log once after 10 failures
                            logging.warning(f"SESSION {self.session_id}: PrintWindow not working with this RDP client - using MSS (may capture overlays)")
                    except Exception as e:
                        self.frames_failed += 1
                        if self.frames_failed % 50 == 0:
                            logging.error(f"SESSION {self.session_id}: Both PrintWindow and MSS failed {self.frames_failed} times")
                        return
                else:
                    if self.frames_captured == 0:  # Log on first success
                        logging.info(f"SESSION {self.session_id}: ✅ Using PrintWindow (no overlays)")
            else:
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
                # ✅ MEMORY: Create resized frame and keep in same variable to release old frame
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Obtém dimensões finais do frame
            final_height, final_width = frame.shape[:2]
            
            # ✅ Verifica se as dimensões mudaram (janela RDP foi redimensionada ou movida)
            if self._check_window_dimension_change(final_width, final_height):
                logging.warning(
                    f"⚠️ RDP Window dimensões mudaram durante gravação! "
                    f"Recriando VideoWriter para evitar erro 'FFmpeg: Failed to write frame'"
                )
                
                # Recria VideoWriter com novas dimensões
                connection_info = {
                    "name": getattr(self, 'current_connection_name', 'Unknown'),
                    "ip": getattr(self, 'current_connection_ip', 'Unknown')
                }
                self._recreate_video_writer(
                    final_width, 
                    final_height, 
                    self.session_id or "unknown", 
                    connection_info
                )

            # Write frame to video
            if self.current_writer:
                try:
                    self.current_writer.write(frame)
                    self.frames_captured += 1
                    if self.frames_captured % 100 == 0:  # Log every 100 frames
                        logging.info(f"SESSION {self.session_id}: ✅ {self.frames_captured} frames recorded")
                except Exception as write_error:
                    self.frames_failed += 1
                    logging.error(
                        f"❌ Erro ao escrever frame (FFmpeg/OpenCV): {write_error}. "
                        f"Dimensões do frame: {final_width}x{final_height}. Failed: {self.frames_failed}",
                        exc_info=True,
                    )

                    # Log disk usage to help diagnose write failures (e.g., no space)
                    try:
                        import shutil

                        usage = shutil.disk_usage(self.output_dir)
                        logging.info(
                            f"Disk usage for {self.output_dir}: total={usage.total}, used={usage.used}, free={usage.free}"
                        )
                    except Exception:
                        logging.debug("Could not determine disk usage for output directory")

                    # Sempre tenta recriar o writer em caso de erro de escrita
                    logging.info("Tentando recriar VideoWriter após erro de escrita...")
                    connection_info = {
                        "name": getattr(self, 'current_connection_name', 'Unknown'),
                        "ip": getattr(self, 'current_connection_ip', 'Unknown')
                    }
                    try:
                        self._recreate_video_writer(
                            final_width,
                            final_height,
                            self.session_id or "unknown",
                            connection_info,
                        )
                    except Exception as recreate_exc:
                        logging.error(f"Falha ao recriar VideoWriter: {recreate_exc}", exc_info=True)

            elif self.ffmpeg_process and self.ffmpeg_stdin:
                try:
                    self.ffmpeg_stdin.write(frame.tobytes())
                    self.frames_captured += 1
                    if self.frames_captured % 100 == 0:
                        logging.info(f"SESSION {self.session_id}: ✅ {self.frames_captured} frames recorded (ffmpeg)")
                except Exception as write_error:
                    self.frames_failed += 1
                    logging.error(
                        f"❌ Erro ao escrever frame (FFmpeg pipe): {write_error}. Failed: {self.frames_failed}",
                        exc_info=True,
                    )

        except Exception as e:
            logging.error(f"Error capturing frame: {e}")
        
        finally:
            # ✅ MEMORY: Explicitly delete frame to free memory immediately
            if frame is not None:
                del frame

    def _create_new_video_file(self, session_id: str, connection_info: Dict[str, Any]) -> bool:
        """Create a new video file for recording. Returns True on success."""
        try:
            # Generate filename with timestamp
            # ⚡ OTIMIZAÇÃO: Grava em .AVI primeiro (mais rápido) - será comprimido para .mp4 depois
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            connection_name = connection_info.get("name", "Unknown").replace(" ", "_")
            filename = f"{session_id}_{connection_name}_{timestamp}.avi"

            self.current_file = self.output_dir / filename
            self.recording_start_time = time.time()

            # Get screen dimensions
            width = self.monitor["width"]
            height = self.monitor["height"]

            if self.resolution_scale != 1.0:
                width = int(width * self.resolution_scale)
                height = int(height * self.resolution_scale)

            # Normalize dimensions for codec compatibility
            width, height = self._normalize_dimensions(width, height)

            # ⚡ OTIMIZAÇÃO: Create VideoWriter with fast AVI codecs (MJPEG primeiro - mais rápido)
            # Será comprimido para H.264/MP4 depois pelo MultiSessionRecordingManager
            api_candidates = []
            for api_name in ("CAP_FFMPEG", "CAP_MSMF", "CAP_DSHOW", "CAP_ANY"):
                api_val = getattr(cv2, api_name, None)
                if api_val is not None:
                    api_candidates.append(api_val)
            api_prefs = tuple(api_candidates) if api_candidates else (0,)

            self.current_writer, tried_codecs = self._try_open_video_writer(
                self.current_file,
                self.fps,
                (width, height),
                ("MJPG", "XVID", "mp4v", "I420", "DIB "),
                api_prefs,
            )

            if self.current_writer and self.current_writer.isOpened():
                logging.info(
                    f"⚡ Created AVI file (fast write): {self.current_file} (dimensions: {width}x{height})"
                )

            # ✅ Fallback: if AVI codecs fail, try MP4 container with compatible codecs
            if not self.current_writer or not self.current_writer.isOpened():
                fallback_filename = f"{session_id}_{connection_name}_{timestamp}.mp4"
                self.current_file = self.output_dir / fallback_filename
                self.current_writer, tried_codecs = self._try_open_video_writer(
                    self.current_file,
                    self.fps,
                    (width, height),
                    ("mp4v",),
                    api_prefs,
                )
                if self.current_writer and self.current_writer.isOpened():
                    logging.info(
                        f"⚡ Created MP4 fallback file: {self.current_file} (dimensions: {width}x{height})"
                    )

            # ✅ Final fallback: FFmpeg pipe writer (if available)
            if not self.current_writer or not self.current_writer.isOpened():
                if self._start_ffmpeg_writer(width, height, session_id, connection_info, timestamp):
                    # Initialize dimensions for ffmpeg writer too
                    self.last_frame_width = int(width)
                    self.last_frame_height = int(height)
                    self.dimension_change_count = 0
                    logging.debug(
                        f"✅ Initialized dimension tracking (ffmpeg): {self.last_frame_width}x{self.last_frame_height}"
                    )
                    return True

            if not self.current_writer or not self.current_writer.isOpened():
                logging.error(f"Failed to open VideoWriter (tried: {tried_codecs})")
                return False

            # ✅ CRITICAL FIX: Initialize dimension tracking IMMEDIATELY after creating writer
            # This prevents spurious dimension changes on first frame capture
            # Without this, the first frame causes _check_window_dimension_change() to
            # trigger _recreate_video_writer(), creating a second output file with only 1 second of video
            self.last_frame_width = int(width)
            self.last_frame_height = int(height)
            self.dimension_change_count = 0
            
            logging.debug(
                f"✅ Initialized dimension tracking: {self.last_frame_width}x{self.last_frame_height} "
                f"(prevents spurious recreation on first frame)"
            )

            return True

        except Exception as e:
            logging.error(f"Error creating video file: {e}", exc_info=True)
            return False

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
            if not self._create_new_video_file(session_id, connection_info):
                logging.error("Rotation failed: no available VideoWriter/FFmpeg backend")
        except Exception as e:
            logging.error(f"Error rotating video file: {e}")

    def _cleanup_current_recording(self):
        """Clean up the current recording resources."""
        try:
            if self.current_writer:
                # ✅ CRITICAL: Ensure VideoWriter is properly released to write file headers
                logging.debug(f"Releasing VideoWriter for: {self.current_file}")
                self.current_writer.release()
                self.current_writer = None
                logging.debug(f"VideoWriter released successfully")
                
                # Give OS time to flush buffers
                time.sleep(0.1)

            self.current_file = None
            self.recording_start_time = None

            # ✅ Cleanup FFmpeg fallback
            try:
                if self.ffmpeg_stdin:
                    self.ffmpeg_stdin.close()
                if self.ffmpeg_process:
                    self.ffmpeg_process.wait(timeout=2)
            except Exception:
                try:
                    if self.ffmpeg_process:
                        self.ffmpeg_process.terminate()
                except Exception:
                    pass
            finally:
                self.ffmpeg_stdin = None
                self.ffmpeg_process = None

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
            "recording_duration": (
                time.time() - self.recording_start_time if self.recording_start_time else 0
            ),
            "output_directory": str(self.output_dir),
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
                        metadata_file = file_path.with_suffix(".json")
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
        try:
            if hasattr(self, 'is_recording') and self.is_recording:
                self.stop_recording()
        except Exception:
            pass  # Ignore errors during cleanup
