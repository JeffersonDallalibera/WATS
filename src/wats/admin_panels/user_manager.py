# WATS_Project/wats_app/admin_panels/user_manager.py (COM FILTRO REUTILIZÁVEL)

import logging
from tkinter import messagebox
from typing import Dict, List, Optional, Tuple

import customtkinter as ctk

from ..db.db_service import DBService
from ..utils import create_user_filter_frame


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

        # Inicializar repositório de permissões individuais
        try:
            from ..db.repositories.individual_permission_repository import (
                IndividualPermissionRepository,
            )

            self.individual_permission_repo = IndividualPermissionRepository(db.db_manager)
        except ImportError:
            logging.warning(
                "IndividualPermissionRepository não encontrado. Permissões individuais não estarão disponíveis."
            )
            self.individual_permission_repo = None

        self.title("Gerenciar Usuários e Permissões")
        self.geometry("900x700")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Criar sistema de abas
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Aba de Usuários (funcionalidade atual)
        self.tab_users = self.tabview.add("Usuários e Grupos")
        self._setup_users_tab()

        # Aba de Permissões Individuais
        self.tab_individual = self.tabview.add("Permissões Individuais")
        self._setup_individual_permissions_tab()

        self.transient(parent)
        self.update_idletasks()  # Força renderização da janela
        
        # Carrega dados em background
        self.after(50, self._load_initial_data)
        
    def _load_initial_data(self):
        """Carrega dados iniciais em background após a janela ser exibida."""
        try:
            # Carrega dados da aba de usuários
            self._load_all_users()
            self._load_all_groups_checkboxes()
            
            # Remove label de loading
            if hasattr(self, 'loading_label_users') and self.loading_label_users:
                self.loading_label_users.destroy()
                
        except Exception as e:
            logging.error(f"Erro ao carregar dados iniciais: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")
        finally:
            self.grab_set()  # Apenas agora torna modal

    def _setup_users_tab(self):
        """Configura a aba de gerenciamento de usuários (funcionalidade original)."""
        self.tab_users.grid_columnconfigure(0, weight=1)  # Coluna da Treeview
        self.tab_users.grid_columnconfigure(1, weight=2)  # Coluna do Formulário
        self.tab_users.grid_rowconfigure(0, weight=1)

        # --- Coluna da Esquerda (Lista com Filtro Reutilizável) ---
        self.user_filter_frame = create_user_filter_frame(self.tab_users)
        self.user_filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Label de loading (será removido após carregar)
        self.loading_label_users = ctk.CTkLabel(
            self.user_filter_frame,
            text="⏳ Carregando usuários...",
            font=("Segoe UI", 12, "italic"),
            text_color="gray"
        )
        self.loading_label_users.place(relx=0.5, rely=0.5, anchor="center")

        # Vincula callback de seleção
        self.user_filter_frame.bind_selection(self._on_user_select)

        # --- Coluna da Direita (Formulário de Edição - Sem Mudanças Estruturais) ---
        frame_right = ctk.CTkFrame(self.tab_users, fg_color="transparent")
        frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        frame_right.grid_columnconfigure(1, weight=1)  # Coluna dos inputs com peso
        frame_right.grid_rowconfigure(4, weight=1)  # Linha do frame de grupos com peso

        self.lbl_form_title = ctk.CTkLabel(
            frame_right, text="Selecione um usuário ou crie um novo", font=("Segoe UI", 14, "bold")
        )
        self.lbl_form_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        ctk.CTkLabel(frame_right, text="Nome de Usuário (ex: suporte.ats):").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.entry_username = ctk.CTkEntry(frame_right)
        self.entry_username.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(frame_right, text="E-mail (Opcional):").grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        self.entry_email = ctk.CTkEntry(frame_right)
        self.entry_email.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        self.check_is_admin = ctk.CTkCheckBox(frame_right, text="É Administrador (Vê TUDO)")
        self.check_is_admin.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.check_is_active = ctk.CTkCheckBox(frame_right, text="Ativo (Pode logar)")
        self.check_is_active.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # Frame de Permissões de Grupo
        group_frame = ctk.CTkFrame(frame_right)
        group_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        group_frame.grid_columnconfigure(0, weight=1)
        group_frame.grid_rowconfigure(2, weight=1)
        self.lbl_groups = ctk.CTkLabel(
            group_frame,
            text="Permissões de Grupo (se não for Admin):",
            font=("Segoe UI", 12, "bold"),
        )
        self.lbl_groups.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Frame para botões de seleção
        btn_selection_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
        btn_selection_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        btn_selection_frame.grid_columnconfigure(0, weight=1)
        btn_selection_frame.grid_columnconfigure(1, weight=1)

        self.btn_select_all = ctk.CTkButton(
            btn_selection_frame,
            text="Selecionar Todos",
            height=28,
            command=self._select_all_groups,
            fg_color="green",
            hover_color="darkgreen",
        )
        self.btn_select_all.grid(row=0, column=0, padx=5, sticky="ew")

        self.btn_deselect_all = ctk.CTkButton(
            btn_selection_frame,
            text="Desmarcar Todos",
            height=28,
            command=self._deselect_all_groups,
            fg_color="red",
            hover_color="darkred",
        )
        self.btn_deselect_all.grid(row=0, column=1, padx=5, sticky="ew")

        self.group_scroll_frame = ctk.CTkScrollableFrame(group_frame, fg_color="transparent")
        self.group_scroll_frame.grid(row=2, column=0, sticky="nsew")
        self.group_checkboxes: Dict[int, ctk.CTkCheckBox] = {}

        # Botões de Ação
        frame_actions = ctk.CTkFrame(frame_right, fg_color="transparent")
        frame_actions.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
        frame_actions.grid_columnconfigure(0, weight=1)
        frame_actions.grid_columnconfigure(1, weight=1)
        self.btn_save = ctk.CTkButton(
            frame_actions, text="Salvar Alterações", height=40, command=self._save_user
        )
        self.btn_save.grid(row=0, column=1, padx=5, sticky="ew")
        self.btn_new = ctk.CTkButton(
            frame_actions,
            text="Novo Usuário",
            height=40,
            command=self._clear_form,
            fg_color="gray40",
        )
        self.btn_new.grid(row=0, column=0, padx=5, sticky="ew")

        # --- Inicialização Otimizada ---
        self._clear_form()  # Limpa form primeiro (instantâneo)

    def _setup_individual_permissions_tab(self):
        """Configura a aba de permissões individuais."""
        if not self.individual_permission_repo:
            # Se o repositório não está disponível, mostrar mensagem
            error_label = ctk.CTkLabel(
                self.tab_individual,
                text="⚠️ Permissões individuais não estão disponíveis.\nRepositório não encontrado.",
                font=(
                    "Segoe UI",
                    14),
            )
            error_label.pack(expand=True)
            return

        self.tab_individual.grid_columnconfigure(0, weight=1)
        self.tab_individual.grid_columnconfigure(1, weight=1)
        self.tab_individual.grid_columnconfigure(2, weight=1)
        self.tab_individual.grid_rowconfigure(1, weight=1)

        # Título
        title_label = ctk.CTkLabel(
            self.tab_individual,
            text="Permissões Individuais de Conexão",
            font=("Segoe UI", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        # Coluna 1: Lista de Usuários
        users_frame = ctk.CTkFrame(self.tab_individual)
        users_frame.grid(row=1, column=0, padx=5, pady=10, sticky="nsew")
        users_frame.grid_columnconfigure(0, weight=1)
        users_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(users_frame, text="👤 Usuários", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, padx=10, pady=5
        )

        self.users_filter_entry = ctk.CTkEntry(users_frame, placeholder_text="Filtrar usuários...")
        self.users_filter_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.users_filter_entry.bind("<KeyRelease>", self._filter_users_individual)

        self.users_listbox = ctk.CTkScrollableFrame(users_frame)
        self.users_listbox.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        # Coluna 2: Lista de Conexões
        connections_frame = ctk.CTkFrame(self.tab_individual)
        connections_frame.grid(row=1, column=1, padx=5, pady=10, sticky="nsew")
        connections_frame.grid_columnconfigure(0, weight=1)
        connections_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(connections_frame, text="🖥️ Conexões", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, padx=10, pady=5
        )

        self.connections_filter_entry = ctk.CTkEntry(
            connections_frame, placeholder_text="Filtrar conexões..."
        )
        self.connections_filter_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.connections_filter_entry.bind("<KeyRelease>", self._filter_connections_individual)

        self.connections_listbox = ctk.CTkScrollableFrame(connections_frame)
        self.connections_listbox.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        # Coluna 3: Permissões Ativas e Ações
        actions_frame = ctk.CTkFrame(self.tab_individual)
        actions_frame.grid(row=1, column=2, padx=5, pady=10, sticky="nsew")
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            actions_frame, text="⚙️ Ações e Permissões Ativas", font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, padx=10, pady=5)

        # Botões de ação
        actions_buttons_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        actions_buttons_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        actions_buttons_frame.grid_columnconfigure(0, weight=1)

        self.btn_grant_individual = ctk.CTkButton(
            actions_buttons_frame,
            text="🔓 Conceder Permissão",
            height=35,
            command=self._grant_individual_permission,
            fg_color="green",
            hover_color="darkgreen",
        )
        self.btn_grant_individual.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

        self.btn_revoke_individual = ctk.CTkButton(
            actions_buttons_frame,
            text="🔒 Revogar Permissão",
            height=35,
            command=self._revoke_individual_permission,
            fg_color="red",
            hover_color="darkred",
        )
        self.btn_revoke_individual.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

        # Lista de permissões ativas
        self.active_permissions_listbox = ctk.CTkScrollableFrame(actions_frame)
        self.active_permissions_listbox.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        # Variáveis para seleções
        self.selected_individual_user_id = None
        self.selected_individual_connection_id = None
        
        # Cache de dados para melhor performance
        self._all_users_individual = []
        self._all_connections_individual = []
        
        # Variáveis para debounce dos filtros
        self._filter_users_job = None
        self._filter_connections_job = None
        
        # Limite de itens exibidos para melhor performance
        self.MAX_DISPLAYED_ITEMS = 100

        # Carregar dados iniciais
        self._load_users_individual()
        self._load_connections_individual()
        self._load_active_individual_permissions()

    def _load_all_users(self, preserve_state=False):
        """Busca todos os usuários do banco e preenche o FilterableTreeFrame (otimizado)."""
        try:
            # A query retorna (Usu_Id, Usu_Nome, Usu_Ativo, Usu_Is_Admin)
            self.all_users = self.db.users.admin_get_all_users()
        except Exception as e:
            messagebox.showerror("Erro de BD", f"Não foi possível carregar usuários:\n{e}")
            self.all_users = []

        if not self.all_users:
            if preserve_state:
                self.user_filter_frame.update_data([])
            else:
                self.user_filter_frame.set_data([])
            return

        # Formata dados para o FilterableTreeFrame usando list comprehension (mais rápido)
        formatted_users = [
            (
                user[0],                              # user_id
                user[1],                              # nome
                "Sim" if user[3] else "Não",         # is_admin
                "Sim" if user[2] else "Não"          # ativo
            )
            for user in self.all_users
        ]

        if preserve_state:
            self.user_filter_frame.update_data(formatted_users)
        else:
            self.user_filter_frame.set_data(formatted_users)

    def _load_all_groups_checkboxes(self):  # Renomeado
        """Busca todos os grupos e cria os checkboxes de permissão."""
        try:
            self.all_groups = self.db.groups.admin_get_all_groups()
        except Exception as e:
            messagebox.showerror("Erro de BD", f"Não foi possível carregar grupos:\n{e}")
            self.all_groups = []

        self.group_checkboxes.clear()
        for widget in self.group_scroll_frame.winfo_children():
            widget.destroy()

        if not self.all_groups:
            ctk.CTkLabel(self.group_scroll_frame, text="Nenhum grupo cadastrado.").pack()
            return

        for group_id, group_name in self.all_groups:
            check = ctk.CTkCheckBox(self.group_scroll_frame, text=f"{group_name} (ID: {group_id})")
            check.grid(sticky="w", padx=10, pady=5)  # Usa grid para alinhar
            self.group_checkboxes[group_id] = check

    def _clear_form(self):
        """Limpa o formulário para um novo cadastro."""
        self.lbl_form_title.configure(text="Criando Novo Usuário")
        self.selected_user_id = None  # Garante modo "criar"
        self.entry_username.delete(0, "end")
        self.entry_email.delete(0, "end")
        self.check_is_admin.deselect()
        self.check_is_active.select()  # Ativo por padrão
        for check in self.group_checkboxes.values():
            check.deselect()
        # Remove seleção do FilterableTreeFrame
        if hasattr(self.user_filter_frame.tree, "selection"):
            selection = self.user_filter_frame.tree.selection()
            if selection:
                self.user_filter_frame.tree.selection_remove(selection)

    def _on_user_select(self, event=None):
        """Chamado quando um usuário é selecionado no FilterableTreeFrame."""
        selected_item = self.user_filter_frame.get_selected_item()
        if not selected_item:
            self.selected_user_id = None
            logging.debug("Nenhum usuário selecionado.")
            return

        try:
            # selected_item é uma tupla (user_id, nome, is_admin_str, ativo_str)
            user_id_db = int(selected_item[0])
            self.selected_user_id = user_id_db  # Define ID para modo "update"
            logging.info(f"ID do usuário (do DB) selecionado: {self.selected_user_id}")
            self._load_user_data_to_form()  # Carrega dados
        except (ValueError, IndexError, TypeError) as e:
            logging.error(f"Erro ao obter ID do usuário selecionado: {e}. Item: {selected_item}")
            self.selected_user_id = None  # Volta para modo "criar"
            messagebox.showerror(
                "Erro Interno", "Não foi possível identificar o usuário selecionado."
            )

    def _load_user_data_to_form(self):
        """Carrega os dados do usuário selecionado (pelo ID do DB) no formulário."""
        if self.selected_user_id is None:
            logging.warning("_load_user_data_to_form chamado sem ID.")
            return

        logging.debug(f"Carregando dados para o ID de usuário: {self.selected_user_id}")
        try:
            user_data = self.db.users.admin_get_user_details(self.selected_user_id)
        except Exception as e:
            messagebox.showerror("Erro de BD", f"Não foi possível carregar usuário:\n{e}")
            return

        if not user_data:
            messagebox.showerror(
                "Erro", "Não foi possível encontrar dados (usuário pode ter sido deletado)."
            )
            self._clear_form()
            self._load_all_users()
            return

        # Preenche o formulário
        self.lbl_form_title.configure(text=f"Editando Usuário: {user_data.get('nome', 'N/A')}")
        self.entry_username.delete(0, "end")
        self.entry_username.insert(0, user_data.get("nome", "") or "")
        self.entry_email.delete(0, "end")
        self.entry_email.insert(0, user_data.get("email", "") or "")
        if user_data.get("is_admin"):
            self.check_is_admin.select()
        else:
            self.check_is_admin.deselect()
        if user_data.get("is_active"):
            self.check_is_active.select()
        else:
            self.check_is_active.deselect()

        # Marca os checkboxes de grupo
        for check in self.group_checkboxes.values():
            check.deselect()
        user_groups = user_data.get("grupos", set())
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
        if not username:
            messagebox.showwarning("Campo Obrigatório", "Nome de Usuário é obrigatório.")
            return

        # --- LÓGICA DE CRIAR vs ATUALIZAR ---
        if self.selected_user_id is None:
            # --- Modo CRIAR ---
            logging.info(f"Tentando CRIAR novo usuário: {username}")
            try:
                success, message = self.db.users.admin_create_user(
                    username, email, is_admin, is_active, selected_group_ids
                )
                if success:
                    messagebox.showinfo("Sucesso", f"Usuário '{username}' criado.")
                    self._load_all_users(preserve_state=True)
                    self._clear_form()
                    # Limpar cache de usuários individuais para forçar recarga
                    self._all_users_individual = []
                else:
                    messagebox.showerror("Erro ao Criar", message)
            except Exception as e:
                logging.error(f"Erro inesperado ao criar usuário: {e}")
                messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")
        else:
            # --- Modo ATUALIZAR ---
            logging.info(f"Tentando ATUALIZAR usuário ID {self.selected_user_id}: {username}")
            try:
                success, message = self.db.users.admin_update_user(
                    self.selected_user_id, username, email, is_admin, is_active, selected_group_ids
                )
                if success:
                    messagebox.showinfo("Sucesso", f"Usuário '{username}' atualizado.")
                    self._load_all_users(preserve_state=True)
                    # Limpar cache de usuários individuais para forçar recarga
                    self._all_users_individual = []
                    # Mantém dados no form
                else:
                    messagebox.showerror("Erro ao Atualizar", message)
            except Exception as e:
                logging.error(f"Erro inesperado ao atualizar usuário: {e}")
                messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")

    def _select_all_groups(self):
        """Seleciona todos os checkboxes de grupos."""
        for check in self.group_checkboxes.values():
            check.select()

    def _deselect_all_groups(self):
        """Desmarca todos os checkboxes de grupos."""
        for check in self.group_checkboxes.values():
            check.deselect()

    def refresh_individual_permissions_cache(self):
        """Limpa o cache das listas de permissões individuais para forçar recarga."""
        self._all_users_individual = []
        self._all_connections_individual = []
        # Recarrega as listas se a aba de permissões individuais foi inicializada
        if hasattr(self, 'users_filter_entry') and hasattr(self, 'connections_filter_entry'):
            filter_users = self.users_filter_entry.get()
            filter_conns = self.connections_filter_entry.get()
            self._load_users_individual(filter_users)
            self._load_connections_individual(filter_conns)

    # === MÉTODOS PARA PERMISSÕES INDIVIDUAIS ===

    def _load_users_individual(self, filter_text: str = ""):
        """Carrega usuários para a aba de permissões individuais com otimização."""
        if not self.individual_permission_repo:
            return

        try:
            # Carregar todos os usuários apenas se o cache estiver vazio
            if not self._all_users_individual:
                self._all_users_individual = self.db.users.admin_get_all_users()

            # Aplicar filtro
            filter_text_lower = filter_text.lower().strip()
            if filter_text_lower:
                filtered_users = [
                    user for user in self._all_users_individual
                    if filter_text_lower in str(user[1]).lower()  # user[1] é o nome
                ]
            else:
                filtered_users = self._all_users_individual

            # Filtrar apenas usuários ativos
            active_users = [user for user in filtered_users if user[2]]  # user[2] é is_active
            
            # Limitar número de itens exibidos para melhor performance
            total_users = len(active_users)
            displayed_users = active_users[:self.MAX_DISPLAYED_ITEMS]

            # Limpar lista atual de forma eficiente
            for widget in self.users_listbox.winfo_children():
                widget.destroy()

            # Mostrar aviso se houver muitos resultados
            if total_users > self.MAX_DISPLAYED_ITEMS:
                warning_label = ctk.CTkLabel(
                    self.users_listbox,
                    text=f"⚠️ Mostrando {self.MAX_DISPLAYED_ITEMS} de {total_users} usuários. Use o filtro para refinar.",
                    font=("Segoe UI", 10, "italic"),
                    text_color="orange"
                )
                warning_label.pack(pady=5)

            # Mostrar usuários ativos e filtrados
            for user_id, username, is_active, is_admin in displayed_users:
                user_btn = ctk.CTkButton(
                    self.users_listbox,
                    text=username,
                    height=30,
                    command=lambda uid=user_id: self._select_user_individual(uid),
                    fg_color=(
                        "gray40" if user_id != self.selected_individual_user_id else "blue"
                    ),
                )
                user_btn.pack(fill="x", padx=5, pady=2)
                
            # Mostrar mensagem se não houver resultados
            if not displayed_users:
                no_results = ctk.CTkLabel(
                    self.users_listbox,
                    text="Nenhum usuário ativo encontrado",
                    font=("Segoe UI", 11),
                    text_color="gray"
                )
                no_results.pack(pady=20)

        except Exception as e:
            logging.error(f"Erro ao carregar usuários individuais: {e}")

    def _load_connections_individual(self, filter_text: str = ""):
        """Carrega conexões para a aba de permissões individuais com otimização."""
        if not self.individual_permission_repo:
            return

        try:
            # Carregar todas as conexões apenas se o cache estiver vazio
            if not self._all_connections_individual:
                self._all_connections_individual = self.db.connections.admin_get_all_connections()

            # Aplicar filtro
            filter_text_lower = filter_text.lower().strip()
            if filter_text_lower:
                filtered_connections = [
                    conn for conn in self._all_connections_individual
                    if filter_text_lower in str(conn[1]).lower() or  # conn[1] é o nome da conexão
                       (len(conn) > 4 and conn[4] and filter_text_lower in str(conn[4]).lower())  # conn[4] é o IP
                ]
            else:
                filtered_connections = self._all_connections_individual

            # Limitar número de itens exibidos para melhor performance
            total_connections = len(filtered_connections)
            displayed_connections = filtered_connections[:self.MAX_DISPLAYED_ITEMS]
            
            # Limpar lista atual de forma eficiente
            for widget in self.connections_listbox.winfo_children():
                widget.destroy()

            # Mostrar aviso se houver muitos resultados
            if total_connections > self.MAX_DISPLAYED_ITEMS:
                warning_label = ctk.CTkLabel(
                    self.connections_listbox,
                    text=f"⚠️ Mostrando {self.MAX_DISPLAYED_ITEMS} de {total_connections} conexões. Use o filtro para refinar.",
                    font=("Segoe UI", 10, "italic"),
                    text_color="orange"
                )
                warning_label.pack(pady=5)

            # Mostrar conexões filtradas (apenas nome, como na tela inicial)
            # Formato: (Con_Codigo, Con_Nome, Gru_Nome, con_tipo, Con_IP)
            for conn in displayed_connections:
                conn_id = conn[0]
                conn_name = conn[1]
                
                conn_btn = ctk.CTkButton(
                    self.connections_listbox,
                    text=conn_name,  # Apenas o nome, sem ID ou IP
                    height=30,
                    command=lambda cid=conn_id: self._select_connection_individual(cid),
                    fg_color=(
                        "gray40" if conn_id != self.selected_individual_connection_id else "blue"
                    ),
                )
                conn_btn.pack(fill="x", padx=5, pady=2)
                
            # Mostrar mensagem se não houver resultados
            if not displayed_connections:
                no_results = ctk.CTkLabel(
                    self.connections_listbox,
                    text="Nenhuma conexão encontrada",
                    font=("Segoe UI", 11),
                    text_color="gray"
                )
                no_results.pack(pady=20)

        except Exception as e:
            logging.error(f"Erro ao carregar conexões individuais: {e}")

    def _load_active_individual_permissions(self):
        """Carrega e exibe permissões individuais ativas do usuário selecionado."""
        if not self.individual_permission_repo:
            return

        try:
            # Limpar lista atual
            for widget in self.active_permissions_listbox.winfo_children():
                widget.destroy()

            # Se nenhum usuário selecionado, mostrar mensagem
            if (
                not hasattr(self, "selected_individual_user_id")
                or self.selected_individual_user_id is None
            ):
                info_label = ctk.CTkLabel(
                    self.active_permissions_listbox,
                    text="Selecione um usuário para ver suas permissões individuais",
                    font=("Segoe UI", 10, "italic"),
                )
                info_label.pack(pady=20)
                return

            # Carregar permissões apenas do usuário selecionado
            permissions = self.individual_permission_repo.list_all_individual_permissions(
                user_id=self.selected_individual_user_id
            )

            if not permissions:
                no_perms_label = ctk.CTkLabel(
                    self.active_permissions_listbox,
                    text="Este usuário não possui permissões individuais ativas",
                    font=("Segoe UI", 10),
                )
                no_perms_label.pack(pady=10)
                return

            # Título com nome do usuário
            user_name = permissions[0]["username"] if permissions else "Usuário"
            title_label = ctk.CTkLabel(
                self.active_permissions_listbox,
                text=f"Permissões de {user_name}:",
                font=("Segoe UI", 12, "bold"),
            )
            title_label.pack(pady=(5, 10))

            for perm in permissions:
                conn_name = perm["conn_name"]
                is_temporary = perm["is_temporary"]
                expires_at = perm["expires_at"]

                perm_text = f"🖥️ {conn_name}"
                if is_temporary and expires_at:
                    perm_text += f"\n🕐 Expira: {expires_at}"
                else:
                    perm_text += "\n🔒 Permanente"

                perm_frame = ctk.CTkFrame(self.active_permissions_listbox)
                perm_frame.pack(fill="x", padx=5, pady=2)

                perm_label = ctk.CTkLabel(perm_frame, text=perm_text, anchor="w")
                perm_label.pack(side="left", padx=10, pady=5)

        except Exception as e:
            logging.error(f"Erro ao carregar permissões ativas: {e}")

    def _select_user_individual(self, user_id):
        """Seleciona um usuário na aba de permissões individuais."""
        self.selected_individual_user_id = user_id
        # Recarrega com filtro atual preservado
        filter_text = self.users_filter_entry.get()
        self._load_users_individual(filter_text)
        self._load_active_individual_permissions()  # Recarregar permissões do usuário selecionado

    def _select_connection_individual(self, conn_id):
        """Seleciona uma conexão na aba de permissões individuais."""
        self.selected_individual_connection_id = conn_id
        # Recarrega com filtro atual preservado
        filter_text = self.connections_filter_entry.get()
        self._load_connections_individual(filter_text)

    def _filter_users_individual(self, event=None):
        """Filtra a lista de usuários conforme texto digitado (com debounce)."""
        # Cancela job anterior se existir
        if self._filter_users_job:
            self.after_cancel(self._filter_users_job)
        
        # Agenda nova busca após 300ms (debounce)
        self._filter_users_job = self.after(300, self._do_filter_users_individual)
    
    def _do_filter_users_individual(self):
        """Executa o filtro de usuários (chamado após debounce)."""
        filter_text = self.users_filter_entry.get()
        self._load_users_individual(filter_text)

    def _filter_connections_individual(self, event=None):
        """Filtra a lista de conexões conforme texto digitado (com debounce)."""
        # Cancela job anterior se existir
        if self._filter_connections_job:
            self.after_cancel(self._filter_connections_job)
        
        # Agenda nova busca após 300ms (debounce)
        self._filter_connections_job = self.after(300, self._do_filter_connections_individual)
    
    def _do_filter_connections_individual(self):
        """Executa o filtro de conexões (chamado após debounce)."""
        filter_text = self.connections_filter_entry.get()
        self._load_connections_individual(filter_text)

    def _grant_individual_permission(self):
        """Concede permissão individual para usuário e conexão selecionados."""
        if not self.individual_permission_repo:
            messagebox.showerror("Erro", "Repositório de permissões não disponível.")
            return

        if not self.selected_individual_user_id:
            messagebox.showwarning("Seleção Necessária", "Selecione um usuário.")
            return

        if not self.selected_individual_connection_id:
            messagebox.showwarning("Seleção Necessária", "Selecione uma conexão.")
            return

        try:
            success, message = self.individual_permission_repo.grant_individual_access(
                user_id=self.selected_individual_user_id,
                connection_id=self.selected_individual_connection_id,
                granted_by_user_id=1,  # ID do admin - ajustar conforme necessário
            )

            if success:
                messagebox.showinfo("Sucesso", message)
                self._load_active_individual_permissions()
            else:
                messagebox.showerror("Erro", message)

        except Exception as e:
            logging.error(f"Erro ao conceder permissão: {e}")
            messagebox.showerror("Erro", f"Erro ao conceder permissão:\n{e}")

    def _revoke_individual_permission(self):
        """Revoga permissão individual para usuário e conexão selecionados."""
        if not self.individual_permission_repo:
            messagebox.showerror("Erro", "Repositório de permissões não disponível.")
            return

        if not self.selected_individual_user_id:
            messagebox.showwarning("Seleção Necessária", "Selecione um usuário.")
            return

        if not self.selected_individual_connection_id:
            messagebox.showwarning("Seleção Necessária", "Selecione uma conexão.")
            return

        try:
            success, message = self.individual_permission_repo.revoke_individual_access(
                user_id=self.selected_individual_user_id,
                connection_id=self.selected_individual_connection_id,
            )

            if success:
                messagebox.showinfo("Sucesso", message)
                self._load_active_individual_permissions()
            else:
                messagebox.showerror("Erro", message)

        except Exception as e:
            logging.error(f"Erro ao revogar permissão: {e}")
            messagebox.showerror("Erro", f"Erro ao revogar permissão:\n{e}")

    # Não há função _delete_user neste painel (apenas inativar via checkbox 'Ativo')
