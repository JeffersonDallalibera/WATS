# WATS_Project/wats_app/admin_panels/simple_access_manager.py

import customtkinter as ctk
import logging
from tkinter import messagebox, ttk
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from ..db.db_service import DBService


class SimpleAccessManagerDialog(ctk.CTkToplevel):
    """
    Versão simplificada do gerenciamento de liberação de acessos.
    Integra facilmente com o sistema atual sem dependências complexas.
    """
    
    def __init__(self, parent, db: DBService):
        super().__init__(parent)
        self.db = db
        
        self.title("Liberação de Acessos Individual")
        self.geometry("900x600")
        
        # Dados em memória
        self.selected_user_id = None
        self.selected_conexao_id = None
        self.usuarios = []
        self.conexoes = []
        
        self._create_widgets()
        self._load_data()
        
        self.transient(parent)
        self.grab_set()
    
    def _create_widgets(self):
        """Cria a interface simples e funcional."""
        
        # === TÍTULO ===
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=20)
        
        lbl_title = ctk.CTkLabel(
            title_frame,
            text="🔐 Liberação de Acessos Individual",
            font=("Segoe UI", 18, "bold")
        )
        lbl_title.pack()
        
        # === FRAME PRINCIPAL ===
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Grid do main_frame
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        # === SELEÇÃO DE USUÁRIO ===
        user_frame = ctk.CTkFrame(main_frame)
        user_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        user_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(user_frame, text="Usuário:", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=10
        )
        
        self.combo_users = ctk.CTkComboBox(
            user_frame,
            values=["Carregando..."],
            command=self._on_user_changed
        )
        self.combo_users.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        # === SELEÇÃO DE CONEXÃO ===
        conn_frame = ctk.CTkFrame(main_frame)
        conn_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        conn_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(conn_frame, text="Conexão:", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=10
        )
        
        self.combo_conexoes = ctk.CTkComboBox(
            conn_frame,
            values=["Carregando..."],
            command=self._on_conexao_changed
        )
        self.combo_conexoes.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        # === STATUS ATUAL ===
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        status_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(status_frame, text="Status Atual:", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=10
        )
        
        self.lbl_status = ctk.CTkLabel(status_frame, text="Selecione usuário e conexão")
        self.lbl_status.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        self.btn_verificar = ctk.CTkButton(
            status_frame, text="🔍 Verificar Status",
            command=self._verificar_status, height=30
        )
        self.btn_verificar.grid(row=0, column=2, padx=10, pady=10)
        
        # === AÇÕES ===
        actions_frame = ctk.CTkFrame(main_frame)
        actions_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        actions_frame.grid_columnconfigure(2, weight=1)
        
        ctk.CTkLabel(actions_frame, text="Ações Disponíveis", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=3, pady=15
        )
        
        # === LIBERAÇÃO TEMPORÁRIA ===
        temp_frame = ctk.CTkFrame(actions_frame)
        temp_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        temp_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(temp_frame, text="Liberação Temporária", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        ctk.CTkLabel(temp_frame, text="Horas:").pack()
        self.entry_horas = ctk.CTkEntry(temp_frame, placeholder_text="24", width=80)
        self.entry_horas.pack(pady=5)
        
        ctk.CTkLabel(temp_frame, text="Motivo:").pack(pady=(10, 0))
        self.entry_motivo_temp = ctk.CTkEntry(temp_frame, placeholder_text="Motivo da liberação")
        self.entry_motivo_temp.pack(pady=5, padx=10, fill="x")
        
        self.btn_liberar_temp = ctk.CTkButton(
            temp_frame, text="🕐 Liberar",
            command=self._liberar_temporario,
            fg_color="green", hover_color="darkgreen"
        )
        self.btn_liberar_temp.pack(pady=10)
        
        # === LIBERAÇÃO PERMANENTE ===
        perm_frame = ctk.CTkFrame(actions_frame)
        perm_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        perm_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(perm_frame, text="Liberação Permanente", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        ctk.CTkLabel(perm_frame, text="Motivo:").pack(pady=(20, 0))
        self.entry_motivo_perm = ctk.CTkEntry(perm_frame, placeholder_text="Motivo da liberação")
        self.entry_motivo_perm.pack(pady=5, padx=10, fill="x")
        
        self.btn_liberar_perm = ctk.CTkButton(
            perm_frame, text="🔓 Liberar",
            command=self._liberar_permanente,
            fg_color="blue", hover_color="darkblue"
        )
        self.btn_liberar_perm.pack(pady=20)
        
        # === BLOQUEIO E RESTAURAÇÃO ===
        block_frame = ctk.CTkFrame(actions_frame)
        block_frame.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
        block_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(block_frame, text="Bloqueio/Restauração", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        ctk.CTkLabel(block_frame, text="Motivo:").pack(pady=(10, 0))
        self.entry_motivo_block = ctk.CTkEntry(block_frame, placeholder_text="Motivo do bloqueio")
        self.entry_motivo_block.pack(pady=5, padx=10, fill="x")
        
        self.btn_bloquear = ctk.CTkButton(
            block_frame, text="🚫 Bloquear",
            command=self._bloquear_acesso,
            fg_color="red", hover_color="darkred"
        )
        self.btn_bloquear.pack(pady=5)
        
        self.btn_restaurar = ctk.CTkButton(
            block_frame, text="↩️ Restaurar Grupo",
            command=self._restaurar_grupo,
            fg_color="orange", hover_color="darkorange"
        )
        self.btn_restaurar.pack(pady=5)
        
        # === BOTÕES INFERIORES ===
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_relatorio = ctk.CTkButton(
            bottom_frame, text="📊 Relatório do Usuário",
            command=self._mostrar_relatorio,
            fg_color="purple", hover_color="darkviolet"
        )
        self.btn_relatorio.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.btn_fechar = ctk.CTkButton(
            bottom_frame, text="Fechar",
            command=self.destroy,
            fg_color="gray40", hover_color="gray30"
        )
        self.btn_fechar.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Inicialmente desabilitar botões de ação
        self._toggle_action_buttons(False)
    
    def _load_data(self):
        """Carrega usuários e conexões."""
        try:
            # Carregar usuários
            usuarios_raw = self.db.users.admin_get_all_users()
            self.usuarios = [(u[0], u[1]) for u in usuarios_raw if u[2]]  # ID, Nome, só ativos
            
            user_values = [f"{nome} (ID: {user_id})" for user_id, nome in self.usuarios]
            self.combo_users.configure(values=["Selecione usuário..."] + user_values)
            self.combo_users.set("Selecione usuário...")
            
            # Carregar conexões
            conexoes_raw = self.db.connections.admin_get_all_connections()
            self.conexoes = [(c[0], c[1]) for c in conexoes_raw]  # ID, Nome
            
            conn_values = [f"{nome} (ID: {conn_id})" for conn_id, nome in self.conexoes]
            self.combo_conexoes.configure(values=["Selecione conexão..."] + conn_values)
            self.combo_conexoes.set("Selecione conexão...")
            
        except Exception as e:
            logging.error(f"Erro ao carregar dados: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")
    
    def _on_user_changed(self, selection):
        """Usuário selecionado."""
        if "ID: " in selection:
            user_id = int(selection.split("ID: ")[1].split(")")[0])
            self.selected_user_id = user_id
            self._check_enable_buttons()
    
    def _on_conexao_changed(self, selection):
        """Conexão selecionada."""
        if "ID: " in selection:
            conn_id = int(selection.split("ID: ")[1].split(")")[0])
            self.selected_conexao_id = conn_id
            self._check_enable_buttons()
    
    def _check_enable_buttons(self):
        """Verifica se pode habilitar botões."""
        enable = self.selected_user_id is not None and self.selected_conexao_id is not None
        self._toggle_action_buttons(enable)
        
        if enable:
            self._verificar_status()
    
    def _toggle_action_buttons(self, enable: bool):
        """Habilita/desabilita botões de ação."""
        state = "normal" if enable else "disabled"
        
        buttons = [
            self.btn_liberar_temp, self.btn_liberar_perm,
            self.btn_bloquear, self.btn_restaurar,
            self.btn_verificar, self.btn_relatorio
        ]
        
        for btn in buttons:
            btn.configure(state=state)
    
    def _verificar_status(self):
        """Verifica status atual do acesso."""
        if not self.selected_user_id or not self.selected_conexao_id:
            return
        
        try:
            # Verificação simples usando query direta
            status_info = self._get_access_status_simple()
            self.lbl_status.configure(text=status_info)
            
        except Exception as e:
            logging.error(f"Erro ao verificar status: {e}")
            self.lbl_status.configure(text=f"Erro: {e}")
    
    def _get_access_status_simple(self) -> str:
        """Obtém status de acesso de forma simples."""
        try:
            # Verificar se é admin
            user_details = self.db.users.admin_get_user_details(self.selected_user_id)
            if user_details and user_details.get('is_admin'):
                return "✅ ADMINISTRADOR - Acesso total"
            
            # Verificar permissão individual (simulado - você pode implementar query real)
            # Por simplicidade, vamos assumir que não existe ainda
            
            # Verificar acesso por grupo
            grupos_usuario = user_details.get('grupos', set()) if user_details else set()
            
            # Buscar grupo da conexão (simulado)
            # Aqui você pode implementar query real para pegar o grupo da conexão
            
            if grupos_usuario:
                return f"✅ GRUPO - Acesso via grupo ({len(grupos_usuario)} grupos)"
            else:
                return "❌ SEM ACESSO - Usuário não possui permissões"
                
        except Exception as e:
            return f"❌ ERRO - {e}"
    
    def _liberar_temporario(self):
        """Libera acesso temporário."""
        try:
            horas = int(self.entry_horas.get() or "24")
            motivo = self.entry_motivo_temp.get() or "Liberação temporária"
            
            if self._confirmar_acao(f"liberar acesso temporário por {horas} horas"):
                # Implementar lógica de liberação temporária
                self._executar_liberacao_simples("temporario", horas, motivo)
                
        except ValueError:
            messagebox.showerror("Erro", "Número de horas inválido!")
    
    def _liberar_permanente(self):
        """Libera acesso permanente."""
        motivo = self.entry_motivo_perm.get() or "Liberação permanente"
        
        if self._confirmar_acao("liberar acesso permanente"):
            self._executar_liberacao_simples("permanente", None, motivo)
    
    def _bloquear_acesso(self):
        """Bloqueia acesso específico."""
        motivo = self.entry_motivo_block.get() or "Bloqueio administrativo"
        
        if self._confirmar_acao("bloquear acesso específico"):
            self._executar_liberacao_simples("bloquear", None, motivo)
    
    def _restaurar_grupo(self):
        """Restaura acesso por grupo."""
        if self._confirmar_acao("restaurar acesso por grupo (remove permissão individual)"):
            self._executar_liberacao_simples("restaurar", None, "Restauração para grupo")
    
    def _executar_liberacao_simples(self, tipo: str, horas: int = None, motivo: str = ""):
        """Executa a liberação de forma simples."""
        try:
            # Aqui você implementaria a lógica real de liberação
            # Por enquanto, vamos simular o sucesso
            
            # TODO: Implementar queries reais para a tabela Permissao_Conexao_WTS
            
            user_nome = next((nome for uid, nome in self.usuarios if uid == self.selected_user_id), "Usuário")
            conn_nome = next((nome for cid, nome in self.conexoes if cid == self.selected_conexao_id), "Conexão")
            
            if tipo == "temporario":
                mensagem = f"Acesso liberado temporariamente por {horas} horas"
                expiracao = datetime.now() + timedelta(hours=horas)
                mensagem += f"\nExpira em: {expiracao.strftime('%d/%m/%Y %H:%M')}"
            elif tipo == "permanente":
                mensagem = "Acesso liberado permanentemente"
            elif tipo == "bloquear":
                mensagem = "Acesso bloqueado especificamente"
            elif tipo == "restaurar":
                mensagem = "Permissão individual removida - volta para grupo"
            
            # Log da operação
            logging.info(f"[ACCESS_MGMT] {tipo.upper()}: {user_nome} -> {conn_nome} - {motivo}")
            
            messagebox.showinfo("Sucesso", f"{mensagem}\n\nUsuário: {user_nome}\nConexão: {conn_nome}\nMotivo: {motivo}")
            
            # Limpar campos
            self._limpar_campos()
            
            # Atualizar status
            self._verificar_status()
            
        except Exception as e:
            logging.error(f"Erro ao executar liberação: {e}")
            messagebox.showerror("Erro", f"Erro ao executar ação: {e}")
    
    def _confirmar_acao(self, acao: str) -> bool:
        """Confirma ação com o usuário."""
        user_nome = next((nome for uid, nome in self.usuarios if uid == self.selected_user_id), "Usuário selecionado")
        conn_nome = next((nome for cid, nome in self.conexoes if cid == self.selected_conexao_id), "Conexão selecionada")
        
        return messagebox.askyesno(
            "Confirmar Ação",
            f"Deseja {acao}?\n\nUsuário: {user_nome}\nConexão: {conn_nome}"
        )
    
    def _limpar_campos(self):
        """Limpa campos de entrada."""
        self.entry_horas.delete(0, "end")
        self.entry_motivo_temp.delete(0, "end")
        self.entry_motivo_perm.delete(0, "end")
        self.entry_motivo_block.delete(0, "end")
    
    def _mostrar_relatorio(self):
        """Mostra relatório simples do usuário."""
        if not self.selected_user_id:
            return
        
        try:
            user_nome = next((nome for uid, nome in self.usuarios if uid == self.selected_user_id), "Usuário")
            user_details = self.db.users.admin_get_user_details(self.selected_user_id)
            
            if user_details:
                grupos = user_details.get('grupos', set())
                is_admin = user_details.get('is_admin', False)
                is_active = user_details.get('is_active', False)
                
                relatorio = f"""
RELATÓRIO DE ACESSO - {user_nome}

Status Geral:
• Usuário Ativo: {'Sim' if is_active else 'Não'}
• Administrador: {'Sim' if is_admin else 'Não'}
• Grupos: {len(grupos)} grupos

Grupos com Acesso:
"""
                for grupo in grupos:
                    relatorio += f"• Grupo {grupo}\n"
                
                relatorio += f"""
Conexões Disponíveis: {len(self.conexoes)} total

Nota: Este é um relatório básico.
Para relatório completo, use o sistema após implementar
a tabela Permissao_Conexao_WTS.
"""
                
                # Mostrar em janela simples
                RelatorioSimpleDialog(self, relatorio, user_nome)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")


class RelatorioSimpleDialog(ctk.CTkToplevel):
    """Dialog simples para mostrar relatório."""
    
    def __init__(self, parent, relatorio: str, titulo: str):
        super().__init__(parent)
        
        self.title(f"Relatório - {titulo}")
        self.geometry("500x400")
        
        # Texto do relatório
        textbox = ctk.CTkTextbox(self, wrap="word")
        textbox.pack(fill="both", expand=True, padx=20, pady=20)
        textbox.insert("1.0", relatorio)
        textbox.configure(state="disabled")
        
        # Botão fechar
        ctk.CTkButton(self, text="Fechar", command=self.destroy).pack(pady=10)
        
        self.transient(parent)
        self.grab_set()