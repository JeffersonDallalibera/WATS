import hashlib
import logging
from tkinter import ttk
from typing import Any, Callable, List, Optional, Tuple

import customtkinter as ctk

# Constante para o URL base da wiki
WIKI_BASE_URL = "https://sites.google.com/atslogistica.com/wikiats/clientes/"


def parse_particularities(particularidade_str: str) -> List[Tuple[str, str]]:
    """
    Parse o campo de particularidades com múltiplos clientes.

    Formato esperado:
    - Com wiki: "Nome1-chave_wiki1|Nome2-chave_wiki2"
    - Sem wiki: "Nome1;Nome2"

    Args:
        particularidade_str: String com formato "Nome1-chave1|Nome2-chave2" ou "Nome1;Nome2"

    Returns:
        Lista de tuplas (nome_cliente, url_cliente_completa_ou_vazia)

    Examples:
        >>> parse_particularities("Cliente A-clientea|Cliente B-clienteb")
        [('Cliente A', 'https://sites.google.com/atslogistica.com/wikiats/clientes/clientea'),
         ('Cliente B', 'https://sites.google.com/atslogistica.com/wikiats/clientes/clienteb')]
        >>> parse_particularities("Cliente A;Cliente B")
        [('Cliente A', ''), ('Cliente B', '')]
    """
    if not particularidade_str or particularidade_str.strip() == "":
        return []

    # logging.info(f"Parsing particularidades: '{particularidade_str}'")
    clients = []

    # Primeiro verifica se é formato sem wiki (separado por ;)
    if ";" in particularidade_str and "-" not in particularidade_str:
        # Formato sem wiki: "Nome1;Nome2"
        client_entries = particularidade_str.split(";")
        for entry in client_entries:
            entry = entry.strip()
            if entry:
                clients.append((entry, ""))  # Nome sem URL
    else:
        # Formato com wiki: "Nome1-chave1|Nome2-chave2"
        client_entries = particularidade_str.split("|")

        for idx, entry in enumerate(client_entries, 1):
            entry = entry.strip()

            if "-" in entry:
                parts = entry.split("-", 1)
                if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                    nome_cliente = parts[0].strip()
                    chave_wiki = parts[1].strip()
                    # Constrói URL completa com base fixa
                    url_completa = f"{WIKI_BASE_URL}{chave_wiki}"
                    clients.append((nome_cliente, url_completa))
                else:
                    # Se não tem chave válida, adiciona sem URL
                    nome_cliente = parts[0].strip() if parts[0].strip() else f"Cliente {idx}"
                    clients.append((nome_cliente, ""))
            else:
                # Entry sem '-', adiciona como nome sem URL
                if entry:
                    clients.append((entry, ""))

    # logging.info(f"Total de clientes parseados: {len(clients)}")
    return clients


def hash_password_md5(password: str) -> str:
    """
    Gera um hash MD5 para a senha fornecida.

    Args:
        password: Senha em texto plano

    Returns:
        Hash MD5 da senha em formato hexadecimal

    Note:
        MD5 é usado para compatibilidade com sistema legado.
        Para novos projetos, recomenda-se bcrypt ou Argon2.
    """
    return hashlib.md5(password.encode()).hexdigest()


