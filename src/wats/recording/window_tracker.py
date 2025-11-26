# WATS_Project/wats_app/recording/window_tracker.py

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple

import win32gui
import win32process


class WindowState(Enum):
    """Estados possíveis da janela."""

    NORMAL = "normal"
    MINIMIZED = "minimized"
    MAXIMIZED = "maximized"
    COVERED = "covered"
    NOT_FOUND = "not_found"
    MOVED = "moved"


@dataclass
class WindowInfo:
    """Informações sobre a janela."""

    hwnd: int
    title: str
    rect: Tuple[int, int, int, int]  # (left, top, right, bottom)
    state: WindowState
    is_foreground: bool
    process_id: int
    thread_id: int
    monitor_index: int
    last_updated: float


class WindowTracker:
    """
    Rastreia o estado de uma janela RDP específica.
    Monitora posição, tamanho, visibilidade e estados (minimizada, sobreposta, etc.).
    """

    def __init__(self, connection_info: Dict[str, Any], update_interval: float = 1.0):
        """
        Initialize the window tracker.

        Args:
            connection_info: Informações da conexão RDP
            update_interval: Intervalo de atualização em segundos
        """
        self.connection_info = connection_info
        self.update_interval = update_interval

        # Políticas de captura
        # Quando true, a gravação NÃO deve ocorrer se a janela estiver coberta
        # (permite que overlays apareçam para o usuário, porém não sejam gravados)
        self.pause_on_covered: bool = bool(
            connection_info.get("pause_on_covered", True)
        )
        # Quando true, usa a área cliente da janela (sem bordas/barra de título)
        # para reduzir risco de capturar elementos externos.
        self.capture_client_area: bool = bool(
            connection_info.get("capture_client_area", True)
        )
        # Quando true, permite que outras janelas sobreponham a janela RDP (não fixa como topmost)
        self.allow_window_override: bool = bool(
            connection_info.get("allow_window_override", True)
        )
        # Percentual mínimo de sobreposição da área de captura para considerar "coberta"
        # Usado em conjunto com a área cliente para evitar capturar overlays.
        self.covered_overlap_threshold: float = float(
            connection_info.get("covered_overlap_threshold", 0.0)
        )

        # Estado atual da janela
        self.current_window: Optional[WindowInfo] = None
        self.target_hwnd: Optional[int] = None
        self.is_tracking = False

        # Thread de monitoramento
        self.tracking_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Configurações de retry para encontrar janela RDP
        self.max_window_wait_attempts = 30  # 30 tentativas = 2 minutos
        self.window_wait_interval = 4.0  # 4 segundos entre tentativas
        self.window_found = False

        # Callbacks para eventos
        self.on_window_state_changed: Optional[Callable[[WindowState, WindowState], None]] = None
        self.on_window_moved: Optional[Callable[[WindowInfo], None]] = None
        self.on_window_resized: Optional[Callable[[WindowInfo], None]] = None
        self.on_window_lost: Optional[Callable[[], None]] = None
        self.on_window_found: Optional[Callable[[WindowInfo], None]] = None

        # Cache para detectar mudanças
        self._last_rect = None
        self._last_state = None
        self._last_monitor = None

        logging.info("WindowTracker initialized")

    def start_tracking(self) -> bool:
        """
        Inicia o rastreamento da janela RDP.
        Espera a janela aparecer se não estiver disponível imediatamente.

        Returns:
            True se conseguiu encontrar e iniciar o rastreamento da janela
        """
        if self.is_tracking:
            logging.warning("Window tracking already active")
            return True

        logging.info("Starting window tracking with RDP window detection...")

        # Inicia thread de monitoramento que vai esperar a janela aparecer
        self.stop_event.clear()
        self.tracking_thread = threading.Thread(
            target=self._tracking_loop_with_wait, daemon=True, name="WindowTracker"
        )
        self.tracking_thread.start()
        self.is_tracking = True

        logging.info("Window tracking thread started, waiting for RDP window...")
        return True

    def stop_tracking(self):
        """Para o rastreamento da janela."""
        if not self.is_tracking:
            return

        self.stop_event.set()
        if self.tracking_thread:
            self.tracking_thread.join(timeout=5.0)

        self.is_tracking = False
        self.current_window = None
        logging.info("Stopped window tracking")

    def get_current_window_info(self) -> Optional[WindowInfo]:
        """Retorna informações atuais da janela."""
        return self.current_window

    def is_window_suitable_for_recording(self) -> bool:
        """
        Verifica se a janela está em condições adequadas para gravação.

        Returns:
            True se a janela pode ser gravada (visível, não minimizada, etc.)
        """
        if not self.current_window:
            logging.debug("❌ Não adequada: current_window é None")
            return False

        # Estados base que podem ser gravados
        base_states = [WindowState.NORMAL, WindowState.MAXIMIZED]
        is_suitable = self.current_window.state in base_states

        # Se outra janela está em primeiro plano e política de pausa está ativa,
        # considerar como não adequado imediatamente (não gravar nada sobreposto).
        try:
            if self.pause_on_covered:
                fg = win32gui.GetForegroundWindow()
                if fg and fg != self.current_window.hwnd:
                    logging.debug("   Foreground diferente do alvo e pause_on_covered=True -> não gravar")
                    return False
        except Exception as e:
            logging.debug(f"   Erro verificando foreground: {e}")

        # Caso a janela esteja coberta
        if self.current_window.state == WindowState.COVERED:
            try:
                is_visible = win32gui.IsWindowVisible(self.current_window.hwnd)
                logging.debug(f"   Janela COVERED - visível: {is_visible}")
                # Se política pause_on_covered estiver ativa, NÃO gravar quando coberta
                if self.pause_on_covered:
                    logging.debug("   Política pause_on_covered=True -> não gravar quando coberta")
                    is_suitable = False
                else:
                    # Se política desativada, permite gravar se ainda for visível
                    is_suitable = is_visible
            except Exception as e:
                logging.debug(f"   Erro verificando visibilidade: {e}")
                is_suitable = False

        logging.debug("🔍 VERIFICANDO ADEQUAÇÃO DA JANELA:")
        logging.debug(f"   Estado atual: {self.current_window.state.value}")
        logging.debug(f"   Estados base adequados: {[s.value for s in base_states]}")
        logging.debug(f"   É adequada: {is_suitable}")
        logging.debug(f"   Título: {self.current_window.title}")
        logging.debug(f"   HWND: {self.current_window.hwnd}")

        return is_suitable

    def get_window_recording_rect(self) -> Optional[Dict[str, int]]:
        """
        Retorna as coordenadas da janela para gravação.

        Returns:
            Dicionário com coordenadas (left, top, width, height) ou None
        """
        logging.debug("🎯 OBTENDO ÁREA DE GRAVAÇÃO:")
        logging.debug(f"   current_window: {self.current_window is not None}")

        if not self.current_window:
            logging.debug("   ❌ Sem janela atual")
            return None

        suitable = self.is_window_suitable_for_recording()
        logging.debug(f"   adequada: {suitable}")

        if not suitable:
            logging.debug("   ❌ Janela não adequada para gravação")
            return None

        # Usa área cliente quando configurado
        rect_tuple = self._get_capture_rect()
        if not rect_tuple:
            logging.debug("   ❌ Falha ao obter área de captura")
            return None

        left, top, right, bottom = rect_tuple
        rect = {"left": left, "top": top, "width": right - left, "height": bottom - top}

        logging.debug(f"   ✅ Área de gravação: {rect}")
        return rect

    def _find_rdp_window(self) -> Optional[int]:
        """
        Encontra a janela RDP baseada nas informações de conexão.

        Returns:
            Handle da janela RDP ou None se não encontrada
        """
        try:
            target_title = self.connection_info.get("name", "")
            target_ip = self.connection_info.get("ip", "")

            # Extrai IP e porta
            if ":" in target_ip:
                ip_part = target_ip.split(":")[0]
            else:
                ip_part = target_ip

            found_windows = []

            def enum_window_callback(hwnd, windows):
                try:
                    if not win32gui.IsWindowVisible(hwnd):
                        return True

                    window_title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)

                    # Verifica se é uma janela RDP
                    is_rdp_window = (
                        "TscShellContainerClass" in class_name
                        or "Remote Desktop" in window_title
                        or "Conexão de Área de Trabalho Remota" in window_title
                        or "Microsoft Terminal Services Client" in class_name
                    )

                    if is_rdp_window:
                        # Tenta fazer match com as informações de conexão
                        title_match = target_title and target_title.lower() in window_title.lower()
                        ip_match = ip_part and ip_part in window_title

                        if title_match or ip_match:
                            windows.append(
                                {
                                    "hwnd": hwnd,
                                    "title": window_title,
                                    "class": class_name,
                                    "score": (2 if title_match else 0) + (1 if ip_match else 0),
                                }
                            )
                        elif not target_title and not ip_part:
                            # Se não temos informações específicas, pega qualquer janela RDP
                            windows.append(
                                {
                                    "hwnd": hwnd,
                                    "title": window_title,
                                    "class": class_name,
                                    "score": 1,
                                }
                            )

                except Exception as e:
                    logging.debug(f"Error checking window {hwnd}: {e}")

                return True

            win32gui.EnumWindows(enum_window_callback, found_windows)

            if found_windows:
                # Ordena por score e retorna a melhor match
                found_windows.sort(key=lambda x: x["score"], reverse=True)
                best_match = found_windows[0]
                logging.info(
                    f"Found RDP window: {best_match['title']} (HWND: {best_match['hwnd']})"
                )

                # Tenta trazer a janela para frente para facilitar a gravação
                self._bring_window_to_front(best_match["hwnd"])

                return best_match["hwnd"]
            else:
                logging.warning("No RDP window found matching connection info")
                return None

        except Exception as e:
            logging.error(f"Error finding RDP window: {e}")
            return None

    def _tracking_loop(self):
        """Loop principal de rastreamento da janela."""
        while not self.stop_event.is_set():
            try:
                # Atualiza informações da janela
                self._update_window_info()

                # Aguarda próxima verificação
                if self.stop_event.wait(self.update_interval):
                    break

            except Exception as e:
                logging.error(f"Error in window tracking loop: {e}")
                # Aguarda um pouco antes de tentar novamente
                if self.stop_event.wait(5.0):
                    break

    def _tracking_loop_with_wait(self):
        """
        Loop de rastreamento que espera a janela RDP aparecer antes de iniciar o monitoramento.
        """
        logging.info("Starting RDP window detection loop...")

        # Fase 1: Espera a janela RDP aparecer
        attempts = 0
        while not self.stop_event.is_set() and attempts < self.max_window_wait_attempts:
            attempts += 1

            # Tenta encontrar a janela RDP
            self.target_hwnd = self._find_rdp_window()

            if self.target_hwnd:
                self.window_found = True
                logging.info(
                    f"RDP window found after {attempts} attempts (HWND: {self.target_hwnd})"
                )

                # Notifica que a janela foi encontrada
                if self.on_window_found:
                    try:
                        window_info = self._get_current_window_info()
                        if window_info:
                            self.on_window_found(window_info)
                    except Exception as e:
                        logging.warning(f"Error calling on_window_found callback: {e}")

                break
            else:
                logging.debug(
                    f"RDP window not found, attempt {attempts}/{self.max_window_wait_attempts}"
                )

                # Espera antes da próxima tentativa
                if self.stop_event.wait(self.window_wait_interval):
                    return  # Stop event foi acionado

        # Verifica se encontrou a janela
        if not self.target_hwnd:
            logging.error(
                f"Failed to find RDP window after {self.max_window_wait_attempts} attempts"
            )
            return

        # Fase 2: Inicia o monitoramento normal da janela
        logging.info("Starting normal window tracking...")
        while not self.stop_event.is_set():
            try:
                # Atualiza informações da janela
                self._update_window_info()

                # Aguarda próxima verificação
                if self.stop_event.wait(self.update_interval):
                    break

            except Exception as e:
                logging.error(f"Error in window tracking loop: {e}")
                # Aguarda um pouco antes de tentar novamente
                if self.stop_event.wait(5.0):
                    break

    def _update_window_info(self):
        """Atualiza as informações da janela e detecta mudanças."""
        try:
            if not self.target_hwnd:
                return

            # Verifica se a janela ainda existe
            if not win32gui.IsWindow(self.target_hwnd):
                self._handle_window_lost()
                return

            # Coleta informações atuais
            try:
                window_title = win32gui.GetWindowText(self.target_hwnd)
                window_rect = win32gui.GetWindowRect(self.target_hwnd)

                logging.debug("🔍 CRIANDO WindowInfo:")
                logging.debug(f"   HWND: {self.target_hwnd}")
                logging.debug(f"   Título: {window_title}")
                logging.debug(f"   Rect: {window_rect}")

                # Determina estado da janela
                window_state = self._determine_window_state()
                logging.debug(f"   Estado determinado: {window_state}")

                # Informações do processo
                thread_id, process_id = win32process.GetWindowThreadProcessId(self.target_hwnd)

                # Verifica se é a janela em primeiro plano
                is_foreground = win32gui.GetForegroundWindow() == self.target_hwnd

                # Determina monitor
                monitor_index = self._get_monitor_index(window_rect)

                # Cria nova informação da janela
                new_window = WindowInfo(
                    hwnd=self.target_hwnd,
                    title=window_title,
                    rect=window_rect,
                    state=window_state,
                    is_foreground=is_foreground,
                    process_id=process_id,
                    thread_id=thread_id,
                    monitor_index=monitor_index,
                    last_updated=time.time(),
                )

                logging.debug("   ✅ WindowInfo criado com sucesso")

                # Atualiza janela atual ANTES dos callbacks
                old_window = self.current_window
                self.current_window = new_window
                logging.debug(f"   📝 current_window atualizado: {new_window is not None}")

                # Detecta e notifica mudanças (após atualizar current_window)
                self._check_for_changes(old_window, new_window)

            except Exception as e:
                logging.error(f"Error getting window info: {e}")
                logging.debug("   ❌ Erro ao criar WindowInfo, current_window será None")
                self._handle_window_lost()

        except Exception as e:
            logging.error(f"Error updating window info: {e}")

    def _determine_window_state(self) -> WindowState:
        """Determina o estado atual da janela."""
        try:
            logging.debug(f"🔍 DETERMINANDO ESTADO DA JANELA {self.target_hwnd}:")

            # Verifica se está minimizada
            is_iconic = win32gui.IsIconic(self.target_hwnd)
            logging.debug(f"   IsIconic: {is_iconic}")
            if is_iconic:
                logging.debug("   ➡️ Estado: MINIMIZED (IsIconic)")
                return WindowState.MINIMIZED

            # Verifica se está maximizada usando GetWindowPlacement
            try:
                placement = win32gui.GetWindowPlacement(self.target_hwnd)
                show_cmd = placement[1]
                logging.debug(f"   GetWindowPlacement showCmd: {show_cmd}")
                # placement[1] é o showCmd: 1=normal, 2=minimized, 3=maximized
                if show_cmd == 3:  # SW_SHOWMAXIMIZED
                    logging.debug("   ➡️ Estado: MAXIMIZED (GetWindowPlacement)")
                    return WindowState.MAXIMIZED
                elif show_cmd == 2:  # SW_SHOWMINIMIZED
                    logging.debug("   ➡️ Estado: MINIMIZED (GetWindowPlacement)")
                    return WindowState.MINIMIZED
            except Exception as e:
                logging.debug(f"GetWindowPlacement failed: {e}, using fallback method")
                # Fallback: verifica se a janela ocupa toda a tela
                try:
                    window_rect = win32gui.GetWindowRect(self.target_hwnd)
                    # Obter tamanho da tela
                    import win32api

                    screen_width = win32api.GetSystemMetrics(0)  # SM_CXSCREEN
                    screen_height = win32api.GetSystemMetrics(1)  # SM_CYSCREEN

                    left, top, right, bottom = window_rect
                    logging.debug(
                        f"   Fallback check - Window: {window_rect}, Screen: {screen_width}x{screen_height}"
                    )
                    if left <= 0 and top <= 0 and right >= screen_width and bottom >= screen_height:
                        logging.debug("   ➡️ Estado: MAXIMIZED (fallback)")
                        return WindowState.MAXIMIZED
                except Exception as e2:
                    logging.debug(f"Fallback maximized check failed: {e2}")

            # Verifica se está coberta por outras janelas
            foreground_hwnd = win32gui.GetForegroundWindow()
            logging.debug(f"   Foreground window: {foreground_hwnd} (nossa: {self.target_hwnd})")
            if foreground_hwnd != self.target_hwnd:
                # Verifica se nossa janela está visível (não totalmente coberta)
                is_covered = self._is_window_covered()
                logging.debug(f"   Window covered: {is_covered}")
                if is_covered:
                    logging.debug("   ➡️ Estado: COVERED")
                    return WindowState.COVERED

            logging.debug("   ➡️ Estado: NORMAL")
            return WindowState.NORMAL

        except Exception as e:
            logging.error(f"Error determining window state: {e}")
            return WindowState.NOT_FOUND

    def _is_window_covered(self) -> bool:
        """Verifica se a janela está coberta por outras janelas."""
        try:
            # Se nossa janela não é visível, está definitivamente coberta
            if not win32gui.IsWindowVisible(self.target_hwnd):
                logging.debug("   _is_window_covered: janela não visível")
                return True

            # Se nossa janela está em primeiro plano, não está coberta
            foreground_hwnd = win32gui.GetForegroundWindow()
            if foreground_hwnd == self.target_hwnd:
                logging.debug("   _is_window_covered: janela em primeiro plano")
                return False

            # Verifica se a janela em primeiro plano realmente sobrepõe a ÁREA DE CAPTURA (cliente)
            try:
                # Use a área de captura (cliente) para calcular sobreposição
                capture_rect = self._get_capture_rect()
                if not capture_rect:
                    capture_rect = win32gui.GetWindowRect(self.target_hwnd)
                our_rect = capture_rect
                fg_rect = win32gui.GetWindowRect(foreground_hwnd)

                overlap_area = self._calculate_overlap_area(our_rect, fg_rect)
                our_area = (our_rect[2] - our_rect[0]) * (our_rect[3] - our_rect[1])

                if our_area > 0:
                    overlap_percentage = overlap_area / our_area
                    logging.debug(
                        f"   _is_window_covered: sobreposição na área de captura {overlap_percentage:.2%} (threshold={self.covered_overlap_threshold:.2f})"
                    )
                    # Considera coberta se exceder o limiar configurado (default 0%)
                    return overlap_percentage > self.covered_overlap_threshold
                else:
                    return True

            except Exception as e:
                logging.debug(f"   _is_window_covered: erro calculando sobreposição: {e}")
                # Fallback: considera coberta se não é foreground
                return True

        except Exception as e:
            logging.error(f"Error checking if window is covered: {e}")
            return False

    def _calculate_overlap_area(self, rect1, rect2):
        """Calcula a área de sobreposição entre dois retângulos."""
        left1, top1, right1, bottom1 = rect1
        left2, top2, right2, bottom2 = rect2

        # Encontra a área de interseção
        left = max(left1, left2)
        top = max(top1, top2)
        right = min(right1, right2)
        bottom = min(bottom1, bottom2)

        # Se não há interseção, retorna 0
        if left >= right or top >= bottom:
            return 0

        return (right - left) * (bottom - top)

    def _get_capture_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """Obtém o retângulo de captura da janela.

        Quando `capture_client_area` está habilitado, usa a área cliente (sem bordas
        e barra de título), mapeada para coordenadas de tela.
        """
        try:
            if not self.current_window:
                return None

            if not self.capture_client_area:
                return self.current_window.rect

            # Converte área cliente para coordenadas de tela
            # GetClientRect retorna coordenadas relativas à janela (0,0)-(w,h).
            import win32con
            hwnd = self.current_window.hwnd
            client_left_top = (0, 0)

            client_rect = win32gui.GetClientRect(hwnd)
            # MapWindowPoints: mapeia pontos da janela para tela
            # Precisamos do topo-esquerdo (0,0) e do bottom-right (w,h)
            pts = win32gui.MapWindowPoints(hwnd, 0, (client_left_top, (client_rect[2], client_rect[3])))
            left = pts[0][0]
            top = pts[0][1]
            right = pts[1][0]
            bottom = pts[1][1]

            # Sanidade: se algo falhar, retorna rect completo
            if left >= right or top >= bottom:
                logging.debug("   _get_capture_rect: área cliente inválida, usando rect da janela")
                return self.current_window.rect

            logging.debug(
                f"   _get_capture_rect: usando área cliente {left, top, right, bottom} (client={client_rect})"
            )
            return (left, top, right, bottom)
        except Exception as e:
            logging.debug(f"   _get_capture_rect: falha ao obter área cliente: {e}")
            return self.current_window.rect if self.current_window else None

    def _bring_window_to_front(self, hwnd: int) -> bool:
        """
        Tenta trazer a janela especificada para frente.

        Args:
            hwnd: Handle da janela

        Returns:
            True se conseguiu trazer para frente
        """
        try:
            logging.debug(f"🔄 Tentando trazer janela {hwnd} para frente...")

            # Primeiro, restaura a janela se estiver minimizada
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
                logging.debug("   Restaurou janela minimizada")

            # Tenta várias abordagens para trazer para frente
            success = False

            # Método 1: SetForegroundWindow
            try:
                win32gui.SetForegroundWindow(hwnd)
                success = True
                logging.debug("   SetForegroundWindow: sucesso")
            except Exception as e:
                logging.debug(f"   SetForegroundWindow falhou: {e}")

            # Método 2: BringWindowToTop
            try:
                win32gui.BringWindowToTop(hwnd)
                success = True
                logging.debug("   BringWindowToTop: sucesso")
            except Exception as e:
                logging.debug(f"   BringWindowToTop falhou: {e}")

            # Método 3: SetWindowPos controlando topmost conforme allow_window_override
            # - Se allow_window_override=True, NÃO usa HWND_TOPMOST (-1); usa HWND_TOP (0)
            #   permitindo que Alt+Tab e outras janelas apareçam por cima.
            # - Se allow_window_override=False, usa HWND_TOPMOST para manter sempre à frente.
            try:
                insert_after = -1 if not self.allow_window_override else 0  # -1=HWND_TOPMOST, 0=HWND_TOP
                win32gui.SetWindowPos(
                    hwnd, insert_after, 0, 0, 0, 0, 0x0001 | 0x0002
                )  # SWP_NOSIZE | SWP_NOMOVE
                success = True
                logging.debug(
                    f"   SetWindowPos: sucesso (allow_window_override={self.allow_window_override}, insert_after={insert_after})"
                )
            except Exception as e:
                logging.debug(f"   SetWindowPos falhou: {e}")

            if success:
                logging.info(f"✅ Janela {hwnd} trazida para frente")
            else:
                logging.warning(f"⚠️ Não foi possível trazer janela {hwnd} para frente")

            return success

        except Exception as e:
            logging.error(f"Erro ao trazer janela para frente: {e}")
            return False

    def _get_monitor_index(self, rect: Tuple[int, int, int, int]) -> int:
        """Determina em qual monitor a janela está localizada."""
        try:
            # Implementação simplificada - retorna 0 para monitor primário
            # Uma versão mais completa usaria MonitorFromRect API
            return 0
        except Exception as e:
            logging.error(f"Error getting monitor index: {e}")
            return 0

    def _check_for_changes(self, old_window: Optional[WindowInfo], new_window: WindowInfo):
        """Verifica mudanças na janela e chama callbacks apropriados."""
        try:
            # Primeira execução
            if not old_window:
                if self.on_window_found:
                    self.on_window_found(new_window)
                return

            # Mudança de estado
            if old_window.state != new_window.state:
                logging.info(
                    f"Window state changed: {old_window.state.value} -> {new_window.state.value}"
                )
                if self.on_window_state_changed:
                    self.on_window_state_changed(old_window.state, new_window.state)

            # Mudança de posição
            if old_window.rect != new_window.rect:
                logging.debug(f"Window moved to: {new_window.rect}")
                if self.on_window_moved:
                    self.on_window_moved(new_window)

            # Mudança de monitor
            if old_window.monitor_index != new_window.monitor_index:
                if self.on_window_moved:
                    self.on_window_moved(new_window)

        except Exception as e:
            logging.error(f"Error checking for window changes: {e}")

    def _handle_window_lost(self):
        """Trata a perda da janela (fechada ou não encontrada)."""
        if self.current_window:
            logging.warning(f"Lost tracking of window: {self.current_window.title}")

            # Tenta revalidar a janela antes de considerá-la perdida
            if self.target_hwnd and win32gui.IsWindow(self.target_hwnd):
                try:
                    # Se a janela ainda existe, tenta recuperar informações
                    title = win32gui.GetWindowText(self.target_hwnd)
                    if title:  # Se consegue obter título, janela está ok
                        logging.info(f"Window still exists, recovering: {title}")
                        return
                except Exception as e:
                    logging.debug(f"Error validating window: {e}")

            # Realmente perdeu a janela
            # old_window = self.current_window  # Não utilizado
            self.current_window = None

            if self.on_window_lost:
                self.on_window_lost()

            # Tenta encontrar a janela novamente com retry
            for attempt in range(3):  # 3 tentativas
                try:
                    self.target_hwnd = self._find_rdp_window()
                    if self.target_hwnd:
                        logging.info(f"Reacquired RDP window for tracking on attempt {attempt + 1}")
                        break
                    else:
                        if attempt < 2:  # Não é a última tentativa
                            time.sleep(1)  # Espera 1 segundo antes da próxima tentativa
                except Exception as e:
                    logging.debug(f"Error trying to reacquire window (attempt {attempt + 1}): {e}")
                    if attempt < 2:
                        time.sleep(1)

    def set_callbacks(
        self,
        on_state_changed: Optional[Callable[[WindowState, WindowState], None]] = None,
        on_moved: Optional[Callable[[WindowInfo], None]] = None,
        on_lost: Optional[Callable[[], None]] = None,
        on_found: Optional[Callable[[WindowInfo], None]] = None,
    ):
        """Define callbacks para eventos da janela."""
        self.on_window_state_changed = on_state_changed
        self.on_window_moved = on_moved
        self.on_window_lost = on_lost
        self.on_window_found = on_found

    def _get_current_window_info(self) -> Optional[WindowInfo]:
        """Cria objeto WindowInfo com informações atuais da janela."""
        try:
            if not self.target_hwnd or not win32gui.IsWindow(self.target_hwnd):
                return None

            window_title = win32gui.GetWindowText(self.target_hwnd)
            window_rect = win32gui.GetWindowRect(self.target_hwnd)
            window_state = self._determine_window_state()
            thread_id, process_id = win32process.GetWindowThreadProcessId(self.target_hwnd)
            is_foreground = win32gui.GetForegroundWindow() == self.target_hwnd
            monitor_index = self._get_monitor_index(window_rect)

            return WindowInfo(
                hwnd=self.target_hwnd,
                title=window_title,
                rect=window_rect,
                state=window_state,
                is_foreground=is_foreground,
                process_id=process_id,
                thread_id=thread_id,
                monitor_index=monitor_index,
                last_updated=time.time(),
            )

        except Exception as e:
            logging.error(f"Error getting current window info: {e}")
            return None

    def __del__(self):
        """Destructor para garantir limpeza adequada."""
        self.stop_tracking()
