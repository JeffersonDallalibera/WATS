# WATS_Project/wats_app/app_window.py (Com Atualização Diferencial)

import json
import logging
import os
import socket
import subprocess
import sys
import webbrowser
from threading import Event, Thread
from tkinter import Menu, messagebox, ttk
from typing import Any, Dict, List, Optional, Set, Tuple
from concurrent.futures import Future

import customtkinter as ctk

from .admin_panels.admin_hub import AdminHubDialog
from .config import (
    ASSETS_DIR,
    BASE_DIR,
    FILTER_PLACEHOLDER,
    USER_DATA_DIR,
    get_app_config,
    is_demo_mode,
)
from .db.db_service import DBService
from .db.exceptions import DatabaseError
from .dialogs import ClientSelectorDialog
from .utils import hash_password_md5, parse_particularities
from .utils.process_monitor import is_rdp_connection_active, get_rdp_monitor
from .util_cache.thread_pool import get_thread_pool, shutdown_thread_pool

# Importação condicional do RecordingManager em modo demo
if not is_demo_mode():
    from .recording import RecordingManager
else:
    # Mock do RecordingManager para modo demo
    class RecordingManager:
        def __init__(self, *args, **kwargs):
            pass

        def initialize(self):
            return True

        def set_callbacks(self, *args, **kwargs):
            pass

        def start_recording(self, *args, **kwargs):
            pass

        def stop_recording(self, *args, **kwargs):
            pass

        def shutdown(self):
            pass


try:
    from .session_protection import CreateSessionProtectionDialog, ValidateSessionPasswordDialog

    # Não importamos session_protection_manager aqui - sempre buscaremos a instância atual
    session_protection_manager = None  # Será sempre buscado dinamicamente
except ImportError as e:
    # Fallback se não encontrar o módulo
    logging.error(f"[IMPORT_DEBUG] ImportError ao importar session_protection: {e}")
    CreateSessionProtectionDialog = None
    ValidateSessionPasswordDialog = None
    session_protection_manager = None


def get_current_session_protection_manager():
    """Retorna a instância atual do session_protection_manager."""
    try:
        from .session_protection import session_protection_manager

        return session_protection_manager
    except ImportError:
        return None


# Define uma estrutura para facilitar a comparação
class ConnectionData:
    def __init__(self, row):
        # Mapeia a linha do DB para atributos nomeados
        self.con_codigo: int = row[0]
        self.ip: str = row[1]
        self.nome: str = row[2]
        self.user: str = row[3]
        self.pwd: str = row[4]
        self.group_name: Optional[str] = row[5]
        self.connected_user: Optional[str] = row[6]  # Usuário(s) conectado(s)
        self.extra: Optional[str] = row[8]
        self.particularidade: Optional[str] = row[9]  # Link Wiki cru
        self.cliente: Optional[str] = row[10]
        self.con_tipo: str = row[11]  # Tipo da conexão
        
        # DEBUG: Log do IP carregado
        if self.ip and "hs103" in self.ip.lower():
            logging.debug(f"[CONNECTIONDATA] Carregado do DB - ID:{self.con_codigo}, IP:{self.ip}, Nome:{self.nome}")

        # Dados derivados para a Treeview
        self.wiki_display_text = self._get_wiki_display(self.particularidade)
        self.tags = ("in_use",) if self.connected_user else ()

    def _get_wiki_display(self, particularidade_str: Optional[str]) -> str:
        if not particularidade_str:
            return ""
        particularidades = parse_particularities(particularidade_str)
        if not particularidades:
            return ""

        # Conta quantos têm URL (links de wiki)
        com_wiki = sum(1 for _, url in particularidades if url)
        total = len(particularidades)

        if total == 1:
            nome, url = particularidades[0]
            if url:
                return f"🔗 {nome}"
            else:
                return f"📋 {nome}"
        else:
            if com_wiki > 0:
                return f"🔗 {com_wiki} Wiki{'s' if com_wiki != 1 else ''} | 📋 {total - com_wiki} Info{'s' if (total - com_wiki) != 1 else ''}"
            else:
                return f"📋 {total} Cliente{'s' if total != 1 else ''}"

    def get_treeview_values(self) -> Tuple:
        """Retorna a tupla de valores na ordem esperada pela Treeview."""
        # Ordem das colunas: ('db_id', 'ip', 'user', 'pwd', 'title', 'extra',
        # 'wiki_link', 'username', 'wiki_text', 'con_cliente')
        return (
            self.con_codigo,
            self.ip,
            self.user,
            self.pwd,
            self.nome,
            self.extra,
            self.particularidade,
            self.connected_user,
            self.wiki_display_text,
            self.cliente,
        )

    # Permite comparar objetos ConnectionData
    def __eq__(self, other):
        if not isinstance(other, ConnectionData):
            return NotImplemented
        # Compara apenas os campos relevantes para a exibição na Treeview
        return (
            self.nome == other.nome
            and self.group_name == other.group_name
            and self.connected_user == other.connected_user
            and self.wiki_display_text == other.wiki_display_text
        )

    # Necessário se __eq__ for definido
    def __hash__(self):
        return hash((self.con_codigo,))


