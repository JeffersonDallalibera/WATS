import logging
from .app_window import Application

def run_app(settings_instance):
    """
    Inicializa a aplicação principal com as configurações fornecidas.
    """
    try:
        logging.info("Iniciando aplicação WATS...")
        import time as _time
        _t0 = _time.perf_counter()
        app = Application(settings_instance)
        logging.info(f"Application initialized in {_time.perf_counter()-_t0:0.3f}s")
        app.mainloop()
        
    except Exception as e:
        logging.critical(f"Erro fatal na aplicação: {e}", exc_info=True)
        # Tenta mostrar um messagebox de erro fatal
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Erro Fatal", f"Ocorreu um erro crítico e a aplicação será fechada.\n\n{e}\n\nVerifique o wats_app.log para detalhes.")
            root.destroy()
        except Exception:
            pass # Se nem o tkinter funcionar, apenas loga e sai