# WATS_Project/wats_app/admin_panels/user_manager.py (COM TREEVIEW)

import customtkinter as ctk
import logging
from tkinter import messagebox, ttk # Importa ttk
from typing import List, Optional, Tuple, Dict, Any
from ..db.db_service import DBService

class ManageUserDialog(ctk.CTkToplevel):
    """
    Janela para Criar, Editar e Gerenciar permissões de Usuários, usando Treeview.
    """
    def __init__(self, parent, db: DBService):
        super().__init__(parent)
        self.db = db
        self.all_users: List[Tuple] = []
        self.all_groups: List[Tuple] = []
        self.selected_user_id: Optional[int] = None

        self.title("Gerenciar Usuários")
        self.geometry("800x600")

        self.grid_columnconfigure(0, weight=1) # Coluna da Treeview
        self.grid_columnconfigure(1, weight=2) # Coluna do Formulário
        self.grid_rowconfigure(0, weight=1)

        # --- Coluna da Esquerda (Lista com Treeview) ---
        frame_left = ctk.CTkFrame(self)
        frame_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame_left.grid_rowconfigure(1, weight=1) # Faz a Treeview expandir

        # Cabeçalho da coluna esquerda (Título apenas)
        lbl_users = ctk.CTkLabel(frame_left, text="Usuários do Sistema", font=("Segoe UI", 14, "bold"))
        lbl_users.grid(row=0, column=0, columnspan=2, padx=10, pady=10) # columnspan=2

        # --- ttk.Treeview ---
        self.style = ttk.Style(self)
        self._apply_treeview_theme()

        tree_columns = ('id', 'nome', 'admin')
        self.user_tree = ttk.Treeview(
            frame_left,
            columns=tree_columns,
            displaycolumns=('nome', 'admin'), # ID oculto
            show='headings',
            selectmode='browse',
            style="Admin.Treeview"
        )
        self.user_tree.grid(row=1, column=0, padx=(10,0), pady=10, sticky="nsew")

        # Configura colunas
        self.user_tree.heading('nome', text='Nome de Usuário', anchor='w')
        self.user_tree.column('nome', anchor='w', width=150, stretch=True)
        self.user_tree.heading('admin', text='Admin', anchor='center')
        self.user_tree.column('admin', anchor='center', width=50, stretch=False) # Largura fixa

        # Scrollbar
        tree_scrollbar = ctk.CTkScrollbar(frame_left, command=self.user_tree.yview)
        tree_scrollbar.grid(row=1, column=1, padx=(0,10), pady=10, sticky="ns")
        self.user_tree.configure(yscrollcommand=tree_scrollbar.set)

        # Evento de seleção
        self.user_tree.bind('<<TreeviewSelect>>', self._on_user_select)
        # --- FIM Treeview ---

        # --- Coluna da Direita (Formulário de Edição - Sem Mudanças Estruturais) ---
        frame_right = ctk.CTkFrame(self, fg_color="transparent")
        frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        frame_right.grid_columnconfigure(1, weight=1) # Coluna dos inputs com peso
        frame_right.grid_rowconfigure(4, weight=1) # Linha do frame de grupos com peso

        self.lbl_form_title = ctk.CTkLabel(frame_right, text="Selecione um usuário ou crie um novo", font=("Segoe UI", 14, "bold"))
        self.lbl_form_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        ctk.CTkLabel(frame_right, text="Nome de Usuário (ex: suporte.ats):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_username = ctk.CTkEntry(frame_right)
        self.entry_username.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(frame_right, text="E-mail (Opcional):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.entry_email = ctk.CTkEntry(frame_right)
        self.entry_email.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        self.check_is_admin = ctk.CTkCheckBox(frame_right, text="É Administrador (Vê TUDO)")
        self.check_is_admin.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.check_is_active = ctk.CTkCheckBox(frame_right, text="Ativo (Pode logar)")
        self.check_is_active.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # Frame de Permissões de Grupo
        group_frame = ctk.CTkFrame(frame_right)
        group_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        group_frame.grid_columnconfigure(0, weight=1); group_frame.grid_rowconfigure(1, weight=1)
        self.lbl_groups = ctk.CTkLabel(group_frame, text="Permissões de Grupo (se não for Admin):", font=("Segoe UI", 12, "bold"))
        self.lbl_groups.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.group_scroll_frame = ctk.CTkScrollableFrame(group_frame, fg_color="transparent")
        self.group_scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.group_checkboxes: Dict[int, ctk.CTkCheckBox] = {}

        # Botões de Ação
        frame_actions = ctk.CTkFrame(frame_right, fg_color="transparent")
        frame_actions.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
        frame_actions.grid_columnconfigure(0, weight=1); frame_actions.grid_columnconfigure(1, weight=1)
        self.btn_save = ctk.CTkButton(frame_actions, text="Salvar Alterações", height=40, command=self._save_user)
        self.btn_save.grid(row=0, column=1, padx=5, sticky="ew")
        self.btn_new = ctk.CTkButton(frame_actions, text="Novo Usuário", height=40, command=self._clear_form, fg_color="gray40")
        self.btn_new.grid(row=0, column=0, padx=5, sticky="ew")

        # --- Inicialização ---
        self._load_all_users()
        self._load_all_groups_checkboxes() # Renomeado para clareza
        self._clear_form()

        self.transient(parent)
        self.grab_set()

    def _apply_treeview_theme(self):
        """Aplica o tema claro/escuro ao ttk.Treeview."""
        mode = ctk.get_appearance_mode()
        if mode == "Dark": colors = ("#E0E0E0", "#2B2B2B", "#3C3F41", "#1F6AA5", "#2B2B2B")
        else: colors = ("#1E1E1E", "#FFFFFF", "#F0F0F0", "#0078D7", "#FFFFFF")
        text_color, bg_color, heading_bg, selected_color, field_bg = colors
        style_name = "Admin.Treeview"
        self.style.configure(style_name, background=bg_color, foreground=text_color, fieldbackground=field_bg, rowheight=25, font=("Segoe UI", 10), borderwidth=0, relief="flat")
        self.style.configure(f"{style_name}.Heading", background=heading_bg, foreground=text_color, font=("Segoe UI", 10, 'bold'), borderwidth=0, relief="flat")
        self.style.map(style_name, background=[('selected', selected_color)], foreground=[('selected', 'white')])

    def _load_all_users(self):
        """Busca todos os usuários do banco e preenche a Treeview."""
        for item in self.user_tree.get_children(): self.user_tree.delete(item)
        try:
            # A query retorna (Usu_Id, Usu_Nome, Usu_Ativo, Usu_Is_Admin)
            self.all_users = self.db.users.admin_get_all_users()
        except Exception as e:
            messagebox.showerror("Erro de BD", f"Não foi possível carregar usuários:\n{e}"); self.all_users = []
        if not self.all_users: return

        for user in self.all_users:
            user_id, nome, _, is_admin = user # Ignora Usu_Ativo (índice 2)
            is_admin_str = "Sim" if is_admin else "Não"
            # Insere com valores ('id', 'nome', 'admin')
            self.user_tree.insert('', 'end', values=(user_id, nome, is_admin_str))


    def _load_all_groups_checkboxes(self): # Renomeado
        """Busca todos os grupos e cria os checkboxes de permissão."""
        try:
            self.all_groups = self.db.groups.admin_get_all_groups()
        except Exception as e:
            messagebox.showerror("Erro de BD", f"Não foi possível carregar grupos:\n{e}"); self.all_groups = []

        self.group_checkboxes.clear()
        for widget in self.group_scroll_frame.winfo_children(): widget.destroy()

        if not self.all_groups:
            ctk.CTkLabel(self.group_scroll_frame, text="Nenhum grupo cadastrado.").pack(); return

        for group_id, group_name in self.all_groups:
            check = ctk.CTkCheckBox(self.group_scroll_frame, text=f"{group_name} (ID: {group_id})")
            check.grid(sticky="w", padx=10, pady=5) # Usa grid para alinhar
            self.group_checkboxes[group_id] = check

    def _clear_form(self):
        """Limpa o formulário para um novo cadastro."""
        self.lbl_form_title.configure(text="Criando Novo Usuário")
        self.selected_user_id = None # Garante modo "criar"
        self.entry_username.delete(0, "end"); self.entry_email.delete(0, "end")
        self.check_is_admin.deselect(); self.check_is_active.select() # Ativo por padrão
        for check in self.group_checkboxes.values(): check.deselect()
        selection = self.user_tree.selection()
        if selection: self.user_tree.selection_remove(selection) # Remove highlight

    def _on_user_select(self, event=None):
        """Chamado quando um usuário é selecionado na Treeview."""
        selected_items = self.user_tree.selection()
        if not selected_items:
            self.selected_user_id = None; logging.debug("Nenhum usuário selecionado."); return

        selected_item_id_internal = selected_items[0]
        item_values = self.user_tree.item(selected_item_id_internal, 'values')
        logging.debug(f"Usuário selecionado: ID interno={selected_item_id_internal}, Valores={item_values}")

        try:
            # Pega o ID REAL do usuário (primeiro valor)
            user_id_db = int(item_values[0])
            self.selected_user_id = user_id_db # Define ID para modo "update"
            logging.info(f"ID do usuário (do DB) selecionado: {self.selected_user_id}")
            self._load_user_data_to_form() # Carrega dados
        except (ValueError, IndexError, TypeError) as e:
            logging.error(f"Erro ao obter ID do usuário selecionado: {e}. Valores: {item_values}")
            self.selected_user_id = None # Volta para modo "criar"
            messagebox.showerror("Erro Interno", "Não foi possível identificar o usuário selecionado.")


    def _load_user_data_to_form(self):
        """Carrega os dados do usuário selecionado (pelo ID do DB) no formulário."""
        if self.selected_user_id is None: logging.warning("_load_user_data_to_form chamado sem ID."); return

        logging.debug(f"Carregando dados para o ID de usuário: {self.selected_user_id}")
        try:
            user_data = self.db.users.admin_get_user_details(self.selected_user_id)
        except Exception as e: messagebox.showerror("Erro de BD", f"Não foi possível carregar usuário:\n{e}"); return

        if not user_data:
            messagebox.showerror("Erro", "Não foi possível encontrar dados (usuário pode ter sido deletado).")
            self._clear_form(); self._load_all_users(); return

        # Preenche o formulário
        self.lbl_form_title.configure(text=f"Editando Usuário: {user_data.get('nome', 'N/A')}")
        self.entry_username.delete(0, "end"); self.entry_username.insert(0, user_data.get('nome', '') or '')
        self.entry_email.delete(0, "end"); self.entry_email.insert(0, user_data.get('email', '') or '')
        if user_data.get('is_admin'): self.check_is_admin.select()
        else: self.check_is_admin.deselect()
        if user_data.get('is_active'): self.check_is_active.select()
        else: self.check_is_active.deselect()

        # Marca os checkboxes de grupo
        for check in self.group_checkboxes.values(): check.deselect()
        user_groups = user_data.get('grupos', set())
        for group_id in user_groups:
            if group_id in self.group_checkboxes:
                self.group_checkboxes[group_id].select()


    def _save_user(self):
        """Salva as alterações (Criação ou Edição)."""
        username = self.entry_username.get().strip()
        email = self.entry_email.get().strip()
        is_admin = bool(self.check_is_admin.get())
        is_active = bool(self.check_is_active.get())
        selected_group_ids = [gid for gid, chk in self.group_checkboxes.items() if chk.get()]
        if not username: messagebox.showwarning("Campo Obrigatório", "Nome de Usuário é obrigatório."); return

        # --- LÓGICA DE CRIAR vs ATUALIZAR ---
        if self.selected_user_id is None:
            # --- Modo CRIAR ---
            logging.info(f"Tentando CRIAR novo usuário: {username}")
            try:
                success, message = self.db.users.admin_create_user(username, email, is_admin, is_active, selected_group_ids)
                if success:
                    messagebox.showinfo("Sucesso", f"Usuário '{username}' criado."); self._load_all_users(); self._clear_form()
                else: messagebox.showerror("Erro ao Criar", message)
            except Exception as e: logging.error(f"Erro inesperado ao criar usuário: {e}"); messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")
        else:
            # --- Modo ATUALIZAR ---
            logging.info(f"Tentando ATUALIZAR usuário ID {self.selected_user_id}: {username}")
            try:
                success, message = self.db.users.admin_update_user(self.selected_user_id, username, email, is_admin, is_active, selected_group_ids)
                if success:
                    messagebox.showinfo("Sucesso", f"Usuário '{username}' atualizado."); self._load_all_users()
                    # Mantém dados no form
                else: messagebox.showerror("Erro ao Atualizar", message)
            except Exception as e: logging.error(f"Erro inesperado ao atualizar usuário: {e}"); messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")

    # Não há função _delete_user neste painel (apenas inativar via checkbox 'Ativo')