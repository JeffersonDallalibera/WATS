# WATS_Project/run.py (COM CONSENTIMENTO)

import os
import sys
import time
import logging
from tkinter import messagebox # Usado para erros MUITO iniciais
import customtkinter as ctk # Importa customtkinter para o diálogo

# Importa as funções/classes necessárias de config
# Nota: NÃO importamos 'settings' aqui ainda
from wats_app.config import setup_logging, load_environment_variables, Settings

# --- [NOVO] Classe para o Diálogo de Consentimento ---
class ConsentDialog(ctk.CTkToplevel):
    """Diálogo modal para obter consentimento de gravação."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Consentimento de Gravação")
        self.geometry("450x250")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close) # Lida com fechamento no X

        self._result = None # Armazena a decisão (True = aceitou, False = recusou)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Permite que os botões fiquem em baixo

        info_text = (
            "AVISO IMPORTANTE\n\n"
            "Para fins de auditoria e segurança corporativa, as sessões de "
            "Área de Trabalho Remota (RDP) iniciadas através desta aplicação "
            "poderão ser gravadas em vídeo.\n\n"
            "As gravações serão armazenadas localmente no seu computador. "
            "Ao clicar em 'Aceitar', você concorda com a gravação das suas sessões RDP."
        )

        label = ctk.CTkLabel(self, text=info_text, wraplength=400, justify="left")
        label.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="sew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        accept_button = ctk.CTkButton(button_frame, text="Aceitar e Continuar", command=self._accept, height=35)
        accept_button.grid(row=0, column=1, padx=(5,0), sticky="ew")

        reject_button = ctk.CTkButton(button_frame, text="Recusar e Sair", command=self._reject, height=35,
                                      fg_color="gray50", hover_color="gray40")
        reject_button.grid(row=0, column=0, padx=(0,5), sticky="ew")

        self.lift() # Traz para frente
        self.attributes("-topmost", True) # Mantém no topo
        self.grab_set() # Torna modal
        self.focus()

    def _accept(self):
        self._result = True
        self.destroy()

    def _reject(self):
        self._result = False
        self.destroy()

    def _on_close(self):
        # Trata o fechamento da janela (clique no 'X') como recusa
        self._reject()

    def show(self):
        """Mostra o diálogo e espera pela resposta."""
        # Cria uma referência à janela pai para esperar por ela
        master = self.master
        master.wait_window(self)
        return self._result
# --- FIM NOVO ---


def main():
    """
    Configura logging, obtém consentimento, carrega env/settings e inicia a app.
    """
    # 1. Configura o logging PRIMEIRO
    try:
        setup_logging()
        # Log inicial é movido para depois do consentimento
    except Exception as e:
        print(f"ERRO CRÍTICO ao configurar logging: {e}")
        try: messagebox.showerror("Erro de Logging", f"Não foi possível configurar o log:\n{e}")
        except: pass
        sys.exit(1)

    # --- [NOVO] Mostrar Diálogo de Consentimento ---
    temp_root = None # Inicializa fora do try
    consent_given = False
    try:
        logging.info("Exibindo diálogo de consentimento...")
        # Precisamos de uma root window temporária para o Toplevel
        temp_root = ctk.CTk()
        temp_root.withdraw() # Esconde a janela root temporária

        # Define o tema rapidamente sem carregar preferências
        ctk.set_appearance_mode("System")

        dialog = ConsentDialog(temp_root)
        consent_given = dialog.show() # Bloqueia até o usuário escolher

        temp_root.destroy() # Destroi a root temporária
        temp_root = None # Limpa a referência

        if consent_given is True:
            logging.info("Consentimento de gravação ACEITO pelo usuário.")
        else:
            logging.warning("Consentimento de gravação RECUSADO pelo usuário. Aplicação será encerrada.")
            # Use a simple messagebox instead of creating another CTk window
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showinfo("Aplicação Encerrada", "O consentimento para gravação é necessário para usar esta aplicação.")
            root.destroy()
            sys.exit(0) # Saída normal

    except Exception as e:
        logging.critical(f"Erro ao exibir diálogo de consentimento: {e}", exc_info=True)
        if temp_root: # Tenta destruir se ainda existir
            try: temp_root.destroy()
            except: pass
        try: messagebox.showerror("Erro Crítico", f"Não foi possível obter o consentimento necessário:\n{e}")
        except: pass
        sys.exit(1)
    # --- FIM NOVO ---

    # --- Continua somente se consent_given for True ---
    logging.info("Iniciando aplicação WATS (após consentimento)...")

    # 2. Carrega as variáveis de ambiente do .env (ou do sistema)
    try:
        env_loaded = load_environment_variables()
        if not env_loaded:
             logging.warning("Arquivo .env não encontrado. Dependendo das variáveis de ambiente do sistema.")
             # Decida se quer parar aqui caso .env seja obrigatório
    except Exception as e:
        logging.critical(f"Erro ao tentar carregar .env: {e}", exc_info=True)
        messagebox.showerror("Erro Crítico", f"Erro ao carregar configurações de ambiente: {e}")
        sys.exit(1)

    # 3. Cria a instância das Settings AGORA
    try:
        start_settings = time.perf_counter()
        settings_instance = Settings()
        logging.info(f"Instância de Settings criada em {time.perf_counter() - start_settings:0.3f}s.")
        if not settings_instance.has_db_config():
             logging.critical("Configuração de banco ausente após carregar .env!")
             messagebox.showerror("Erro de Configuração", "Configuração de banco ausente!\nVerifique o arquivo .env ou as variáveis de ambiente.")
             sys.exit(1)
        else:
            logging.info("Configuração de banco encontrada e validada.")
    except Exception as e:
        logging.critical(f"Erro ao criar instância de Settings: {e}", exc_info=True)
        messagebox.showerror("Erro Crítico", f"Erro ao carregar configurações: {e}")
        sys.exit(1)

    # 4. Importa e executa o app principal, passando a instância de settings
    try:
        # Importa run_app DEPOIS que tudo foi configurado
        from wats_app.main import run_app
        run_app(settings_instance)
    except ImportError as e:
        logging.critical(f"Erro ao importar wats_app.main: {e}", exc_info=True)
        messagebox.showerror("Erro de Importação", f"Não foi possível encontrar o módulo principal da aplicação:\n{e}")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Erro fatal durante a execução da aplicação: {e}", exc_info=True)
        try: messagebox.showerror("Erro Fatal", f"A aplicação encontrou um erro inesperado e precisa fechar:\n\n{e}")
        except: pass
        sys.exit(1)

if __name__ == "__main__":
    main()