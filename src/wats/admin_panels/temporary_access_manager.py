# WATS_Project/wats_app/admin_panels/temporary_access_manager.py

import logging
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from ..db.db_service import DBService
from ..db.repositories.individual_permission_repository import IndividualPermissionRepository


class TemporaryAccessDialog(ctk.CTkToplevel):
    """
    Painel dedicado para gerenciamento de permissões temporárias.
    Interface focada em conceder acessos com data de expiração.
    """

    def __init__(self, parent, db: DBService):
        super().__init__(parent)
        self.db = db
        self.individual_perm_repo = IndividualPermissionRepository(db.db_manager)

        self.title("🕐 Gerenciar Permissões Temporárias")
        self.geometry("1400x800")

        # Configuração do grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_widgets()

        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        """Cria a interface principal."""

        # === TÍTULO ===
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        lbl_title = ctk.CTkLabel(
            title_frame,
            text="🕐 Gerenciamento de Permissões Temporárias",
            font=("Segoe UI", 18, "bold"),
        )
        lbl_title.pack()

        # === FRAME PRINCIPAL ===
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(2, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # === SEÇÃO SUPERIOR: CONCESSÃO ===
        self._create_grant_section(main_frame)

        # === SEÇÃO INFERIOR: MONITORAMENTO ===
        self._create_monitoring_section(main_frame)

        # === BOTÕES DE AÇÃO ===
        self._create_action_buttons()

    def _create_grant_section(self, parent):
        """Cria a seção superior para concessão de acessos temporários."""

        grant_frame = ctk.CTkFrame(parent)
        grant_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        grant_frame.grid_columnconfigure(0, weight=1)
        grant_frame.grid_columnconfigure(1, weight=1)
        grant_frame.grid_columnconfigure(2, weight=1)
        grant_frame.grid_rowconfigure(1, weight=1)

        # Título da seção
        ctk.CTkLabel(
            grant_frame, text="✨ Conceder Acesso Temporário", font=("Segoe UI", 16, "bold")
        ).grid(row=0, column=0, columnspan=3, pady=10)

        # === COLUNA 1: USUÁRIOS ===
        users_frame = ctk.CTkFrame(grant_frame)
        users_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        users_frame.grid_columnconfigure(0, weight=1)
        users_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(users_frame, text="👤 USUÁRIOS", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, pady=(10, 5)
        )

        # Filtro de busca de usuários
        self.entry_filter_users = ctk.CTkEntry(users_frame, placeholder_text="🔍 Buscar usuário...")
        self.entry_filter_users.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.entry_filter_users.bind("<KeyRelease>", self._filter_users)

        # Lista de usuários
        users_list_frame = ctk.CTkFrame(users_frame)
        users_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        users_list_frame.grid_columnconfigure(0, weight=1)
        users_list_frame.grid_rowconfigure(0, weight=1)

        self.listbox_users = tk.Listbox(users_list_frame, selectmode="single")
        self.listbox_users.grid(row=0, column=0, sticky="nsew")
        self.listbox_users.bind("<<ListboxSelect>>", self._on_user_selected)

        scrollbar_users = ttk.Scrollbar(
            users_list_frame, orient="vertical", command=self.listbox_users.yview
        )
        self.listbox_users.configure(yscrollcommand=scrollbar_users.set)
        scrollbar_users.grid(row=0, column=1, sticky="ns")

        # === COLUNA 2: CONEXÕES ===
        connections_frame = ctk.CTkFrame(grant_frame)
        connections_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        connections_frame.grid_columnconfigure(0, weight=1)
        connections_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(connections_frame, text="🖥️ CONEXÕES", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, pady=(10, 5)
        )

        # Filtro de busca de conexões
        self.entry_filter_connections = ctk.CTkEntry(
            connections_frame, placeholder_text="🔍 Buscar conexão..."
        )
        self.entry_filter_connections.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.entry_filter_connections.bind("<KeyRelease>", self._filter_connections)

        # Lista de conexões
        conn_list_frame = ctk.CTkFrame(connections_frame)
        conn_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        conn_list_frame.grid_columnconfigure(0, weight=1)
        conn_list_frame.grid_rowconfigure(0, weight=1)

        self.tree_connections = ttk.Treeview(
            conn_list_frame, columns=("ip", "grupo"), show="tree headings", height=8
        )

        self.tree_connections.heading("#0", text="Conexão")
        self.tree_connections.heading("ip", text="IP")
        self.tree_connections.heading("grupo", text="Grupo")

        self.tree_connections.column("#0", width=150)
        self.tree_connections.column("ip", width=120)
        self.tree_connections.column("grupo", width=100)

        scrollbar_conn = ttk.Scrollbar(
            conn_list_frame, orient="vertical", command=self.tree_connections.yview
        )
        self.tree_connections.configure(yscrollcommand=scrollbar_conn.set)

        self.tree_connections.grid(row=0, column=0, sticky="nsew")
        scrollbar_conn.grid(row=0, column=1, sticky="ns")

        # === COLUNA 3: DURAÇÃO E AÇÕES ===
        duration_frame = ctk.CTkFrame(grant_frame)
        duration_frame.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
        duration_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(duration_frame, text="⏰ DURAÇÃO", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, pady=(10, 5)
        )

        # Frame para organizar radio buttons em grid 2x3
        radio_frame = ctk.CTkFrame(duration_frame, fg_color="transparent")
        radio_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Configurar grid 2x3 para radio buttons
        for i in range(3):
            radio_frame.grid_columnconfigure(i, weight=1)

        # Radio buttons para duração em layout 2x3
        self.duration_var = tk.StringVar(value="1.0")
        durations = self.individual_perm_repo.get_duration_options()

        # Primeira linha: 30min, 1h, 2h
        positions = [
            (0, 0),
            (0, 1),
            (0, 2),  # Primeira linha
            (1, 0),
            (1, 1),
            (1, 2),  # Segunda linha
        ]

        for i, (label, hours) in enumerate(durations):
            if i < len(positions):
                row, col = positions[i]
                radio = ctk.CTkRadioButton(
                    radio_frame,
                    text=label,
                    variable=self.duration_var,
                    value=str(hours),
                    font=("Segoe UI", 10),
                )
                radio.grid(row=row, column=col, sticky="w", padx=5, pady=3)

        # Campo de observações
        ctk.CTkLabel(duration_frame, text="📝 Observações:", font=("Segoe UI", 12, "bold")).grid(
            row=2, column=0, sticky="w", padx=10, pady=(15, 5)
        )

        self.entry_observations = ctk.CTkEntry(
            duration_frame, placeholder_text="Motivo do acesso temporário...", height=35
        )
        self.entry_observations.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        # Info do usuário selecionado
        self.lbl_selected_user = ctk.CTkLabel(
            duration_frame, text="Nenhum usuário selecionado", font=("Segoe UI", 10, "italic")
        )
        self.lbl_selected_user.grid(row=4, column=0, pady=10)

        # BOTÃO CONCEDER - Grande e visível
        self.btn_grant_temporary = ctk.CTkButton(
            duration_frame,
            text="🕐 CONCEDER ACESSO",
            command=self._grant_temporary_access,
            fg_color="darkgreen",
            hover_color="green",
            height=40,
            font=("Segoe UI", 12, "bold"),
        )
        self.btn_grant_temporary.grid(row=4, column=0, pady=15, padx=10, sticky="ew")

    def _create_monitoring_section(self, parent):
        """Cria a seção inferior para monitoramento de acessos ativos."""

        monitor_frame = ctk.CTkFrame(parent)
        monitor_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        monitor_frame.grid_columnconfigure(0, weight=1)
        monitor_frame.grid_rowconfigure(1, weight=1)

        # Título da seção
        title_frame = ctk.CTkFrame(monitor_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=10)
        title_frame.grid_columnconfigure(0, weight=1)
        title_frame.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            title_frame, text="📋 Permissões Temporárias Ativas", font=("Segoe UI", 16, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10)

        # Botão atualizar
        self.btn_refresh = ctk.CTkButton(
            title_frame,
            text="🔄 Atualizar",
            command=self._refresh_active_permissions,
            fg_color="gray40",
            hover_color="gray30",
            width=100,
        )
        self.btn_refresh.grid(row=0, column=1, padx=10)

        # Lista de permissões ativas
        active_frame = ctk.CTkFrame(monitor_frame)
        active_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        active_frame.grid_columnconfigure(0, weight=1)
        active_frame.grid_rowconfigure(0, weight=1)

        self.tree_active = ttk.Treeview(
            active_frame,
            columns=("usuario", "conexao", "ip", "expira", "tempo_restante", "criado_por"),
            show="headings",
            height=10,
        )

        self.tree_active.heading("usuario", text="Usuário")
        self.tree_active.heading("conexao", text="Conexão")
        self.tree_active.heading("ip", text="IP")
        self.tree_active.heading("expira", text="Expira em")
        self.tree_active.heading("tempo_restante", text="Tempo Restante")
        self.tree_active.heading("criado_por", text="Criado por")

        self.tree_active.column("usuario", width=120)
        self.tree_active.column("conexao", width=150)
        self.tree_active.column("ip", width=120)
        self.tree_active.column("expira", width=140)
        self.tree_active.column("tempo_restante", width=120)
        self.tree_active.column("criado_por", width=120)

        scrollbar_active = ttk.Scrollbar(
            active_frame, orient="vertical", command=self.tree_active.yview
        )
        self.tree_active.configure(yscrollcommand=scrollbar_active.set)

        self.tree_active.grid(row=0, column=0, sticky="nsew")
        scrollbar_active.grid(row=0, column=1, sticky="ns")

    def _create_action_buttons(self):
        """Cria botões de ação na parte inferior."""

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=10)

        self.btn_revoke_selected = ctk.CTkButton(
            btn_frame,
            text="❌ Revogar Selecionado",
            command=self._revoke_selected_access,
            fg_color="red",
            hover_color="darkred",
        )
        self.btn_revoke_selected.pack(side="left", padx=5)

        self.btn_cleanup = ctk.CTkButton(
            btn_frame,
            text="🧹 Limpar Expirados",
            command=self._cleanup_expired,
            fg_color="gray40",
            hover_color="gray30",
        )
        self.btn_cleanup.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Fechar", command=self.destroy, fg_color="gray40", hover_color="gray30"
        ).pack(side="left", padx=5)

        # Carregar dados iniciais
        self._load_initial_data()

    # ========== MÉTODOS DE DADOS ==========

    def _load_initial_data(self):
        """Carrega dados iniciais."""
        try:
            self._load_users_list()
            self._load_connections_list()
            self._refresh_active_permissions()

        except Exception as e:
            logging.error(f"Erro ao carregar dados iniciais: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")

    def _load_users_list(self):
        """Carrega lista de usuários."""
        try:
            # Limpar lista
            self.listbox_users.delete(0, tk.END)

            # Carregar usuários
            usuarios = self.db.users.admin_get_all_users()
            self.all_users = []

            for usuario in usuarios:
                if len(usuario) >= 3 and usuario[2]:  # Só usuários ativos
                    user_info = f"{usuario[1]} (ID: {usuario[0]})"
                    self.listbox_users.insert(tk.END, user_info)
                    self.all_users.append((usuario[0], usuario[1], user_info))

        except Exception as e:
            logging.error(f"Erro ao carregar usuários: {e}")

    def _load_connections_list(self):
        """Carrega lista de conexões disponíveis."""
        try:
            # Limpar tree
            for item in self.tree_connections.get_children():
                self.tree_connections.delete(item)

            # Carregar conexões
            connections = self.db.connections.get_available_connections_for_individual_grant()
            self.all_connections = []

            for conn in connections:
                if len(conn) >= 5:
                    conn_id = conn[0]
                    conn_name = conn[1]
                    conn_ip = conn[2]
                    group_name = conn[3]
                    # conn_type = conn[4]  # Não utilizado

                    item_id = self.tree_connections.insert(
                        "",
                        "end",
                        text=conn_name or f"Conexão {conn_id}",
                        values=(conn_ip or "N/A", group_name or "Sem grupo"),
                    )

                    self.all_connections.append(
                        {
                            "id": conn_id,
                            "name": conn_name,
                            "ip": conn_ip,
                            "group": group_name,
                            "item_id": item_id,
                        }
                    )

        except Exception as e:
            logging.error(f"Erro ao carregar conexões: {e}")

    def _refresh_active_permissions(self):
        """Atualiza a lista de permissões temporárias ativas."""
        try:
            # Limpar tree
            for item in self.tree_active.get_children():
                self.tree_active.delete(item)

            # Carregar permissões ativas
            permissions = self.individual_perm_repo.list_active_temporary_permissions()

            for perm in permissions:
                # Formatar data de expiração
                expira_em = ""
                if perm.get("Data_Fim"):
                    expira_em = perm["Data_Fim"].strftime("%d/%m/%Y %H:%M")

                # Inserir na tree com ID da permissão como tag
                item_id = self.tree_active.insert(
                    "",
                    "end",
                    values=(
                        perm.get("Usu_Nome", "N/A"),
                        perm.get("Con_Nome", "N/A"),
                        perm.get("Con_IP", "N/A"),
                        expira_em,
                        perm.get("Tempo_Restante", "N/A"),
                        perm.get("Criado_Por", "N/A"),
                    ),
                    tags=[str(perm.get("Id", ""))],
                )

                # Colorir baseado no tempo restante
                tempo_restante = perm.get("Tempo_Restante", "")
                if "Expirado" in tempo_restante:
                    self.tree_active.set(item_id, "tempo_restante", "⚠️ Expirado")
                    self.tree_active.item(item_id, tags=["expired"])
                elif tempo_restante.startswith("0h") and "min" in tempo_restante:
                    # Menos de 1 hora
                    self.tree_active.item(item_id, tags=["warning"])
                else:
                    self.tree_active.item(item_id, tags=["normal"])

            # Configurar cores das tags
            self.tree_active.tag_configure("expired", background="#ffebee", foreground="red")
            self.tree_active.tag_configure("warning", background="#fff3e0", foreground="orange")
            self.tree_active.tag_configure("normal", background="#e8f5e8", foreground="darkgreen")

        except Exception as e:
            logging.error(f"Erro ao atualizar permissões ativas: {e}")

    # ========== MÉTODOS DE FILTRO ==========

    def _filter_users(self, event=None):
        """Filtra lista de usuários baseado no texto digitado."""
        try:
            search_text = self.entry_filter_users.get().lower()

            # Limpar listbox
            self.listbox_users.delete(0, tk.END)

            # Filtrar e exibir usuários
            for user_id, user_name, user_info in self.all_users:
                if search_text in user_name.lower() or search_text in str(user_id):
                    self.listbox_users.insert(tk.END, user_info)

        except Exception as e:
            logging.error(f"Erro ao filtrar usuários: {e}")

    def _filter_connections(self, event=None):
        """Filtra lista de conexões baseado no texto digitado."""
        try:
            search_text = self.entry_filter_connections.get().lower()

            # Limpar tree
            for item in self.tree_connections.get_children():
                self.tree_connections.delete(item)

            # Filtrar e exibir conexões
            for conn in self.all_connections:
                conn_name = conn["name"] or ""
                conn_ip = conn["ip"] or ""
                conn_group = conn["group"] or ""

                if (
                    search_text in conn_name.lower()
                    or search_text in conn_ip.lower()
                    or search_text in conn_group.lower()
                    or search_text in str(conn["id"])
                ):

                    self.tree_connections.insert(
                        "", "end", text=conn_name, values=(conn_ip, conn_group)
                    )

        except Exception as e:
            logging.error(f"Erro ao filtrar conexões: {e}")

    # ========== MÉTODOS DE SELEÇÃO ==========

    def _on_user_selected(self, event=None):
        """Callback quando usuário é selecionado."""
        try:
            selection = self.listbox_users.curselection()
            if selection:
                selected_text = self.listbox_users.get(selection[0])

                # Extrair ID do usuário
                if "ID: " in selected_text:
                    user_id = int(selected_text.split("ID: ")[1].split(")")[0])
                    user_name = selected_text.split(" (ID:")[0]

                    self.selected_user_id = user_id
                    self.selected_user_name = user_name

                    # Atualizar label
                    self.lbl_selected_user.configure(text=f"Usuário: {user_name}")

        except Exception as e:
            logging.error(f"Erro ao selecionar usuário: {e}")

    # ========== MÉTODOS DE AÇÃO ==========

    def _grant_temporary_access(self):
        """Concede acesso temporário à conexão selecionada."""
        try:
            # Verificar se usuário está selecionado
            if not hasattr(self, "selected_user_id"):
                messagebox.showwarning("Aviso", "Selecione um usuário primeiro!")
                return

            # Verificar se conexão está selecionada
            selection = self.tree_connections.selection()
            if not selection:
                messagebox.showwarning("Aviso", "Selecione uma conexão na lista!")
                return

            # Obter dados da conexão selecionada
            item = self.tree_connections.item(selection[0])
            conn_name = item["text"]
            conn_ip = item["values"][0]

            # Encontrar ID da conexão
            conn_id = None
            for conn in self.all_connections:
                if conn["name"] == conn_name and conn["ip"] == conn_ip:
                    conn_id = conn["id"]
                    break

            if conn_id is None:
                messagebox.showerror("Erro", "Não foi possível identificar a conexão selecionada!")
                return

            # Obter duração selecionada
            try:
                duration_hours = float(self.duration_var.get())
            except ValueError:
                messagebox.showerror("Erro", "Duração inválida selecionada!")
                return

            # Obter observações
            observations = self.entry_observations.get().strip()
            if not observations:
                observations = "Acesso temporário via painel admin"

            # Formatar duração para exibição
            if duration_hours < 1:
                duration_text = f"{int(duration_hours * 60)} minutos"
            else:
                duration_text = f"{duration_hours} hora(s)"

            # Confirmar ação
            if messagebox.askyesno(
                "Confirmar Acesso Temporário",
                "Deseja conceder acesso temporário?\n\n"
                f"Usuário: {self.selected_user_name}\n"
                f"Conexão: {conn_name} ({conn_ip})\n"
                f"Duração: {duration_text}\n"
                f"Observações: {observations}",
            ):
                # Conceder acesso (assumindo admin_user_id = 1)
                success, message = self.individual_perm_repo.grant_temporary_access(
                    user_id=self.selected_user_id,
                    connection_id=conn_id,
                    granted_by_user_id=1,  # ID do admin - ajustar conforme necessário
                    duration_hours=duration_hours,
                    observations=observations,
                )

                if success:
                    messagebox.showinfo("Sucesso", message)
                    self._refresh_active_permissions()
                    self.entry_observations.delete(0, "end")  # Limpar campo
                else:
                    messagebox.showerror("Erro", message)

        except Exception as e:
            logging.error(f"Erro ao conceder acesso temporário: {e}")
            messagebox.showerror("Erro", f"Erro ao conceder acesso: {e}")

    def _revoke_selected_access(self):
        """Revoga acesso temporário selecionado."""
        try:
            # Verificar se há permissão selecionada
            selection = self.tree_active.selection()
            if not selection:
                messagebox.showwarning("Aviso", "Selecione uma permissão na lista para revogar!")
                return

            # Obter ID da permissão
            item = self.tree_active.item(selection[0])
            tags = self.tree_active.item(selection[0], "tags")

            if not tags or not tags[0]:
                messagebox.showerror(
                    "Erro", "Não foi possível identificar a permissão selecionada!"
                )
                return

            try:
                permission_id = int(tags[0])
            except ValueError:
                messagebox.showerror("Erro", "ID da permissão inválido!")
                return

            # Obter dados para confirmação
            usuario = item["values"][0]
            conexao = item["values"][1]
            expira = item["values"][3]

            # Confirmar revogação
            if messagebox.askyesno(
                "Confirmar Revogação",
                "Deseja revogar o acesso temporário?\n\n"
                f"Usuário: {usuario}\n"
                f"Conexão: {conexao}\n"
                f"Expiraria em: {expira}",
            ):
                # Revogar acesso
                success, message = self.individual_perm_repo.revoke_temporary_access(permission_id)

                if success:
                    messagebox.showinfo("Sucesso", message)
                    self._refresh_active_permissions()
                else:
                    messagebox.showerror("Erro", message)

        except Exception as e:
            logging.error(f"Erro ao revogar acesso temporário: {e}")
            messagebox.showerror("Erro", f"Erro ao revogar acesso: {e}")

    def _cleanup_expired(self):
        """Remove permissões expiradas."""
        try:
            if messagebox.askyesno(
                "Confirmar Limpeza",
                "Deseja remover todas as permissões temporárias expiradas?\n\n"
                "Esta ação irá desativar permanentemente os acessos que já expiraram.",
            ):
                count, message = self.individual_perm_repo.cleanup_expired_permissions()

                messagebox.showinfo("Limpeza Concluída", message)
                self._refresh_active_permissions()

        except Exception as e:
            logging.error(f"Erro ao limpar permissões expiradas: {e}")
            messagebox.showerror("Erro", f"Erro ao limpar permissões: {e}")
