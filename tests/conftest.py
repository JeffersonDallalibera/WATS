"""Test configuration and fixtures for WATS application."""

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, patch

import pytest

from src.wats.config import Settings
from src.wats.db.database_manager import DatabaseManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Fornece um diretório temporário para testes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_settings(temp_dir: Path) -> Settings:
    """Fornece uma instância mock das configurações para testes."""
    config_data = {
        "database": {
            "type": "sqlite",
            "connection_string": f"sqlite:///{temp_dir}/test.db"
        },
        "recording": {
            "enabled": False,
            "output_path": str(temp_dir / "recordings")
        },
        "api": {
            "enabled": False,
            "base_url": "http://localhost:8000"
        }
    }
    
    with patch.dict(os.environ, {"WATS_DEMO_MODE": "true"}):
        settings = Settings()
        settings._config_data = config_data
        return settings


@pytest.fixture
def mock_db_manager() -> Mock:
    """Fornece um mock do DatabaseManager para testes."""
    mock_manager = Mock(spec=DatabaseManager)
    mock_manager.is_demo_mode = True
    mock_manager.test_connection.return_value = (True, "Mock connection successful")
    return mock_manager


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configura automaticamente o ambiente de teste."""
    # Força modo demo para todos os testes
    with patch.dict(os.environ, {"WATS_DEMO_MODE": "true"}):
        yield


@pytest.fixture
def sample_user_data():
    """Fornece dados de exemplo de usuários para testes."""
    return [
        (1, "admin", True, True),
        (2, "user1", True, False),
        (3, "user2", False, False),
        (4, "test_user", True, False)
    ]


@pytest.fixture
def sample_connection_data():
    """Fornece dados de exemplo de conexões para testes."""
    return [
        (1, "Server1", "Windows Server", 1, "192.168.1.100", 3389, "administrator", "encrypted_pass", "RDP", "Production", ""),
        (2, "DevBox", "Development Machine", 2, "192.168.1.101", 22, "developer", "encrypted_pass", "SSH", "Development", ""),
        (3, "TestDB", "Test Database", 1, "192.168.1.102", 1433, "sa", "encrypted_pass", "Database", "Testing", "")
    ]


class TestHelper:
    """Classe auxiliar com métodos utilitários para testes."""
    
    @staticmethod
    def create_mock_event(event_type: str = "Button-1", x: int = 0, y: int = 0) -> Mock:
        """Cria um evento mock para testes de interface."""
        event = Mock()
        event.type = event_type
        event.x = x
        event.y = y
        return event
    
    @staticmethod
    def assert_log_contains(caplog, level: str, message: str) -> None:
        """Verifica se uma mensagem específica foi logada."""
        records = [record for record in caplog.records if record.levelname == level]
        messages = [record.message for record in records]
        assert any(message in msg for msg in messages), f"Log message '{message}' not found in {level} logs"


# Markers personalizados para categorizar testes
pytestmark = pytest.mark.unit