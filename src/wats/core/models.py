"""Data models and validation using Pydantic."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator
from pydantic.networks import IPvAnyAddress


class ConnectionType(str, Enum):
    """Tipos de conexão suportados."""

    RDP = "RDP"
    SSH = "SSH"
    VNC = "VNC"
    TELNET = "TELNET"
    DATABASE = "Database"
    WEB = "Web"


class UserRole(str, Enum):
    """Roles de usuário."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class DatabaseConfig(BaseModel):
    """Configuração de banco de dados para SQL Server."""

    type: str = Field(default="sqlserver", description="Tipo do banco (sqlserver, sqlite)")
    host: Optional[str] = Field(None, description="Host do SQL Server")
    port: Optional[int] = Field(1433, ge=1, le=65535, description="Porta do SQL Server")
    database: str = Field(..., description="Nome do banco de dados")
    username: Optional[str] = Field(None, description="Usuário do SQL Server")
    password: Optional[str] = Field(None, description="Senha do SQL Server")
    connection_string: Optional[str] = Field(None, description="String de conexão completa")
    driver: str = Field(default="ODBC Driver 17 for SQL Server", description="Driver ODBC")
    trust_server_certificate: bool = Field(
        default=True, description="Confiar no certificado do servidor"
    )
    encrypt: bool = Field(default=False, description="Usar conexão criptografada")
    integrated_security: bool = Field(default=False, description="Usar autenticação do Windows")
    mars_connection: bool = Field(default=True, description="Multiple Active Result Sets")
    connection_timeout: int = Field(default=30, ge=5, le=300, description="Timeout de conexão")

    @root_validator
    def validate_connection_info(cls, values):
        """Valida se há informações suficientes para conexão com SQL Server."""
        conn_string = values.get("connection_string")
        host = values.get("host")
        db_type = values.get("type")

        if db_type == "sqlserver":
            if not conn_string and not host:
                raise ValueError(
                    "Para SQL Server é necessário fornecer connection_string OU host/database"
                )

            # Se usar integrated security, não precisa de usuário/senha
            integrated = values.get("integrated_security", False)
            username = values.get("username")
            password = values.get("password")

            if not integrated and not conn_string:
                if not username or not password:
                    raise ValueError(
                        "Para SQL Server sem integrated security é necessário username E password"
                    )

        return values

    @validator("type")
    def validate_db_type(cls, v):
        """Valida se o tipo de banco é suportado."""
        valid_types = ["sqlserver", "sqlite"]
        if v not in valid_types:
            raise ValueError(f"Tipo de banco deve ser um de: {valid_types}")
        return v


