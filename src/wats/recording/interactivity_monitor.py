# WATS_Project/wats_app/recording/interactivity_monitor.py

import ctypes
import ctypes.wintypes
import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional

import win32gui


class ActivityType(Enum):
    """Tipos de atividade detectados."""

    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    KEYBOARD = "keyboard"
    WINDOW_FOCUS = "window_focus"


@dataclass
class ActivityEvent:
    """Evento de atividade detectado."""

    activity_type: ActivityType
    timestamp: float
    window_hwnd: int
    details: Dict[str, Any]


class InteractivityMonitor:
    """
    Monitora atividade do usuário em uma janela específica.
    Detecta interações via mouse, teclado e foco da janela.
    """

    def __init__(self, target_hwnd: int, inactivity_timeout: float = 600.0):
        """
        Initialize the interactivity monitor.

        Args:
            target_hwnd: Handle da janela a ser monitorada
            inactivity_timeout: Timeout de inatividade em segundos (padrão: 10 minutos)
        """
        self.target_hwnd = target_hwnd
        self.inactivity_timeout = inactivity_timeout

        # Estado de monitoramento
        self.is_monitoring = False
        self.last_activity_time = time.time()
        self.is_active = True

        # Threads de monitoramento
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Callbacks
        self.on_activity_detected: Optional[Callable[[ActivityEvent], None]] = None
        self.on_inactivity_timeout: Optional[Callable[[], None]] = None
        self.on_activity_resumed: Optional[Callable[[], None]] = None

        # Cache para detecção de mudanças
        self._last_cursor_pos = None
        self._last_focus_hwnd = None
        self._activity_events = []

        # Windows API setup para hooks
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

        logging.info(f"InteractivityMonitor initialized for window {target_hwnd}")

    def start_monitoring(self) -> bool:
        """
        Inicia o monitoramento de atividade.

        Returns:
            True se o monitoramento foi iniciado com sucesso
        """
        if self.is_monitoring:
            logging.warning("Interactivity monitoring already active")
            return True

        try:
            self.stop_event.clear()
            self.last_activity_time = time.time()
            self.is_active = True

            # Inicia thread de monitoramento
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True, name="InteractivityMonitor"
            )
            self.monitoring_thread.start()
            self.is_monitoring = True

            logging.info("Started interactivity monitoring")
            return True

        except Exception as e:
            logging.error(f"Failed to start interactivity monitoring: {e}")
            return False

    def stop_monitoring(self):
        """Para o monitoramento de atividade."""
        if not self.is_monitoring:
            return

        self.stop_event.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)

        self.is_monitoring = False
        logging.info("Stopped interactivity monitoring")

    def update_target_window(self, new_hwnd: int):
        """
        Atualiza a janela alvo para monitoramento.

        Args:
            new_hwnd: Novo handle da janela
        """
        self.target_hwnd = new_hwnd
        self.last_activity_time = time.time()
        logging.info(f"Updated target window to {new_hwnd}")

    def get_time_since_last_activity(self) -> float:
        """
        Retorna o tempo em segundos desde a última atividade.

        Returns:
            Segundos desde a última atividade
        """
        return time.time() - self.last_activity_time

    def is_user_active(self) -> bool:
        """
        Verifica se o usuário está ativo (dentro do timeout).

        Returns:
            True se o usuário está ativo
        """
        return self.get_time_since_last_activity() < self.inactivity_timeout

    def force_activity_reset(self):
        """Força reset do timer de atividade."""
        self.last_activity_time = time.time()
        if not self.is_active:
            self.is_active = True
            if self.on_activity_resumed:
                self.on_activity_resumed()

    def _monitoring_loop(self):
        """Loop principal de monitoramento."""
        while not self.stop_event.is_set():
            try:
                # Verifica atividade na janela alvo
                self._check_window_activity()

                # Verifica timeout de inatividade
                self._check_inactivity_timeout()

                # Aguarda próxima verificação
                if self.stop_event.wait(0.5):  # Verifica a cada 500ms
                    break

            except Exception as e:
                logging.error(f"Error in interactivity monitoring loop: {e}")
                if self.stop_event.wait(5.0):
                    break

    def _check_window_activity(self):
        """Verifica atividade na janela alvo."""
        try:
            if not win32gui.IsWindow(self.target_hwnd):
                return

            # Verifica foco da janela
            current_focus = win32gui.GetForegroundWindow()
            if current_focus == self.target_hwnd and current_focus != self._last_focus_hwnd:
                self._register_activity(
                    ActivityType.WINDOW_FOCUS,
                    {"previous_window": self._last_focus_hwnd, "current_window": current_focus},
                )
                self._last_focus_hwnd = current_focus

            # Verifica movimento do cursor (apenas se a janela está em foco)
            if current_focus == self.target_hwnd:
                cursor_pos = win32gui.GetCursorPos()
                if cursor_pos != self._last_cursor_pos:
                    # Verifica se o cursor está dentro da janela
                    if self._is_cursor_in_window(cursor_pos):
                        self._register_activity(
                            ActivityType.MOUSE_MOVE,
                            {"position": cursor_pos, "previous_position": self._last_cursor_pos},
                        )
                    self._last_cursor_pos = cursor_pos

                # Verifica cliques do mouse
                self._check_mouse_clicks()

                # Verifica teclas pressionadas
                self._check_keyboard_activity()

        except Exception as e:
            logging.error(f"Error checking window activity: {e}")

    def _is_cursor_in_window(self, cursor_pos: tuple) -> bool:
        """
        Verifica se o cursor está dentro da janela alvo.

        Args:
            cursor_pos: Posição do cursor (x, y)

        Returns:
            True se o cursor está dentro da janela
        """
        try:
            window_rect = win32gui.GetWindowRect(self.target_hwnd)
            left, top, right, bottom = window_rect
            x, y = cursor_pos

            return left <= x <= right and top <= y <= bottom

        except Exception as e:
            logging.error(f"Error checking cursor position: {e}")
            return False

    def _check_mouse_clicks(self):
        """Verifica cliques do mouse na janela."""
        try:
            # Verifica estado dos botões do mouse
            left_button = self.user32.GetAsyncKeyState(0x01) & 0x8000  # VK_LBUTTON
            right_button = self.user32.GetAsyncKeyState(0x02) & 0x8000  # VK_RBUTTON
            middle_button = self.user32.GetAsyncKeyState(0x04) & 0x8000  # VK_MBUTTON

            if any([left_button, right_button, middle_button]):
                cursor_pos = win32gui.GetCursorPos()
                if self._is_cursor_in_window(cursor_pos):
                    button_info = {
                        "left": bool(left_button),
                        "right": bool(right_button),
                        "middle": bool(middle_button),
                        "position": cursor_pos,
                    }
                    self._register_activity(ActivityType.MOUSE_CLICK, button_info)

        except Exception as e:
            logging.error(f"Error checking mouse clicks: {e}")

    def _check_keyboard_activity(self):
        """Verifica atividade do teclado."""
        try:
            # Verifica se alguma tecla está pressionada
            # Esta é uma implementação simplificada que verifica teclas comuns
            key_ranges = [
                (0x08, 0x12),  # Backspace to Alt
                (0x20, 0x5A),  # Space to Z
                (0x60, 0x6F),  # Numpad 0 to Numpad /
                (0x70, 0x87),  # F1 to F24
            ]

            pressed_keys = []
            for start, end in key_ranges:
                for key_code in range(start, end + 1):
                    if self.user32.GetAsyncKeyState(key_code) & 0x8000:
                        pressed_keys.append(key_code)

            if pressed_keys and win32gui.GetForegroundWindow() == self.target_hwnd:
                self._register_activity(
                    ActivityType.KEYBOARD,
                    {"pressed_keys": pressed_keys, "key_count": len(pressed_keys)},
                )

        except Exception as e:
            logging.error(f"Error checking keyboard activity: {e}")

    def _register_activity(self, activity_type: ActivityType, details: Dict[str, Any]):
        """
        Registra uma atividade detectada.

        Args:
            activity_type: Tipo da atividade
            details: Detalhes específicos da atividade
        """
        try:
            current_time = time.time()
            self.last_activity_time = current_time

            # Se estava inativo, marca como ativo novamente
            if not self.is_active:
                self.is_active = True
                if self.on_activity_resumed:
                    self.on_activity_resumed()
                logging.info("User activity resumed")

            # Cria evento de atividade
            event = ActivityEvent(
                activity_type=activity_type,
                timestamp=current_time,
                window_hwnd=self.target_hwnd,
                details=details,
            )

            # Chama callback se definido
            if self.on_activity_detected:
                self.on_activity_detected(event)

            # Mantém histórico limitado
            self._activity_events.append(event)
            if len(self._activity_events) > 100:  # Mantém apenas os últimos 100 eventos
                self._activity_events.pop(0)

        except Exception as e:
            logging.error(f"Error registering activity: {e}")

    def _check_inactivity_timeout(self):
        """Verifica se o timeout de inatividade foi atingido."""
        try:
            if self.is_active and self.get_time_since_last_activity() >= self.inactivity_timeout:
                self.is_active = False
                if self.on_inactivity_timeout:
                    self.on_inactivity_timeout()
                logging.info(f"User inactivity timeout reached ({self.inactivity_timeout}s)")

        except Exception as e:
            logging.error(f"Error checking inactivity timeout: {e}")

    def get_activity_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo da atividade recente.

        Returns:
            Dicionário com estatísticas de atividade
        """
        try:
            current_time = time.time()
            recent_events = [
                event
                for event in self._activity_events
                if current_time - event.timestamp <= 300  # Últimos 5 minutos
            ]

            activity_counts = {}
            for event in recent_events:
                activity_type = event.activity_type.value
                activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1

            return {
                "is_active": self.is_active,
                "last_activity_time": self.last_activity_time,
                "time_since_last_activity": self.get_time_since_last_activity(),
                "inactivity_timeout": self.inactivity_timeout,
                "recent_activity_counts": activity_counts,
                "total_events": len(self._activity_events),
                "recent_events": len(recent_events),
            }

        except Exception as e:
            logging.error(f"Error getting activity summary: {e}")
            return {"is_active": self.is_active, "error": str(e)}

    def set_callbacks(
        self,
        on_activity: Optional[Callable[[ActivityEvent], None]] = None,
        on_timeout: Optional[Callable[[], None]] = None,
        on_resumed: Optional[Callable[[], None]] = None,
    ):
        """Define callbacks para eventos de atividade."""
        self.on_activity_detected = on_activity
        self.on_inactivity_timeout = on_timeout
        self.on_activity_resumed = on_resumed

    def __del__(self):
        """Destructor para garantir limpeza adequada."""
        self.stop_monitoring()