class FilterableTreeFrame(ctk.CTkFrame):
    """
    Frame reutilizável que combina campo de filtro com TreeView.

    Permite busca em tempo real nos painéis administrativos com as seguintes funcionalidades:
    - Campo de busca com placeholder
    - Filtro em tempo real conforme o usuário digita
    - Preservação do estado do filtro durante atualizações
    - Suporte a seleção de itens
    - Callback customizável para eventos de seleção

    Attributes:
        treeview: Componente TreeView do tkinter
        search_entry: Campo de entrada para filtro
        filter_text: Texto atual do filtro

    Examples:
        >>> frame = FilterableTreeFrame(parent, ["ID", "Nome"], on_select=callback)
        >>> frame.set_data([(1, "Item 1"), (2, "Item 2")])
    """

    def __init__(
        self,
        parent,
        placeholder_text: str = "🔍 Buscar...",
        tree_columns: tuple = (),
        display_columns: tuple = (),
        column_configs: dict = None,
        **kwargs,
    ):
        """
        Inicializa o frame com filtro e TreeView.

        Args:
            parent: Widget pai
            placeholder_text: Texto do placeholder do campo de busca
            tree_columns: Colunas do TreeView (incluindo IDs ocultos)
            display_columns: Colunas visíveis no TreeView
            column_configs: Configuração das colunas {coluna: {config}}
        """
        super().__init__(parent, **kwargs)

        self.placeholder_text = placeholder_text
        self.tree_columns = tree_columns
        self.display_columns = display_columns
        self.column_configs = column_configs or {}

        # Dados e filtro
        self.all_data: List[Any] = []
        self.filtered_data: List[Any] = []
        self.filter_callback: Optional[Callable] = None

        self._setup_ui()
        self._apply_treeview_theme()

    def _setup_ui(self):
        """Configura a interface do componente."""

        # Configuração do grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # TreeView expandível

        # Frame do filtro
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.filter_frame.grid_columnconfigure(0, weight=1)

        # Campo de filtro
        self.filter_var = ctk.StringVar()
        self.filter_entry = ctk.CTkEntry(
            self.filter_frame,
            textvariable=self.filter_var,
            placeholder_text=self.placeholder_text,
            font=("Segoe UI", 13),
            height=35,
            border_width=1,
        )
        self.filter_entry.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")

        # Botão de limpar filtro
        self.clear_button = ctk.CTkButton(
            self.filter_frame,
            text="✖",
            width=35,
            height=35,
            font=("Segoe UI", 12),
            command=self._clear_filter,
            fg_color="gray50",
            hover_color="gray40",
        )
        self.clear_button.grid(row=0, column=1, pady=5)

        # Bind do filtro
        self.filter_var.trace_add("write", lambda *args: self._on_filter_change())

        # Frame do TreeView com scrollbar
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # TreeView
        self.style = ttk.Style(self)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=self.tree_columns,
            displaycolumns=self.display_columns,
            show="headings",
            selectmode="browse",
            style="Filterable.Treeview",
        )
        self.tree.grid(row=0, column=0, padx=(10, 0), pady=10, sticky="nsew")

        # Configura colunas
        for col in self.display_columns:
            config = self.column_configs.get(col, {})
            heading_text = config.get("heading", col.title())
            width = config.get("width", 100)
            anchor = config.get("anchor", "w")
            stretch = config.get("stretch", True)

            self.tree.heading(col, text=heading_text, anchor=anchor)
            self.tree.column(col, anchor=anchor, width=width, stretch=stretch)

        # Scrollbar
        tree_scrollbar = ctk.CTkScrollbar(tree_frame, command=self.tree.yview)
        tree_scrollbar.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="ns")
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        # Label de resultados
        self.results_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color="gray60")
        self.results_label.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="w")

    def _apply_treeview_theme(self):
        """Aplica tema ao TreeView para combinar com CustomTkinter."""
        try:
            # Cores baseadas no tema atual
            bg_color = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#ffffff"
            fg_color = "#ffffff" if ctk.get_appearance_mode() == "Dark" else "#000000"
            select_bg = "#1f538d" if ctk.get_appearance_mode() == "Dark" else "#0078d4"
            select_fg = "#ffffff"

            self.style.theme_use("clam")
            self.style.configure(
                "Filterable.Treeview",
                background=bg_color,
                foreground=fg_color,
                rowheight=25,
                fieldbackground=bg_color,
                borderwidth=0,
            )

            self.style.configure(
                "Filterable.Treeview.Heading",
                background="#404040" if ctk.get_appearance_mode() == "Dark" else "#f0f0f0",
                foreground=fg_color,
                relief="flat",
            )

            self.style.map(
                "Filterable.Treeview",
                background=[("selected", select_bg)],
                foreground=[("selected", select_fg)],
            )

        except Exception as e:
            logging.warning(f"Erro ao aplicar tema TreeView: {e}")

    def _on_filter_change(self):
        """Callback quando o filtro muda."""
        filter_text = self.filter_var.get().lower().strip()
        self._apply_filter(filter_text)
        self._update_results_label()

        # Chama callback personalizado se definido
        if self.filter_callback:
            self.filter_callback(filter_text, self.filtered_data)

    def _apply_filter(self, filter_text: str):
        """Aplica o filtro aos dados e atualiza o TreeView."""
        if not filter_text:
            self.filtered_data = self.all_data.copy()
        else:
            self.filtered_data = [
                item for item in self.all_data if self._item_matches_filter(item, filter_text)
            ]

        self._rebuild_tree()

    def _item_matches_filter(self, item: Any, filter_text: str) -> bool:
        """
        Verifica se um item corresponde ao filtro.
        Deve ser sobrescrito pela classe filha ou configurado via callback.
        """
        # Implementação padrão: busca em todos os campos string
        if hasattr(item, "__dict__"):
            # Para objetos com atributos
            for value in item.__dict__.values():
                if isinstance(value, str) and filter_text in value.lower():
                    return True
        elif isinstance(item, (tuple, list)):
            # Para tuplas/listas
            for value in item:
                if isinstance(value, str) and filter_text in value.lower():
                    return True
        elif isinstance(item, dict):
            # Para dicionários
            for value in item.values():
                if isinstance(value, str) and filter_text in value.lower():
                    return True

        return False

    def _rebuild_tree(self):
        """Reconstrói o TreeView com dados filtrados."""
        # Limpa TreeView
        for child in self.tree.get_children():
            self.tree.delete(child)

        # Adiciona dados filtrados
        for item in self.filtered_data:
            values = self._extract_tree_values(item)
            self.tree.insert("", "end", values=values)

    def _extract_tree_values(self, item: Any) -> tuple:
        """
        Extrai valores do item para exibição no TreeView.
        Deve ser sobrescrito pela classe filha.
        """
        if isinstance(item, (tuple, list)):
            return tuple(item)
        elif isinstance(item, dict):
            return tuple(item.get(col, "") for col in self.tree_columns)
        elif hasattr(item, "__dict__"):
            return tuple(getattr(item, col, "") for col in self.tree_columns)
        else:
            return (str(item),)

    def _clear_filter(self):
        """Limpa o filtro."""
        self.filter_var.set("")

    def _update_results_label(self):
        """Atualiza o label de resultados."""
        total = len(self.all_data)
        filtered = len(self.filtered_data)

        if total == 0:
            text = "Nenhum item"
        elif total == filtered:
            text = f"{total} item(s)"
        else:
            text = f"{filtered} de {total} item(s)"

        self.results_label.configure(text=text)

    def set_data(self, data: List[Any]):
        """Define os dados para o componente, preservando o filtro atual."""
        self.all_data = data.copy()

        # Preserva o filtro atual se existir
        current_filter = self.filter_var.get().strip().lower()
        if current_filter:
            # Reaplica o filtro aos novos dados
            self._apply_filter(current_filter)
        else:
            # Sem filtro, mostra todos os dados
            self.filtered_data = data.copy()

        self._rebuild_tree()
        self._update_results_label()

    def update_data(self, data: List[Any]):
        """
        Atualiza os dados preservando o filtro e a seleção atual.
        Método preferível para atualizações automáticas.
        """
        # Salva o item selecionado atual (pelo ID se possível)
        selected_item = self.get_selected_item()
        selected_id = None
        if selected_item and len(selected_item) > 0:
            try:
                selected_id = selected_item[0]  # Assume que o primeiro elemento é o ID
            except (IndexError, ValueError):
                selected_id = None

        # Atualiza os dados preservando o filtro
        self.set_data(data)

        # Restaura a seleção se possível
        if selected_id is not None:
            self._restore_selection_by_id(selected_id)

    def _restore_selection_by_id(self, item_id):
        """Tenta restaurar a seleção baseada no ID do item."""
        try:
            for child in self.tree.get_children():
                values = self.tree.item(child, "values")
                if values and str(values[0]) == str(item_id):
                    self.tree.selection_set(child)
                    self.tree.see(child)  # Garante que o item está visível
                    break
        except Exception as e:
            # Se falhar, não é crítico
            logging.debug(f"Não foi possível restaurar seleção para ID {item_id}: {e}")

    def set_filter_callback(self, callback: Callable):
        """Define callback personalizado para filtros."""
        self.filter_callback = callback

    def set_item_matcher(self, matcher: Callable[[Any, str], bool]):
        """Define função personalizada para verificar se item corresponde ao filtro."""
        self._item_matches_filter = matcher

    def set_value_extractor(self, extractor: Callable[[Any], tuple]):
        """Define função personalizada para extrair valores do item."""
        self._extract_tree_values = extractor

    def get_selected_item(self) -> Optional[Any]:
        """Retorna o item selecionado no TreeView."""
        selection = self.tree.selection()
        if not selection:
            return None

        item_index = self.tree.index(selection[0])
        if 0 <= item_index < len(self.filtered_data):
            return self.filtered_data[item_index]

        return None

    def get_selected_values(self) -> Optional[tuple]:
        """Retorna os valores do item selecionado no TreeView."""
        selection = self.tree.selection()
        if not selection:
            return None

        return self.tree.item(selection[0])["values"]

    def bind_selection(self, callback: Callable):
        """Vincula callback para seleção de itens."""
        def on_select(event):
            """Wrapper para chamar callback com o item selecionado."""
            selected_item = self.get_selected_values()
            callback(selected_item)

        self.tree.bind("<<TreeviewSelect>>", on_select)

    def clear_selection(self):
        """Limpa a seleção atual do TreeView."""
        self.tree.selection_remove(self.tree.selection())

    def refresh_theme(self):
        """Atualiza o tema do TreeView."""
        self._apply_treeview_theme()


