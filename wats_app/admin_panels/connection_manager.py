# WATS_Project/wats_app/admin_panels/connection_manager.py (COM TREEVIEW - REVISADO)

import customtkinter as ctk
import logging
from tkinter import messagebox, ttk # Importa ttk
from typing import List, Optional, Tuple, Dict, Any
from ..db.db_service import DBService

class ManageConnectionDialog(ctk.CTkToplevel):
    """
    Janela para Criar, Editar e Deletar Conexões (Bases), usando Treeview para a lista.
    """
    def __init__(self, parent, db: DBService):
        super().__init__(parent)
        self.db = db
        self.all_connections: List[Tuple] = []
        self.group_map: Dict[str, Optional[int]] = {} # Permite None como valor
        self.selected_connection_id: Optional[int] = None
        self.connection_types = ['RDP', 'AnyDesk', 'TeamViewer']

        self.title("Gerenciar Conexões (Bases)")
        self.geometry("900x750")

        self.grid_columnconfigure(0, weight=1) # Coluna da Treeview
        self.grid_columnconfigure(1, weight=2) # Coluna do Formulário
        self.grid_rowconfigure(0, weight=1)

        # --- Coluna da Esquerda (Lista com Treeview) ---
        frame_left = ctk.CTkFrame(self)
        frame_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame_left.grid_rowconfigure(1, weight=1) # Faz a Treeview expandir

        # Cabeçalho da coluna esquerda
        frame_left_header = ctk.CTkFrame(frame_left, fg_color="transparent")
        frame_left_header.grid(row=0, column=0, columnspan=2, padx=10, pady=(10,0), sticky="ew")
        frame_left_header.grid_columnconfigure(0, weight=1)

        lbl_conns = ctk.CTkLabel(frame_left_header, text="Conexões", font=("Segoe UI", 14, "bold"))
        lbl_conns.grid(row=0, column=0, sticky="w")

        self.btn_delete_conn = ctk.CTkButton(frame_left_header, text="Deletar Selecionada",
                                           command=self._delete_connection,
                                           fg_color="#D32F2F", hover_color="#B71C1C",
                                           width=150)
        self.btn_delete_conn.grid(row=0, column=1, padx=(10,0), sticky="e")
        self.btn_delete_conn.configure(state="disabled")

        # --- ttk.Treeview ---
        self.style = ttk.Style(self)
        self._apply_treeview_theme() # Aplica o tema atual

        tree_columns = ('id', 'nome', 'grupo', 'tipo')
        self.connection_tree = ttk.Treeview(
            frame_left,
            columns=tree_columns,
            displaycolumns=('nome', 'grupo', 'tipo'),
            show='headings',
            selectmode='browse',
            style="Admin.Treeview"
        )
        self.connection_tree.grid(row=1, column=0, padx=(10,0), pady=10, sticky="nsew")

        # Configura as colunas
        self.connection_tree.heading('nome', text='Nome da Conexão', anchor='w')
        self.connection_tree.column('nome', anchor='w', width=200, stretch=True)
        self.connection_tree.heading('grupo', text='Grupo', anchor='w')
        self.connection_tree.column('grupo', anchor='w', width=100)
        self.connection_tree.heading('tipo', text='Tipo', anchor='w')
        self.connection_tree.column('tipo', anchor='w', width=60)

        # Scrollbar
        tree_scrollbar = ctk.CTkScrollbar(frame_left, command=self.connection_tree.yview)
        tree_scrollbar.grid(row=1, column=1, padx=(0,10), pady=10, sticky="ns")
        self.connection_tree.configure(yscrollcommand=tree_scrollbar.set)

        # Evento de seleção
        self.connection_tree.bind('<<TreeviewSelect>>', self._on_connection_select)
        # --- FIM Treeview ---


        # --- Coluna da Direita (Formulário de Edição) ---
        frame_right = ctk.CTkFrame(self, fg_color="transparent")
        frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        frame_right.grid_columnconfigure(1, weight=1)
        frame_right.grid_rowconfigure(10, weight=1)

        self.lbl_form_title = ctk.CTkLabel(frame_right, text="Selecione ou crie uma conexão", font=("Segoe UI", 14, "bold"))
        self.lbl_form_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        fields = [
            ("Nome da Conexão:", "entry_con_nome", 1), ("Grupo:", "option_menu_group", 2),
            ("Tipo:", "option_menu_tipo", 3), ("IP / Host / ID:", "entry_con_ip", 4),
            ("Usuário RDP/Acesso:", "entry_con_usuario", 5), ("Senha RDP/Acesso:", "entry_con_senha", 6),
            ("Link Wiki/Particularidade:", "entry_con_particularidade", 7),
            ("Cliente (Nome Fantasia):", "entry_con_cliente", 8), ("Extra (Opcional):", "entry_extra", 9)
        ]
        self.group_var = ctk.StringVar(value="Selecione...")
        self.conn_type_var = ctk.StringVar(value=self.connection_types[0])

        for label, widget_name, row_num in fields:
            ctk.CTkLabel(frame_right, text=label).grid(row=row_num, column=0, padx=10, pady=5, sticky="w")
            if widget_name == "option_menu_group":
                self.option_menu_group = ctk.CTkOptionMenu(frame_right, variable=self.group_var, values=["Carregando..."])
                self.option_menu_group.grid(row=row_num, column=1, padx=10, pady=5, sticky="ew")
            elif widget_name == "option_menu_tipo":
                self.option_menu_tipo = ctk.CTkOptionMenu(frame_right, variable=self.conn_type_var, values=self.connection_types)
                self.option_menu_tipo.grid(row=row_num, column=1, padx=10, pady=5, sticky="ew")
            else:
                entry = ctk.CTkEntry(frame_right)
                entry.grid(row=row_num, column=1, padx=10, pady=5, sticky="ew")
                setattr(self, widget_name, entry)
                if widget_name == "entry_con_senha": entry.configure(show="*")

        frame_actions = ctk.CTkFrame(frame_right, fg_color="transparent")
        frame_actions.grid(row=10, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="sew")
        frame_actions.grid_columnconfigure(0, weight=1); frame_actions.grid_columnconfigure(1, weight=1)
        self.btn_save = ctk.CTkButton(frame_actions, text="Salvar Alterações", height=40, command=self._save_connection)
        self.btn_save.grid(row=0, column=1, padx=5, sticky="ew")
        self.btn_new = ctk.CTkButton(frame_actions, text="Nova Conexão", height=40, command=self._clear_form, fg_color="gray40")
        self.btn_new.grid(row=0, column=0, padx=5, sticky="ew")

        # --- Inicialização ---
        self._load_all_connections()
        self._load_groups_for_dropdown()
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

    def _load_groups_for_dropdown(self):
        """Busca os grupos e popula o OptionMenu."""
        self.group_map.clear()
        try:
            all_groups = self.db.groups.admin_get_all_groups()
        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar os grupos:\n{e}"); all_groups = []

        if not all_groups:
            self.option_menu_group.configure(values=["Nenhum grupo"], state="disabled"); self.group_var.set("Nenhum grupo"); return

        group_names_list = ["(Nenhum grupo)"]
        self.group_map["(Nenhum grupo)"] = None
        for (group_id, group_name) in all_groups:
            display_name = f"{group_name} (ID: {group_id})"
            self.group_map[display_name] = group_id
            group_names_list.append(display_name)
        self.option_menu_group.configure(values=group_names_list, state="normal")
        self.group_var.set(group_names_list[0]) # Define "(Nenhum grupo)" como padrão inicial

    def _load_all_connections(self):
        """Busca todas as conexões do banco e preenche a Treeview."""
        for item in self.connection_tree.get_children(): self.connection_tree.delete(item)
        try:
            self.all_connections = self.db.connections.admin_get_all_connections()
        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar as conexões:\n{e}"); self.all_connections = []
        if not self.all_connections: return

        for conn in self.all_connections:
            conn_id, conn_nome, group_nome, conn_tipo = conn[0], conn[1], conn[2] or "-", conn[3] or "RDP"
            # Insere na Treeview com os valores na ordem ('id', 'nome', 'grupo', 'tipo')
            self.connection_tree.insert('', 'end', values=(conn_id, conn_nome, group_nome, conn_tipo))

    def _clear_form(self):
        """Limpa o formulário para um novo cadastro."""
        self.lbl_form_title.configure(text="Criando Nova Conexão")
        self.selected_connection_id = None # Garante que estamos no modo "criar"
        self.entry_con_nome.delete(0, "end"); self.entry_con_ip.delete(0, "end")
        self.entry_con_usuario.delete(0, "end"); self.entry_con_senha.delete(0, "end")
        self.entry_con_particularidade.delete(0, "end"); self.entry_con_cliente.delete(0, "end")
        self.entry_extra.delete(0, "end")
        self.group_var.set("(Nenhum grupo)"); self.conn_type_var.set("RDP")
        self.btn_delete_conn.configure(state="disabled")
        selection = self.connection_tree.selection() # Pega seleção atual
        if selection: self.connection_tree.selection_remove(selection) # Remove highlight

    def _on_connection_select(self, event=None):
        """Chamado quando uma conexão é selecionada na Treeview."""
        selected_items = self.connection_tree.selection()
        if not selected_items:
            self.selected_connection_id = None
            self.btn_delete_conn.configure(state="disabled")
            # Opcional: Limpar o formulário se clicar fora de um item
            # self._clear_form()
            logging.debug("Nenhum item selecionado na Treeview.")
            return

        selected_item_id_internal = selected_items[0] # ID interno do widget Treeview
        item_values = self.connection_tree.item(selected_item_id_internal, 'values')
        logging.debug(f"Item selecionado: ID interno={selected_item_id_internal}, Valores={item_values}")

        try:
            # Pega o ID REAL da conexão (primeiro valor na tupla 'values')
            connection_id_db = int(item_values[0])
            self.selected_connection_id = connection_id_db # Define o ID para o modo "update"
            logging.info(f"ID da conexão (do DB) selecionada: {self.selected_connection_id}")
            self._load_connection_data_to_form() # Carrega dados no formulário
            # Botão delete é habilitado dentro de _load_connection_data_to_form
        except (ValueError, IndexError, TypeError) as e:
            logging.error(f"Erro ao obter ID da conexão selecionada: {e}. Valores: {item_values}")
            self.selected_connection_id = None # Volta para o modo "criar" em caso de erro
            self.btn_delete_conn.configure(state="disabled")
            messagebox.showerror("Erro Interno", "Não foi possível identificar a conexão selecionada.")


    def _load_connection_data_to_form(self):
        """Carrega os dados da conexão selecionada (pelo ID do DB) no formulário."""
        if self.selected_connection_id is None:
            logging.warning("_load_connection_data_to_form chamado sem ID selecionado.")
            return

        logging.debug(f"Carregando dados para o ID: {self.selected_connection_id}")
        try:
            conn_data = self.db.connections.admin_get_connection_details(self.selected_connection_id)
        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar os detalhes da conexão:\n{e}"); return

        if not conn_data:
            messagebox.showerror("Erro", "Não foi possível encontrar os dados desta conexão (pode ter sido deletada).")
            self._clear_form(); self._load_all_connections(); return

        # Preenche o formulário (CORRIGIDO com 'or ""')
        self.lbl_form_title.configure(text=f"Editando Conexão: {conn_data.get('con_nome', 'N/A')}")
        self.entry_con_nome.delete(0, "end"); self.entry_con_nome.insert(0, conn_data.get('con_nome', '') or '')
        self.entry_con_ip.delete(0, "end"); self.entry_con_ip.insert(0, conn_data.get('con_ip', '') or '')
        self.entry_con_usuario.delete(0, "end"); self.entry_con_usuario.insert(0, conn_data.get('con_usuario', '') or '')
        self.entry_con_senha.delete(0, "end"); self.entry_con_senha.insert(0, conn_data.get('con_senha', '') or '')
        self.entry_con_particularidade.delete(0, "end"); self.entry_con_particularidade.insert(0, conn_data.get('con_particularidade', '') or '')
        self.entry_con_cliente.delete(0, "end"); self.entry_con_cliente.insert(0, conn_data.get('con_cliente', '') or '')
        self.entry_extra.delete(0, "end"); self.entry_extra.insert(0, conn_data.get('extra', '') or '') # <-- Linha corrigida

        conn_tipo = conn_data.get('con_tipo', 'RDP')
        if conn_tipo in self.connection_types: self.conn_type_var.set(conn_tipo)
        else: self.conn_type_var.set('RDP')

        selected_group_id = conn_data.get('gru_codigo')
        display_name_to_set = "(Nenhum grupo)"
        for display_name, group_id in self.group_map.items():
            if group_id == selected_group_id: display_name_to_set = display_name; break
        self.group_var.set(display_name_to_set)

        self.btn_delete_conn.configure(state="normal") # Habilita o botão deletar


    def _save_connection(self):
        """Salva as alterações (Criação ou Edição)."""
        # Coleta os dados do formulário
        data = {
            "con_nome": self.entry_con_nome.get().strip() or None,
            "con_ip": self.entry_con_ip.get().strip() or None,
            "con_usuario": self.entry_con_usuario.get().strip() or None,
            "con_senha": self.entry_con_senha.get().strip() or None,
            "con_particularidade": self.entry_con_particularidade.get().strip() or None,
            "con_cliente": self.entry_con_cliente.get().strip() or None,
            "extra": self.entry_extra.get().strip() or None,
            "gru_codigo": self.group_map.get(self.group_var.get()), # Pega o ID do grupo pelo nome no dropdown
            "con_tipo": self.conn_type_var.get()
        }
        # Validação básica
        if not data["con_nome"]: messagebox.showwarning("Campo Obrigatório", "O Nome da Conexão é obrigatório."); return
        if not data["con_ip"]: messagebox.showwarning("Campo Obrigatório", "O campo 'IP / Host / ID' é obrigatório."); return

        # --- LÓGICA DE CRIAR vs ATUALIZAR ---
        if self.selected_connection_id is None:
            # --- Modo CRIAR ---
            logging.info(f"Tentando CRIAR nova conexão: {data['con_nome']}")
            try:
                success, message = self.db.connections.admin_create_connection(data)
                if success:
                    messagebox.showinfo("Sucesso", f"Conexão '{data['con_nome']}' criada.")
                    self._load_all_connections() # Recarrega a lista
                    self._clear_form() # Limpa o formulário
                else: messagebox.showerror("Erro ao Criar", message)
            except Exception as e:
                logging.error(f"Erro inesperado ao criar conexão: {e}")
                messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")
        else:
            # --- Modo ATUALIZAR ---
            logging.info(f"Tentando ATUALIZAR conexão ID {self.selected_connection_id}: {data['con_nome']}")
            try:
                success, message = self.db.connections.admin_update_connection(self.selected_connection_id, data)
                if success:
                    messagebox.showinfo("Sucesso", f"Conexão '{data['con_nome']}' atualizada.")
                    self._load_all_connections() # Recarrega a lista
                    # Mantém os dados no formulário após a edição bem-sucedida
                else: messagebox.showerror("Erro ao Atualizar", message)
            except Exception as e:
                logging.error(f"Erro inesperado ao atualizar conexão: {e}")
                messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")

    def _delete_connection(self):
        """Deleta a conexão selecionada."""
        if self.selected_connection_id is None:
            messagebox.showwarning("Nenhuma Conexão", "Selecione uma conexão para deletar."); return
        conn_name = self.entry_con_nome.get() # Pega o nome do form para a mensagem
        if not messagebox.askyesno("Confirmar Deleção", f"Deletar a conexão '{conn_name}' (ID: {self.selected_connection_id})?"): return

        logging.info(f"Tentando DELETAR conexão ID {self.selected_connection_id}: {conn_name}")
        try:
            success, message = self.db.connections.admin_delete_connection(self.selected_connection_id)
            if success:
                messagebox.showinfo("Sucesso", f"Conexão '{conn_name}' deletada.")
                self._load_all_connections() # Recarrega a lista
                self._clear_form() # Limpa o formulário
            else: messagebox.showerror("Erro ao Deletar", message)
        except Exception as e:
            logging.error(f"Erro inesperado ao deletar conexão: {e}")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")