# WATS_Project/wats_app/db/demo_adapter.py

"""
Adaptador que detecta automaticamente quando usar mock service
baseado na disponibilidade de conexão com o banco de dados.
"""

import logging
from typing import Any, Optional
from src.wats.config import is_demo_mode

logger = logging.getLogger(__name__)

class DemoAdapter:
    """Adaptador que decide entre usar banco real ou mock service."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._mock_service = None
    
    def get_mock_service(self):
        """Retorna instância do mock service (lazy loading)."""
        if self._mock_service is None:
            from docs.mock_data_service import get_mock_service
            self._mock_service = get_mock_service()
        return self._mock_service
    
    def should_use_mock(self, cursor: Optional[Any] = None) -> bool:
        """Determina se deve usar mock service baseado no contexto."""
        # Se está explicitamente em modo demo
        if is_demo_mode():
            return True
            
        # Se não conseguiu obter cursor/conexão
        if cursor is None:
            return True
            
        return False
    
    def execute_with_fallback(self, operation_name: str, mock_method: str, *args, **kwargs):
        """
        Executa operação tentando banco real primeiro, faz fallback para mock se necessário.
        
        Args:
            operation_name: Nome da operação para logs
            mock_method: Nome do método no mock service
            *args, **kwargs: Argumentos para o método mock
        """
        cursor = None
        
        try:
            # Tenta obter cursor do banco real
            if not is_demo_mode():
                cursor = self.db_manager.get_cursor()
        except Exception as e:
            logger.warning(f"Falha ao conectar banco para {operation_name}: {e}")
            cursor = None
        
        # Decide se usa mock
        if self.should_use_mock(cursor):
            logger.info(f"[DEMO] Usando mock service para {operation_name}")
            mock_service = self.get_mock_service()
            method = getattr(mock_service, mock_method)
            return method(*args, **kwargs)
        
        # Se chegou aqui, usa banco real
        # (implementação específica fica no repositório)
        return None  # Indica que deve usar banco real