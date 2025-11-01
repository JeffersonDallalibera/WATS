# WATS_Project/wats_app/recording/smart_session_recorder.py

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import cv2
import mss
import numpy as np

from .codec_installer import ensure_codecs_installed
from .interactivity_monitor import ActivityEvent, InteractivityMonitor
from .window_tracker import WindowInfo, WindowState, WindowTracker


class RecordingState(Enum):
    """Estados da gravação inteligente."""

    STOPPED = "stopped"
    RECORDING = "recording"
    PAUSED = "paused"
    WAITING_FOR_ACTIVITY = "waiting_for_activity"
    WAITING_FOR_WINDOW = "waiting_for_window"


@dataclass
class RecordingSegment:
    """Segmento de gravação."""

    file_path: Path
    start_time: float
    end_time: Optional[float]
    reason: str
    frame_count: int
    size_bytes: int


class SmartSessionRecorder:
    """
    Gravador inteligente que combina rastreamento de janela e monitoramento de atividade.
    Recursos:
    - Pausa/retoma automaticamente baseado no estado da janela
    - Monitora atividade do usuário
    - Cria novos arquivos baseado em critérios configuráveis
    - Gerencia múltiplos segmentos de gravação
    """

    def __init__(
        self, output_dir: str, connection_info: Dict[str, Any], recording_config: Dict[str, Any]
    ):
        """
        Initialize the smart session recorder.

        Args:
            output_dir: Diretório de saída para gravações
            connection_info: Informações da conexão RDP
            recording_config: Configurações de gravação
        """
        # Inicializar atributos básicos primeiro
        self.connection_info = connection_info
        self.config = recording_config

        # Estado da gravação
        self.state = RecordingState.STOPPED
        self.session_id: Optional[str] = None
        self.current_segment: Optional[RecordingSegment] = None
        self.all_segments: List[RecordingSegment] = []
        self.is_recording = False

        # Configurar diretório de saída
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Log detalhado da inicialização
        logging.info("🎥 SMART SESSION RECORDER INICIALIZADO:")
        logging.info(f"   📁 Diretório de saída: {self.output_dir}")
        logging.info(f"   🔗 Caminho absoluto: {self.output_dir.absolute()}")
        logging.info(f"   🆔 Session ID: {self.session_id}")
        logging.info(
            f"   🌐 Servidor: {connection_info.get('server_ip', 'N/A')}:{connection_info.get('server_port', 'N/A')}"
        )

        # Verifica se diretório é acessível
        if self.output_dir.exists() and self.output_dir.is_dir():
            logging.info("   ✅ Diretório existe e é acessível")
        else:
            logging.warning("   ⚠️  Diretório pode não estar acessível")

        # Componentes de monitoramento
        self.window_tracker: Optional[WindowTracker] = None
        self.interactivity_monitor: Optional[InteractivityMonitor] = None

        # Gravação
        self.current_writer: Optional[cv2.VideoWriter] = None
        self.recording_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        # Configurações de gravação
        self.fps = self.config.get("fps", 30)
        self.quality = self.config.get("quality", 75)
        self.resolution_scale = self.config.get("resolution_scale", 1.0)
        self.inactivity_timeout = self.config.get("inactivity_timeout_minutes", 10) * 60
        self.create_new_file_after_pause = self.config.get("create_new_file_after_pause", True)
        self.pause_on_minimized = self.config.get("pause_on_minimized", True)
        self.pause_on_covered = self.config.get("pause_on_covered", True)
        self.max_file_duration = self.config.get("max_file_duration_minutes", 30) * 60

        # Callbacks
        self.on_recording_started: Optional[Callable[[str], None]] = None
        self.on_recording_stopped: Optional[Callable[[str], None]] = None
        self.on_recording_paused: Optional[Callable[[str], None]] = None
        self.on_recording_resumed: Optional[Callable[[str], None]] = None
        self.on_new_segment_created: Optional[Callable[[RecordingSegment], None]] = None

        # MSS para captura de tela
        self.sct = mss.mss()

        # Inicializa instalador de codecs e garante que estejam disponíveis
        logging.info("🔧 Verificando e instalando codecs necessários...")
        self.codec_installer = ensure_codecs_installed(str(self.output_dir))

        logging.info("SmartSessionRecorder initialized")

    def start_recording(self, session_id: str) -> bool:
        """
        Inicia a gravação inteligente.

        Args:
            session_id: ID único da sessão

        Returns:
            True se a gravação foi iniciada com sucesso
        """
        if self.state != RecordingState.STOPPED:
            logging.warning(f"Recording already active in state: {self.state}")
            return False

        try:
            self.session_id = session_id

            # Inicializa rastreamento de janela
            self.window_tracker = WindowTracker(
                self.connection_info,
                update_interval=self.config.get("window_tracking_interval", 1.0),
            )

            # Configura callbacks do window tracker
            self.window_tracker.set_callbacks(
                on_state_changed=self._on_window_state_changed,
                on_moved=self._on_window_moved,
                on_lost=self._on_window_lost,
                on_found=self._on_window_found,
            )

            # Inicia rastreamento da janela (agora com espera automática)
            if not self.window_tracker.start_tracking():
                logging.error("Failed to start window tracking")
                return False

            logging.info("Window tracking started, will begin recording when RDP window is found")

            # O window tracker agora vai esperar a janela aparecer automaticamente
            # e chamar _on_window_found quando encontrar

            # Inicia em estado de espera pela janela
            self.state = RecordingState.WAITING_FOR_WINDOW

            # Inicia thread de gravação
            self.stop_event.clear()
            self.pause_event.clear()

            self.recording_thread = threading.Thread(
                target=self._recording_loop, daemon=True, name="SmartSessionRecorder"
            )
            self.recording_thread.start()

            self.is_recording = True
            logging.info("Smart recording initialized, waiting for RDP window to appear")

            if self.on_recording_started:
                self.on_recording_started(session_id)

            return True

        except Exception as e:
            logging.error(f"Failed to start smart recording: {e}")
            self._cleanup_components()
            return False

    def stop_recording(self) -> List[str]:
        """
        Para a gravação e retorna lista de arquivos criados.

        Returns:
            Lista de caminhos dos arquivos de gravação criados
        """
        if self.state == RecordingState.STOPPED:
            logging.debug("Recording already stopped")
            return []

        try:
            # Para thread de gravação
            self.stop_event.set()
            if self.recording_thread:
                self.recording_thread.join(timeout=10.0)

            # Finaliza segmento atual
            if self.current_segment:
                self._finalize_current_segment("session_end")

            # Limpa componentes
            self._cleanup_components()

            # Coleta arquivos criados
            file_paths = [str(segment.file_path) for segment in self.all_segments]

            self.state = RecordingState.STOPPED

            if self.on_recording_stopped:
                self.on_recording_stopped(self.session_id)

            # Log detalhado dos arquivos criados
            if file_paths:
                total_frames = sum(segment.frame_count for segment in self.all_segments)
                total_duration = self.get_recording_duration()

                logging.info("🎬 GRAVAÇÃO FINALIZADA COM SUCESSO:")
                logging.info(f"   📊 Segmentos criados: {len(file_paths)}")
                logging.info(f"   🎞️  Total de frames: {total_frames}")
                logging.info(f"   ⏱️  Duração total: {total_duration:.1f}s")
                logging.info(f"   📁 Diretório: {self.output_dir}")
                logging.info("   📄 Arquivos criados:")

                for i, file_path in enumerate(file_paths, 1):
                    segment = self.all_segments[i - 1]
                    size_mb = segment.size_bytes / (1024 * 1024) if segment.size_bytes > 0 else 0
                    duration = (segment.end_time - segment.start_time) if segment.end_time else 0
                    logging.info(f"      {i}. {Path(file_path).name}")
                    logging.info(f"         🎞️  Frames: {segment.frame_count}")
                    logging.info(f"         ⏱️  Duração: {duration:.1f}s")
                    logging.info(f"         💾 Tamanho: {size_mb:.1f}MB")
                    logging.info(f"         🔗 Caminho: {file_path}")
            else:
                logging.warning("⚠️  GRAVAÇÃO FINALIZADA SEM ARQUIVOS CRIADOS")

            logging.info(f"Stopped smart recording, created {len(file_paths)} segments")
            return file_paths

        except Exception as e:
            logging.error(f"Error stopping smart recording: {e}")
            return []

    def get_recording_duration(self) -> float:
        """Retorna duração total da gravação em segundos."""
        total_duration = 0.0
        for segment in self.all_segments:
            if segment.end_time:
                total_duration += segment.end_time - segment.start_time

        # Adiciona duração do segmento atual se existir
        if self.current_segment and self.state == RecordingState.RECORDING:
            total_duration += time.time() - self.current_segment.start_time

        return total_duration

    def get_recording_info(self) -> Dict[str, Any]:
        """Retorna informações detalhadas da gravação."""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "total_duration": self.get_recording_duration(),
            "segments_count": len(self.all_segments),
            "current_segment": {
                "file_path": str(self.current_segment.file_path) if self.current_segment else None,
                "start_time": self.current_segment.start_time if self.current_segment else None,
                "frame_count": self.current_segment.frame_count if self.current_segment else 0,
            },
            "total_files": len(self.all_segments),
            "total_size_mb": sum(s.size_bytes for s in self.all_segments) / (1024 * 1024),
            "window_info": (
                self.window_tracker.get_current_window_info().__dict__
                if self.window_tracker
                else None
            ),
            "activity_info": (
                self.interactivity_monitor.get_activity_summary()
                if self.interactivity_monitor
                else None
            ),
        }

    def _recording_loop(self):
        """Loop principal de gravação."""
        thread_sct = mss.mss()

        try:
            while not self.stop_event.is_set():
                try:
                    if self.state == RecordingState.RECORDING:
                        # Grava frame se não estiver pausado
                        if not self.pause_event.is_set():
                            self._capture_and_write_frame(thread_sct)

                        # Verifica se deve rotacionar arquivo
                        if self._should_rotate_file():
                            self._rotate_to_new_segment("file_rotation")

                    # Aguarda próximo frame
                    time.sleep(1.0 / self.fps)

                except Exception as e:
                    logging.error(f"Error in recording loop: {e}")
                    time.sleep(1.0)

        except Exception as e:
            logging.error(f"Fatal error in recording loop: {e}")
        finally:
            thread_sct.close()
            self._cleanup_current_writer()

    def _capture_and_write_frame(self, sct_instance):
        """Captura e escreve um frame."""
        try:
            if not self.current_writer or not self.window_tracker:
                return

            # Obtém área de gravação
            recording_rect = self.window_tracker.get_window_recording_rect()
            if not recording_rect:
                return

            # Captura tela
            screenshot = sct_instance.grab(recording_rect)

            # Converte screenshot para array numpy (método compatível com versões recentes do MSS)
            frame = np.array(screenshot)

            # Converte BGRA para BGR (remove canal alpha se presente)
            if frame.shape[2] == 4:  # BGRA
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            elif frame.shape[2] == 3:  # RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            logging.debug(f"📸 Frame capturado: {frame.shape}, dtype: {frame.dtype}")

            # Redimensiona se necessário
            if self.resolution_scale != 1.0:
                height, width = frame.shape[:2]
                new_width = int(width * self.resolution_scale)
                new_height = int(height * self.resolution_scale)
                frame = cv2.resize(frame, (new_width, new_height))
                logging.debug(f"📏 Frame redimensionado para: {frame.shape}")

            # Escreve frame
            self.current_writer.write(frame)
            logging.debug("✍️ Frame escrito no arquivo")

            # Atualiza contador
            if self.current_segment:
                self.current_segment.frame_count += 1

                # Log periódico de progresso (a cada 300 frames = ~10 segundos a 30fps)
                if self.current_segment.frame_count % 300 == 0:
                    duration = time.time() - self.current_segment.start_time
                    fps_actual = self.current_segment.frame_count / duration if duration > 0 else 0
                    logging.info("📊 GRAVAÇÃO EM PROGRESSO:")
                    logging.info(f"   🎞️  Frames gravados: {self.current_segment.frame_count}")
                    logging.info(f"   ⏱️  Duração: {duration:.1f}s")
                    logging.info(f"   📈 FPS atual: {fps_actual:.1f}")
                    logging.info(f"   📄 Arquivo: {self.current_segment.file_path.name}")

                # Log inicial quando começar a gravar
                elif self.current_segment.frame_count == 1:
                    logging.info("🎬 GRAVAÇÃO DE FRAMES INICIADA:")
                    logging.info(f"   📄 Arquivo: {self.current_segment.file_path}")
                    logging.info(f"   📐 Resolução: {frame.shape[1]}x{frame.shape[0]}")
                    logging.info("   🎞️  Primeiro frame capturado com sucesso!")

        except Exception as e:
            logging.error(f"Error capturing frame: {e}")

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitiza uma string para ser usada como nome de arquivo.

        Args:
            name: Nome original

        Returns:
            Nome sanitizado seguro para arquivos
        """
        import re

        # Remove caracteres não permitidos em nomes de arquivo
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)

        # Remove espaços extras e substitui por underscore
        sanitized = re.sub(r"\s+", "_", sanitized.strip())

        # Remove caracteres especiais
        sanitized = re.sub(r"[^\w\-_.]", "_", sanitized)

        # Limita o tamanho
        if len(sanitized) > 50:
            sanitized = sanitized[:50]

        # Remove underscores duplos
        sanitized = re.sub(r"_{2,}", "_", sanitized)

        # Remove underscore no início/fim
        sanitized = sanitized.strip("_")

        # Se ficou vazio, usa um padrão
        if not sanitized:
            sanitized = "conexao"

        return sanitized

    def _create_new_segment(self, reason: str) -> bool:
        """Cria um novo segmento de gravação."""
        try:
            # Finaliza segmento anterior
            if self.current_segment:
                self._finalize_current_segment(reason)

            # Obtém nome da conexão e sanitiza para nome de arquivo
            connection_name = self.connection_info.get("name", "conexao_rdp")
            safe_name = self._sanitize_filename(connection_name)

            # Cria novo arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            segment_number = len(self.all_segments) + 1
            filename = f"{safe_name}_seg{segment_number:03d}_{timestamp}.avi"
            file_path = self.output_dir / filename

            # Log detalhado do local de salvamento
            logging.info("🎥 CRIANDO NOVO SEGMENTO DE GRAVAÇÃO:")
            logging.info(f"   📁 Diretório: {self.output_dir}")
            logging.info(f"   📄 Arquivo: {filename}")
            logging.info(f"   🔗 Caminho completo: {file_path}")
            logging.info(f"   🎯 Nome original: {connection_name}")
            logging.info(f"   🔧 Nome sanitizado: {safe_name}")
            logging.info(f"   📊 Motivo: {reason}")
            logging.info(f"   #️⃣  Segmento número: {segment_number}")

            # Obtém configurações de gravação
            recording_rect = self.window_tracker.get_window_recording_rect()
            if not recording_rect:
                logging.error("Cannot create segment: no recording area available")
                return False

            width = int(recording_rect["width"] * self.resolution_scale)
            height = int(recording_rect["height"] * self.resolution_scale)

            logging.info(f"   📐 Resolução: {width}x{height} (escala: {self.resolution_scale})")
            logging.info(f"   🎞️  FPS: {self.fps}")

            # Obtém lista de codecs recomendados (com OpenH264 se disponível)
            recommended_codecs = self.codec_installer.get_recommended_codec_fallback()

            # Mapeia códigos para nomes legíveis
            codec_names = {
                cv2.VideoWriter_fourcc(*"H264"): "H.264 (OpenH264)",
                cv2.VideoWriter_fourcc(*"avc1"): "H.264 (AVC1)",
                cv2.VideoWriter_fourcc(*"XVID"): "XVID",
                cv2.VideoWriter_fourcc(*"MP4V"): "MP4V",
                cv2.VideoWriter_fourcc(*"MJPG"): "MJPEG",
                cv2.VideoWriter_fourcc(*"X264"): "x264",
            }

            self.current_writer = None
            for fourcc in recommended_codecs:
                try:
                    codec_name = codec_names.get(fourcc, f"Unknown({fourcc})")
                    writer = cv2.VideoWriter(str(file_path), fourcc, self.fps, (width, height))

                    if writer.isOpened():
                        self.current_writer = writer
                        logging.info(f"   🎬 Codec usado: {codec_name}")
                        break
                    else:
                        writer.release()

                except Exception as e:
                    logging.debug(f"   Codec {codec_name} falhou: {e}")
                    continue

            if not self.current_writer or not self.current_writer.isOpened():
                logging.error(
                    f"❌ Failed to create video writer for {file_path} - nenhum codec funcionou"
                )
                return False

            # Cria novo segmento
            self.current_segment = RecordingSegment(
                file_path=file_path,
                start_time=time.time(),
                end_time=None,
                reason=reason,
                frame_count=0,
                size_bytes=0,
            )

            if self.on_new_segment_created:
                self.on_new_segment_created(self.current_segment)

            logging.info(f"✅ Created new recording segment: {filename} (reason: {reason})")
            logging.info(f"🎬 GRAVAÇÃO INICIADA - Arquivo: {file_path}")
            return True

        except Exception as e:
            logging.error(f"❌ Error creating new segment: {e}")
            return False

    def _finalize_current_segment(self, reason: str):
        """Finaliza o segmento atual."""
        if not self.current_segment:
            return

        try:
            self.current_segment.end_time = time.time()

            # Fecha writer
            if self.current_writer:
                self.current_writer.release()
                self.current_writer = None

            # Obtém tamanho do arquivo
            if self.current_segment.file_path.exists():
                self.current_segment.size_bytes = self.current_segment.file_path.stat().st_size

            # Adiciona à lista de segmentos
            self.all_segments.append(self.current_segment)

            duration = self.current_segment.end_time - self.current_segment.start_time
            logging.info(
                f"Finalized segment: {self.current_segment.file_path.name} "
                f"(duration: {duration:.1f}s, frames: {self.current_segment.frame_count}, "
                f"size: {self.current_segment.size_bytes / (1024*1024):.1f}MB)"
            )

            self.current_segment = None

        except Exception as e:
            logging.error(f"Error finalizing segment: {e}")

    def _rotate_to_new_segment(self, reason: str):
        """Rotaciona para um novo segmento."""
        if self.state == RecordingState.RECORDING:
            self._create_new_segment(reason)

    def _should_rotate_file(self) -> bool:
        """Verifica se deve rotacionar para um novo arquivo."""
        if not self.current_segment:
            return False

        # Verifica duração máxima
        duration = time.time() - self.current_segment.start_time
        if duration >= self.max_file_duration:
            return True

        # Verifica tamanho do arquivo (estimado)
        estimated_size = self.current_segment.frame_count * 50000  # ~50KB por frame estimado
        max_size = self.config.get("max_file_size_mb", 100) * 1024 * 1024
        if estimated_size >= max_size:
            return True

        return False

    def _cleanup_current_writer(self):
        """Limpa o writer atual."""
        try:
            if self.current_writer:
                self.current_writer.release()
                self.current_writer = None
        except Exception as e:
            logging.error(f"Error cleaning up writer: {e}")

    def _cleanup_components(self):
        """Limpa todos os componentes."""
        try:
            if self.interactivity_monitor:
                self.interactivity_monitor.stop_monitoring()
                self.interactivity_monitor = None

            if self.window_tracker:
                self.window_tracker.stop_tracking()
                self.window_tracker = None

            self._cleanup_current_writer()

        except Exception as e:
            logging.error(f"Error cleaning up components: {e}")

    # Callbacks dos componentes de monitoramento

    def _on_window_state_changed(self, old_state: WindowState, new_state: WindowState):
        """Callback para mudança de estado da janela."""
        logging.info(f"Window state changed: {old_state.value} -> {new_state.value}")

        if new_state in [WindowState.MINIMIZED, WindowState.COVERED] and self.pause_on_minimized:
            if self.state == RecordingState.RECORDING:
                self._pause_recording("window_minimized_or_covered")

        elif new_state in [WindowState.NORMAL, WindowState.MAXIMIZED]:
            if self.state in [RecordingState.PAUSED, RecordingState.WAITING_FOR_WINDOW]:
                self._resume_recording("window_restored")

    def _on_window_moved(self, window_info: WindowInfo):
        """Callback para janela movida."""
        logging.debug(f"Window moved to: {window_info.rect}")

        # Atualiza monitor no interactivity monitor se necessário
        if self.interactivity_monitor:
            self.interactivity_monitor.update_target_window(window_info.hwnd)

    def _on_window_lost(self):
        """Callback para janela perdida."""
        logging.warning("RDP window lost")
        if self.state == RecordingState.RECORDING:
            self._pause_recording("window_lost")

    def _on_window_found(self, window_info: WindowInfo):
        """Callback para janela encontrada."""
        logging.info(f"RDP window found: {window_info.title}")

        # Inicializa monitoramento de atividade agora que temos a janela
        if not self.interactivity_monitor:
            try:
                self.interactivity_monitor = InteractivityMonitor(
                    window_info.hwnd, self.inactivity_timeout
                )

                # Configura callbacks do interactivity monitor
                self.interactivity_monitor.set_callbacks(
                    on_activity=self._on_activity_detected,
                    on_timeout=self._on_inactivity_timeout,
                    on_resumed=self._on_activity_resumed,
                )

                # Inicia monitoramento de atividade
                self.interactivity_monitor.start_monitoring()

                logging.info("Interactivity monitoring initialized and started")

            except Exception as e:
                logging.error(f"Error initializing interactivity monitor: {e}")

        # Inicia gravação se estivermos esperando a janela
        if self.state == RecordingState.WAITING_FOR_WINDOW:
            self._resume_recording("window_found")

    def _on_activity_detected(self, event: ActivityEvent):
        """Callback para atividade detectada."""
        if self.state == RecordingState.WAITING_FOR_ACTIVITY:
            self._resume_recording("activity_detected")

    def _on_inactivity_timeout(self):
        """Callback para timeout de inatividade."""
        logging.info("User inactivity timeout reached")
        if self.state == RecordingState.RECORDING:
            self._pause_recording("inactivity_timeout")

    def _on_activity_resumed(self):
        """Callback para atividade retomada."""
        logging.info("User activity resumed")
        if self.state == RecordingState.WAITING_FOR_ACTIVITY:
            self._resume_recording("activity_resumed")

    def _pause_recording(self, reason: str):
        """Pausa a gravação."""
        if self.state != RecordingState.RECORDING:
            return

        self.pause_event.set()

        if self.create_new_file_after_pause:
            self._finalize_current_segment(f"paused_{reason}")
            self.state = RecordingState.PAUSED
        else:
            self.state = RecordingState.PAUSED

        if self.on_recording_paused:
            self.on_recording_paused(reason)

        logging.info(f"Recording paused: {reason}")

    def _resume_recording(self, reason: str):
        """Retoma a gravação."""
        logging.info(f"🎬 TENTANDO RETOMAR GRAVAÇÃO: {reason}")
        logging.info(f"   📊 Estado atual: {self.state.value}")

        if self.state not in [
            RecordingState.PAUSED,
            RecordingState.WAITING_FOR_WINDOW,
            RecordingState.WAITING_FOR_ACTIVITY,
        ]:
            logging.warning(f"   ❌ Estado não permite retomar: {self.state.value}")
            return

        # Verifica se window_tracker está disponível
        if not self.window_tracker:
            logging.error("   ❌ Window tracker não disponível")
            return

        # Verifica se janela está adequada para gravação
        window_suitable = self.window_tracker.is_window_suitable_for_recording()
        logging.info(f"   🪟 Janela adequada para gravação: {window_suitable}")

        if not window_suitable:
            logging.warning("   ⚠️  Janela não está adequada, mudando para WAITING_FOR_WINDOW")
            self.state = RecordingState.WAITING_FOR_WINDOW
            return

        # Tenta criar novo segmento
        logging.info(
            f"   📄 Criando novo segmento: create_new_after_pause={self.create_new_file_after_pause}"
        )

        if self.create_new_file_after_pause or not self.current_segment:
            if not self._create_new_segment(f"resumed_{reason}"):
                logging.error("   ❌ Falha ao criar novo segmento")
                return
            else:
                logging.info("   ✅ Novo segmento criado com sucesso")

        self.pause_event.clear()
        self.state = RecordingState.RECORDING

        if self.on_recording_resumed:
            self.on_recording_resumed(reason)

        logging.info(f"✅ Recording resumed: {reason} - Estado: {self.state.value}")

    def set_callbacks(
        self,
        on_started: Optional[Callable[[str], None]] = None,
        on_stopped: Optional[Callable[[str], None]] = None,
        on_paused: Optional[Callable[[str], None]] = None,
        on_resumed: Optional[Callable[[str], None]] = None,
        on_new_segment: Optional[Callable[[RecordingSegment], None]] = None,
    ):
        """Define callbacks para eventos de gravação."""
        self.on_recording_started = on_started
        self.on_recording_stopped = on_stopped
        self.on_recording_paused = on_paused
        self.on_recording_resumed = on_resumed
        self.on_new_segment_created = on_new_segment

    def __del__(self):
        """Destructor para garantir limpeza adequada."""
        try:
            if hasattr(self, "state") and self.state != RecordingState.STOPPED:
                self.stop_recording()
        except Exception:
            pass  # Ignora erros no destructor
