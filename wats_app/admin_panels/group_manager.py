# WATS_Project/wats_app/admin_panels/group_manager.py (COM TREEVIEW)

import customtkinter as ctk
import logging
from tkinter import messagebox, ttk # Importa ttk
from typing import List, Optional, Tuple, Dict
from ..db.db_service import DBService

class ManageGroupDialog(ctk.CTkToplevel):
    """
    Janela para Criar, Editar e Deletar Grupos, usando Treeview para a lista.
    """
    def __init__(self, parent, db: DBService):
        super().__init__(parent)
        self.db = db
        self.all_groups: List[Tuple] = []
        self.selected_group_id: Optional[int] = None

        self.title("Gerenciar Grupos de Conexão")
        self.geometry("700x450")

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

        lbl_groups = ctk.CTkLabel(frame_left_header, text="Grupos", font=("Segoe UI", 14, "bold"))
        lbl_groups.grid(row=0, column=0, sticky="w")

        self.btn_delete = ctk.CTkButton(frame_left_header, text="Deletar Selecionado",
                                        command=self._delete_group,
                                        fg_color="#D32F2F", hover_color="#B71C1C",
                                        width=150)
        self.btn_delete.grid(row=0, column=1, padx=(10,0), sticky="e")
        self.btn_delete.configure(state="disabled")

        # --- ttk.Treeview ---
        self.style = ttk.Style(self)
        self._apply_treeview_theme()

        tree_columns = ('id', 'nome')
        self.group_tree = ttk.Treeview(
            frame_left,
            columns=tree_columns,
            displaycolumns=('nome',), # Mostra só o nome, ID fica oculto
            show='headings',
            selectmode='browse',
            style="Admin.Treeview"
        )
        self.group_tree.grid(row=1, column=0, padx=(10,0), pady=10, sticky="nsew")

        # Configura as colunas
        self.group_tree.heading('nome', text='Nome do Grupo', anchor='w')
        self.group_tree.column('nome', anchor='w', stretch=True) # Usa todo o espaço

        # Scrollbar
        tree_scrollbar = ctk.CTkScrollbar(frame_left, command=self.group_tree.yview)
        tree_scrollbar.grid(row=1, column=1, padx=(0,10), pady=10, sticky="ns")
        self.group_tree.configure(yscrollcommand=tree_scrollbar.set)

        # Evento de seleção
        self.group_tree.bind('<<TreeviewSelect>>', self._on_group_select)
        # --- FIM Treeview ---

        # --- Coluna da Direita (Formulário de Edição - Sem Mudanças) ---
        frame_right = ctk.CTkFrame(self, fg_color="transparent")
        frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        frame_right.grid_columnconfigure(0, weight=1)
        frame_right.grid_rowconfigure(5, weight=1)

        self.lbl_form_title = ctk.CTkLabel(frame_right, text="Selecione um grupo ou crie um novo", font=("Segoe UI", 14, "bold"))
        self.lbl_form_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(frame_right, text="Nome do Grupo:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_group_name = ctk.CTkEntry(frame_right)
        self.entry_group_name.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(frame_right, text="Descrição (Opcional):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_group_desc = ctk.CTkEntry(frame_right, height=60)
        self.entry_group_desc.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        frame_actions = ctk.CTkFrame(frame_right, fg_color="transparent")
        frame_actions.grid(row=5, column=0, padx=10, pady=(20, 10), sticky="sew")
        frame_actions.grid_columnconfigure(0, weight=1); frame_actions.grid_columnconfigure(1, weight=1)
        self.btn_save = ctk.CTkButton(frame_actions, text="Salvar Alterações", height=40, command=self._save_group)
        self.btn_save.grid(row=0, column=1, padx=5, sticky="ew")
        self.btn_new = ctk.CTkButton(frame_actions, text="Novo Grupo", height=40, command=self._clear_form, fg_color="gray40")
        self.btn_new.grid(row=0, column=0, padx=5, sticky="ew")

        # --- Inicialização ---
        self._load_all_groups()
        self._clear_form()

        self.transient(parent)
        self.grab_set()

    def _apply_treeview_theme(self):
        """Aplica o tema claro/escuro ao ttk.Treeview."""
        mode = ctk.get_appearance_mode()
        if mode == "Dark": colors = ("#E0E0E0", "#2B2B2B", "#3C3F41", "#1F6AA5", "#2B2B2B")
        else: colors = ("#1E1E1E", "#FFFFFF", "#F0F0F0", "#0078D7", "#FFFFFF")
        text_color, bg_color, heading_bg, selected_color, field_bg = colors
        style_name = "Admin.Treeview" # Usa o mesmo estilo do connection_manager
        self.style.configure(style_name, background=bg_color, foreground=text_color, fieldbackground=field_bg, rowheight=25, font=("Segoe UI", 10), borderwidth=0, relief="flat")
        self.style.configure(f"{style_name}.Heading", background=heading_bg, foreground=text_color, font=("Segoe UI", 10, 'bold'), borderwidth=0, relief="flat")
        self.style.map(style_name, background=[('selected', selected_color)], foreground=[('selected', 'white')])


    def _load_all_groups(self):
        """Busca todos os grupos do banco e preenche a Treeview."""
        for item in self.group_tree.get_children(): self.group_tree.delete(item)
        try:
            self.all_groups = self.db.groups.admin_get_all_groups()
        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar os grupos:\n{e}"); self.all_groups = []
        if not self.all_groups: return

        for group in self.all_groups:
            group_id, nome = group[0], group[1]
            # Insere com os valores ('id', 'nome')
            self.group_tree.insert('', 'end', values=(group_id, nome))

    def _clear_form(self):
        """Limpa o formulário para um novo cadastro."""
        self.lbl_form_title.configure(text="Criando Novo Grupo")
        self.selected_group_id = None # Garante modo "criar"
        self.entry_group_name.delete(0, "end")
        self.entry_group_desc.delete(0, "end")
        self.btn_delete.configure(state="disabled")
        selection = self.group_tree.selection() # Pega seleção
        if selection: self.group_tree.selection_remove(selection) # Remove highlight

    def _on_group_select(self, event=None):
        """Chamado quando um grupo é selecionado na Treeview."""
        selected_items = self.group_tree.selection()
        if not selected_items:
            self.selected_group_id = None
            self.btn_delete.configure(state="disabled")
            logging.debug("Nenhum grupo selecionado.")
            return

        selected_item_id_internal = selected_items[0]
        item_values = self.group_tree.item(selected_item_id_internal, 'values')
        logging.debug(f"Grupo selecionado: ID interno={selected_item_id_internal}, Valores={item_values}")

        try:
            # Pega o ID REAL do grupo (primeiro valor)
            group_id_db = int(item_values[0])
            self.selected_group_id = group_id_db # Define ID para modo "update"
            logging.info(f"ID do grupo (do DB) selecionado: {self.selected_group_id}")
            self._load_group_data_to_form() # Carrega dados
        except (ValueError, IndexError, TypeError) as e:
            logging.error(f"Erro ao obter ID do grupo selecionado: {e}. Valores: {item_values}")
            self.selected_group_id = None # Volta para modo "criar"
            self.btn_delete.configure(state="disabled")
            messagebox.showerror("Erro Interno", "Não foi possível identificar o grupo selecionado.")


    def _load_group_data_to_form(self):
        """Carrega os dados do grupo selecionado (pelo ID do DB) no formulário."""
        if self.selected_group_id is None:
            logging.warning("_load_group_data_to_form chamado sem ID selecionado.")
            return

        logging.debug(f"Carregando dados para o ID de grupo: {self.selected_group_id}")
        try:
            group_data = self.db.groups.admin_get_group_details(self.selected_group_id)
        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar o grupo:\n{e}"); return

        if not group_data:
            messagebox.showerror("Erro", "Não foi possível encontrar os dados deste grupo (pode ter sido deletado).")
            self._clear_form(); self._load_all_groups(); return

        # Preenche o formulário
        self.lbl_form_title.configure(text=f"Editando Grupo: {group_data.get('nome', 'N/A')}")
        self.entry_group_name.delete(0, "end"); self.entry_group_name.insert(0, group_data.get('nome', '') or '')
        self.entry_group_desc.delete(0, "end"); self.entry_group_desc.insert(0, group_data.get('desc', '') or '')
        self.btn_delete.configure(state="normal") # Habilita deletar


    def _save_group(self):
        """Salva as alterações (Criação ou Edição)."""
        nome = self.entry_group_name.get().strip()
        desc = self.entry_group_desc.get().strip()
        if not nome: messagebox.showwarning("Campo Obrigatório", "O Nome do Grupo é obrigatório."); return

        # --- LÓGICA DE CRIAR vs ATUALIZAR ---
        if self.selected_group_id is None:
            # --- Modo CRIAR ---
            logging.info(f"Tentando CRIAR novo grupo: {nome}")
            try:
                success, message = self.db.groups.admin_create_group(nome, desc or None)
                if success:
                    messagebox.showinfo("Sucesso", f"Grupo '{nome}' criado com sucesso.")
                    self._load_all_groups()
                    self._clear_form()
                else: messagebox.showerror("Erro ao Criar", message)
            except Exception as e:
                logging.error(f"Erro inesperado ao criar grupo: {e}"); messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")
        else:
            # --- Modo ATUALIZAR ---
            logging.info(f"Tentando ATUALIZAR grupo ID {self.selected_group_id}: {nome}")
            try:
                success, message = self.db.groups.admin_update_group(self.selected_group_id, nome, desc or None)
                if success:
                    messagebox.showinfo("Sucesso", f"Grupo '{nome}' atualizado com sucesso.")
                    self._load_all_groups()
                    # Mantém os dados no form após edição
                else: messagebox.showerror("Erro ao Atualizar", message)
            except Exception as e:
                logging.error(f"Erro inesperado ao atualizar grupo: {e}"); messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")

    def _delete_group(self):
        """Deleta o grupo selecionado."""
        if self.selected_group_id is None: messagebox.showwarning("Nenhum Grupo", "Selecione um grupo para deletar."); return
        group_name = self.entry_group_name.get()
        if not messagebox.askyesno("Confirmar Deleção", f"Deletar o grupo '{group_name}' (ID: {self.selected_group_id})?\n\nAVISO: Pode falhar se o grupo estiver em uso."): return

        logging.info(f"Tentando DELETAR grupo ID {self.selected_group_id}: {group_name}")
        try:
            success, message = self.db.groups.admin_delete_group(self.selected_group_id)
            if success:
                messagebox.showinfo("Sucesso", f"Grupo '{group_name}' deletado.")
                self._load_all_groups()
                self._clear_form()
            else: messagebox.showerror("Erro ao Deletar", message)
        except Exception as e:
            logging.error(f"Erro inesperado ao deletar grupo: {e}"); messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")