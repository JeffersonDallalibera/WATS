import time
import importlib
import sys

print('PID', sys.pid if hasattr(sys, 'pid') else '')


def time_import(name):
    t0 = time.perf_counter()
    try:
        importlib.import_module(name)
        ok = True
        err = ''
    except Exception as e:
        ok = False
        err = str(e)
    t1 = time.perf_counter()
    print(f"IMPORT {name:20} | {t1-t0:0.3f}s | {'OK' if ok else 'ERR'} {err}")


modules = [
    'dotenv',
    'customtkinter',
    'tkinter',
    'pyodbc',
    'psycopg2',
    'json',
    'socket',
    'threading']
for m in modules:
    time_import(m)

# Time importing app modules
print('\n-- Importing wats_app.main --')
t0 = time.perf_counter()
try:
    ma = importlib.import_module('wats_app.main')
    imp_ok = True
    imp_err = ''
except Exception as e:
    ma = None
    imp_ok = False
    imp_err = str(e)
t1 = time.perf_counter()
print(f"IMPORT wats_app.main       | {t1-t0:0.3f}s | {'OK' if imp_ok else 'ERR'} {imp_err}")

# Time instantiating Application (may create a GUI window)
print('\n-- Instantiating Application (will destroy immediately) --')
try:
    from src.wats.app_window import Application
    t0 = time.perf_counter()
    app = Application()
    t1 = time.perf_counter()
    print(f"Application().__init__     | {t1-t0:0.3f}s | OK")
    # Avoid entering the Tk mainloop. Process pending events so the window
    # can initialize and then destroy it. This prevents the script from
    # blocking and avoids KeyboardInterrupt during profiling.
    try:
        # Schedule idle tasks and process any pending events
        app.update_idletasks()
        app.update()
    except Exception:
        pass
    try:
        app.destroy()
    except Exception:
        pass
except Exception as e:
    print(f"Application instantiation error: {e}")

print('\nDone')
