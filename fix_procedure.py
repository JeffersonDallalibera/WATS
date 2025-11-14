"""Script para corrigir a stored procedure sp_Limpar_Logs_Orfaos"""
import logging
from src.wats.db.database_manager import DatabaseManager
from src.wats.config import Settings

logging.basicConfig(level=logging.INFO, format='%(message)s')

def fix_cleanup_procedure():
    """Executa o script de correção da stored procedure."""
    try:
        # Carrega settings
        settings = Settings()
        db = DatabaseManager(settings)
        
        with open('scripts/fix_cleanup_procedure.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Divide por GO e executa cada batch
        batches = [batch.strip() for batch in sql_script.split('GO') if batch.strip()]
        
        for i, batch in enumerate(batches, 1):
            if batch and not batch.startswith('--'):
                logging.info(f"Executando batch {i}/{len(batches)}...")
                try:
                    cursor = db.get_cursor()
                    cursor.execute(batch)
                    cursor.commit()
                    cursor.close()
                except Exception as e:
                    logging.error(f"Erro no batch {i}: {e}")
                    raise
        
        logging.info("\n✅ Stored procedure corrigida com sucesso!")
        logging.info("A procedure agora usa mensagens mais curtas para evitar truncamento.")
        
    except Exception as e:
        logging.error(f"\n❌ Erro ao corrigir procedure: {e}")
        raise

if __name__ == "__main__":
    fix_cleanup_procedure()