class Application(ctk.CTk):
    def __init__(self, settings_instance):
        super().__init__()
        # Store settings instance
        self.settings = settings_instance

        # ... (inicialização de user_session_name, user_ip, etc. idêntica) ...
        self.user_session_name: str = os.environ.get("USERNAME", "Desconhecido")
        # Defer potentially slow network operation
        self.user_ip: str = "127.0.0.1"  # Default, will be set async
        self.computer_name: str = os.environ.get("COMPUTERNAME", "N/A")
        self.os_user: str = os.environ.get("USERNAME", "N/A")
        self.settings_file = os.path.join(USER_DATA_DIR, "wats_settings.json")

        logging.info(f"Arquivo de settings definido como: {self.settings_file}")
        # Apply theme preference quickly (small, local IO)
        self._load_and_apply_theme()

        # Initialize thread pool for async operations
        self.thread_pool = get_thread_pool()
        logging.info("ThreadPool inicializado para operações assíncronas")

        # Defer heavy operations (DB initialization and heavy widget creation)
        # to improve perceived startup time. We'll create a minimal window
        # quickly and then schedule the rest.
        self.db = None  # Will be set later by background init
        self.recording_manager = None  # Will be set later by background init

        # Lightweight initial state
        self.data_cache: List[ConnectionData] = []
        self.active_heartbeats: Dict[int, Event] = {}
        self._refresh_job = None
        self.tree_item_map: Dict[int, str] = {}
        self.group_item_map: Dict[str, str] = {}

        # Configure basic window and show a quick loading indicator
        self._configure_window()

        # Create immediate simple loading label
        self._create_immediate_loading()

        # Schedule deferred full initialization shortly after the window is responsive
        self.after(50, self._deferred_init)

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_immediate_loading(self):
        """Creates a simple loading message immediately to show responsiveness."""
        # Create a minimal loading interface without heavy widgets
        self.immediate_loading_frame = ctk.CTkFrame(self)
        self.immediate_loading_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.immediate_loading_label = ctk.CTkLabel(
            self.immediate_loading_frame, text="🔄 Inicializando WATS...", font=("Segoe UI", 16)
        )
        self.immediate_loading_label.pack(expand=True, pady=50)

    # --- [NOVOS MÉTODOS] Para salvar e carregar o tema ---
    def _load_theme_preference(self) -> Optional[str]:
        """Lê o arquivo JSON e retorna o tema salvo."""
        if not os.path.exists(self.settings_file):
            return None
        try:
            # --- [NOVO] Verifica se o arquivo está vazio ---
            if os.path.getsize(self.settings_file) == 0:
                logging.warning("Arquivo de settings encontrado, mas está VAZIO.")
                # Opcional: Tenta deletar o arquivo vazio para a próxima tentativa criar um novo
                try:
                    os.remove(self.settings_file)
                except OSError as del_err:
                    logging.error(f"Não foi possível deletar arquivo vazio: {del_err}")
                return None  # Trata como não existente
            # --- FIM NOVO ---

            with open(self.settings_file, "r", encoding="utf-8") as f:  # Adiciona encoding
                data = json.load(f)
                theme = data.get("theme")
                return theme
        except (json.JSONDecodeError, IOError) as e:
            # O log "Expecting value..." entra aqui
            logging.warning(f"Não foi possível LER o arquivo de settings: {e}")
            return None

    def _save_theme_preference(self, theme_mode: str):
        """Salva o tema escolhido no arquivo JSON."""
        try:
            os.makedirs(
                os.path.dirname(self.settings_file), exist_ok=True
            )  # Cria diretórios, se não existirem
            with open(self.settings_file, "w", encoding="utf-8") as f:  # Adiciona encoding
                json.dump({"theme": theme_mode}, f, indent=4)
        except IOError as e:
            logging.error(f"Não foi possível SALVAR o arquivo de settings: {e}")
            # --- [NOVO] Mostra erro para o usuário ---
            messagebox.showwarning(
                "Erro ao Salvar Configuração",
                "Não foi possível salvar a preferência de tema.\n\n"
                f"Verifique as permissões de escrita na pasta:\n{os.path.dirname(self.settings_file)}\n\n"
                f"Erro: {e}",
            )

    def _load_and_apply_theme(self):
        """Lê a preferência e aplica o tema na inicialização."""
        theme = self._load_theme_preference()
        if theme in ["Light", "Dark"]:
            ctk.set_appearance_mode(theme)
        else:
            ctk.set_appearance_mode("System")

    # --- Fim dos novos métodos ---

    def _on_closing(self):
        logging.info("Fechando aplicação...")
        if self._refresh_job:
            self.after_cancel(self._refresh_job)  # Cancela refresh pendente
        
        # Stop all heartbeats
        for stop_event in self.active_heartbeats.values():
            stop_event.set()

        # Shutdown recording manager
        if self.recording_manager:
            try:
                self.recording_manager.shutdown()
                logging.info("Recording manager shutdown completed")
            except Exception as e:
                logging.error(f"Error shutting down recording manager: {e}")

        # Cleanup collaborative sessions
        self._cleanup_collaborative_sessions()

        # Shutdown thread pool gracefully
        try:
            logging.info("Shutting down thread pool...")
            shutdown_thread_pool(wait=True, timeout=5.0)
            logging.info("Thread pool shut down successfully")
        except Exception as e:
            logging.error(f"Error shutting down thread pool: {e}")

        self.destroy()

    # --- Deferred initialization helpers ---
    def _deferred_init(self):
        """Runs on the main thread soon after the window is displayed.
        This creates the heavier widgets and starts DB initialization in a
        background thread so the UI appears quickly.
        """
        logging.info("Deferred UI init starting...")
        try:
            # Remove immediate loading
            if hasattr(self, "immediate_loading_frame"):
                self.immediate_loading_frame.destroy()

            # Create the widgets/styles (may be somewhat expensive)
            self._create_widgets()
            self._apply_treeview_theme()

            # Show the proper loading message now that widgets are created
            self._show_loading_message(True)
        except Exception as e:
            logging.error(f"Erro durante criação de widgets: {e}", exc_info=True)

        # Start DB initialization in background; when DB is ready it will start the
        # initial data load in its own background thread.
        logging.info("[CONFIG_DEBUG] Iniciando thread de inicialização do DB...")
        Thread(target=self._init_db_and_start, daemon=True).start()
        logging.info("[CONFIG_DEBUG] Thread de inicialização do DB iniciada")

    def _init_db_and_start(self):
        """Initialize DBService in a background thread and then start the
        initial data load (also in background). Any UI-side error display is
        marshalled to the main thread via `after`.
        """
        logging.info("Inicializando banco de dados...")

        # Resolve IP address in background to avoid blocking startup
        try:
            self.user_ip = socket.gethostbyname(socket.gethostname())
        except socket.gaierror as e:
            logging.warning(f"Could not resolve hostname: {e}, using localhost")
            self.user_ip = "127.0.0.1"

        try:
            self.db = DBService(self.settings)

            # Configura o sistema de proteção de sessão com acesso ao DB
            try:
                # Tenta fazer import direto primeiro
                try:
                    from src.wats.session_protection import configure_session_protection_with_db
                except ImportError:
                    from .session_protection import configure_session_protection_with_db

                configure_session_protection_with_db(self.db)
                logging.info("Sistema de proteção de sessão configurado")

            except Exception as e:
                logging.warning(f"Falha ao configurar proteção de sessão: {e}")

            # Initialize recording manager
            self.recording_manager = RecordingManager(self.settings)
            if self.recording_manager.initialize():
                logging.info("Recording manager inicializado")
                # Set up recording callbacks
                self.recording_manager.set_callbacks(
                    on_started=self._on_recording_started,
                    on_stopped=self._on_recording_stopped,
                    on_error=self._on_recording_error,
                )
            else:
                logging.warning("Recording manager initialization failed.")
                self.recording_manager = None

        except DatabaseError as e:
            logging.critical(f"Falha CRÍTICA ao inicializar DB (background): {e}", exc_info=True)
            self.after(
                0,
                messagebox.showerror,
                "Erro Crítico de Banco de Dados",
                f"Não foi possível iniciar a aplicação.\n\n{e}",
            )
            self.after(0, self._show_loading_message, False)
            return

        # Start the initial data fetch in its own background thread
        Thread(target=self._initial_load_in_background, daemon=True).start()

    def _configure_window(self):
        """Configura a janela principal."""
        # Carrega configurações da aplicação
        app_config = get_app_config()
        window_title = app_config.get("window_title", "WATS - Sistema de Gravação RDP")

        # Define o título com o nome da sessão do usuário
        self.title(f"{window_title} ({self.user_session_name})")
        self.geometry("800x650")
        self.minsize(700, 500)

        # [ALTERADO] O 'set_appearance_mode' foi movido para _load_and_apply_theme
        # Esta linha agora apenas lê o modo que já foi definido.
        initial_mode = ctk.get_appearance_mode()
        self.initial_button_icon = "☀️" if initial_mode == "Light" else "🌙"

        icon_path = os.path.join(ASSETS_DIR, "ats.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                logging.warning(f"Não foi possível carregar o ícone: {e}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _apply_treeview_theme(self):
        """Aplica o tema atual (claro ou escuro) ao widget ttk.Treeview."""
        mode = ctk.get_appearance_mode()

        if mode == "Dark":
            colors = ("#E0E0E0", "#2B2B2B", "#3C3F41", "#1F6AA5", "#2B2B2B", "#6B2D2D", "#FFFFFF")
        else:
            colors = ("#1E1E1E", "#FFFFFF", "#F0F0F0", "#0078D7", "#FFFFFF", "#FFDDE0", "#990000")

        text_color, bg_color, heading_bg, selected_color, field_bg, in_use_bg, in_use_fg = colors

        self.style.configure(
            "Treeview",
            background=bg_color,
            foreground=text_color,
            fieldbackground=field_bg,
            rowheight=28,
            font=("Segoe UI", 10),
            borderwidth=0,
            relief="flat",
        )
        self.style.configure(
            "Treeview.Heading",
            background=heading_bg,
            foreground=text_color,
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            relief="flat",
        )
        self.style.map(
            "Treeview",
            background=[("selected", selected_color)],
            foreground=[("selected", "white")],
        )
        self.style.configure("in_use.Treeview", background=in_use_bg, foreground=in_use_fg)

        try:
            self.context_menu.config(
                bg=bg_color,
                fg=text_color,
                activebackground=selected_color,
                activeforeground="white",
            )
        except AttributeError:
            pass

    def _toggle_theme(self):
        mode = ctk.get_appearance_mode()
        new_mode = "Light" if mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        self.theme_button.configure(text="☀️" if new_mode == "Light" else "🌙")
        self._apply_treeview_theme()
        self._save_theme_preference(new_mode)

    def _create_widgets(self):
        """Cria todos os widgets da interface, incluindo a Treeview."""
        # --- INÍCIO DO CABEÇALHO ---
        header_frame = ctk.CTkFrame(self, corner_radius=10)
        header_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        self.filter_var = ctk.StringVar()
        self.filter_entry = ctk.CTkEntry(
            header_frame,
            textvariable=self.filter_var,
            placeholder_text=FILTER_PLACEHOLDER,
            font=("Segoe UI", 13),
            height=40,
            border_width=0,
        )
        self.filter_entry.grid(row=0, column=0, padx=(15, 10), pady=10, sticky="ew")
        self.filter_var.trace_add("write", lambda *args: self._on_filter_change())

        self.theme_button = ctk.CTkButton(
            header_frame,
            text=self.initial_button_icon,  # Este valor é definido em _configure_window
            width=40,
            height=40,
            font=("Segoe UI", 20),
            command=self._toggle_theme,
        )
        self.theme_button.grid(row=0, column=1, padx=(0, 10), pady=10)

        # Botão de gravações (se disponível)
        if self.recording_manager:
            self.recording_button = ctk.CTkButton(
                header_frame,
                text="📹",
                width=40,
                height=40,
                font=("Segoe UI", 20),
                command=self._show_recording_info,
            )
            self.recording_button.grid(row=0, column=2, padx=(0, 10), pady=10)
            admin_column = 3
        else:
            admin_column = 2

        self.admin_button = ctk.CTkButton(
            header_frame,
            text="⚙️",
            width=40,
            height=40,
            font=("Segoe UI", 20),
            command=self._open_admin_login,
        )
        self.admin_button.grid(row=0, column=admin_column, padx=(0, 15), pady=10)
        # --- FIM DO CABEÇALHO ---

        # --- CONTAINER DA TREEVIEW (O código restante deve estar aqui) ---
        tree_container = ctk.CTkFrame(self, fg_color="transparent")
        tree_container.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        self.style = ttk.Style(self)  # Importante ter o estilo antes da Treeview
        self.style.theme_use("clam")

        columns = (
            "db_id",
            "ip",
            "user",
            "pwd",
            "title",
            "extra",
            "wiki_link",
            "username",
            "wiki_text",
            "con_cliente",
        )
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            displaycolumns=("username", "wiki_text"),
            height=20,
            selectmode="browse",
            show="tree headings",  # Mostra cabeçalhos, não a coluna #0
            style="Treeview",  # Estilo definido em _apply_treeview_theme
        )

        tree_container = ctk.CTkFrame(self, fg_color="transparent")
        tree_container.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        self.style = ttk.Style(self)  # Importante ter o estilo antes da Treeview
        self.style.theme_use("clam")

        columns = (
            "db_id",
            "ip",
            "user",
            "pwd",
            "title",
            "extra",
            "wiki_link",
            "username",
            "wiki_text",
            "con_cliente",
        )
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            displaycolumns=("username", "wiki_text"),
            height=20,
            selectmode="browse",
            show="tree headings",  # Mostra cabeçalhos, não a coluna #0
            style="Treeview",  # Estilo definido em _apply_treeview_theme
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Configura as colunas (igual a antes)
        self.tree.column(
            "#0", width=300, minwidth=200, stretch=True
        )  # Coluna da árvore (Nome/Grupo)
        self.tree.column("username", width=220, anchor="w")
        self.tree.heading("username", text="👤 Usuário Conectado", anchor="w")
        self.tree.column("wiki_text", width=220, anchor="w")
        self.tree.heading("wiki_text", text="📋 Particularidades", anchor="w")

        scrollbar = ctk.CTkScrollbar(tree_container, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Menu de Contexto (igual a antes)
        self.context_menu = Menu(self, tearoff=0, font=("Segoe UI", 9), borderwidth=0)
        self.context_menu.add_command(label="🔓 Liberar Conexão", command=self._release_connection)
        self.context_menu.add_command(
            label="🖥️ Usar WTS Nativo (mstsc)", command=self._connect_native_wts
        )

        # Adiciona opções de proteção de sessão
        current_session_manager = get_current_session_protection_manager()
        if CreateSessionProtectionDialog and current_session_manager:
            self.context_menu.add_separator()
            self.context_menu.add_command(label="🔒 Proteger Sessão", command=self._protect_session)
            self.context_menu.add_command(
                label="🔓 Remover Proteção", command=self._remove_session_protection
            )

        # Adiciona opção de gravações
        if self.recording_manager:
            self.context_menu.add_separator()
            self.context_menu.add_command(
                label="📹 Ver Gravações", command=self._show_recording_info
            )

        self.tree.bind("<Double-1>", self._on_item_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)

        # [NOVO] Label para mensagem de "Carregando..."
        self.loading_label = ctk.CTkLabel(
            tree_container,
            text="Carregando conexões...",
            font=("Segoe UI", 16),
            text_color="gray50",
        )
        # Será posicionado sobre a Treeview quando necessário

    # [NOVO] Método para mostrar/ocultar "Carregando..."
    def _show_loading_message(self, show: bool):
        def task():
            # Defensive: loading_label may not exist yet (deferred init). If so,
            # reschedule this action shortly so it runs after widgets are created.
            if not hasattr(self, "loading_label"):
                if show:
                    # Try again shortly; avoid tight loop by scheduling after 50ms
                    self.after(50, lambda: self._show_loading_message(show))
                return

            try:
                if show and not self.loading_label.winfo_ismapped():
                    # Coloca o label sobre a treeview
                    self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
                elif not show and self.loading_label.winfo_ismapped():
                    self.loading_label.place_forget()
            except Exception as e:
                # Log and swallow UI errors to avoid crashing the mainloop
                logging.warning(f"_show_loading_message UI error: {e}")

        self.after(0, task)  # Agenda para a thread principal da UI

    def _on_filter_change(self):
        # [ALTERADO] Filtro agora opera sobre o data_cache e reconstrói a view (mais simples)
        # A atualização diferencial só ocorre no refresh automático/manual
        filter_text = self.filter_var.get().lower()
        self._rebuild_tree_from_cache(filter_text)

    def _rebuild_tree_from_cache(self, filter_text: str = ""):
        """Limpa e reconstrói a Treeview usando self.data_cache, aplicando filtro."""
        # Limpa completamente a Treeview e os mapas
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.tree_item_map.clear()
        self.group_item_map.clear()

        # Reconstrói a partir do cache, aplicando o filtro
        current_group_name = None
        filtered_data = [
            conn
            for conn in self.data_cache
            if (
                not filter_text
                or filter_text in conn.nome.lower()
                or (conn.group_name and filter_text in conn.group_name.lower())
                or (conn.cliente and filter_text in conn.cliente.lower())
                or (conn.connected_user and filter_text in conn.connected_user.lower())
            )
        ]

        # Ordena (opcional, mas bom para consistência)
        filtered_data.sort(key=lambda c: (c.group_name or c.nome, c.nome))

        for conn_data in filtered_data:
            parent_iid = ""
            if conn_data.group_name:
                if conn_data.group_name != current_group_name:
                    current_group_name = conn_data.group_name
                    if current_group_name not in self.group_item_map:
                        # Cria o nó do grupo se não existir
                        group_iid = self.tree.insert(
                            "", "end", text=f"📁 {current_group_name}", open=True
                        )
                        self.group_item_map[current_group_name] = group_iid
                parent_iid = self.group_item_map.get(current_group_name, "")

            # Insere o item de conexão
            item_iid = self.tree.insert(
                parent_iid,
                "end",
                text=f" 	{conn_data.nome}",  # Texto principal na coluna #0
                values=conn_data.get_treeview_values(),
                tags=conn_data.tags,
            )
            self.tree_item_map[conn_data.con_codigo] = item_iid  # Atualiza o mapa

    def _populate_tree(self):
        """Busca novos dados e aplica atualizações diferenciais na Treeview."""
        if self._refresh_job:
            self.after_cancel(self._refresh_job)  # Cancela job anterior

        # 0. Limpeza periódica em background (não bloqueia a UI)
        def periodic_cleanup():
            """Executa limpezas de manutenção em background."""
            try:
                # ⚡ NOVO: Limpa conexões órfãs (usuários sem processo RDP ativo)
                self._cleanup_orphaned_connections()
                
                # Limpa proteções órfãs
                self._cleanup_orphaned_protections()
                
                # A cada ~6 refreshes (30s * 6 = ~3 min), limpa logs órfãos
                if not hasattr(self, '_cleanup_counter'):
                    self._cleanup_counter = 0
                self._cleanup_counter += 1
                
                if self._cleanup_counter >= 6:
                    logs_cleaned = self.db.logs.cleanup_orphaned_access_logs(hours_limit=24, simulate=False)
                    if logs_cleaned > 0:
                        logging.info(f"🧹 Manutenção periódica: {logs_cleaned} logs órfãos finalizados")
                    self._cleanup_counter = 0
            except Exception as e:
                logging.error(f"Erro durante limpeza periódica: {e}")
        
        # Executa limpeza em thread separada para não bloquear
        Thread(target=periodic_cleanup, daemon=True).start()

        # 1. Busca novos dados em BACKGROUND
        def fetch_data_task():
            """Task para buscar dados do banco em background."""
            try:
                raw_data = self.db.connections.select_all(self.user_session_name)
                return [ConnectionData(row) for row in raw_data]
            except Exception as e:
                logging.error(f"Erro ao buscar dados para refresh: {e}")
                return None

        def on_data_fetched(future: Future):
            """Callback quando dados são buscados (executa no main thread)."""
            try:
                new_data_list = future.result()
                if new_data_list is None:
                    # Erro na query, reagendar refresh
                    self._refresh_job = self.after(30000, self._populate_tree)
                    return
                
                # Processa dados na main thread (operação rápida)
                self._process_tree_update(new_data_list)
                
            except Exception as e:
                logging.error(f"Erro ao processar dados de refresh: {e}")
            finally:
                # Agenda próximo refresh
                self._refresh_job = self.after(30000, self._populate_tree)
        
        # Submit task e agendar callback no main thread
        future = self.thread_pool.submit_io_task(fetch_data_task)
        
        # Usar after() para garantir callback no main thread
        def schedule_callback():
            on_data_fetched(future)
        
        # Aguardar resultado e processar no main thread
        self.after(100, schedule_callback)
    
    def _process_tree_update(self, new_data_list: List[ConnectionData]):
        """
        Processa atualização diferencial da Treeview (executa no main thread).
        
        Args:
            new_data_list: Lista de ConnectionData atualizada
        """
        try:
            # Converte para objetos e cria mapa/set para lookup rápido
            new_data_map: Dict[int, ConnectionData] = {
                conn.con_codigo: conn for conn in new_data_list
            }
            new_ids: Set[int] = set(new_data_map.keys())

            # 2. Pega IDs atuais da Treeview
            current_ids: Set[int] = set(self.tree_item_map.keys())

            # 3. Identifica Adições, Deleções, Potenciais Atualizações
            ids_to_add = new_ids - current_ids
            ids_to_delete = current_ids - new_ids
            ids_to_check_update = current_ids.intersection(new_ids)

            # --- 4. Processa Deleções ---
            for con_codigo in ids_to_delete:
                item_iid = self.tree_item_map.pop(con_codigo, None)  # Remove do mapa
                if item_iid and self.tree.exists(item_iid):
                    self.tree.delete(item_iid)

            # --- 5. Processa Adições e Atualizações ---
            groups_to_recheck = set()  # Grupos que podem ter ficado vazios
            for con_codigo in ids_to_check_update:
                item_iid = self.tree_item_map[con_codigo]
                if not self.tree.exists(item_iid):
                    logging.warning(
                        f"Item ID {con_codigo} estava no mapa mas não na Treeview (iid={item_iid}). Será recriado."
                    )
                    ids_to_add.add(con_codigo)  # Marca para recriar
                    del self.tree_item_map[con_codigo]
                    continue

                new_conn_data = new_data_map[con_codigo]
                # Pega dados atuais da Treeview para comparação
                # Precisamos reconstruir um objeto ConnectionData a partir dos valores da Treeview
                # NOTA: Isso é menos eficiente. Se o desempenho for crítico, armazene
                # os objetos ConnectionData no self.tree_item_map em vez do iid.
                try:
                    current_values = self.tree.item(item_iid, "values")
                    # Recria uma tupla no formato da linha do banco para o construtor
                    # Ordem: cod, ip, nome, user, pwd, group?, conn_user?, ?, extra?, partic?,
                    # cliente?, tipo?
                    current_parent_iid = self.tree.parent(item_iid)
                    current_group_name = (
                        self.tree.item(current_parent_iid, "text").replace("📁 ", "")
                        if current_parent_iid
                        else None
                    )

                    # Simula a linha do DB (índices baseados na ordem de ConnectionData)
                    simulated_row = (
                        int(current_values[0]),
                        current_values[1],
                        current_values[4],
                        current_values[2],
                        current_values[3],
                        current_group_name,
                        current_values[7],
                        None,
                        current_values[5],
                        current_values[6],
                        current_values[9],
                        "RDP",  # Tipo não está nos values, assume RDP ou busca no cache antigo? Melhor buscar no cache
                    )
                    # Busca tipo no cache antigo se possível
                    old_conn = next(
                        (c for c in self.data_cache if c.con_codigo == con_codigo), None
                    )
                    if old_conn:
                        simulated_row = simulated_row[:-1] + (old_conn.con_tipo,)

                    current_conn_data = ConnectionData(simulated_row)
                except Exception as e:
                    logging.error(
                        f"Erro ao recriar ConnectionData para ID {con_codigo} a partir da Treeview: {e}. Reconstruindo item."
                    )
                    ids_to_add.add(con_codigo)  # Marca para recriar
                    if item_iid and self.tree.exists(item_iid):
                        self.tree.delete(item_iid)
                    del self.tree_item_map[con_codigo]
                    continue

                # Compara (usando o __eq__ que definimos)
                if current_conn_data != new_conn_data:
                    # Atualiza os campos na Treeview
                    self.tree.item(
                        item_iid,
                        text=f" 	{new_conn_data.nome}",
                        values=new_conn_data.get_treeview_values(),
                        tags=new_conn_data.tags,
                    )

                    # Verifica se o grupo mudou
                    new_parent_iid = (
                        self.group_item_map.get(new_conn_data.group_name, "")
                        if new_conn_data.group_name
                        else ""
                    )
                    if current_parent_iid != new_parent_iid:
                        # Cria novo grupo se necessário
                        if (
                            new_conn_data.group_name
                            and new_conn_data.group_name not in self.group_item_map
                        ):
                            new_parent_iid = self.tree.insert(
                                "", "end", text=f"📁 {new_conn_data.group_name}", open=True
                            )
                            self.group_item_map[new_conn_data.group_name] = new_parent_iid
                        self.tree.move(item_iid, new_parent_iid, "end")
                        if current_parent_iid:
                            groups_to_recheck.add(
                                current_parent_iid
                            )  # Marca grupo antigo para ver se ficou vazio

            # Adiciona novos itens (os de ids_to_add)
            for con_codigo in ids_to_add:
                conn_data = new_data_map[con_codigo]
                parent_iid = ""
                if conn_data.group_name:
                    if conn_data.group_name not in self.group_item_map:
                        # Cria o nó do grupo se não existir
                        group_iid = self.tree.insert(
                            "", "end", text=f"📁 {conn_data.group_name}", open=True
                        )
                        self.group_item_map[conn_data.group_name] = group_iid
                    parent_iid = self.group_item_map.get(conn_data.group_name, "")

                item_iid = self.tree.insert(
                    parent_iid,
                    "end",
                    text=f" 	{conn_data.nome}",
                    values=conn_data.get_treeview_values(),
                    tags=conn_data.tags,
                )
                self.tree_item_map[conn_data.con_codigo] = item_iid  # Adiciona ao mapa

            # --- 6. Limpa Grupos Vazios ---
            groups_to_delete = set()
            # Adiciona grupos que podem ter ficado vazios por causa de movimentação
            for group_iid in groups_to_recheck:
                if (
                    group_iid
                    and self.tree.exists(group_iid)
                    and not self.tree.get_children(group_iid)
                ):
                    groups_to_delete.add(group_iid)
            # Adiciona grupos que podem ter ficado vazios por causa de deleção direta
            for group_name, group_iid in list(
                self.group_item_map.items()
            ):  # Usa list() para poder modificar o dict
                if (
                    group_iid
                    and self.tree.exists(group_iid)
                    and not self.tree.get_children(group_iid)
                ):
                    groups_to_delete.add(group_iid)

            for group_iid in groups_to_delete:
                group_name = next(
                    (name for name, iid in self.group_item_map.items() if iid == group_iid), None
                )
                if self.tree.exists(group_iid):
                    self.tree.delete(group_iid)
                if group_name in self.group_item_map:
                    del self.group_item_map[group_name]

            # --- 7. Finalização ---
            self.data_cache = new_data_list  # Atualiza o cache principal

        except Exception as e:
            logging.error(f"Erro inesperado durante atualização diferencial: {e}", exc_info=True)
            # Fallback: Reconstrução total em caso de erro grave
            messagebox.showerror(
                "Erro Interno",
                f"Ocorreu um erro ao atualizar a lista:\n{e}\n\nA lista será recarregada completamente.",
            )
            self._rebuild_tree_from_cache(
                self.filter_var.get().lower()
            )  # Tenta reconstruir com filtro atual
        finally:
            self._show_loading_message(False)  # Esconde "Carregando..."

    # --- [NOVO] Métodos de carregamento inicial movidos para background ---
    def _initial_load_in_background(self):
        """Busca os dados iniciais e agenda a construção da Treeview."""
        try:
            # 1. Limpa conexões fantasmas primeiro
            self.db.logs.cleanup_ghost_connections()

            # 2. Limpa logs de acesso órfãos (nova funcionalidade)
            logs_cleaned = self.db.logs.cleanup_orphaned_access_logs(hours_limit=24, simulate=False)
            if logs_cleaned > 0:
                logging.info(f"🧹 Limpeza inicial: {logs_cleaned} logs órfãos finalizados")

            # 3. Limpa proteções órfãs
            self._cleanup_orphaned_protections()

            # 4. Busca os dados
            initial_raw_data = self.db.connections.select_all(self.user_session_name)
            initial_data = [ConnectionData(row) for row in initial_raw_data]
            # 5. Agenda a construção da UI na thread principal
            self.after(0, self._build_initial_tree, initial_data)
        except DatabaseError as e:
            logging.error(f"Falha CRÍTICA no carregamento inicial: {e}", exc_info=True)
            self.after(
                0,
                messagebox.showerror,
                "Erro de Conexão Inicial",
                f"Não foi possível carregar os dados iniciais:\n{e}",
            )
            self.after(0, self._show_loading_message, False)  # Esconde loading
        except Exception as e:
            logging.error(f"Erro INESPERADO no carregamento inicial: {e}", exc_info=True)
            self.after(0, messagebox.showerror, "Erro Inesperado", f"Ocorreu um erro:\n{e}")
            self.after(0, self._show_loading_message, False)

    def _build_initial_tree(self, initial_data: List[ConnectionData]):
        """Constrói a Treeview pela primeira vez com os dados carregados."""
        self.data_cache = initial_data
        self._rebuild_tree_from_cache()  # Usa a função de reconstrução (sem filtro)
        self._show_loading_message(False)  # Esconde "Carregando..."
        # Inicia o ciclo de refresh automático APÓS a carga inicial
        self._refresh_job = self.after(60000, self._populate_tree)

    # --- FIM Background Load ---

    def _get_selected_item_data(self) -> Optional[Dict[str, Any]]:
        """Obtém os dados do item selecionado na Treeview."""
        selection = self.tree.selection()
        if not selection:
            return None
        item = self.tree.item(selection[0])
        if not item["values"] or len(item["values"]) != len(self.tree["columns"]):
            logging.warning(f"Item com valores incompletos ou malformados: {item.get('values')}")
            return None
        return dict(zip(self.tree["columns"], item["values"]))

    def _on_item_double_click(self, event):
        """Lida com o duplo clique."""
        column = self.tree.identify_column(event.x)
        data = self._get_selected_item_data()
        if not data:
            return

        # 🔒 VERIFICAÇÃO PRIORITÁRIA DE PROTEÇÃO DE SESSÃO
        con_codigo = data.get("db_id")
        session_protection_manager = get_current_session_protection_manager()

        if session_protection_manager and session_protection_manager.is_session_protected(
            con_codigo
        ):
            # Sessão protegida - vai diretamente para validação de senha
            logging.info(f"[PROTECTION_ACCESS] Sessão {con_codigo} protegida, solicitando senha")
            protection_info = session_protection_manager.get_session_protection_info(con_codigo)
            protected_by = (
                protection_info.get("protected_by", "Unknown") if protection_info else "Unknown"
            )

            # Mostra diálogo de validação de senha
            validation_dialog = ValidateSessionPasswordDialog(
                parent=self,
                connection_data=data,
                requesting_user=self.user_session_name,
                protected_by=protected_by,
            )

            # Aguarda resultado da validação
            validation_dialog.wait_window()
            result = validation_dialog.get_result()

            if not result or not result.get("validated"):
                # Acesso negado - não prossegue
                logging.warning(
                    f"🔒 Acesso negado para {self.user_session_name} ao servidor protegido {data.get('title')}"
                )
                messagebox.showwarning(
                    "Acesso Negado",
                    f"Não foi possível acessar o servidor '{data.get('title')}'.\n\n"
                    "A sessão está protegida e você não forneceu a senha correta.",
                )
                return

            # Acesso autorizado - prossegue com a conexão
            logging.info(
                f"🔓 Acesso autorizado para {self.user_session_name} ao servidor protegido {data.get('title')}"
            )
            # Continua para executar a conexão normalmente

        elif data.get("username") and column != "#2":
            # Conexão em uso mas SEM proteção - oferece opções colaborativas
            choice = self._show_connection_in_use_dialog(data)
            if choice == "cancel":
                return
            elif choice == "collaborative":
                self._request_collaborative_access(data)
                return
            # Se choice == "force", continua normalmente

        if column == "#2" and data.get("wiki_link"):
            particularidades = parse_particularities(data["wiki_link"])

            if not particularidades:
                messagebox.showinfo("Informação", "Nenhum link de wiki disponível.")
                return

            if len(particularidades) == 1:
                try:
                    webbrowser.open_new(particularidades[0][1])
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível abrir o link:\n{e}")
            else:
                dialog = ClientSelectorDialog(self, particularidades, f"Clientes - {data['title']}")
                self.wait_window(dialog)
                selected_link = dialog.get_selected_link()
                if selected_link:
                    try:
                        webbrowser.open_new(selected_link)
                    except Exception as e:
                        messagebox.showerror("Erro", f"Não foi possível abrir o link:\n{e}")
        else:
            # Verifica o tipo de conexão (NOVO)
            # con_tipo = "RDP"  # Valor padrão - TODO: Implementar lógica para outros tipos
            # Busca o row original no cache para pegar o 'con_tipo'
            # try:
            #     row_original = next(
            #         r for r in self.data_cache if r.con_codigo == int(data["db_id"])
            #     )
            #     # con_tipo = row_original.con_tipo  # TODO: Implementar lógica para outros tipos
            # except (StopIteration, IndexError):
            #     logging.warning(
            #         f"Não foi possível encontrar o tipo da conexão {data['db_id']} no cache. Usando RDP padrão."
            #     )

            # --- AQUI VOCÊ ADICIONARIA A LÓGICA PARA OUTROS TIPOS ---
            # if con_tipo == 'SSH':
            #     Thread(target=self._connect_ssh, args=(data,), daemon=True).start()
            # elif con_tipo == 'VNC':
            #     Thread(target=self._connect_vnc, args=(data,), daemon=True).start()
            # else: # RDP ou tipo desconhecido
            #     Thread(target=self._connect_rdp, args=(data,), daemon=True).start()

            # Por enquanto, só chama RDP
            Thread(target=self._connect_rdp, args=(data,), daemon=True).start()

    def _show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.context_menu.post(event.x_root, event.y_root)

    def _update_username_cell(self, item_id: str, new_username: str):
        """Atualiza a célula do nome de usuário na UI de forma segura."""

        def update_task():
            try:
                if self.tree.exists(item_id):
                    current_values = list(self.tree.item(item_id, "values"))
                    if len(current_values) > 7:
                        current_values[7] = new_username
                        self.tree.item(item_id, values=tuple(current_values))
            except Exception as e:
                logging.warning(f"Erro ao atualizar célula da UI: {e}")

        self.after(0, update_task)

    def _cleanup_ui_after_disconnect(self, con_codigo: int, username: str):
        """
        Limpa a UI após detecção de desconexão automática do processo RDP.
        
        Args:
            con_codigo: Código da conexão
            username: Nome do usuário desconectado
        """
        try:
            # Procura o item na árvore
            item_id = self.tree_item_map.get(con_codigo)
            
            if item_id and self.tree.exists(item_id):
                current_values = self.tree.item(item_id, "values")
                if len(current_values) > 7:
                    current_users = current_values[7]
                    
                    if current_users:
                        # Remove o usuário específico da string
                        users_list = [u for u in current_users.split("|") if u != username]
                        new_users = "|".join(users_list)
                        
                        # Atualiza a célula
                        self._update_username_cell(item_id, new_users)
                        
                        logging.info(f"[UI_CLEANUP] Usuário {username} removido da UI para conexão {con_codigo}")
            
            # Se não conseguiu encontrar/atualizar especificamente, força refresh completo
            else:
                logging.warning(f"[UI_CLEANUP] Item {con_codigo} não encontrado, forçando refresh")
                self._populate_tree()
                
        except Exception as e:
            logging.error(f"[UI_CLEANUP] Erro ao limpar UI após desconexão: {e}")
            # Em caso de erro, força refresh completo
            self._populate_tree()

    def _execute_connection(self, data: Dict[str, Any], connection_func, *args, recording_session_id=None, recording_connection_info=None):
        """
        Lida com a lógica de log, heartbeat e atualização da UI
        para qualquer tipo de conexão (esta versão é apenas para RDP/Gerenciada).
        
        OTIMIZAÇÃO: UI primeiro, validações depois (threads assíncronas)
        
        Args:
            data: Dados da conexão
            connection_func: Função que executa a conexão
            *args: Argumentos para connection_func
            recording_session_id: ID da sessão de gravação (opcional)
            recording_connection_info: Informações para gravação (opcional)
        """
        selection = self.tree.selection()
        if not selection:
            return
        selected_item_id = selection[0]
        con_codigo = int(data["db_id"])
        username = self.user_session_name

        if con_codigo in self.active_heartbeats:
            logging.warning(
                f"Tentativa de reconectar a {con_codigo} enquanto já há um heartbeat ativo."
            )
            return

        # ⚡ OTIMIZAÇÃO 1: ADICIONA USUÁRIO NA UI IMEDIATAMENTE (1-5ms)
        # Feedback visual instantâneo para o usuário
        logging.info(f"[PERF] Adicionando usuário {username} à UI IMEDIATAMENTE")
        try:
            current_users = self.tree.item(selected_item_id, "values")[7]
            new_users = username if not current_users else f"{current_users}|{username}"
            self._update_username_cell(selected_item_id, new_users)
            logging.info(f"[PERF] ✓ Usuário adicionado à UI em <5ms")
        except (IndexError, Exception) as e:
            logging.error(f"[PERF] Erro ao adicionar usuário à UI: {e}")
            return

        # ⚡ OTIMIZAÇÃO 2: OPERAÇÕES DE BANCO EM THREAD ASSÍNCRONA
        # Não bloqueia a UI nem o início do RDP
        db_success = {'connection_log': False, 'access_log': None}
        
        def async_db_operations():
            """Executa operações de banco em thread separada."""
            try:
                # Registro da conexão
                logging.info(f"[PERF] Iniciando insert_connection_log em thread assíncrona")
                db_success['connection_log'] = self.db.logs.insert_connection_log(
                    con_codigo, self.user_session_name, self.user_ip, self.computer_name, self.os_user
                )
                
                if not db_success['connection_log']:
                    logging.error(f"[PERF] Falha ao registrar conexão no banco")
                    # Remove da UI se falhou
                    def rollback_ui():
                        try:
                            current_users = self.tree.item(selected_item_id, "values")[7]
                            if current_users:
                                users_list = [u for u in current_users.split("|") if u != username]
                                new_users = "|".join(users_list)
                                self._update_username_cell(selected_item_id, new_users)
                        except Exception as e:
                            logging.error(f"[PERF] Erro ao reverter UI: {e}")
                    self.after(0, rollback_ui)
                    return
                
                # Log de acesso detalhado
                con_tipo = "RDP"
                con_nome = data.get("title", "N/A")
                try:
                    row_original = next(r for r in self.data_cache if r.con_codigo == con_codigo)
                    con_tipo = row_original.con_tipo
                    con_nome = row_original.nome
                except (StopIteration, IndexError):
                    pass
                
                user_machine_info = f"{self.user_session_name}@{self.computer_name}"
                db_success['access_log'] = self.db.logs.log_access_start(
                    user_machine_info, con_codigo, con_nome, con_tipo
                )
                logging.info(f"[PERF] ✓ Operações de banco concluídas (log_id={db_success['access_log']})")
                
            except Exception as e:
                logging.error(f"[PERF] Erro em operações de banco: {e}")
        
        # Inicia thread de banco (não bloqueia)
        Thread(target=async_db_operations, daemon=True, name=f"DB-{con_codigo}").start()

        stop_event = Event()
        self.active_heartbeats[con_codigo] = stop_event

        def heartbeat_task(con_id, user, stop_flag: Event):
            """Thread que envia heartbeats a cada 60 segundos com validação de processo RDP."""
            
            logging.info(f"[HB {con_id}] Heartbeat iniciado para {user}.")
            
            # Obtém dados da conexão para validação do processo
            connection_data = data  # Dados já disponíveis no escopo
            server_ip = connection_data.get("ip", "").split(":")[0]  # Remove porta se houver
            rdp_user = connection_data.get("user", "")
            connection_title = connection_data.get("title", "")
            
            # LOG DETALHADO: Mostra todos os dados da conexão
            logging.info(f"[HB {con_id}] DADOS DA CONEXÃO:")
            logging.info(f"[HB {con_id}]   - IP original: {connection_data.get('ip', 'N/A')}")
            logging.info(f"[HB {con_id}]   - IP processado: {server_ip}")
            logging.info(f"[HB {con_id}]   - Usuário RDP: {rdp_user}")
            logging.info(f"[HB {con_id}]   - Título: {connection_title}")
            logging.info(f"[HB {con_id}]   - DB_ID: {connection_data.get('db_id', 'N/A')}")
            
            missed_heartbeats = 0
            max_missed_heartbeats = 3  # AUMENTADO: Tolerância para evitar falsos positivos (6s total)
            heartbeat_interval = 2  # Intervalo muito curto para detecção rápida
            
            while not stop_flag.wait(heartbeat_interval):
                try:
                    # 1. Verifica se o processo RDP ainda está ativo
                    logging.debug(f"[HB {con_id}] Chamando is_rdp_connection_active('{server_ip}', '{rdp_user}', '{connection_title}')")
                    rdp_active = is_rdp_connection_active(server_ip, rdp_user, connection_title)
                    
                    if not rdp_active:
                        missed_heartbeats += 1
                        logging.warning(
                            f"[HB {con_id}] Processo RDP não encontrado para {server_ip} "
                            f"(tentativa {missed_heartbeats}/{max_missed_heartbeats})"
                        )
                        
                        if missed_heartbeats >= max_missed_heartbeats:
                            logging.warning(
                                f"[HB {con_id}] Processo RDP definitivamente inativo para {server_ip}. "
                                f"Limpando sessão automaticamente."
                            )
                            
                            # Para o heartbeat e limpa a sessão
                            stop_flag.set()
                            
                            # Agenda limpeza na thread principal
                            def cleanup_disconnected_session():
                                try:
                                    logging.info(f"[CLEANUP] Limpando sessão desconectada {con_id} do usuário {user}")
                                    
                                    # Remove do banco de dados
                                    if self.db.logs.delete_connection_log(con_id, user):
                                        logging.info(f"[CLEANUP] Sessão {con_id} removida do banco com sucesso")
                                        
                                        # Atualiza a UI
                                        self._cleanup_ui_after_disconnect(con_id, user)
                                        
                                        # Remove do active_heartbeats
                                        if con_id in self.active_heartbeats:
                                            del self.active_heartbeats[con_id]
                                            
                                    else:
                                        logging.error(f"[CLEANUP] Falha ao remover sessão {con_id} do banco")
                                        
                                except Exception as e:
                                    logging.error(f"[CLEANUP] Erro durante limpeza da sessão {con_id}: {e}")
                            
                            # Executa limpeza na thread principal da UI
                            self.after(0, cleanup_disconnected_session)
                            break
                    else:
                        # Processo RDP está ativo, reset contador
                        if missed_heartbeats > 0:
                            logging.info(f"[HB {con_id}] Processo RDP redetectado para {server_ip}")
                            missed_heartbeats = 0
                    
                    # 2. Envia heartbeat normal apenas se processo está ativo
                    if rdp_active:
                        heartbeat_sent = self.db.logs.update_heartbeat(con_id, user)
                        
                        # CORREÇÃO: Se update_heartbeat retorna False, o registro foi removido do banco
                        # (desconexão forçada ou limpeza automática). Parar o heartbeat.
                        if not heartbeat_sent:
                            logging.warning(
                                f"[HB {con_id}] Registro do usuário {user} não existe mais no banco. "
                                "Parando heartbeat e limpando UI."
                            )
                            stop_flag.set()
                            
                            # Agenda limpeza da UI na thread principal
                            def cleanup_removed_user():
                                try:
                                    logging.info(f"[CLEANUP] Limpando UI para usuário removido {user} da conexão {con_id}")
                                    self._cleanup_ui_after_disconnect(con_id, user)
                                    
                                    # Remove do active_heartbeats
                                    if con_id in self.active_heartbeats:
                                        del self.active_heartbeats[con_id]
                                        
                                except Exception as e:
                                    logging.error(f"[CLEANUP] Erro ao limpar UI após detectar remoção: {e}")
                            
                            self.after(0, cleanup_removed_user)
                            break
                    
                except Exception as e:
                    logging.error(f"[HB {con_id}] Erro durante heartbeat: {e}")
                    
            logging.info(f"[HB {con_id}] Heartbeat parado para {user}.")

        hb_thread = Thread(
            target=heartbeat_task,
            args=(con_codigo, self.user_session_name, stop_event),
            daemon=True,
            name=f"Heartbeat-{con_codigo}"
        )
        hb_thread.start()

        # OTIMIZAÇÃO: Não precisa mais de try/except complexo
        # As operações de banco já estão em thread assíncrona
        connection_executed = False
        
        try:
            # ⚡ Executa a conexão (rdp.exe com Popen - NÃO bloqueante no início)
            # Esta função agora retorna rapidamente após iniciar o processo
            connection_executed = True
            connection_func(*args)
            
            # ⚡ VALIDAÇÃO PÓS-CONEXÃO: Verifica se processo RDP foi realmente criado
            # Aguarda até 5.5 segundos para processo aparecer (10 tentativas × 0.5s)
            logging.info(f"[VALIDATION] Validando criação do processo RDP para {data.get('ip', 'N/A')}")
            
            server_ip = data.get("ip", "").split(":")[0]
            rdp_user = data.get("user", "")
            connection_title = data.get("title", "")
            
            max_validation_attempts = 11  # 11 tentativas × 0.5s = 5.5 segundos
            validation_interval = 0.5
            process_found = False
            
            for attempt in range(max_validation_attempts):
                if is_rdp_connection_active(server_ip, rdp_user, connection_title):
                    process_found = True
                    logging.info(
                        f"[VALIDATION] ✓ Processo RDP confirmado em {attempt * validation_interval:.1f}s "
                        f"para {server_ip}"
                    )
                    
                    # ⚡ GRAVAÇÃO: Inicia APENAS após confirmar que processo RDP existe
                    if recording_session_id and recording_connection_info and self.recording_manager:
                        def start_recording_async():
                            try:
                                if self.recording_manager.start_session_recording(
                                    recording_session_id, recording_connection_info
                                ):
                                    logging.info(
                                        f"[RECORDING] ✓ Gravação iniciada (session_id={recording_session_id}) "
                                        f"para {data.get('ip')} após validação do processo"
                                    )
                                else:
                                    logging.warning(
                                        f"[RECORDING] ❌ Falha ao iniciar gravação para {data.get('ip')}"
                                    )
                            except Exception as e:
                                logging.error(f"[RECORDING] Erro ao iniciar gravação: {e}")
                        
                        # Inicia gravação em thread separada (não bloqueia)
                        Thread(target=start_recording_async, daemon=True, name="StartRecording").start()
                    
                    break
                
                if attempt < max_validation_attempts - 1:  # Não aguarda na última tentativa
                    import time
                    time.sleep(validation_interval)
            
            # Se processo não foi encontrado, REMOVE da UI e limpa
            if not process_found:
                logging.error(
                    f"[VALIDATION] ❌ PROCESSO RDP NÃO CRIADO após {max_validation_attempts * validation_interval}s! "
                    f"Removendo {username} da UI (con_codigo={con_codigo})"
                )
                
                # Para heartbeat imediatamente
                stop_event.set()
                if con_codigo in self.active_heartbeats:
                    del self.active_heartbeats[con_codigo]
                
                # Remove da UI
                def rollback_ui_no_process():
                    try:
                        current_users = self.tree.item(selected_item_id, "values")[7]
                        if current_users:
                            users_list = [u for u in current_users.split("|") if u != username]
                            new_users = "|".join(users_list)
                            self._update_username_cell(selected_item_id, new_users)
                            logging.info(f"[VALIDATION] ✓ Usuário {username} removido da UI")
                    except Exception as e:
                        logging.error(f"[VALIDATION] Erro ao remover usuário da UI: {e}")
                
                self.after(0, rollback_ui_no_process)
                
                # Remove do banco
                if db_success.get('connection_log'):
                    def remove_from_db():
                        try:
                            self.db.logs.delete_connection_log(con_codigo, username)
                            logging.info(f"[VALIDATION] ✓ Registro removido do banco")
                        except Exception as e:
                            logging.error(f"[VALIDATION] Erro ao remover do banco: {e}")
                    Thread(target=remove_from_db, daemon=True).start()
                
                return  # Não continua se processo não foi criado

        except Exception as e:
            # CORREÇÃO: Captura exceções durante a conexão
            logging.error(f"[PERF] Erro durante execução da conexão {con_codigo}: {e}", exc_info=True)
            # Finaliza log mesmo em caso de erro (em thread para não bloquear)
            def finalize_log_on_error():
                if db_success.get('access_log'):
                    try:
                        self.db.logs.log_access_end(db_success['access_log'])
                        logging.info(f"[PERF] Log de acesso {db_success['access_log']} finalizado após erro")
                    except Exception as log_error:
                        logging.error(f"[PERF] Erro ao finalizar log após exceção: {log_error}")
            Thread(target=finalize_log_on_error, daemon=True).start()
            raise  # Re-raise a exceção para não suprimir erros
            
        finally:
            # Esta seção 'finally' é executada assim que 'connection_func' termina
            logging.info(f"[DISCONNECT] === INICIANDO LIMPEZA DA CONEXÃO {con_codigo} ===")
            logging.info(f"[DISCONNECT] Conexão {con_codigo} fechada pelo usuário {username}")

            # OTIMIZAÇÃO: Finaliza log em thread assíncrona (não bloqueia)
            def finalize_access_log():
                if db_success.get('access_log') and connection_executed:
                    try:
                        if self.db.logs.log_access_end(db_success['access_log']):
                            logging.info(f"[DISCONNECT] ✅ Log de acesso {db_success['access_log']} finalizado")
                        else:
                            logging.warning(f"[DISCONNECT] ⚠️ Log {db_success['access_log']} não encontrado")
                    except Exception as e:
                        logging.error(f"[DISCONNECT] ❌ Erro ao finalizar log: {e}")
            Thread(target=finalize_access_log, daemon=True).start()

            # CORREÇÃO: Para o heartbeat ANTES de remover do banco para evitar race condition
            # Se não parar primeiro, o heartbeat pode tentar atualizar enquanto estamos deletando
            logging.info(f"[DISCONNECT] Parando heartbeat da conexão {con_codigo}")
            stop_event.set()
            
            # Aguarda um breve momento para garantir que o heartbeat parou
            import time
            time.sleep(0.05)  # Delay mínimo para garantir parada do heartbeat
            
            if con_codigo in self.active_heartbeats:
                del self.active_heartbeats[con_codigo]
                logging.info(f"[DISCONNECT] ✓ Heartbeat removido de active_heartbeats")

            # Deleta o log de conexão ativa usando usuário WATS
            logging.info(f"[DISCONNECT] Removendo registro do banco para usuário {self.user_session_name}")
            db_removed = False
            try:
                db_removed = self.db.logs.delete_connection_log(con_codigo, self.user_session_name)
                if db_removed:
                    logging.info(f"[DISCONNECT] ✓ Registro removido com sucesso do banco")
                else:
                    logging.warning(f"[DISCONNECT] ⚠ Registro não encontrado no banco (pode já ter sido removido pelo heartbeat)")
            except Exception as e:
                logging.error(f"[DISCONNECT] ❌ Erro ao remover registro do banco: {e}")
            
            # CORREÇÃO: SEMPRE limpa a UI, independente do resultado do banco
            # Isso garante que mesmo se o heartbeat já limpou o banco, a UI será atualizada
            logging.info(f"[DISCONNECT] Limpando UI para usuário {username}")
            try:
                def cleanup_ui_task():
                    try:
                        if self.tree.exists(selected_item_id):
                            current_users = self.tree.item(selected_item_id, "values")[7]
                            if current_users:
                                users_list = [u for u in current_users.split("|") if u != username]
                                new_users = "|".join(users_list)
                                
                                # Atualiza a célula diretamente (sem chamar _update_username_cell que usa self.after)
                                current_values = list(self.tree.item(selected_item_id, "values"))
                                if len(current_values) > 7:
                                    current_values[7] = new_users
                                    self.tree.item(selected_item_id, values=tuple(current_values))
                                    logging.info(f"[DISCONNECT] ✓ UI atualizada, usuário {username} removido da lista")
                        else:
                            logging.warning(f"[DISCONNECT] ⚠ Item {selected_item_id} não existe mais na árvore")
                    except (IndexError, Exception) as e:
                        logging.error(f"[DISCONNECT] ❌ Erro ao limpar UI: {e}")
                        # Em caso de erro, força refresh completo
                        self._populate_tree()
                
                # Executa na thread principal da UI
                self.after(0, cleanup_ui_task)
                
            except Exception as e:
                logging.error(f"[DISCONNECT] ❌ Erro crítico ao agendar limpeza da UI: {e}")
                # Última tentativa: força refresh completo
                self.after(0, self._populate_tree)
            
            logging.info(f"[DISCONNECT] === LIMPEZA DA CONEXÃO {con_codigo} CONCLUÍDA ===")

    def _connect_rdp(self, data: Dict[str, Any]):
        """Conecta usando o executável rdp.exe customizado."""

        # con_codigo = data.get("db_id")  # TODO: Usar quando necessário

        # DEBUG: Verificar se logging está funcionando
        print(f"[DEBUG CONSOLE] Iniciando conexão RDP para {data.get('title')}")
        logging.info(f"[DEBUG LOGGING] Iniciando conexão RDP para {data.get('title')}")

        # DEBUG: Verificar onde estão os logs
        from .config import LOG_FILE, USER_DATA_DIR

        print(f"[DEBUG] USER_DATA_DIR: {USER_DATA_DIR}")
        print(f"[DEBUG] LOG_FILE: {LOG_FILE}")
        print(f"[DEBUG] Log file exists: {os.path.exists(LOG_FILE)}")

        # Verificar handlers do logger
        root_logger = logging.getLogger()
        print(f"[DEBUG] Logger level: {root_logger.level}")
        print(f"[DEBUG] Logger handlers: {len(root_logger.handlers)}")
        for i, handler in enumerate(root_logger.handlers):
            print(f"[DEBUG] Handler {i}: {type(handler).__name__}")

        rdp_exe_path = os.path.join(ASSETS_DIR, "rdp.exe")

        # Debug detalhado para localizar o rdp.exe
        logging.info(f"[RDP] BASE_DIR: {BASE_DIR}")
        logging.info(f"[RDP] ASSETS_DIR: {ASSETS_DIR}")
        logging.info(f"[RDP] Procurando rdp.exe em: {rdp_exe_path}")
        logging.info(f"[RDP] sys.frozen: {getattr(sys, 'frozen', False)}")
        logging.info(f"[RDP] sys.executable: {sys.executable}")

        if not os.path.exists(rdp_exe_path):
            # Tenta localizar o rdp.exe em outros locais possíveis
            possible_paths = [
                os.path.join(os.path.dirname(sys.executable), "assets", "rdp.exe"),
                os.path.join(os.path.dirname(sys.executable), "_internal", "assets", "rdp.exe"),
                os.path.join(os.getcwd(), "assets", "rdp.exe"),
                os.path.join(BASE_DIR, "..", "assets", "rdp.exe"),
            ]

            found_path = None
            for path in possible_paths:
                logging.info(f"[RDP] Tentando: {path}")
                if os.path.exists(path):
                    found_path = path
                    logging.info(f"[RDP] Encontrado rdp.exe em: {path}")
                    break

            if found_path:
                rdp_exe_path = found_path
            else:
                logging.error("[RDP] rdp.exe não encontrado em nenhum local")
                messagebox.showerror(
                    "Erro",
                    f"Executável não encontrado:\n{rdp_exe_path}\n\nCaminhos testados:\n"
                    + "\n".join(possible_paths),
                )
                return

        # ⚡ OTIMIZAÇÃO: Prepara gravação mas NÃO inicia ainda
        # Gravação só será iniciada APÓS validar que processo RDP foi criado
        session_id = None
        connection_info = None
        if (
            self.recording_manager
            and self.settings.RECORDING_ENABLED
            and self.settings.RECORDING_AUTO_START
        ):
            import time

            session_id = f"rdp_{data.get('db_id', 'unknown')}_{int(time.time())}"
            connection_info = {
                "con_codigo": data.get("db_id"),
                "ip": data.get("ip"),
                "name": data.get("title"),
                "user": data.get("user"),
                "connection_type": "RDP",
                # NOVO: Informações do usuário WATS para auditoria
                "wats_user": self.user_session_name,
                "wats_user_machine": self.computer_name,
                "wats_user_ip": self.user_ip,
                "session_timestamp": int(time.time()),
            }
            logging.info(f"[RECORDING] Gravação preparada (session_id={session_id}) - aguardando validação do processo RDP")

        # CORREÇÃO: Captura a seleção atual e informações necessárias ANTES de chamar _execute_connection
        # Isso permite que a função task() tenha acesso a essas variáveis
        selection = self.tree.selection()
        selected_item_id = selection[0] if selection else None
        con_codigo = int(data.get("db_id"))
        username = self.user_session_name

        def task():
            """⚡ OTIMIZADO: Inicia RDP com Popen (não bloqueante) e monitora em thread separada."""
            import time
            
            # Carrega configuração do monitor e RDP
            app_config = get_app_config()
            monitor = app_config.get("monitor", 1)
            rdp_config = app_config.get("rdp", {})

            # Constrói comando base do RDP
            cmd = [
                rdp_exe_path,
                f"/v:{data['ip']}",
                f"/u:{data['user']}",
                f"/p:{data['pwd']}",
                f"/title:{data['title']}",
                "/noprinters",
                "/nosound",
                "/nowallpaper",
                "/drives:fixed,-c:",
                f"/mon:{monitor}",
            ]

            # Adiciona parâmetros de janela baseado na configuração
            if rdp_config.get("fullscreen", False):
                cmd.append("/f")
            elif rdp_config.get("maximize_window", False):
                cmd.append("/max")
            else:
                # Para janela normal, usa dimensões configuradas
                width = rdp_config.get("default_width", 1024)
                height = rdp_config.get("default_height", 768)
                cmd.extend([f"/w:{width}", f"/h:{height}"])
            icon_path = os.path.join(ASSETS_DIR, "ats.ico")
            if os.path.exists(icon_path):
                cmd.append(f"/icon:{icon_path}")
            
            try:
                # Don't log the raw password. Create a masked copy for logging.
                masked_cmd = [c if not c.startswith("/p:") else "/p:***" for c in cmd]
                logging.info(f"[PERF] Executando RDP: {' '.join(masked_cmd)}")

                # ⚡ OTIMIZAÇÃO: subprocess.Popen ao invés de subprocess.run
                # Retorna IMEDIATAMENTE sem bloquear
                start_time = time.time()
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                logging.info(f"[PERF] ✓ Processo RDP iniciado em {(time.time() - start_time)*1000:.1f}ms (PID: {proc.pid})")
                
                # Thread para monitorar processo RDP e registrar quando detectado
                def monitor_rdp_process():
                    """Monitora processo RDP até ser detectado ou falhar."""
                    try:
                        # Aguarda processo estabilizar
                        time.sleep(0.3)
                        
                        # Tenta detectar processo RDP
                        rdp_monitor = get_rdp_monitor()
                        max_attempts = 8
                        rdp_detected = False
                        
                        for attempt in range(max_attempts):
                            # Verifica se processo ainda está rodando
                            if proc.poll() is not None:
                                # Processo terminou prematuramente
                                stdout, stderr = proc.communicate()
                                logging.error(
                                    f"[PERF] ❌ Processo RDP terminou prematuramente (exit {proc.returncode})\n"
                                    f"stdout: {stdout}\nstderr: {stderr}"
                                )
                                # Remove da UI
                                def remove_from_ui():
                                    try:
                                        current_users = self.tree.item(selected_item_id, "values")[7]
                                        if current_users:
                                            users_list = [u for u in current_users.split("|") if u != username]
                                            new_users = "|".join(users_list)
                                            self._update_username_cell(selected_item_id, new_users)
                                    except Exception:
                                        pass
                                self.after(0, remove_from_ui)
                                
                                # Mostra erro ao usuário
                                err_msg = stderr.strip() or stdout.strip() or f"Exit code {proc.returncode}"
                                if len(err_msg) > 500:
                                    err_msg = err_msg[:500] + "..."
                                self.after(0, lambda: messagebox.showerror(
                                    "Erro RDP", f"Falha ao conectar:\n{err_msg}"
                                ))
                                return
                            
                            # Tenta detectar processo
                            if is_rdp_connection_active(
                                data['ip'].split(':')[0],
                                data['user'],
                                data['title']
                            ):
                                rdp_detected = True
                                logging.info(f"[PERF] ✓ Processo RDP detectado na tentativa {attempt + 1}")
                                
                                # Registra conexão
                                pid = rdp_monitor.register_rdp_connection(
                                    data['ip'].split(':')[0],
                                    data['user'],
                                    data['title']
                                )
                                if pid:
                                    logging.info(f"[PERF] ✓ Conexão RDP registrada com PID {pid}")
                                break
                            
                            if attempt < max_attempts - 1:
                                time.sleep(0.4)
                        
                        if not rdp_detected:
                            logging.warning(f"[PERF] ⚠ Processo RDP não detectado após {max_attempts} tentativas")
                    
                    except Exception as e:
                        logging.error(f"[PERF] Erro ao monitorar processo RDP: {e}")
                
                # Inicia monitoramento em thread separada
                Thread(target=monitor_rdp_process, daemon=True, name=f"RDP-Monitor-{con_codigo}").start()
                
                # ⚡ AGUARDA processo terminar (usuário desconectar)
                # Mas o controle já foi retornado imediatamente após Popen
                proc.wait()
                logging.info(f"[PERF] Processo RDP finalizado (exit code: {proc.returncode})")

            except FileNotFoundError as e:
                logging.error(f"rdp.exe não encontrado: {e}")
                messagebox.showerror("Erro", f"Executável rdp.exe não encontrado:\n{e}")
            except Exception as e:
                logging.exception("Erro inesperado ao executar rdp.exe")
                messagebox.showerror("Erro", f"Falha ao executar o rdp.exe:\n{e}")
            finally:
                # Stop recording when RDP session ends
                if session_id and self.recording_manager:
                    if self.recording_manager.stop_session_recording():
                        logging.info(f"Recording stopped for session {session_id}")
                    else:
                        logging.warning(f"Failed to stop recording for session {session_id}")

        # Passa session_id e connection_info como parâmetros nomeados
        self._execute_connection(
            data, 
            task, 
            recording_session_id=session_id, 
            recording_connection_info=connection_info
        )

    def _connect_native_wts(self):
        """Conecta usando o cliente MSTSC."""
        data = self._get_selected_item_data()
        if not data:
            return

        # con_codigo = data.get("db_id")  # TODO: Usar quando necessário

        if data.get("username"):
            msg = f"'{data['username']}' já está conectado(a) a este cliente.\nDeseja continuar e conectar mesmo assim?"
            if not messagebox.askyesno("Alerta: Conexão em Uso", msg):
                return

        def task():
            ip = data["ip"].split(":")[0]
            subprocess.run(f"cmdkey /delete:TERMSRV/{ip}", shell=True, capture_output=True)
            subprocess.run(
                f'cmdkey /generic:TERMSRV/{ip} /user:"{data["user"]}" /pass:"{data["pwd"]}"',
                shell=True,
                capture_output=True,
            )
            try:
                subprocess.run(f'mstsc /v:{data["ip"]} /f', shell=True, check=True)
            finally:
                subprocess.run(f"cmdkey /delete:TERMSRV/{ip}", shell=True, capture_output=True)

        Thread(target=lambda: self._execute_connection(data, task), daemon=True).start()

    def _release_connection(self):
        """Libera uma conexão protegida solicitando a senha de proteção."""
        data = self._get_selected_item_data()
        if not data:
            return

        con_codigo = data.get("db_id")
        logging.info(f"[RELEASE_DEBUG] Tentando liberar conexão {con_codigo}")
        logging.info(f"[RELEASE_DEBUG] Tipo do con_codigo: {type(con_codigo)}")

        session_protection_manager = get_current_session_protection_manager()
        logging.info(
            f"[RELEASE_DEBUG] session_protection_manager existe: {session_protection_manager is not None}"
        )
        if session_protection_manager:
            logging.info(
                f"[RELEASE_DEBUG] session_protection_manager ID: {getattr(session_protection_manager, 'instance_id', 'NO_ID')}"
            )
            logging.info(
                f"[RELEASE_DEBUG] session_protection_manager.db_service: {session_protection_manager.db_service is not None}"
            )
            logging.info(
                f"[RELEASE_DEBUG] session_protection_manager.session_repo: {session_protection_manager.session_repo is not None}"
            )
        try:
            con_codigo = int(con_codigo) if con_codigo else None
            logging.info(f"[RELEASE_DEBUG] con_codigo convertido para int: {con_codigo}")
        except (ValueError, TypeError) as e:
            logging.error(f"[RELEASE_DEBUG] Erro ao converter con_codigo para int: {e}")
            messagebox.showerror("Erro", "ID da conexão inválido.")
            return

        if not con_codigo:
            logging.error("[RELEASE_DEBUG] con_codigo é None ou inválido")
            messagebox.showerror("Erro", "ID da conexão não encontrado.")
            return

        if session_protection_manager:
            logging.info(
                f"[RELEASE_DEBUG] session_protection_manager ID: {getattr(session_protection_manager, 'instance_id', 'NO_ID')}"
            )
            logging.info(
                f"[RELEASE_DEBUG] session_protection_manager.db_service: {session_protection_manager.db_service is not None}"
            )
            logging.info(
                f"[RELEASE_DEBUG] session_protection_manager.session_repo: {session_protection_manager.session_repo is not None}"
            )

        # Verifica se existe proteção de sessão
        session_protection_manager = get_current_session_protection_manager()

        if not session_protection_manager or not session_protection_manager.is_session_protected(
            con_codigo
        ):
            logging.info(f"[RELEASE_DEBUG] Sem proteção ativa detectada para conexão {con_codigo}")
            logging.info(f"[RELEASE_DEBUG] Dados da conexão: {data}")
            messagebox.showinfo(
                "Sem Proteção", "Este servidor não possui proteção ativa para liberar."
            )
            return

        # Obtém informações da proteção
        protection_info = session_protection_manager.get_session_protection_info(con_codigo)
        protected_by = (
            protection_info.get("protected_by", "Unknown") if protection_info else "Unknown"
        )

        # Mostra diálogo de validação de senha para liberação
        validation_dialog = ValidateSessionPasswordDialog(
            parent=self,
            connection_data=data,
            requesting_user=self.user_session_name,
            protected_by=protected_by,
            unlock_mode=True,  # Indica que é para liberar a conexão
        )

        # Aguarda resultado da validação
        validation_dialog.wait_window()
        result = validation_dialog.get_result()

        if not result or not result.get("validated"):
            # Senha incorreta - não prossegue com a liberação
            logging.warning(
                f"🔒 Tentativa de liberação negada para {self.user_session_name} do servidor {data.get('title')}"
            )
            messagebox.showwarning(
                "Acesso Negado",
                f"Não foi possível liberar a proteção do servidor '{data.get('title')}'.\n\n"
                "Você não forneceu a senha correta.",
            )
            return

        # Senha correta - remove a proteção
        success = session_protection_manager.remove_session_protection(
            con_codigo, self.user_session_name
        )

        if success:
            logging.info(
                f"🔓 Conexão liberada por {self.user_session_name} para {data.get('title')}"
            )
            messagebox.showinfo(
                "Conexão Liberada",
                "Proteção removida com sucesso!\n\n"
                f"O servidor '{data.get('title')}' está agora disponível para todos os usuários.",
            )
            # Atualiza a lista para refletir as mudanças
            self._populate_tree()
        else:
            logging.error(f"Falha ao liberar proteção para {data.get('title')}")
            messagebox.showerror(
                "Erro na Liberação",
                "Ocorreu um erro ao tentar liberar a proteção.\n\n"
                "Tente novamente ou contate o administrador do sistema.",
            )

    def _open_admin_login(self):
        """Abre o diálogo para login de administrador."""
        password = ctk.CTkInputDialog(
            text="Digite a senha de Administrador:",
            title="Login Admin",
        ).get_input()

        if not password:
            return

        # --- ATUALIZADO: Acessa repositório de usuários ---
        try:
            admin_hash = self.db.users.get_admin_password_hash()
        except DatabaseError as e:
            messagebox.showerror(
                "Erro de Banco de Dados", f"Não foi possível verificar a senha:\n{e}"
            )
            return

        if not admin_hash:
            messagebox.showerror(
                "Erro de Configuração", "Senha de administrador não encontrada no banco."
            )
            return

        input_hash = hash_password_md5(password)

        if input_hash == admin_hash:
            logging.info(f"Usuário {self.user_session_name} logou como admin.")
            self._open_admin_panel()
        else:
            logging.warning(f"Tentativa falha de login admin por {self.user_session_name}.")
            messagebox.showerror("Acesso Negado", "Senha incorreta.")

    def _open_admin_panel(self):
        """Abre o HUB de administração."""
        # A instância 'self.db' (que agora é o DBService) é passada
        # para o AdminHub. O AdminHub também precisará ser refatorado
        # para usar os repositórios (ex: self.db.users.admin_get_all_users)
        admin_hub = AdminHubDialog(self, self.db)
        self.wait_window(admin_hub)

        logging.info("Painel admin fechado. Recarregando lista de conexões.")
        self._populate_tree()

    # Sistema de Proteção de Sessões
    def _protect_session(self):
        """Permite ao usuário atual proteger uma sessão com senha."""
        data = self._get_selected_item_data()
        if not data:
            return

        con_codigo = data.get("db_id")

        session_protection_manager = get_current_session_protection_manager()
        if not CreateSessionProtectionDialog or not session_protection_manager:
            messagebox.showwarning(
                "Não Disponível", "Sistema de proteção de sessão não está disponível."
            )
            return

        # Verifica se já existe proteção
        if session_protection_manager.is_session_protected(con_codigo):
            existing_protection = session_protection_manager.get_session_protection_info(con_codigo)
            protected_by = (
                existing_protection.get("protected_by", "Unknown")
                if existing_protection
                else "Unknown"
            )

            if protected_by == self.user_session_name:
                messagebox.showinfo(
                    "Já Protegida",
                    "Você já criou uma proteção para este servidor.\n\n"
                    "Use 'Remover Proteção' para desativar.",
                )
            else:
                messagebox.showinfo(
                    "Já Protegida",
                    f"Este servidor já está protegido por '{protected_by}'.\n\n"
                    "Apenas o criador da proteção pode removê-la.",
                )
            return

        # Adiciona informações necessárias ao data
        enhanced_data = data.copy()
        enhanced_data["machine_name"] = self.computer_name
        enhanced_data["ip_address"] = self.user_ip

        # Mostra diálogo de criação de proteção
        protection_dialog = CreateSessionProtectionDialog(
            parent=self, connection_data=enhanced_data, current_user=self.user_session_name
        )

        # Aguarda resultado
        protection_dialog.wait_window()
        result = protection_dialog.get_result()

        if result and result.get("activated"):
            logging.info(
                f"🔒 Proteção criada por {self.user_session_name} para {data.get('title')}"
            )
            messagebox.showinfo(
                "Proteção Ativada",
                "Proteção ativada com sucesso!\n\n"
                f"Outros usuários precisarão da senha para acessar '{data.get('title')}'.",
            )
        else:
            logging.info(f"Criação de proteção cancelada por {self.user_session_name}")

    def _remove_session_protection_legacy(self):
        """Remove proteção de sessão criada pelo usuário atual (versão antiga)."""
        data = self._get_selected_item_data()
        if not data:
            return

        con_codigo = data.get("db_id")

        if not session_protection_manager:
            messagebox.showwarning(
                "Não Disponível", "Sistema de proteção de sessão não está disponível."
            )
            return

        # Verifica se existe proteção
        if not session_protection_manager.is_session_protected(con_codigo):
            logging.info(f"Data:{ data}")
            messagebox.showinfo("Sem Proteção", "Este servidor não possui proteção ativa.")
            return

        # Verifica informações da proteção
        protection_info = session_protection_manager.get_session_protection_info(con_codigo)
        protected_by = (
            protection_info.get("protected_by", "Unknown") if protection_info else "Unknown"
        )

        # Verifica se o usuário atual é o criador da proteção
        if protected_by != self.user_session_name:
            messagebox.showwarning(
                "Não Autorizado",
                f"Esta proteção foi criada por '{protected_by}'.\n\n"
                "Apenas o criador pode remover a proteção.",
            )
            return

        # Confirma remoção
        if messagebox.askyesno(
            "Confirmar Remoção",
            f"Tem certeza que deseja remover a proteção do servidor '{data.get('title')}'?\n\n"
            "Outros usuários voltarão a ter acesso livre.",
        ):
            success = session_protection_manager.remove_session_protection(
                con_codigo, self.user_session_name
            )

            if success:
                logging.info(
                    f"🔓 Proteção removida por {self.user_session_name} para {data.get('title')}"
                )
                messagebox.showinfo(
                    "Proteção Removida",
                    "Proteção removida com sucesso!\n\n"
                    f"O servidor '{data.get('title')}' agora tem acesso livre.",
                )
            else:
                messagebox.showerror("Erro", "Falha ao remover a proteção. Tente novamente.")

    # Recording Manager Callbacks
    def _on_recording_started(self, session_id: str):
        """Called when recording starts."""
        logging.info(f"Recording started for session: {session_id}")
        # Update UI to show recording status if needed
        self.after(0, self._update_recording_status_ui)

    def _on_recording_stopped(self, session_id: str):
        """Called when recording stops."""
        logging.info(f"Recording stopped for session: {session_id}")
        # Update UI to show recording status if needed
        self.after(0, self._update_recording_status_ui)

    def _on_recording_error(self, session_id: str, error_message: str):
        """Called when recording error occurs."""
        logging.error(f"Recording error for session {session_id}: {error_message}")
        # Show error message to user
        self.after(
            0,
            messagebox.showerror,
            "Recording Error",
            f"Recording failed for session {session_id}:\n{error_message}",
        )

    def _update_recording_status_ui(self):
        """Update UI to reflect recording status."""
        try:
            if self.recording_manager:
                status = self.recording_manager.get_recording_status()
                # Update window title or status bar to show recording status
                if status.get("is_recording", False):
                    current_title = self.title()
                    if "🔴" not in current_title:
                        self.title(f"🔴 {current_title}")
                else:
                    current_title = self.title()
                    if "🔴" in current_title:
                        self.title(current_title.replace("🔴 ", ""))
        except Exception as e:
            logging.error(f"Error updating recording status UI: {e}")

    def _check_session_recordings(self, session_id: str = None):
        """
        Verifica se existem gravações para uma sessão específica ou lista todas.

        Args:
            session_id: ID da sessão para verificar. Se None, lista todas as gravações.

        Returns:
            List[Dict]: Lista de informações sobre gravações encontradas
        """
        if not self.recording_manager:
            return []

        try:
            from pathlib import Path

            recordings_dir = Path(self.settings.RECORDING_OUTPUT_DIR)
            recordings_info = []

            if session_id:
                # Verifica gravações específicas da sessão
                video_files = list(recordings_dir.glob(f"{session_id}_*.mp4"))
                metadata_file = recordings_dir / f"{session_id}_metadata.json"

                if video_files or metadata_file.exists():
                    info = {
                        "session_id": session_id,
                        "video_files": [str(f) for f in video_files],
                        "metadata_file": str(metadata_file) if metadata_file.exists() else None,
                        "total_size_mb": sum(f.stat().st_size for f in video_files) / (1024 * 1024),
                        "file_count": len(video_files),
                    }
                    recordings_info.append(info)
            else:
                # Lista todas as gravações
                all_videos = list(recordings_dir.glob("*.mp4"))
                sessions = {}

                for video_file in all_videos:
                    # Extrai session_id do nome do arquivo (formato: session_id_part_X.mp4)
                    name_parts = video_file.stem.split("_")
                    if len(name_parts) >= 2:
                        session_id = (
                            "_".join(name_parts[:-2])
                            if name_parts[-2] == "part"
                            else "_".join(name_parts[:-1])
                        )

                        if session_id not in sessions:
                            sessions[session_id] = {
                                "session_id": session_id,
                                "video_files": [],
                                "metadata_file": None,
                                "total_size_mb": 0,
                                "file_count": 0,
                            }

                        sessions[session_id]["video_files"].append(str(video_file))
                        sessions[session_id]["total_size_mb"] += video_file.stat().st_size / (
                            1024 * 1024
                        )
                        sessions[session_id]["file_count"] += 1

                        # Verifica se existe metadata
                        metadata_file = recordings_dir / f"{session_id}_metadata.json"
                        if metadata_file.exists():
                            sessions[session_id]["metadata_file"] = str(metadata_file)

                recordings_info = list(sessions.values())

            return recordings_info

        except Exception as e:
            logging.error(f"Erro ao verificar gravações: {e}")
            return []

    def _show_recording_info(self):
        """Mostra informações sobre gravações existentes."""
        recordings = self._check_session_recordings()

        if not recordings:
            messagebox.showinfo(
                "Gravações",
                "Nenhuma gravação encontrada.\n\n"
                f"Diretório de gravações: {self.settings.RECORDING_OUTPUT_DIR}",
            )
            return

        # Cria uma janela com informações das gravações
        info_window = ctk.CTkToplevel(self)
        info_window.title("Informações de Gravação")
        info_window.geometry("600x400")
        info_window.transient(self)

        # Frame principal
        main_frame = ctk.CTkFrame(info_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Título
        title_label = ctk.CTkLabel(
            main_frame, text="📹 Gravações de Sessão", font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=(10, 5))

        # Diretório
        dir_label = ctk.CTkLabel(
            main_frame,
            text=f"Diretório: {self.settings.RECORDING_OUTPUT_DIR}",
            font=("Segoe UI", 10),
        )
        dir_label.pack(pady=(0, 10))

        # Frame scrollável para lista
        scroll_frame = ctk.CTkScrollableFrame(main_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Lista as gravações
        for recording in recordings:
            session_frame = ctk.CTkFrame(scroll_frame)
            session_frame.pack(fill="x", pady=5)

            session_info = (
                f"🎥 Sessão: {recording['session_id']}\n"
                f"📁 Arquivos: {recording['file_count']}\n"
                f"💾 Tamanho: {recording['total_size_mb']:.1f} MB\n"
                f"📄 Metadata: {'✅' if recording['metadata_file'] else '❌'}"
            )

            info_label = ctk.CTkLabel(session_frame, text=session_info, justify="left", anchor="w")
            info_label.pack(padx=10, pady=10, fill="x")

        # Botão para abrir diretório
        def open_recordings_dir():
            try:
                import subprocess

                subprocess.run(["explorer", self.settings.RECORDING_OUTPUT_DIR], check=True)
            except Exception as e:
                logging.error(f"Erro ao abrir diretório: {e}")
                messagebox.showerror("Erro", f"Não foi possível abrir o diretório:\n{e}")

        open_button = ctk.CTkButton(
            main_frame, text="📂 Abrir Diretório de Gravações", command=open_recordings_dir
        )
        open_button.pack(pady=10)

    # Métodos para Sistema de Acesso Colaborativo

    def _show_connection_in_use_dialog(self, data: Dict[str, Any]) -> str:
        """
        Mostra diálogo com opções quando uma conexão está em uso.

        Returns:
            "cancel", "force", ou "collaborative"
        """
        connected_user = data.get("username", "Usuário desconhecido")
        connection_name = data.get("title", "Conexão")

        # Cria diálogo customizado
        dialog = ctk.CTkToplevel(self)
        dialog.title("Conexão em Uso")
        dialog.geometry("450x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Centraliza o diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        result = {"choice": "cancel"}

        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        # Ícone e título
        title_label = ctk.CTkLabel(
            main_frame, text="⚠️ Conexão em Uso", font=("Segoe UI", 18, "bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 20))

        # Mensagem
        message = f"'{connected_user}' já está conectado(a) ao cliente '{connection_name}'."
        message_label = ctk.CTkLabel(
            main_frame, text=message, font=("Segoe UI", 12), wraplength=400
        )
        message_label.grid(row=1, column=0, pady=(0, 20))

        # Opções
        options_label = ctk.CTkLabel(
            main_frame, text="O que você deseja fazer?", font=("Segoe UI", 12, "bold")
        )
        options_label.grid(row=2, column=0, pady=(0, 15))

        # Botões de opção
        def set_result(choice):
            result["choice"] = choice
            dialog.destroy()

        # Acesso colaborativo
        collab_button = ctk.CTkButton(
            main_frame,
            text="🤝 Solicitar Acesso Colaborativo",
            command=lambda: set_result("collaborative"),
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color="#2E8B57",
            hover_color="#228B22",
        )
        collab_button.grid(row=3, column=0, pady=5, sticky="ew", padx=20)

        # Forçar conexão
        force_button = ctk.CTkButton(
            main_frame,
            text="⚡ Conectar Mesmo Assim",
            command=lambda: set_result("force"),
            height=40,
            font=("Segoe UI", 12),
            fg_color="#FF6B35",
            hover_color="#E55039",
        )
        force_button.grid(row=4, column=0, pady=5, sticky="ew", padx=20)

        # Cancelar
        cancel_button = ctk.CTkButton(
            main_frame,
            text="❌ Cancelar",
            command=lambda: set_result("cancel"),
            height=40,
            font=("Segoe UI", 12),
            fg_color="gray50",
            hover_color="gray40",
        )
        cancel_button.grid(row=5, column=0, pady=(15, 10), sticky="ew", padx=20)

        # Tooltip/descrição
        desc_label = ctk.CTkLabel(
            main_frame,
            text="💡 Acesso colaborativo gera senha temporária para uso controlado",
            font=("Segoe UI", 10),
            text_color="gray60",
        )
        desc_label.grid(row=6, column=0, pady=5)

        # Aguarda resposta
        dialog.wait_window()
        return result["choice"]

    def _request_collaborative_access(self, data: Dict[str, Any]):
        """Verifica se sessão está protegida e solicita senha."""
        try:
            connection_id = data.get("db_id")
            current_user = self.user_session_name

            # Verifica se a sessão está protegida
            if session_protection_manager.is_session_protected(connection_id):
                protection_info = session_protection_manager.get_session_protection_info(
                    connection_id
                )
                protected_by = protection_info.get("protected_by", "Usuário desconhecido")

                # Mostra diálogo de validação de senha
                dialog = ValidateSessionPasswordDialog(self, data, current_user, protected_by)

                dialog.wait_window()
                result = dialog.get_result()

                if result and result.get("validated"):
                    # Senha correta - pode conectar
                    logging.info(
                        f"Acesso autorizado para {current_user} no servidor protegido {data.get('title')}"
                    )
                    return True
                else:
                    # Senha incorreta ou cancelado
                    logging.info(
                        f"Acesso negado para {current_user} no servidor protegido {data.get('title')}"
                    )
                    return False
            else:
                # Sessão não protegida - mostra diálogo de conexão em uso
                self._show_connection_in_use_dialog(data)
                return False

        except Exception as e:
            logging.error(f"Erro ao verificar proteção de sessão: {e}")
            messagebox.showerror("Erro", f"Falha na verificação de proteção:\n{e}")
            return False

    def _create_session_protection(self, data: Dict[str, Any]):
        """Permite ao usuário conectado criar proteção para sua sessão."""
        try:
            current_user = self.user_session_name

            # Verifica se já existe proteção ativa
            connection_id = data.get("db_id")
            if session_protection_manager.is_session_protected(connection_id):
                existing_protection = session_protection_manager.get_session_protection_info(
                    connection_id
                )
                if existing_protection.get("protected_by") == current_user:
                    messagebox.showinfo(
                        "Sessão Já Protegida",
                        "Esta sessão já está protegida por você.\n\n"
                        f"Criada em: {existing_protection.get('created_at', 'N/A')}\n"
                        f"Válida até: {existing_protection.get('expiry_time', 'N/A')}",
                    )
                else:
                    messagebox.showwarning(
                        "Sessão Protegida por Outro Usuário",
                        f"Esta sessão está protegida por: {existing_protection.get('protected_by')}",
                    )
                return

            # Cria nova proteção
            dialog = CreateSessionProtectionDialog(self, data, current_user)

            dialog.wait_window()
            result = dialog.get_result()

            if result and result.get("activated"):
                # Proteção criada com sucesso
                logging.info(
                    f"Proteção de sessão criada por {current_user} para {data.get('title')}"
                )

                # Atualiza interface se necessário
                self._populate_tree()

        except Exception as e:
            logging.error(f"Erro ao criar proteção de sessão: {e}")
            messagebox.showerror("Erro", f"Falha ao criar proteção:\n{e}")

    def _remove_session_protection(self, data: Dict[str, Any]):
        """Remove proteção da sessão (apenas o criador pode remover)."""
        try:
            connection_id = data.get("db_id")
            current_user = self.user_session_name

            if not session_protection_manager.is_session_protected(connection_id):
                messagebox.showinfo(
                    "Sessão Não Protegida", "Esta sessão não possui proteção ativa."
                )
                return

            # Confirma remoção
            confirm = messagebox.askyesno(
                "Remover Proteção",
                "Tem certeza que deseja remover a proteção desta sessão?\n\n"
                "Outros usuários poderão acessar o servidor normalmente.",
            )

            if confirm:
                success = session_protection_manager.remove_session_protection(
                    connection_id, current_user
                )

                if success:
                    messagebox.showinfo(
                        "Proteção Removida",
                        "✅ Proteção removida com sucesso!\n\nA sessão não está mais protegida.",
                    )
                    logging.info(
                        f"Proteção removida por {current_user} da conexão {data.get('title')}"
                    )

                    # Atualiza interface
                    self._populate_tree()
                else:
                    messagebox.showwarning(
                        "Não Autorizado", "Apenas o usuário que criou a proteção pode removê-la."
                    )

        except Exception as e:
            logging.error(f"Erro ao remover proteção: {e}")
            messagebox.showerror("Erro", f"Falha ao remover proteção:\n{e}")

    def _disconnect_other_user(self, connection_id: int, request_data: Dict[str, Any]):
        """Desconecta outro usuário para acesso exclusivo."""
        try:
            connected_user = request_data.get("connected_user")
            if connected_user:
                logging.info(f"Tentando desconectar usuário '{connected_user}' da conexão {connection_id}")
                
                # Força desconexão do outro usuário
                if self.db.logs.delete_connection_log(connection_id, connected_user):
                    logging.info(f"Usuário {connected_user} desconectado para acesso exclusivo")
                    
                    # CORREÇÃO: Para heartbeats órfãos quando há múltiplos usuários
                    # Se não há mais usuários conectados nesta conexão, limpar o heartbeat
                    try:
                        # Verificar se ainda há outros usuários conectados
                        remaining_users = self._get_connected_users_for_connection(connection_id)
                        if not remaining_users:
                            # Nenhum usuário restante, parar heartbeat
                            if connection_id in self.active_heartbeats:
                                logging.info(f"Parando heartbeat órfão da conexão {connection_id}")
                                self.active_heartbeats[connection_id].set()
                                del self.active_heartbeats[connection_id]
                    except Exception as e:
                        logging.error(f"Erro ao limpar heartbeat órfão: {e}")
                    
                    messagebox.showinfo(
                        "Acesso Exclusivo",
                        f"Usuário '{connected_user}' foi desconectado para permitir seu acesso exclusivo.",
                    )
                    
                    # Ao desconectar um usuário, tenta liberar quaisquer proteções que ele
                    # tenha criado
                    try:
                        protection_manager = get_current_session_protection_manager()
                        if protection_manager:
                            protection_manager.cleanup_current_user_protections(
                                connected_user, show_notification=False
                            )
                            logging.info(
                                f"[SESSION_PROTECTION] Proteções do usuário {connected_user} verificadas/removidas após desconexão"
                            )
                        else:
                            logging.warning(
                                f"[SESSION_PROTECTION] Não foi possível obter session_protection_manager para limpar proteções de {connected_user}"
                            )
                    except Exception as e:
                        logging.error(
                            f"Erro ao limpar proteções após desconexão de {connected_user}: {e}"
                        )

                    # Atualiza a visualização
                    self._populate_tree()
                    
                else:
                    logging.error(f"Falha ao desconectar usuário {connected_user} da conexão {connection_id}")
                    messagebox.showerror("Erro", f"Não foi possível desconectar o usuário '{connected_user}'")

        except Exception as e:
            logging.error(f"Erro ao desconectar outro usuário: {e}")

    def _get_connected_users_for_connection(self, con_codigo: int) -> List[str]:
        """
        Obtém lista de usuários ainda conectados em uma conexão específica.
        
        Args:
            con_codigo: Código da conexão
            
        Returns:
            Lista de nomes de usuários conectados
        """
        try:
            query = "SELECT Usu_Nome FROM Usuario_Conexao_WTS WHERE Con_Codigo = ?"
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (con_codigo,))
                rows = cursor.fetchall()
                return [row[0] for row in rows] if rows else []
        except Exception as e:
            logging.error(f"Erro ao buscar usuários conectados na conexão {con_codigo}: {e}")
            return []

    def _show_active_collaborative_sessions(self):
        """Mostra proteções de sessão ativas (para administradores)."""
        try:
            current_user = self.user_session_name
            protection_manager = get_current_session_protection_manager()
            if protection_manager:
                user_protections = protection_manager.get_user_protected_sessions(current_user)
                total_protections = len(protection_manager.protected_sessions)
            else:
                logging.warning(
                    "[SESSION_PROTECTION] session_protection_manager não disponível ao exibir proteções ativas"
                )
                user_protections = []
                total_protections = 0

            if user_protections:
                protection_list = []
                for protection in user_protections:
                    protection_list.append(
                        f"- {protection.get('connection_name')} (até {protection.get('expiry_time', 'N/A')})"
                    )

                message = f"Suas proteções ativas ({len(user_protections)}):\n\n" + "\n".join(
                    protection_list
                )
                messagebox.showinfo("Proteções Ativas", message)
            else:
                messagebox.showinfo(
                    "Proteções Ativas", "Você não possui proteções de sessão ativas."
                )

            if total_protections > 0:
                logging.info(f"Proteções de sessão ativas no sistema: {total_protections}")
            else:
                logging.info("Nenhuma proteção de sessão ativa no sistema")

        except Exception as e:
            logging.error(f"Erro ao verificar proteções ativas: {e}")

    def _cleanup_collaborative_sessions(self):
        """Limpa proteções de sessão criadas pelo usuário atual (chamado no shutdown)."""
        try:
            import os

            current_user = os.getenv("USERNAME", "unknown")

            logging.info(f"🔒 SHUTDOWN: Iniciando limpeza de proteções para usuário {current_user}")

            # Obtém a instância atual do session_protection_manager
            protection_manager = get_current_session_protection_manager()

            if protection_manager:
                # Remove proteções criadas pelo usuário atual (sem notificação gráfica no shutdown)
                removed_count = protection_manager.cleanup_current_user_protections(
                    current_user, show_notification=False
                )

                if removed_count > 0:
                    logging.info(
                        f"🔒 SHUTDOWN: {removed_count} proteções do usuário {current_user} removidas automaticamente"
                    )

                # Limpeza geral (proteções locais)
                protection_manager.cleanup_all_protections()
                logging.info("🔒 SHUTDOWN: Limpeza de proteções de sessão concluída")
            else:
                logging.warning(
                    "🔒 SHUTDOWN: session_protection_manager não disponível, pulando limpeza de proteções"
                )

        except Exception as e:
            logging.error(f"Erro na limpeza de proteções: {e}")

    def _cleanup_orphaned_protections(self):
        """Executa limpeza de proteções órfãs em background (assíncrono)."""
        def cleanup_task():
            """Task executada em background thread."""
            try:
                protection_manager = get_current_session_protection_manager()
                if protection_manager:
                    success, message, count = protection_manager.cleanup_orphaned_protections()
                    if count > 0:
                        logging.info(f"🧹 Limpeza automática: {count} proteções órfãs removidas")
                    return count
                return 0
            except Exception as e:
                logging.error(f"Erro na limpeza automática de proteções: {e}")
                return 0
        
        # Executa em background, sem bloquear UI
        self.thread_pool.submit_io_task(cleanup_task)

    def _cleanup_orphaned_connections(self):
        """
        ⚡ OTIMIZADO: Remove conexões órfãs do banco (SOMENTE DO USUÁRIO DA MÁQUINA ATUAL).
        
        Casos tratados:
        1. WATS foi fechado enquanto conectado (heartbeat parou, processo RDP ainda ativo)
        2. Processo RDP foi morto externamente
        3. Registros antigos que não foram limpos corretamente
        
        Esta função é executada:
        - A cada refresh da árvore (~30s)
        - Em thread separada (não bloqueia UI)
        """
        try:
            logging.info(f"[CLEANUP_ORPHAN] 🔍 Iniciando limpeza para: {self.user_session_name}")
            
            # ⚡ OTIMIZAÇÃO: Busca APENAS conexões do usuário atual (query filtrada no banco)
            user_connections = self.db.logs.get_active_connections_for_user(self.user_session_name)
            
            logging.info(f"[CLEANUP_ORPHAN] Conexões do usuário encontradas: {len(user_connections) if user_connections else 0}")
            
            if not user_connections:
                logging.debug(f"[CLEANUP_ORPHAN] Nenhuma conexão do usuário no banco")
                return
            
            orphaned_count = 0
            
            for conn in user_connections:
                con_codigo = conn.get('Con_Codigo')
                
                # Pula se tiver heartbeat ativo (conexão válida e gerenciada)
                if con_codigo in self.active_heartbeats:
                    logging.debug(f"[CLEANUP_ORPHAN] Con {con_codigo} - heartbeat ativo, OK")
                    continue
                
                logging.info(f"[CLEANUP_ORPHAN] ⚠️ Con {con_codigo} SEM heartbeat - validando processo RDP...")
                
                # Tenta obter IP da conexão do cache
                server_ip = None
                connection_title = None
                rdp_user = None
                
                try:
                    conn_data = next((c for c in self.data_cache if c.con_codigo == con_codigo), None)
                    if conn_data:
                        server_ip = conn_data.ip.split(':')[0] if conn_data.ip else None
                        connection_title = conn_data.nome
                        rdp_user = conn_data.user
                except Exception as e:
                    logging.debug(f"[CLEANUP_ORPHAN] Erro ao buscar cache para {con_codigo}: {e}")
                
                # Fallback: busca direto do banco
                if not server_ip:
                    try:
                        query = f"SELECT Con_IP FROM Conexao WHERE Con_Codigo = {self.db.PARAM}"
                        with self.db.get_cursor() as cursor:
                            cursor.execute(query, (con_codigo,))
                            row = cursor.fetchone()
                            if row:
                                server_ip = row[0].split(':')[0] if row[0] else None
                    except Exception as e:
                        logging.debug(f"[CLEANUP_ORPHAN] Erro ao buscar IP do banco: {e}")
                
                # Se não tem IP, remove sem validar processo (dados insuficientes)
                if not server_ip:
                    logging.warning(
                        f"[CLEANUP_ORPHAN] ⚠️ Con {con_codigo} sem IP - "
                        f"REMOVENDO órfã sem validação de processo"
                    )
                    if self.db.logs.delete_connection_log(con_codigo, self.user_session_name):
                        orphaned_count += 1
                        self._remove_user_from_ui(con_codigo, self.user_session_name)
                    continue
                
                # Verifica se processo RDP existe
                logging.info(f"[CLEANUP_ORPHAN] Validando RDP: IP={server_ip}, user={rdp_user}")
                is_active = is_rdp_connection_active(server_ip, rdp_user, connection_title)
                
                if not is_active:
                    logging.warning(f"[CLEANUP_ORPHAN] 🧟 Órfã detectada: Con {con_codigo} @ {server_ip}")
                    
                    # Remove do banco
                    if self.db.logs.delete_connection_log(con_codigo, self.user_session_name):
                        orphaned_count += 1
                        logging.info(f"[CLEANUP_ORPHAN] ✓ Removida do banco: Con {con_codigo}")
                        
                        # Remove da UI (método separado para evitar race conditions)
                        self._remove_user_from_ui(con_codigo, self.user_session_name)
                else:
                    logging.info(f"[CLEANUP_ORPHAN] ✓ Processo RDP ativo para Con {con_codigo} - mantendo")
            
            if orphaned_count > 0:
                logging.info(f"[CLEANUP_ORPHAN] 🧟 Total removido: {orphaned_count} conexão(ões)")
                
        except Exception as e:
            logging.error(f"[CLEANUP_ORPHAN] Erro: {e}", exc_info=True)

    def _remove_user_from_ui(self, con_codigo: int, username: str):
        """
        Remove usuário da UI de forma segura (evita race conditions).
        Executa na thread principal com validações.
        """
        def update_ui():
            try:
                item_id = self.tree_item_map.get(con_codigo)
                if not item_id or not self.tree.exists(item_id):
                    logging.debug(f"[UI_UPDATE] Item {con_codigo} não existe na árvore")
                    return
                
                current_users = self.tree.item(item_id, "values")[7]
                if not current_users or username not in current_users:
                    logging.debug(f"[UI_UPDATE] Usuário {username} já removido da UI")
                    return
                
                # Remove usuário da lista
                users_list = [u for u in current_users.split("|") if u != username]
                new_users = "|".join(users_list)
                
                # Atualiza UI
                current_values = list(self.tree.item(item_id, "values"))
                current_values[7] = new_users
                self.tree.item(item_id, values=tuple(current_values))
                
                logging.info(f"[UI_UPDATE] ✓ Removido {username} da UI (Con {con_codigo})")
                
            except Exception as e:
                logging.error(f"[UI_UPDATE] Erro ao atualizar UI: {e}")
        
        # Garante execução na thread principal
        self.after(0, update_ui)
