# WATS_Project/wats_app/admin_panels/admin_hub.py (CORRIGIDO)

import customtkinter as ctk
import logging
from tkinter import messagebox
from ..db.db_service import DBService 
from .user_manager import ManageUserDialog
from .group_manager import ManageGroupDialog
from .connection_manager import ManageConnectionDialog
from .temporary_access_manager import TemporaryAccessDialog


class AdminHubDialog(ctk.CTkToplevel):
    """
    O "Hub" principal do Painel de Administração.
    """
    # --- CORREÇÃO AQUI ---
    # O tipo do 'db' é DBService, não Database
    def __init__(self, parent, db: DBService):
    # --- FIM DA CORREÇÃO ---
        super().__init__(parent)
        self.db = db
        self.parent_app = parent
        
        self.title("Painel de Administração")
        self.geometry("400x550")  # Aumentar altura para novo botão
        
        self.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(self, text="Painel de Administração", font=("Segoe UI", 18, "bold"))
        lbl_title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- Botões ---
        btn_manage_users = ctk.CTkButton(
            self, text="👤 Gerenciar Usuários e Permissões",
            height=45, command=self._open_user_manager
        )
        btn_manage_users.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        btn_manage_connections = ctk.CTkButton(
            self, text="🖥️ Gerenciar Conexões (Bases)",
            height=45, command=self._open_connection_manager, state="normal" 
        )
        btn_manage_connections.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        btn_manage_groups = ctk.CTkButton(
            self, text="📁 Gerenciar Grupos",
            height=45, command=self._open_group_manager, state="normal" 
        )
        btn_manage_groups.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # NOVO: Botão para permissões temporárias
        btn_temporary_access = ctk.CTkButton(
            self, text="🕐 Permissões Temporárias",
            height=45, command=self._open_temporary_access_manager, state="normal",
            fg_color="orange", hover_color="darkorange"
        )
        btn_temporary_access.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        btn_close = ctk.CTkButton(
            self, text="Fechar Painel Admin",
            height=35, command=self.destroy, fg_color="gray40", hover_color="gray30"
        )
        btn_close.grid(row=5, column=0, padx=20, pady=(20, 20), sticky="ew")

        self.transient(parent)
        self.grab_set()
        self.focus()

    def _open_user_manager(self):
        """Abre o diálogo de gerenciamento de usuários."""
        logging.info("Abrindo gerenciador de usuários...")
        dialog = ManageUserDialog(self, self.db)
        self.wait_window(dialog)
        self._on_admin_dialog_close()

    def _open_connection_manager(self): 
        """Abre o diálogo de gerenciamento de conexões."""
        logging.info("Abrindo gerenciador de conexões...")
        dialog = ManageConnectionDialog(self, self.db)
        self.wait_window(dialog)
        self._on_admin_dialog_close()
        
    def _open_group_manager(self): 
        """Abre o diálogo de gerenciamento de grupos."""
        logging.info("Abrindo gerenciador de grupos...")
        dialog = ManageGroupDialog(self, self.db)
        self.wait_window(dialog)
        self._on_admin_dialog_close()

    def _open_temporary_access_manager(self):
        """Abre o diálogo de gerenciamento de permissões temporárias."""
        logging.info("Abrindo gerenciador de permissões temporárias...")
        dialog = TemporaryAccessDialog(self, self.db)
        self.wait_window(dialog)
        self._on_admin_dialog_close()
        
    def _on_admin_dialog_close(self):
        """Chamado quando qualquer painel admin fecha."""
        # Força o refresh da lista principal na janela 'Application'
        if hasattr(self.parent_app, '_populate_tree'):
             self.parent_app._populate_tree()