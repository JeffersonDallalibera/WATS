# Configuração SQL Server para WATS

Este documento contém exemplos e guias para configurar o SQL Server no projeto WATS.

## Pré-requisitos

### 1. Microsoft ODBC Driver for SQL Server

Baixe e instale o driver ODBC mais recente:

- [ODBC Driver 17 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- [ODBC Driver 18 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) (mais recente)

### 2. Dependências Python

```bash
pip install pyodbc
```

## Configurações de Ambiente

### Desenvolvimento Local

```json
{
  "database": {
    "type": "sqlserver",
    "host": "localhost",
    "port": 1433,
    "database": "wats_dev",
    "username": "sa",
    "password": "SuaSenhaAqui",
    "driver": "ODBC Driver 17 for SQL Server",
    "trust_server_certificate": true,
    "encrypt": false,
    "integrated_security": false,
    "mars_connection": true,
    "connection_timeout": 30
  }
}
```

### Produção com Autenticação Windows

```json
{
  "database": {
    "type": "sqlserver",
    "host": "servidor-producao.empresa.com",
    "port": 1433,
    "database": "wats_production",
    "driver": "ODBC Driver 17 for SQL Server",
    "trust_server_certificate": true,
    "encrypt": true,
    "integrated_security": true,
    "mars_connection": true,
    "connection_timeout": 30
  }
}
```

### Connection String Customizada

```json
{
  "database": {
    "type": "sqlserver",
    "connection_string": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=servidor,1433;DATABASE=wats;UID=usuario;PWD=senha;TrustServerCertificate=yes;MARS_Connection=yes"
  }
}
```

## Variáveis de Ambiente

### Arquivo .env para Desenvolvimento

```bash
# SQL Server - Desenvolvimento
DB_TYPE=sqlserver
DB_HOST=localhost
DB_PORT=1433
DB_NAME=wats_dev
DB_USER=sa
DB_PASSWORD=SuaSenhaSegura123!
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUST_CERT=true
DB_ENCRYPT=false
DB_INTEGRATED_AUTH=false
DB_MARS=true
DB_TIMEOUT=30
```

### Arquivo .env para Produção

```bash
# SQL Server - Produção
DB_TYPE=sqlserver
DB_HOST=sql-server-prod.empresa.com
DB_PORT=1433
DB_NAME=wats_production
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUST_CERT=true
DB_ENCRYPT=true
DB_INTEGRATED_AUTH=true
DB_MARS=true
DB_TIMEOUT=60
```

## Exemplos de Connection String

### Autenticação SQL Server

```
DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=wats;UID=sa;PWD=senha;TrustServerCertificate=yes
```

### Autenticação Windows

```
DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=wats;Trusted_Connection=yes;TrustServerCertificate=yes
```

### Instância Nomeada

```
DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=wats;UID=sa;PWD=senha;TrustServerCertificate=yes
```

### Conexão Criptografada

```
DRIVER={ODBC Driver 17 for SQL Server};SERVER=servidor.empresa.com;DATABASE=wats;UID=usuario;PWD=senha;Encrypt=yes;TrustServerCertificate=no
```

## Troubleshooting

### Erro: "Data source name not found"

- Verifique se o driver ODBC está instalado
- Execute `pyodbc.drivers()` para listar drivers disponíveis

### Erro: "Login failed for user"

- Verifique credenciais de usuário e senha
- Confirme se o usuário tem permissões no banco
- Para autenticação Windows, use `integrated_security: true`

### Erro: "Cannot open database"

- Verifique se o banco de dados existe
- Confirme se o usuário tem acesso ao banco específico

### Erro de Conexão (Timeout)

- Verifique conectividade de rede com o servidor
- Aumente o `connection_timeout`
- Confirme se o SQL Server está aceitando conexões TCP/IP

### Erro de Certificado SSL

- Use `trust_server_certificate: true` para desenvolvimento
- Configure certificados SSL adequados para produção

## Scripts de Validação

### Testar Conexão

```python
import pyodbc

def test_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=wats;"
        "UID=sa;"
        "PWD=senha;"
        "TrustServerCertificate=yes"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            print(f"Conectado ao SQL Server: {version}")
            return True
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

### Listar Drivers Disponíveis

```python
import pyodbc

def list_drivers():
    drivers = pyodbc.drivers()
    sql_drivers = [d for d in drivers if 'SQL Server' in d]

    print("Drivers SQL Server disponíveis:")
    for driver in sql_drivers:
        print(f"  - {driver}")

if __name__ == "__main__":
    list_drivers()
```

## Configuração de Desenvolvimento

Para configurar rapidamente o ambiente de desenvolvimento:

1. **Instale o SQL Server Express** (gratuito)
2. **Configure o SA (System Administrator)**
3. **Crie o banco de dados**:
   ```sql
   CREATE DATABASE wats_dev;
   ```
4. **Configure as variáveis de ambiente**
5. **Execute o script de validação**:
   ```bash
   python scripts/validate_sqlserver_config.py
   ```

## Segurança

### Boas Práticas

- Use autenticação Windows quando possível
- Mantenha senhas em variáveis de ambiente, não no código
- Use conexões criptografadas em produção
- Configure firewalls adequadamente
- Mantenha drivers ODBC atualizados

### Exemplo de Configuração Segura

```json
{
  "database": {
    "type": "sqlserver",
    "host": "${DB_HOST}",
    "port": "${DB_PORT}",
    "database": "${DB_NAME}",
    "username": "${DB_USER}",
    "password": "${DB_PASSWORD}",
    "driver": "ODBC Driver 17 for SQL Server",
    "trust_server_certificate": true,
    "encrypt": true,
    "integrated_security": false,
    "mars_connection": true,
    "connection_timeout": 30
  }
}
```