# Funções utilitárias para facilitar uso nos painéis administrativos


def create_user_filter_frame(parent) -> FilterableTreeFrame:
    """Cria frame de filtro específico para usuários."""
    column_configs = {
        "nome": {"heading": "Nome de Usuário", "width": 150, "stretch": True},
        "admin": {"heading": "Admin", "width": 60, "stretch": False, "anchor": "center"},
        "ativo": {"heading": "Ativo", "width": 60, "stretch": False, "anchor": "center"},
    }

    frame = FilterableTreeFrame(
        parent,
        placeholder_text="🔍 Buscar usuários...",
        tree_columns=("id", "nome", "admin", "ativo"),
        display_columns=("nome", "admin", "ativo"),
        column_configs=column_configs,
    )

    # Matcher personalizado para usuários
    def user_matcher(item, filter_text):
        if isinstance(item, tuple) and len(item) >= 2:
            # item = (id, nome, admin, ativo, ...)
            nome = str(item[1]).lower() if len(item) > 1 else ""
            return filter_text in nome
        return False

    frame.set_item_matcher(user_matcher)
    return frame


def create_group_filter_frame(parent) -> FilterableTreeFrame:
    """Cria frame de filtro específico para grupos."""
    column_configs = {
        "nome": {"heading": "Nome do Grupo", "width": 200, "stretch": True},
        "descricao": {"heading": "Descrição", "width": 300, "stretch": True},
    }

    frame = FilterableTreeFrame(
        parent,
        placeholder_text="🔍 Buscar grupos...",
        tree_columns=("id", "nome", "descricao"),
        display_columns=("nome", "descricao"),
        column_configs=column_configs,
    )

    # Matcher personalizado para grupos
    def group_matcher(item, filter_text):
        if isinstance(item, tuple) and len(item) >= 2:
            # item = (id, nome, descricao, ...)
            nome = str(item[1]).lower() if len(item) > 1 else ""
            descricao = str(item[2]).lower() if len(item) > 2 else ""
            return filter_text in nome or filter_text in descricao
        return False

    frame.set_item_matcher(group_matcher)
    return frame


def create_connection_filter_frame(parent) -> FilterableTreeFrame:
    """Cria frame de filtro específico para conexões."""
    column_configs = {
        "nome": {"heading": "Nome da Conexão", "width": 200, "stretch": True},
        "host": {"heading": "Host/IP", "width": 150, "stretch": False},
        "porta": {"heading": "Porta", "width": 80, "stretch": False, "anchor": "center"},
    }

    frame = FilterableTreeFrame(
        parent,
        placeholder_text="🔍 Buscar conexões...",
        tree_columns=("id", "nome", "host", "porta"),
        display_columns=("nome", "host", "porta"),
        column_configs=column_configs,
    )

    # Matcher personalizado para conexões
    def connection_matcher(item, filter_text):
        if isinstance(item, tuple) and len(item) >= 3:
            # item = (id, nome, host, porta, ...)
            nome = str(item[1]).lower() if len(item) > 1 else ""
            host = str(item[2]).lower() if len(item) > 2 else ""
            return filter_text in nome or filter_text in host
        return False

    frame.set_item_matcher(connection_matcher)
    return frame