class APIConfig(BaseModel):
    """Configuração da API."""

    enabled: bool = Field(default=False, description="Se a API está habilitada")
    base_url: str = Field(..., description="URL base da API")
    api_key: Optional[str] = Field(None, description="Chave da API")
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout em segundos")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="Tentativas de retry")

    @validator("base_url")
    def validate_url(cls, v):
        """Valida se a URL está no formato correto."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        return v


class RecordingConfig(BaseModel):
    """Configuração de gravação."""

    enabled: bool = Field(default=True, description="Se gravação está habilitada")
    output_path: str = Field(..., description="Caminho de saída das gravações")
    max_file_size_mb: int = Field(
        default=100, ge=1, le=1000, description="Tamanho máximo do arquivo em MB"
    )
    fps: int = Field(default=10, ge=1, le=60, description="Frames por segundo")
    quality: int = Field(default=80, ge=1, le=100, description="Qualidade da gravação")
    auto_rotation: bool = Field(default=True, description="Rotação automática de arquivos")

    @validator("output_path")
    def validate_output_path(cls, v):
        """Valida se o caminho é válido."""
        import os

        if not os.path.isabs(v):
            raise ValueError("Caminho deve ser absoluto")
        return v


class ConnectionModel(BaseModel):
    """Modelo de conexão validado."""

    id: Optional[int] = Field(None, description="ID da conexão")
    name: str = Field(..., min_length=1, max_length=100, description="Nome da conexão")
    description: Optional[str] = Field(None, max_length=500, description="Descrição")
    connection_type: ConnectionType = Field(..., description="Tipo de conexão")
    host: str = Field(..., description="Host ou IP")
    port: int = Field(..., ge=1, le=65535, description="Porta")
    username: str = Field(..., min_length=1, description="Usuário")
    password: str = Field(..., description="Senha (será criptografada)")
    group_id: Optional[int] = Field(None, description="ID do grupo")
    environment: str = Field(default="Production", description="Ambiente (Dev/Test/Prod)")
    particularity: Optional[str] = Field(None, description="Particularidades")
    created_at: Optional[datetime] = Field(None, description="Data de criação")
    updated_at: Optional[datetime] = Field(None, description="Data de atualização")

    @validator("host")
    def validate_host(cls, v):
        """Valida se o host é um IP válido ou hostname."""
        try:
            # Tenta validar como IP
            IPvAnyAddress(v)
        except BaseException:
            # Se não for IP, valida como hostname
            if not v.replace("-", "").replace(".", "").replace("_", "").isalnum():
                raise ValueError("Host deve ser um IP válido ou hostname")
        return v

    class Config:
        """Configuração do modelo."""

        use_enum_values = True
        validate_assignment = True


class UserModel(BaseModel):
    """Modelo de usuário validado."""

    id: Optional[int] = Field(None, description="ID do usuário")
    username: str = Field(..., min_length=3, max_length=50, description="Nome de usuário")
    email: Optional[str] = Field(None, description="Email do usuário")
    is_admin: bool = Field(default=False, description="Se é administrador")
    is_active: bool = Field(default=True, description="Se está ativo")
    role: UserRole = Field(default=UserRole.USER, description="Role do usuário")
    group_ids: List[int] = Field(default_factory=list, description="IDs dos grupos")
    created_at: Optional[datetime] = Field(None, description="Data de criação")
    last_login: Optional[datetime] = Field(None, description="Último login")

    @validator("username")
    def validate_username(cls, v):
        """Valida nome de usuário."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username deve conter apenas letras, números, _ e -")
        return v

    @validator("email")
    def validate_email(cls, v):
        """Valida email se fornecido."""
        if v and "@" not in v:
            raise ValueError("Email deve ter formato válido")
        return v

    class Config:
        """Configuração do modelo."""

        use_enum_values = True


class GroupModel(BaseModel):
    """Modelo de grupo validado."""

    id: Optional[int] = Field(None, description="ID do grupo")
    name: str = Field(..., min_length=1, max_length=100, description="Nome do grupo")
    description: Optional[str] = Field(None, max_length=500, description="Descrição")
    is_active: bool = Field(default=True, description="Se está ativo")
    created_at: Optional[datetime] = Field(None, description="Data de criação")

    @validator("name")
    def validate_name(cls, v):
        """Valida nome do grupo."""
        if v.strip() != v:
            raise ValueError("Nome não pode ter espaços no início ou fim")
        return v


class LogEntryModel(BaseModel):
    """Modelo de entrada de log."""

    id: Optional[int] = Field(None, description="ID do log")
    user_name: str = Field(..., description="Nome do usuário")
    connection_id: int = Field(..., description="ID da conexão")
    connection_name: str = Field(..., description="Nome da conexão")
    action: str = Field(..., description="Ação realizada")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")
    ip_address: Optional[str] = Field(None, description="IP do usuário")
    computer_name: Optional[str] = Field(None, description="Nome do computador")
    session_id: Optional[str] = Field(None, description="ID da sessão")

    class Config:
        """Configuração do modelo."""

        validate_assignment = True


def validate_data(data: Dict[str, Any], model_class: BaseModel) -> BaseModel:
    """
    Valida dados usando um modelo Pydantic.

    Args:
        data: Dados a serem validados
        model_class: Classe do modelo Pydantic

    Returns:
        Instância validada do modelo

    Raises:
        ValidationError: Se os dados não são válidos
    """
    return model_class(**data)


def sanitize_input(value: Any, field_type: str = "string") -> Any:
    """
    Sanitiza entrada do usuário.

    Args:
        value: Valor a ser sanitizado
        field_type: Tipo do campo (string, int, float, bool)

    Returns:
        Valor sanitizado
    """
    if value is None:
        return None

    if field_type == "string":
        # Remove caracteres perigosos e limita tamanho
        clean_value = str(value).strip()
        # Remove caracteres de controle
        clean_value = "".join(char for char in clean_value if ord(char) >= 32)
        return clean_value[:1000]  # Limita a 1000 caracteres

    elif field_type == "int":
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Valor '{value}' não pode ser convertido para inteiro")

    elif field_type == "float":
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Valor '{value}' não pode ser convertido para float")

    elif field_type == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    return value
