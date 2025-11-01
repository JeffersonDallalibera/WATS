"""Main entry point for WATS application."""

import logging
import time
import tkinter as tk
from tkinter import messagebox
from typing import NoReturn

from .app_window import Application
from .config import Settings


def run_app(settings_instance: Settings) -> NoReturn:
    """
    Inicializa a aplicação principal com as configurações fornecidas.

    Args:
        settings_instance: Instância configurada das configurações da aplicação

    Raises:
        Exception: Qualquer erro crítico que impeça a execução da aplicação
    """
    try:
        logging.info("Iniciando aplicação WATS...")
        start_time = time.perf_counter()
        app = Application(settings_instance)
        elapsed_time = time.perf_counter() - start_time
        logging.info(f"Application initialized in {elapsed_time:0.3f}s")
        app.mainloop()

    except Exception as e:
        logging.critical(f"Erro fatal na aplicação: {e}", exc_info=True)
        _show_fatal_error_dialog(str(e))
        raise


def _show_fatal_error_dialog(error_message: str) -> None:
    """
    Exibe um diálogo de erro fatal para o usuário.

    Args:
        error_message: Mensagem de erro a ser exibida
    """
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Erro Fatal",
            f"Ocorreu um erro crítico e a aplicação será fechada.\n\n{error_message}\n\nVerifique o wats_app.log para detalhes.",
        )
        root.destroy()
    except Exception:
        # Se nem o tkinter funcionar, apenas loga e continua
        pass
