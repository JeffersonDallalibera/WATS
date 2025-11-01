# WATS_Project/wats_app/admin_panels/group_manager.py (COM FILTRO REUTILIZÁVEL)

import logging
from tkinter import messagebox
from typing import List, Optional, Tuple

import customtkinter as ctk

from ..db.db_service import DBService
from ..utils import create_group_filter_frame


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

        self.grid_columnconfigure(0, weight=1)  # Coluna da Treeview
        self.grid_columnconfigure(1, weight=2)  # Coluna do Formulário
        self.grid_rowconfigure(0, weight=1)

        # --- Coluna da Esquerda (Lista com Filtro Reutilizável) ---
        self.group_filter_frame = create_group_filter_frame(self)
        self.group_filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Label de loading (será removido após carregar)
        self.loading_label = ctk.CTkLabel(
            self.group_filter_frame,
            text="⏳ Carregando grupos...",
            font=("Segoe UI", 12, "italic"),
            text_color="gray"
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")

        # Adiciona botão de deletar ao frame do filtro
        self.btn_delete = ctk.CTkButton(
            self.group_filter_frame.filter_frame,
            text="Deletar",
            command=self._delete_group,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            width=80,
        )
        # Colocar no filter_frame (row=0) ao lado do botão limpar
        self.btn_delete.grid(row=0, column=2, padx=(10, 0), pady=5, sticky="e")
        self.btn_delete.configure(state="disabled")

        # Vincula callback de seleção
        self.group_filter_frame.bind_selection(self._on_group_select)

        # --- Coluna da Direita (Formulário de Edição) ---
        frame_right = ctk.CTkFrame(self, fg_color="transparent")
        frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        frame_right.grid_columnconfigure(0, weight=1)
        frame_right.grid_rowconfigure(5, weight=1)

        self.lbl_form_title = ctk.CTkLabel(
            frame_right, text="Selecione um grupo ou crie um novo", font=("Segoe UI", 14, "bold")
        )
        self.lbl_form_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(frame_right, text="Nome do Grupo:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.entry_group_name = ctk.CTkEntry(frame_right)
        self.entry_group_name.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(frame_right, text="Descrição (Opcional):").grid(
            row=3, column=0, padx=10, pady=5, sticky="w"
        )
        self.entry_group_desc = ctk.CTkEntry(frame_right, height=60)
        self.entry_group_desc.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        frame_actions = ctk.CTkFrame(frame_right, fg_color="transparent")
        frame_actions.grid(row=5, column=0, padx=10, pady=(20, 10), sticky="sew")
        frame_actions.grid_columnconfigure(0, weight=1)
        frame_actions.grid_columnconfigure(1, weight=1)
        self.btn_save = ctk.CTkButton(
            frame_actions, text="Salvar Alterações", height=40, command=self._save_group
        )
        self.btn_save.grid(row=0, column=1, padx=5, sticky="ew")
        self.btn_new = ctk.CTkButton(
            frame_actions, text="Novo Grupo", height=40, command=self._clear_form, fg_color="gray40"
        )
        self.btn_new.grid(row=0, column=0, padx=5, sticky="ew")

        # --- Inicialização Otimizada ---
        self._clear_form()  # Limpa form primeiro (instantâneo)
        
        self.transient(parent)
        self.update_idletasks()  # Força renderização da janela
        
        # Carrega dados em background
        self.after(50, self._load_initial_data)
        
    def _load_initial_data(self):
        """Carrega dados iniciais em background após a janela ser exibida."""
        try:
            self._load_all_groups()
            
            # Remove label de loading
            if hasattr(self, 'loading_label') and self.loading_label:
                self.loading_label.destroy()
                
        except Exception as e:
            logging.error(f"Erro ao carregar dados iniciais: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")
        finally:
            self.grab_set()  # Apenas agora torna modal

    def _load_all_groups(self, preserve_state=False):
        """
        Busca todos os grupos do banco e preenche o FilterableTreeFrame.

        Args:
            preserve_state (bool): Se True, preserva filtro e seleção atuais.
                                 Se False, carrega do zero (usado na inicialização).
        """
        try:
            self.all_groups = self.db.groups.admin_get_all_groups()
        except Exception as e:
            messagebox.showerror(
                "Erro de Banco de Dados", f"Não foi possível carregar os grupos:\n{e}"
            )
            self.all_groups = []

        # Converte para formato esperado pelo FilterableTreeFrame
        # Formato: (id, nome, descrição)
        groups_for_display = []
        for group in self.all_groups:
            group_id, nome = group[0], group[1]
            # Se houver descrição no banco, usa ela; senão, usa string vazia
            descricao = group[2] if len(group) > 2 else ""
            groups_for_display.append((group_id, nome, descricao))

        # Usa update_data para preservar estado ou set_data para carregamento inicial
        if preserve_state:
            self.group_filter_frame.update_data(groups_for_display)
        else:
            self.group_filter_frame.set_data(groups_for_display)

    def _clear_form(self):
        """Limpa o formulário para um novo cadastro."""
        self.lbl_form_title.configure(text="Criando Novo Grupo")
        self.selected_group_id = None  # Garante modo "criar"
        self.entry_group_name.delete(0, "end")
        self.entry_group_desc.delete(0, "end")
        self.btn_delete.configure(state="disabled")
        # Remove seleção do FilterableTreeFrame
        self.group_filter_frame.clear_selection()

    def _on_group_select(self, selected_item):
        """Chamado quando um grupo é selecionado no FilterableTreeFrame."""
        if not selected_item:
            self.selected_group_id = None
            self.btn_delete.configure(state="disabled")
            logging.debug("Nenhum grupo selecionado.")
            return

        try:
            # selected_item é uma tupla (id, nome, descrição)
            group_id_db = int(selected_item[0])
            self.selected_group_id = group_id_db  # Define ID para modo "update"
            self.btn_delete.configure(state="normal")
            logging.info(f"ID do grupo (do DB) selecionado: {self.selected_group_id}")
            self._load_group_data_to_form()  # Carrega dados
        except (ValueError, IndexError, TypeError) as e:
            logging.error(f"Erro ao obter ID do grupo selecionado: {e}. Item: {selected_item}")
            self.selected_group_id = None  # Volta para modo "criar"
            self.btn_delete.configure(state="disabled")
            messagebox.showerror(
                "Erro Interno", "Não foi possível identificar o grupo selecionado."
            )

    def _load_group_data_to_form(self):
        """Carrega os dados do grupo selecionado (pelo ID do DB) no formulário."""
        if self.selected_group_id is None:
            logging.warning("_load_group_data_to_form chamado sem ID selecionado.")
            return

        logging.debug(f"Carregando dados para o ID de grupo: {self.selected_group_id}")
        try:
            group_data = self.db.groups.admin_get_group_details(self.selected_group_id)
        except Exception as e:
            messagebox.showerror(
                "Erro de Banco de Dados", f"Não foi possível carregar o grupo:\n{e}"
            )
            return

        if not group_data:
            messagebox.showerror(
                "Erro", "Não foi possível encontrar os dados deste grupo (pode ter sido deletado)."
            )
            self._clear_form()
            self._load_all_groups()
            return

        # Preenche o formulário
        self.lbl_form_title.configure(text=f"Editando Grupo: {group_data.get('nome', 'N/A')}")
        self.entry_group_name.delete(0, "end")
        self.entry_group_name.insert(0, group_data.get("nome", "") or "")
        self.entry_group_desc.delete(0, "end")
        self.entry_group_desc.insert(0, group_data.get("desc", "") or "")
        self.btn_delete.configure(state="normal")  # Habilita deletar

    def _save_group(self):
        """Salva as alterações (Criação ou Edição)."""
        nome = self.entry_group_name.get().strip()
        desc = self.entry_group_desc.get().strip()
        if not nome:
            messagebox.showwarning("Campo Obrigatório", "O Nome do Grupo é obrigatório.")
            return

        # --- LÓGICA DE CRIAR vs ATUALIZAR ---
        if self.selected_group_id is None:
            # --- Modo CRIAR ---
            logging.info(f"Tentando CRIAR novo grupo: {nome}")
            try:
                success, message = self.db.groups.admin_create_group(nome, desc or None)
                if success:
                    messagebox.showinfo("Sucesso", f"Grupo '{nome}' criado com sucesso.")
                    self._load_all_groups(preserve_state=True)
                    self._clear_form()
                else:
                    messagebox.showerror("Erro ao Criar", message)
            except Exception as e:
                logging.error(f"Erro inesperado ao criar grupo: {e}")
                messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")
        else:
            # --- Modo ATUALIZAR ---
            logging.info(f"Tentando ATUALIZAR grupo ID {self.selected_group_id}: {nome}")
            try:
                success, message = self.db.groups.admin_update_group(
                    self.selected_group_id, nome, desc or None
                )
                if success:
                    messagebox.showinfo("Sucesso", f"Grupo '{nome}' atualizado com sucesso.")
                    self._load_all_groups(preserve_state=True)
                    # Mantém os dados no form após edição
                else:
                    messagebox.showerror("Erro ao Atualizar", message)
            except Exception as e:
                logging.error(f"Erro inesperado ao atualizar grupo: {e}")
                messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")

    def _delete_group(self):
        """Deleta o grupo selecionado."""
        if self.selected_group_id is None:
            messagebox.showwarning("Nenhum Grupo", "Selecione um grupo para deletar.")
            return
        group_name = self.entry_group_name.get()
        if not messagebox.askyesno(
            "Confirmar Deleção",
            f"Deletar o grupo '{group_name}' (ID: {self.selected_group_id})?\n\nAVISO: Pode falhar se o grupo estiver em uso.",
        ):
            return

        logging.info(f"Tentando DELETAR grupo ID {self.selected_group_id}: {group_name}")
        try:
            success, message = self.db.groups.admin_delete_group(self.selected_group_id)
            if success:
                messagebox.showinfo("Sucesso", f"Grupo '{group_name}' deletado.")
                self._load_all_groups(preserve_state=True)
                self._clear_form()
            else:
                messagebox.showerror("Erro ao Deletar", message)
        except Exception as e:
            logging.error(f"Erro inesperado ao deletar grupo: {e}")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")
