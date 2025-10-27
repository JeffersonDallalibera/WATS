# WATS_Project/wats_app/session_protection.py - Sistema de Proteção de Sessão CORRETO

import customtkinter as ctk
import logging
import secrets
import string
import time
from tkinter import messagebox
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timedelta


class CreateSessionProtectionDialog(ctk.CTkToplevel):
    """
    Diálogo para o usuário CONECTADO criar proteção em sua sessão.
    
    Fluxo: Usuário A (conectado) clica botão direito → "Proteger Sessão" → Define senha
    """
    
    def __init__(self, parent, connection_data: Dict[str, Any], current_user: str):
        super().__init__(parent)
        
        self.connection_data = connection_data
        self.current_user = current_user
        self.protection_password = None
        self.result = None
        
        self._setup_ui()
        self._center_window()
        
        # Configurações da janela
        self.title("🔒 Proteger Sessão")
        self.geometry("480x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Auto-foco no primeiro campo
        self.after(100, lambda: self.password_entry.focus())

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔒 Proteger Sua Sessão",
            font=("Segoe UI", 18, "bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 20), sticky="ew")
        
        # Informações da conexão
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.grid(row=1, column=0, pady=(0, 15), sticky="ew", padx=10)
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Servidor
        ctk.CTkLabel(info_frame, text="Servidor:", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        ctk.CTkLabel(info_frame, text=self.connection_data.get('title', 'N/A')).grid(
            row=0, column=1, padx=10, pady=5, sticky="w"
        )
        
        # Usuário conectado
        ctk.CTkLabel(info_frame, text="Você (conectado):", font=("Segoe UI", 12, "bold")).grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        ctk.CTkLabel(info_frame, text=self.current_user, text_color="#2E8B57").grid(
            row=1, column=1, padx=10, pady=5, sticky="w"
        )
        
        # Explicação
        explanation_frame = ctk.CTkFrame(main_frame, fg_color="#2E8B57")
        explanation_frame.grid(row=2, column=0, pady=(0, 15), sticky="ew", padx=10)
        
        explanation_label = ctk.CTkLabel(
            explanation_frame,
            text="🛡️ Criar proteção temporária para sua sessão\n\nOutros usuários precisarão da senha que você definir para acessar este servidor.\nVocê mantém controle total sobre quem pode conectar.",
            font=("Segoe UI", 11),
            text_color="white",
            wraplength=420
        )
        explanation_label.pack(padx=15, pady=15)
        
        # Configuração da senha
        password_frame = ctk.CTkFrame(main_frame)
        password_frame.grid(row=3, column=0, pady=(0, 15), sticky="ew", padx=10)
        password_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(password_frame, text="🔐 Configuração da Proteção", 
                    font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, padx=10, pady=10
        )
        
        # Senha personalizada
        ctk.CTkLabel(password_frame, text="Senha de proteção:", font=("Segoe UI", 12, "bold")).grid(
            row=1, column=0, padx=10, pady=(5, 5), sticky="w"
        )
        
        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Digite uma senha (6-20 caracteres)",
            show="*",
            width=200
        )
        self.password_entry.grid(row=1, column=1, padx=10, pady=(5, 5), sticky="ew")
        
        # Botão gerar senha
        generate_button = ctk.CTkButton(
            password_frame,
            text="🎲 Gerar Automática",
            command=self._generate_password,
            width=120,
            height=28
        )
        generate_button.grid(row=2, column=1, padx=10, pady=(5, 10), sticky="w")
        
        # Duração da proteção
        ctk.CTkLabel(password_frame, text="Duração da proteção:", font=("Segoe UI", 12, "bold")).grid(
            row=3, column=0, padx=10, pady=(5, 5), sticky="w"
        )
        
        self.duration_var = ctk.StringVar(value="60")
        duration_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        duration_frame.grid(row=3, column=1, padx=10, pady=(5, 5), sticky="ew")
        
        ctk.CTkRadioButton(
            duration_frame,
            text="30 minutos",
            variable=self.duration_var,
            value="30"
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkRadioButton(
            duration_frame,
            text="1 hora",
            variable=self.duration_var,
            value="60"
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkRadioButton(
            duration_frame,
            text="2 horas",
            variable=self.duration_var,
            value="120"
        ).pack(side="left")
        
        # Observações opcionais
        ctk.CTkLabel(main_frame, text="Observações (opcional):", font=("Segoe UI", 12)).grid(
            row=4, column=0, padx=10, pady=(5, 5), sticky="w"
        )
        
        self.notes_entry = ctk.CTkTextbox(
            main_frame,
            height=60,
            placeholder_text="Ex: Trabalho crítico até 18h, manutenção em andamento..."
        )
        self.notes_entry.grid(row=5, column=0, padx=10, pady=(0, 15), sticky="ew")
        
        # Botões
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=6, column=0, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            command=self._cancel,
            fg_color="gray50",
            hover_color="gray40"
        )
        cancel_button.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
        
        protect_button = ctk.CTkButton(
            button_frame,
            text="🔒 Ativar Proteção",
            command=self._activate_protection,
            font=("Segoe UI", 12, "bold")
        )
        protect_button.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="ew")

    def _center_window(self):
        """Centraliza a janela na tela."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _generate_password(self):
        """Gera uma senha automática."""
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(8))
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, password)
        
        # Mostra a senha gerada
        messagebox.showinfo(
            "Senha Gerada",
            f"Senha automática gerada: {password}\n\nGuarde esta senha para compartilhar com quem precisar acessar."
        )

    def _activate_protection(self):
        """Ativa a proteção da sessão."""
        
        # Validação da senha
        password = self.password_entry.get().strip()
        if not password or len(password) < 6:
            messagebox.showwarning(
                "Senha Necessária", 
                "Por favor, digite uma senha com pelo menos 6 caracteres"
            )
            self.password_entry.focus()
            return
        
        if len(password) > 20:
            messagebox.showwarning(
                "Senha Muito Longa", 
                "A senha deve ter no máximo 20 caracteres"
            )
            self.password_entry.focus()
            return
        
        try:
            duration_minutes = int(self.duration_var.get())
            notes = self.notes_entry.get("1.0", "end-1c").strip()
            
            # Calcula expiração
            expiry_time = datetime.now() + timedelta(minutes=duration_minutes)
            
            # Dados da proteção
            protection_data = {
                "connection_id": self.connection_data.get('db_id'),
                "connection_name": self.connection_data.get('title'),
                "protected_by": self.current_user,
                "password": password,
                "duration_minutes": duration_minutes,
                "expiry_time": expiry_time.isoformat(),
                "created_at": datetime.now().isoformat(),
                "notes": notes,
                "status": "active"
            }
            
            # Registra a proteção
            self._log_protection_created(protection_data)
            
            # Ativa no gerenciador
            session_protection_manager.activate_session_protection(
                self.connection_data.get('db_id'),
                password,
                protection_data
            )
            
            # Mostra confirmação
            self._show_protection_confirmation(expiry_time, password)
            
            self.protection_password = password
            self.result = {
                "activated": True,
                "password": password,
                "expiry_time": expiry_time,
                "protection_data": protection_data
            }
            
            self.destroy()
            
        except Exception as e:
            logging.error(f"Erro ao ativar proteção: {e}")
            messagebox.showerror("Erro", f"Falha ao ativar proteção:\n{e}")

    def _log_protection_created(self, protection_data: Dict[str, Any]):
        """Registra a criação da proteção nos logs."""
        try:
            log_message = (
                f"🔒 PROTEÇÃO DE SESSÃO ATIVADA - "
                f"Servidor: {protection_data['connection_name']} | "
                f"Protegido por: {protection_data['protected_by']} | "
                f"Duração: {protection_data['duration_minutes']} min | "
                f"Observações: {protection_data['notes'][:50]}..."
            )
            
            logging.info(log_message)
            
        except Exception as e:
            logging.error(f"Erro ao registrar log de proteção: {e}")

    def _show_protection_confirmation(self, expiry_time: datetime, password: str):
        """Mostra confirmação da proteção ativada."""
        expiry_str = expiry_time.strftime("%d/%m/%Y %H:%M:%S")
        message = (
            f"🔒 PROTEÇÃO ATIVADA COM SUCESSO!\n\n"
            f"Senha de proteção: {password}\n"
            f"Válida até: {expiry_str}\n\n"
            f"✅ Sua sessão está protegida!\n"
            f"✅ Outros usuários precisarão desta senha para acessar\n"
            f"✅ Você pode desativar a proteção a qualquer momento"
        )
        messagebox.showinfo("Proteção Ativada", message)

    def _cancel(self):
        """Cancela a criação da proteção."""
        self.result = {"activated": False}
        self.destroy()

    def get_result(self) -> Optional[Dict[str, Any]]:
        """Retorna o resultado da proteção."""
        return self.result


class ValidateSessionPasswordDialog(ctk.CTkToplevel):
    """
    Diálogo para validar senha de sessão protegida.
    
    Fluxo: Usuário B tenta acessar → Recebe este diálogo → Digita senha do Usuário A
    """
    
    def __init__(self, parent, connection_data: Dict[str, Any], requesting_user: str, protected_by: str):
        super().__init__(parent)
        
        self.connection_data = connection_data
        self.requesting_user = requesting_user
        self.protected_by = protected_by
        self.result = None
        
        self._setup_ui()
        self._center_window()
        
        # Configurações da janela
        self.title("🔒 Sessão Protegida")
        self.geometry("450x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Auto-foco no campo senha
        self.after(100, lambda: self.password_entry.focus())

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔒 Sessão Protegida",
            font=("Segoe UI", 18, "bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 20), sticky="ew")
        
        # Informações
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.grid(row=1, column=0, pady=(0, 15), sticky="ew", padx=10)
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Servidor
        ctk.CTkLabel(info_frame, text="Servidor:", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        ctk.CTkLabel(info_frame, text=self.connection_data.get('title', 'N/A')).grid(
            row=0, column=1, padx=10, pady=5, sticky="w"
        )
        
        # Protegido por
        ctk.CTkLabel(info_frame, text="Protegido por:", font=("Segoe UI", 12, "bold")).grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        ctk.CTkLabel(info_frame, text=self.protected_by, text_color="#FF6B35").grid(
            row=1, column=1, padx=10, pady=5, sticky="w"
        )
        
        # Aviso
        warning_frame = ctk.CTkFrame(main_frame, fg_color="#FF6B35")
        warning_frame.grid(row=2, column=0, pady=(0, 15), sticky="ew", padx=10)
        
        warning_label = ctk.CTkLabel(
            warning_frame,
            text="🔒 Esta sessão está protegida!\n\nO usuário conectado definiu uma senha de proteção.\nDigite a senha para acessar o servidor.",
            font=("Segoe UI", 11, "bold"),
            text_color="white",
            wraplength=400
        )
        warning_label.pack(padx=15, pady=15)
        
        # Campo senha
        password_frame = ctk.CTkFrame(main_frame)
        password_frame.grid(row=3, column=0, pady=(0, 15), sticky="ew", padx=10)
        password_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(password_frame, text="🔐 Senha de Proteção", 
                    font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, padx=10, pady=10
        )
        
        ctk.CTkLabel(password_frame, text="Senha:", font=("Segoe UI", 12, "bold")).grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        
        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Digite a senha de proteção",
            show="*",
            width=250
        )
        self.password_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Bind Enter para validar
        self.password_entry.bind("<Return>", lambda e: self._validate_password())
        
        # Instruções
        instructions_label = ctk.CTkLabel(
            main_frame,
            text="💡 Dica: Entre em contato com o usuário conectado para obter a senha",
            font=("Segoe UI", 10),
            text_color="gray"
        )
        instructions_label.grid(row=4, column=0, padx=10, pady=(0, 15))
        
        # Botões
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=5, column=0, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            command=self._cancel,
            fg_color="gray50",
            hover_color="gray40"
        )
        cancel_button.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
        
        validate_button = ctk.CTkButton(
            button_frame,
            text="🔓 Validar Senha",
            command=self._validate_password,
            font=("Segoe UI", 12, "bold")
        )
        validate_button.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="ew")

    def _center_window(self):
        """Centraliza a janela na tela."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _validate_password(self):
        """Valida a senha de proteção."""
        
        password = self.password_entry.get().strip()
        if not password:
            messagebox.showwarning("Senha Necessária", "Por favor, digite a senha de proteção")
            self.password_entry.focus()
            return
        
        try:
            # Valida no gerenciador
            validation = session_protection_manager.validate_session_password(
                self.connection_data.get('db_id'),
                password,
                self.requesting_user
            )
            
            if validation["valid"]:
                # Senha correta
                logging.info(f"Senha de proteção validada para {self.requesting_user} no servidor {self.connection_data.get('title')}")
                
                self.result = {
                    "validated": True,
                    "password": password,
                    "protection_data": validation["protection_data"]
                }
                
                messagebox.showinfo(
                    "Acesso Liberado",
                    "✅ Senha correta!\n\nAcesso ao servidor liberado."
                )
                
                self.destroy()
                
            else:
                # Senha incorreta
                messagebox.showerror("Senha Incorreta", validation["reason"])
                self.password_entry.delete(0, "end")
                self.password_entry.focus()
                
        except Exception as e:
            logging.error(f"Erro ao validar senha de proteção: {e}")
            messagebox.showerror("Erro", f"Falha na validação:\n{e}")

    def _cancel(self):
        """Cancela a validação."""
        self.result = {"validated": False}
        self.destroy()

    def get_result(self) -> Optional[Dict[str, Any]]:
        """Retorna o resultado da validação."""
        return self.result


class SessionProtectionManager:
    """
    Gerenciador de proteção de sessão - IMPLEMENTAÇÃO COM SERVIDOR.
    
    Funcionalidades:
    1. Usuário conectado CRIA proteção com senha no servidor
    2. Outros usuários VALIDAM a senha via servidor
    3. Proteção tem expiração automática no banco
    4. Logs completos de todas as ações
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
        self.session_repo = None
        if self.db_service:
            try:
                from src.wats.db.repositories.session_protection_repository import SessionProtectionRepository
                self.session_repo = SessionProtectionRepository(self.db_service.db_manager)
            except ImportError:
                logging.warning("SessionProtectionRepository não encontrado, usando modo local")
        
        # Fallback para modo local (testes e compatibilidade)
        self.protected_sessions: Dict[int, Dict[str, Any]] = {}
        self.cleanup_interval = 300  # 5 minutos
        self.last_cleanup = time.time()

    def activate_session_protection(self, connection_id: int, password: str, protection_data: Dict[str, Any]):
        """Ativa proteção para uma sessão no servidor."""
        
        # Tenta usar o repositório do servidor
        if self.session_repo:
            try:
                user_name = protection_data.get('protected_by', 'unknown')
                machine_name = protection_data.get('machine_name', 'unknown')
                duration_minutes = protection_data.get('duration_minutes', 60)
                notes = protection_data.get('notes', '')
                ip_address = protection_data.get('ip_address')
                
                success, message, protection_id = self.session_repo.create_session_protection(
                    con_codigo=connection_id,
                    user_name=user_name,
                    machine_name=machine_name,
                    password=password,
                    duration_minutes=duration_minutes,
                    notes=notes,
                    ip_address=ip_address
                )
                
                if success:
                    logging.info(f"Proteção criada no servidor - ID: {protection_id}, Conexão: {connection_id}")
                    return True
                else:
                    logging.error(f"Falha ao criar proteção no servidor: {message}")
                    # Fallback para modo local
                    
            except Exception as e:
                logging.error(f"Erro ao acessar servidor para criar proteção: {e}")
                # Fallback para modo local
        
        # Modo local (fallback)
        self.protected_sessions[connection_id] = {
            "password": password,
            "protection_data": protection_data,
            "created_at": datetime.now().isoformat()
        }
        
        logging.info(f"Proteção ativada localmente para conexão {connection_id} por {protection_data.get('protected_by')}")
        return True

    def is_session_protected(self, connection_id: int) -> bool:
        """Verifica se uma sessão está protegida (servidor ou local)."""
        
        # Verifica no servidor primeiro
        if self.session_repo:
            try:
                protections = self.session_repo.get_active_protections_by_connection(connection_id)
                if protections:
                    return True
            except Exception as e:
                logging.error(f"Erro ao verificar proteção no servidor: {e}")
        
        # Verifica localmente (fallback)
        self._cleanup_expired_protections()
        return connection_id in self.protected_sessions

    def get_session_protection_info(self, connection_id: int) -> Optional[Dict[str, Any]]:
        """Retorna informações da proteção ativa."""
        self._cleanup_expired_protections()
        
        if connection_id in self.protected_sessions:
            return self.protected_sessions[connection_id]["protection_data"]
        return None

    def validate_session_password(self, connection_id: int, password: str, requesting_user: str) -> Dict[str, Any]:
        """
        Valida senha de proteção de sessão no servidor.
        
        Returns:
            Dict com resultado da validação
        """
        
        # Tenta validar no servidor primeiro
        if self.session_repo:
            try:
                import socket
                machine_name = socket.gethostname()
                ip_address = socket.gethostbyname(socket.gethostname())
                
                result = self.session_repo.validate_session_password(
                    con_codigo=connection_id,
                    password=password,
                    requesting_user=requesting_user,
                    requesting_machine=machine_name,
                    ip_address=ip_address
                )
                
                if result.get("valid"):
                    logging.info(f"🔓 ACESSO AUTORIZADO VIA SERVIDOR - Usuário: {requesting_user} | Conexão: {connection_id}")
                else:
                    logging.warning(f"🔒 ACESSO NEGADO VIA SERVIDOR - Usuário: {requesting_user} | Razão: {result.get('message')}")
                
                return result
                
            except Exception as e:
                logging.error(f"Erro ao validar senha no servidor: {e}")
                # Fallback para modo local
        
        # Validação local (fallback)
        self._cleanup_expired_protections()
        
        if connection_id not in self.protected_sessions:
            return {
                "valid": False,
                "reason": "Esta sessão não está protegida (local)"
            }
        
        protection = self.protected_sessions[connection_id]
        stored_password = protection["password"]
        protection_data = protection["protection_data"]
        
        # Verifica se a senha está correta
        if password != stored_password:
            # Log de tentativa incorreta
            logging.warning(f"Tentativa de acesso com senha incorreta (local) - Usuário: {requesting_user} | Servidor: {protection_data.get('connection_name')}")
            return {
                "valid": False,
                "reason": "Senha de proteção incorreta (local)"
            }
        
        # Senha correta - registra acesso autorizado
        self._log_authorized_access(requesting_user, protection_data)
        
        return {
            "valid": True,
            "protection_data": protection_data
        }

    def remove_session_protection(self, connection_id: int, user: str) -> bool:
        """Remove proteção de uma sessão no servidor."""
        
        # Tenta remover no servidor primeiro
        if self.session_repo:
            try:
                success, message = self.session_repo.remove_session_protection(
                    con_codigo=connection_id,
                    removing_user=user
                )
                
                if success:
                    logging.info(f"Proteção removida do servidor - Conexão: {connection_id} por {user}")
                    return True
                else:
                    logging.warning(f"Falha ao remover proteção do servidor: {message}")
                    # Tenta fallback local
                    
            except Exception as e:
                logging.error(f"Erro ao remover proteção do servidor: {e}")
                # Fallback para modo local
        
        # Remoção local (fallback)
        try:
            if connection_id not in self.protected_sessions:
                return False
            
            protection_data = self.protected_sessions[connection_id]["protection_data"]
            
            # Verifica se é o usuário que criou a proteção
            if user != protection_data.get("protected_by"):
                logging.warning(f"Tentativa não autorizada de remover proteção local por {user}")
                return False
            
            # Remove a proteção
            del self.protected_sessions[connection_id]
            
            logging.info(f"Proteção removida localmente da conexão {connection_id} por {user}")
            return True
            
        except Exception as e:
            logging.error(f"Erro ao remover proteção local: {e}")
            return False

    def get_user_protected_sessions(self, user: str) -> List[Dict[str, Any]]:
        """Retorna sessões protegidas por um usuário específico."""
        self._cleanup_expired_protections()
        
        user_sessions = []
        for connection_id, protection in self.protected_sessions.items():
            protection_data = protection["protection_data"]
            if protection_data.get("protected_by") == user:
                session_info = protection_data.copy()
                session_info["connection_id"] = connection_id
                # Remove senha por segurança
                if "password" in session_info:
                    del session_info["password"]
                user_sessions.append(session_info)
        
        return user_sessions

    def _cleanup_expired_protections(self):
        """Remove proteções expiradas."""
        current_time = time.time()
        
        # Para testes, permite forçar limpeza
        if hasattr(self, '_force_cleanup') and self._force_cleanup:
            pass  # Força execução
        elif current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        now = datetime.now()
        expired_connections = []
        
        for connection_id, protection in self.protected_sessions.items():
            protection_data = protection["protection_data"]
            expiry_time = datetime.fromisoformat(protection_data["expiry_time"])
            if now > expiry_time:
                expired_connections.append(connection_id)
        
        for connection_id in expired_connections:
            protection_data = self.protected_sessions[connection_id]["protection_data"]
            logging.info(f"Proteção expirada removida - Servidor: {protection_data.get('connection_name')} | Protegido por: {protection_data.get('protected_by')}")
            del self.protected_sessions[connection_id]
        
        self.last_cleanup = current_time

    def force_cleanup_expired(self):
        """Força limpeza de proteções expiradas (para testes)."""
        self._force_cleanup = True
        self._cleanup_expired_protections()
        self._force_cleanup = False

    def _log_authorized_access(self, user: str, protection_data: Dict[str, Any]):
        """Registra acesso autorizado com senha correta."""
        log_message = (
            f"🔓 ACESSO AUTORIZADO COM SENHA - "
            f"Usuário: {user} | "
            f"Servidor: {protection_data.get('connection_name')} | "
            f"Protegido por: {protection_data.get('protected_by')} | "
            f"Senha validada com sucesso"
        )
        logging.info(log_message)

    def cleanup_all_protections(self):
        """Remove todas as proteções (para shutdown)."""
        count = len(self.protected_sessions)
        self.protected_sessions.clear()
        if count > 0:
            logging.info(f"Limpeza completa: {count} proteções de sessão removidas")

    def cleanup_orphaned_protections(self):
        """Remove proteções órfãs (usuários desconectados)."""
        if self.session_repo:
            try:
                success, message, count = self.session_repo.cleanup_orphaned_protections()
                if success and count > 0:
                    logging.info(f"Limpeza automática: {count} proteções órfãs removidas")
                return success, message, count
            except Exception as e:
                logging.error(f"Erro na limpeza de proteções órfãs: {e}")
                return False, f"Erro: {e}", 0
        
        # Fallback local - remove proteções de usuários que não existem mais
        orphaned_count = 0
        current_time = datetime.now()
        to_remove = []
        
        for connection_id, protection in self.protected_sessions.items():
            protection_data = protection["protection_data"]
            # Se a proteção é muito antiga (mais de 4 horas), considera órfã
            created_time = datetime.fromisoformat(protection["created_at"])
            if (current_time - created_time).total_seconds() > 14400:  # 4 horas
                to_remove.append(connection_id)
                orphaned_count += 1
                
        for connection_id in to_remove:
            protection_data = self.protected_sessions[connection_id]["protection_data"]
            logging.info(f"Removendo proteção órfã local: {protection_data.get('connection_name')}")
            del self.protected_sessions[connection_id]
            
        return True, f"Limpeza local: {orphaned_count} proteções órfãs removidas", orphaned_count


# Instância global do gerenciador (será configurada com DB no main)
session_protection_manager = SessionProtectionManager()

def configure_session_protection_with_db(db_service):
    """Configura o gerenciador com acesso ao banco de dados."""
    global session_protection_manager
    session_protection_manager = SessionProtectionManager(db_service)