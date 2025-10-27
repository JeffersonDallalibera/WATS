# WATS_Project/wats_app/dialogs.py

import customtkinter as ctk
import os
from typing import List, Optional, Tuple

# Importa o caminho dos assets
from .config import ASSETS_DIR


class ClientSelectorDialog(ctk.CTkToplevel):
    """Janela de diálogo para selecionar cliente quando há múltiplos."""
    
    def __init__(self, parent, clients_data: List[Tuple[str, str]], title: str = "Selecione o Cliente"):
        super().__init__(parent)
        self.selected_link: Optional[str] = None
        self.clients_data = clients_data
        
        self._configure_dialog(title)
        self._create_widgets()
        
        self.transient(parent)
        self.grab_set()
        self.focus()
        
    def _configure_dialog(self, title: str):
        self.title(title)
        self.geometry("500x400")
        self.minsize(500, 400)
        
        icon_path = os.path.join(ASSETS_DIR, 'ats.ico')
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                print(f"Erro ao carregar ícone do diálogo: {e}")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def _create_widgets(self):
        header = ctk.CTkLabel(self, text="📋 Múltiplos Clientes Disponíveis", font=("Segoe UI", 16, "bold"))
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        info = ctk.CTkLabel(self, text="Selecione o cliente desejado para acessar a wiki:", font=("Segoe UI", 11))
        info.grid(row=0, column=0, padx=20, pady=(65, 10), sticky="w")
        
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        for idx, (client_name, client_link) in enumerate(self.clients_data):
            btn = ctk.CTkButton(
                scroll_frame, text=f"🏢 {client_name}", font=("Segoe UI", 12),
                height=45, anchor="w",
                command=lambda link=client_link: self._on_client_selected(link)
            )
            btn.grid(row=idx, column=0, padx=5, pady=5, sticky="ew")
        
        cancel_btn = ctk.CTkButton(
            self, text="❌ Cancelar", font=("Segoe UI", 11),
            fg_color="gray40", hover_color="gray30",
            height=35, command=self.destroy
        )
        cancel_btn.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
    
    def _on_client_selected(self, link: str):
        self.selected_link = link
        self.destroy()
    
    def get_selected_link(self) -> Optional[str]:
        return self.selected_link