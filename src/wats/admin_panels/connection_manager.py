# WATS_Project/wats_app/admin_panels/connection_manager.py (COM FILTRO REUTILIZÁVEL)

import logging
from tkinter import messagebox
from typing import Dict, List, Optional, Tuple

import customtkinter as ctk

from ..db.db_service import DBService
from ..utils import create_connection_filter_frame

# Constante para o URL base da wiki
WIKI_BASE_URL = "https://sites.google.com/atslogistica.com/wikiats/clientes/"


class ManageConnectionDialog(ctk.CTkToplevel):
    """
    Janela para Criar, Editar e Deletar Conexões (Bases), usando Treeview para a lista.
    """

    def __init__(self, parent, db: DBService):
        super().__init__(parent)
        self.db = db
        self.all_connections: List[Tuple] = []
        self.group_map: Dict[str, Optional[int]] = {}  # Permite None como valor
        self.selected_connection_id: Optional[int] = None
        self.connection_types = ["RDP", "AnyDesk", "TeamViewer"]

        self.title("Gerenciar Conexões (Bases)")
        self.geometry("900x750")

        self.grid_columnconfigure(0, weight=1)  # Coluna da Treeview
        self.grid_columnconfigure(1, weight=2)  # Coluna do Formulário
        self.grid_rowconfigure(0, weight=1)

        # --- Coluna da Esquerda (Lista com Filtro Reutilizável) ---
        self.connection_filter_frame = create_connection_filter_frame(self)
        self.connection_filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Adiciona botão de deletar ao frame do filtro
        self.btn_delete_conn = ctk.CTkButton(
            self.connection_filter_frame.filter_frame,
            text="Deletar",
            command=self._delete_connection,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            width=80,
        )
        # Colocar no filter_frame (row=0) ao lado do botão limpar
        self.btn_delete_conn.grid(row=0, column=2, padx=(10, 0), pady=5, sticky="e")
        self.btn_delete_conn.configure(state="disabled")

        # Vincula callback de seleção
        self.connection_filter_frame.bind_selection(self._on_connection_select)

        # --- Coluna da Direita (Formulário de Edição) ---
        frame_right = ctk.CTkFrame(self, fg_color="transparent")
        frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        frame_right.grid_columnconfigure(1, weight=1)
        frame_right.grid_rowconfigure(10, weight=1)

        self.lbl_form_title = ctk.CTkLabel(
            frame_right, text="Selecione ou crie uma conexão", font=("Segoe UI", 14, "bold")
        )
        self.lbl_form_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        fields = [
            ("Nome da Conexão:", "entry_con_nome", 1),
            ("Grupo:", "option_menu_group", 2),
            ("Tipo:", "option_menu_tipo", 3),
            ("IP / Host / ID:", "entry_con_ip", 4),
            ("Usuário RDP/Acesso:", "entry_con_usuario", 5),
            ("Senha RDP/Acesso:", "entry_con_senha", 6),
            ("Particularidades (Nome-chave|Nome2-chave2):", "entry_con_particularidade", 7),
            ("Cliente (Nome Fantasia):", "entry_con_cliente", 8),
            ("Extra (Opcional):", "entry_extra", 9),
        ]
        self.group_var = ctk.StringVar(value="Selecione...")
        self.conn_type_var = ctk.StringVar(value=self.connection_types[0])

        for label, widget_name, row_num in fields:
            ctk.CTkLabel(frame_right, text=label).grid(
                row=row_num, column=0, padx=10, pady=5, sticky="w"
            )
            if widget_name == "option_menu_group":
                self.option_menu_group = ctk.CTkOptionMenu(
                    frame_right, variable=self.group_var, values=["Carregando..."]
                )
                self.option_menu_group.grid(row=row_num, column=1, padx=10, pady=5, sticky="ew")
            elif widget_name == "option_menu_tipo":
                self.option_menu_tipo = ctk.CTkOptionMenu(
                    frame_right, variable=self.conn_type_var, values=self.connection_types
                )
                self.option_menu_tipo.grid(row=row_num, column=1, padx=10, pady=5, sticky="ew")
            elif widget_name == "entry_con_particularidade":
                # Frame para o campo de particularidade com botão de gerar link
                particularidade_frame = ctk.CTkFrame(frame_right, fg_color="transparent")
                particularidade_frame.grid(row=row_num, column=1, padx=10, pady=5, sticky="ew")
                particularidade_frame.grid_columnconfigure(0, weight=1)

                entry = ctk.CTkEntry(particularidade_frame)
                entry.grid(row=0, column=0, sticky="ew")
                setattr(self, widget_name, entry)

                # Botão para gerar link da wiki
                btn_gerar_wiki = ctk.CTkButton(
                    particularidade_frame,
                    text="🔗 Gerar Link Wiki",
                    width=120,
                    height=32,
                    command=self._gerar_link_wiki,
                )
                btn_gerar_wiki.grid(row=0, column=1, padx=(5, 0), sticky="e")

                # Botão de ajuda para formato
                btn_ajuda = ctk.CTkButton(
                    particularidade_frame,
                    text="❓",
                    width=30,
                    height=32,
                    command=self._mostrar_ajuda_formato,
                )
                btn_ajuda.grid(row=0, column=2, padx=(5, 0), sticky="e")
            else:
                entry = ctk.CTkEntry(frame_right)
                entry.grid(row=row_num, column=1, padx=10, pady=5, sticky="ew")
                setattr(self, widget_name, entry)
                if widget_name == "entry_con_senha":
                    entry.configure(show="*")

        frame_actions = ctk.CTkFrame(frame_right, fg_color="transparent")
        frame_actions.grid(row=10, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="sew")
        frame_actions.grid_columnconfigure(0, weight=1)
        frame_actions.grid_columnconfigure(1, weight=1)
        self.btn_save = ctk.CTkButton(
            frame_actions, text="Salvar Alterações", height=40, command=self._save_connection
        )
        self.btn_save.grid(row=0, column=1, padx=5, sticky="ew")
        self.btn_new = ctk.CTkButton(
            frame_actions,
            text="Nova Conexão",
            height=40,
            command=self._clear_form,
            fg_color="gray40",
        )
        self.btn_new.grid(row=0, column=0, padx=5, sticky="ew")

        # --- Inicialização ---
        self._load_all_connections()
        self._load_groups_for_dropdown()
        self._clear_form()

        self.transient(parent)
        self.grab_set()

    def _gerar_link_wiki(self):
        """Gera o link da wiki automaticamente baseado na chave do cliente."""
        cliente = self.entry_con_cliente.get().strip()

        if not cliente:
            messagebox.showwarning(
                "Campo Obrigatório",
                "Por favor, preencha o campo 'Cliente (Nome Fantasia)' antes de gerar o link da wiki.",
            )
            return

        # Remove espaços e caracteres especiais para criar uma chave válida para URL
        # Mantém apenas letras, números e converte para minúsculas
        import re

        chave_cliente = re.sub(r"[^a-zA-Z0-9]", "", cliente.lower())

        if not chave_cliente:
            messagebox.showwarning(
                "Nome Inválido", "O nome do cliente deve conter pelo menos uma letra ou número."
            )
            return

        # Gera o link no formato simplificado: "Nome_Cliente-chave_wiki"
        # O usuário não vê o URL base, apenas a parte final
        link_simplificado = f"{cliente}-{chave_cliente}"

        # Preenche o campo de particularidade
        self.entry_con_particularidade.delete(0, "end")
        self.entry_con_particularidade.insert(0, link_simplificado)

        messagebox.showinfo(
            "Link Gerado",
            "Link da wiki gerado com sucesso!\n\n"
            f"Formato no campo: {cliente}-{chave_cliente}\n"
            f"URL completa: {WIKI_BASE_URL}{chave_cliente}\n\n"
            "💡 Dica: Para múltiplos clientes use '|' como separador:\n"
            "Cliente1-chave1|Cliente2-chave2\n\n"
            "Para clientes sem wiki use ';':\n"
            "Cliente1;Cliente2",
        )

    def _mostrar_ajuda_formato(self):
        """Mostra ajuda sobre o formato do campo de particularidades."""
        ajuda_text = """FORMATO DO CAMPO PARTICULARIDADES

📋 OPÇÕES DISPONÍVEIS:

1️⃣ COM WIKI (usando hífen '-'):
   • Um cliente: Nome-chave
   • Múltiplos: Nome1-chave1|Nome2-chave2

   Exemplo:
   Empresa ABC-empresaabc|XYZ Corp-xyzcorp

2️⃣ SEM WIKI (usando ponto e vírgula ';'):
   • Um cliente: Nome
   • Múltiplos: Nome1;Nome2;Nome3

   Exemplo:
   Empresa ABC;XYZ Corp;Outra Empresa

3️⃣ GERAÇÃO AUTOMÁTICA:
   • Preencha "Cliente (Nome Fantasia)"
   • Clique em "🔗 Gerar Link Wiki"
   • Sistema cria automaticamente no formato Nome-chave

🌐 URL BASE FIXA (oculta do usuário):
   https://sites.google.com/atslogistica.com/wikiats/clientes/

📝 IMPORTANTE:
   • Para links de wiki, SEMPRE use hífen '-'
   • Para múltiplos clientes com wiki, use pipe '|'
   • Para clientes sem wiki, use ponto e vírgula ';'
   • Não misture formatos diferentes no mesmo campo"""

        messagebox.showinfo("Ajuda - Formato de Particularidades", ajuda_text)

    def _validar_formato_particularidades(self, particularidade_str: str) -> Tuple[bool, str]:
        """
        Valida o formato do campo de particularidades.

        Formatos válidos:
        - Com wiki: "Nome1-chave1|Nome2-chave2"
        - Sem wiki: "Nome1;Nome2"

        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        if not particularidade_str or particularidade_str.strip() == "":
            return True, ""  # Campo opcional

        particularidade_str = particularidade_str.strip()

        # Verifica se é formato sem wiki (só com ;)
        if ";" in particularidade_str and "-" not in particularidade_str:
            # Formato sem wiki é sempre válido se tem conteúdo
            partes = particularidade_str.split(";")
            for parte in partes:
                if not parte.strip():
                    return (
                        False,
                        "Formato inválido: nomes vazios não são permitidos.\nFormato sem wiki: 'Nome1;Nome2'",
                    )
            return True, ""

        # Verifica formato com wiki
        if "|" in particularidade_str or "-" in particularidade_str:
            entradas = particularidade_str.split("|")
            for entrada in entradas:
                entrada = entrada.strip()
                if not entrada:
                    return False, "Formato inválido: entradas vazias não são permitidas."

                if "-" not in entrada:
                    return (
                        False,
                        f"Formato inválido: '{entrada}' deve conter '-' para separar nome da chave da wiki.\nFormato correto: 'Nome-chave'",
                    )

                partes = entrada.split("-", 1)
                if len(partes) != 2 or not partes[0].strip() or not partes[1].strip():
                    return (
                        False,
                        f"Formato inválido: '{entrada}' deve ter nome e chave separados por '-'.\nFormato correto: 'Nome-chave'",
                    )

            return True, ""

        # Se chegou até aqui, é texto simples sem separadores especiais
        return True, ""

    def _load_groups_for_dropdown(self):
        """Busca os grupos e popula o OptionMenu."""
        self.group_map.clear()
        try:
            all_groups = self.db.groups.admin_get_all_groups()
        except Exception as e:
            messagebox.showerror(
                "Erro de Banco de Dados", f"Não foi possível carregar os grupos:\n{e}"
            )
            all_groups = []

        if not all_groups:
            self.option_menu_group.configure(values=["Nenhum grupo"], state="disabled")
            self.group_var.set("Nenhum grupo")
            return

        group_names_list = ["(Nenhum grupo)"]
        self.group_map["(Nenhum grupo)"] = None
        for group_id, group_name in all_groups:
            display_name = f"{group_name} (ID: {group_id})"
            self.group_map[display_name] = group_id
            group_names_list.append(display_name)
        self.option_menu_group.configure(values=group_names_list, state="normal")
        self.group_var.set(group_names_list[0])  # Define "(Nenhum grupo)" como padrão inicial

    def _load_all_connections(self, preserve_state=False):
        """Busca todas as conexões do banco e preenche o FilterableTreeFrame."""
        try:
            self.all_connections = self.db.connections.admin_get_all_connections()
        except Exception as e:
            messagebox.showerror(
                "Erro de Banco de Dados", f"Não foi possível carregar as conexões:\n{e}"
            )
            self.all_connections = []

        # Converte para formato esperado pelo FilterableTreeFrame
        # Formato: (id, nome, host, porta)
        connections_for_display = []
        for conn in self.all_connections:
            conn_id, conn_nome = conn[0], conn[1]
            # Busca IP/Host e Porta (assumindo que estão nas colunas corretas)
            conn_ip = conn[4] if len(conn) > 4 else ""  # IP/Host
            conn_porta = conn[5] if len(conn) > 5 else "3389"  # Porta padrão RDP
            connections_for_display.append((conn_id, conn_nome, conn_ip, conn_porta))

        if preserve_state:
            self.connection_filter_frame.update_data(connections_for_display)
        else:
            self.connection_filter_frame.set_data(connections_for_display)

    def _clear_form(self):
        """Limpa o formulário para um novo cadastro."""
        self.lbl_form_title.configure(text="Criando Nova Conexão")
        self.selected_connection_id = None  # Garante que estamos no modo "criar"
        self.entry_con_nome.delete(0, "end")
        self.entry_con_ip.delete(0, "end")
        self.entry_con_usuario.delete(0, "end")
        self.entry_con_senha.delete(0, "end")
        self.entry_con_particularidade.delete(0, "end")
        self.entry_con_cliente.delete(0, "end")
        self.entry_extra.delete(0, "end")
        self.group_var.set("(Nenhum grupo)")
        self.conn_type_var.set("RDP")
        self.btn_delete_conn.configure(state="disabled")
        # Remove seleção do FilterableTreeFrame
        self.connection_filter_frame.clear_selection()

    def _on_connection_select(self, event):
        """Chamado quando uma conexão é selecionada no FilterableTreeFrame."""
        # Obter item selecionado do TreeView
        selection = self.connection_filter_frame.tree.selection()
        if not selection:
            self.selected_connection_id = None
            self.btn_delete_conn.configure(state="disabled")
            logging.debug("Nenhuma conexão selecionada.")
            return

        try:
            # Obter os valores do item selecionado
            selected_item = self.connection_filter_frame.tree.item(selection[0])["values"]
            if not selected_item:
                self.selected_connection_id = None
                self.btn_delete_conn.configure(state="disabled")
                return

            # selected_item é uma tupla (id, nome, host, porta)
            connection_id_db = int(selected_item[0])
            self.selected_connection_id = connection_id_db  # Define ID para modo "update"
            self.btn_delete_conn.configure(state="normal")
            logging.info(f"ID da conexão (do DB) selecionada: {self.selected_connection_id}")
            self._load_connection_data_to_form()  # Carrega dados
        except (ValueError, IndexError, TypeError) as e:
            logging.error(
                f"Erro ao obter ID da conexão selecionada: {e}. Item: {selected_item if 'selected_item' in locals() else 'N/A'}"
            )
            self.selected_connection_id = None  # Volta para modo "criar"
            self.btn_delete_conn.configure(state="disabled")
            messagebox.showerror(
                "Erro Interno", "Não foi possível identificar a conexão selecionada."
            )
            self._load_connection_data_to_form()  # Carrega dados no formulário
            # Botão delete é habilitado dentro de _load_connection_data_to_form
        except Exception as e:
            logging.error(f"Erro inesperado ao processar seleção: {e}")
            self.selected_connection_id = None  # Volta para o modo "criar" em caso de erro
            self.btn_delete_conn.configure(state="disabled")

    def _load_connection_data_to_form(self):
        """Carrega os dados da conexão selecionada (pelo ID do DB) no formulário."""
        if self.selected_connection_id is None:
            logging.warning("_load_connection_data_to_form chamado sem ID selecionado.")
            return

        logging.debug(f"Carregando dados para o ID: {self.selected_connection_id}")
        try:
            conn_data = self.db.connections.admin_get_connection_details(
                self.selected_connection_id
            )
        except Exception as e:
            messagebox.showerror(
                "Erro de Banco de Dados", f"Não foi possível carregar os detalhes da conexão:\n{e}"
            )
            return

        if not conn_data:
            messagebox.showerror(
                "Erro",
                "Não foi possível encontrar os dados desta conexão (pode ter sido deletada).",
            )
            self._clear_form()
            self._load_all_connections()
            return

        # Preenche o formulário (CORRIGIDO com 'or ""')
        self.lbl_form_title.configure(text=f"Editando Conexão: {conn_data.get('con_nome', 'N/A')}")
        self.entry_con_nome.delete(0, "end")
        self.entry_con_nome.insert(0, conn_data.get("con_nome", "") or "")
        self.entry_con_ip.delete(0, "end")
        self.entry_con_ip.insert(0, conn_data.get("con_ip", "") or "")
        self.entry_con_usuario.delete(0, "end")
        self.entry_con_usuario.insert(0, conn_data.get("con_usuario", "") or "")
        self.entry_con_senha.delete(0, "end")
        self.entry_con_senha.insert(0, conn_data.get("con_senha", "") or "")
        self.entry_con_particularidade.delete(0, "end")
        self.entry_con_particularidade.insert(0, conn_data.get("con_particularidade", "") or "")
        self.entry_con_cliente.delete(0, "end")
        self.entry_con_cliente.insert(0, conn_data.get("con_cliente", "") or "")
        self.entry_extra.delete(0, "end")
        self.entry_extra.insert(0, conn_data.get("extra", "") or "")  # <-- Linha corrigida

        conn_tipo = conn_data.get("con_tipo", "RDP")
        if conn_tipo in self.connection_types:
            self.conn_type_var.set(conn_tipo)
        else:
            self.conn_type_var.set("RDP")

        selected_group_id = conn_data.get("gru_codigo")
        display_name_to_set = "(Nenhum grupo)"
        for display_name, group_id in self.group_map.items():
            if group_id == selected_group_id:
                display_name_to_set = display_name
                break
        self.group_var.set(display_name_to_set)

        self.btn_delete_conn.configure(state="normal")  # Habilita o botão deletar

    def _save_connection(self):
        """Salva as alterações (Criação ou Edição)."""
        # Coleta os dados do formulário
        particularidade = self.entry_con_particularidade.get().strip() or None

        # Valida o formato das particularidades
        if particularidade:
            valido, erro = self._validar_formato_particularidades(particularidade)
            if not valido:
                messagebox.showwarning("Formato Inválido", erro)
                return

        data = {
            "con_nome": self.entry_con_nome.get().strip() or None,
            "con_ip": self.entry_con_ip.get().strip() or None,
            "con_usuario": self.entry_con_usuario.get().strip() or None,
            "con_senha": self.entry_con_senha.get().strip() or None,
            "con_particularidade": particularidade,
            "con_cliente": self.entry_con_cliente.get().strip() or None,
            "extra": self.entry_extra.get().strip() or None,
            "gru_codigo": self.group_map.get(
                self.group_var.get()
            ),  # Pega o ID do grupo pelo nome no dropdown
            "con_tipo": self.conn_type_var.get(),
        }
        # Validação básica
        if not data["con_nome"]:
            messagebox.showwarning("Campo Obrigatório", "O Nome da Conexão é obrigatório.")
            return
        if not data["con_ip"]:
            messagebox.showwarning("Campo Obrigatório", "O campo 'IP / Host / ID' é obrigatório.")
            return

        # --- LÓGICA DE CRIAR vs ATUALIZAR ---
        if self.selected_connection_id is None:
            # --- Modo CRIAR ---
            logging.info(f"Tentando CRIAR nova conexão: {data['con_nome']}")
            try:
                success, message = self.db.connections.admin_create_connection(data)
                if success:
                    messagebox.showinfo("Sucesso", f"Conexão '{data['con_nome']}' criada.")
                    self._load_all_connections(preserve_state=True)  # Recarrega a lista
                    self._clear_form()  # Limpa o formulário
                else:
                    messagebox.showerror("Erro ao Criar", message)
            except Exception as e:
                logging.error(f"Erro inesperado ao criar conexão: {e}")
                messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")
        else:
            # --- Modo ATUALIZAR ---
            logging.info(
                f"Tentando ATUALIZAR conexão ID {self.selected_connection_id}: {data['con_nome']}"
            )
            try:
                success, message = self.db.connections.admin_update_connection(
                    self.selected_connection_id, data
                )
                if success:
                    messagebox.showinfo("Sucesso", f"Conexão '{data['con_nome']}' atualizada.")
                    self._load_all_connections(preserve_state=True)  # Recarrega a lista
                    # Mantém os dados no formulário após a edição bem-sucedida
                else:
                    messagebox.showerror("Erro ao Atualizar", message)
            except Exception as e:
                logging.error(f"Erro inesperado ao atualizar conexão: {e}")
                messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")

    def _delete_connection(self):
        """Deleta a conexão selecionada."""
        if self.selected_connection_id is None:
            messagebox.showwarning("Nenhuma Conexão", "Selecione uma conexão para deletar.")
            return
        conn_name = self.entry_con_nome.get()  # Pega o nome do form para a mensagem
        if not messagebox.askyesno(
            "Confirmar Deleção",
            f"Deletar a conexão '{conn_name}' (ID: {self.selected_connection_id})?",
        ):
            return

        logging.info(f"Tentando DELETAR conexão ID {self.selected_connection_id}: {conn_name}")
        try:
            success, message = self.db.connections.admin_delete_connection(
                self.selected_connection_id
            )
            if success:
                messagebox.showinfo("Sucesso", f"Conexão '{conn_name}' deletada.")
                self._load_all_connections(preserve_state=True)  # Recarrega a lista
                self._clear_form()  # Limpa o formulário
            else:
                messagebox.showerror("Erro ao Deletar", message)
        except Exception as e:
            logging.error(f"Erro inesperado ao deletar conexão: {e}")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{e}")
