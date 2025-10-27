# API para Upload de Gravações - WATS

## 📡 Visão Geral

O sistema de API para upload de gravações permite que o WATS envie automaticamente as sessões gravadas para um servidor de armazenamento externo. Este sistema oferece backup automático, armazenamento centralizado e redundância para as gravações de sessões RDP.

## 🎯 Funcionalidades

### ✅ Recursos Implementados:

- **Upload Automático**: Envio automático das gravações após conclusão
- **Retry Inteligente**: Tentativas automáticas com backoff exponencial
- **Upload Concorrente**: Múltiplos uploads simultâneos configuráveis
- **Monitoramento de Progresso**: Callbacks para atualizações de progresso
- **Autenticação Segura**: Token-based authentication
- **Validação de Metadados**: Verificação de integridade dos dados
- **Cleanup Automático**: Exclusão opcional de arquivos após upload
- **Estado Persistente**: Manutenção de estado entre reinicializações
- **Upload de Arquivos Antigos**: Processamento de gravações anteriores

### 🔧 Componentes Arquiteturais:

1. **RecordingUploadClient**: Cliente HTTP para comunicação com API
2. **UploadManager**: Gerenciador de fila e coordenação de uploads
3. **ApiIntegrationManager**: Integração com sistema de gravação WATS
4. **ProgressFileWrapper**: Monitoramento de progresso de upload

## ⚙️ Configuração

### Exemplo de Configuração no `config.json`:

```json
{
  "database": {
    "type": "sqlserver",
    "server": "192.168.1.100",
    "database": "WATS_DB",
    "username": "wats_user",
    "password": "senha_segura",
    "port": "1433"
  },
  "recording": {
    "enabled": true,
    "auto_start": true,
    "mode": "rdp_window",
    "output_dir": "D:\\WATS_Recordings",
    "fps": 15,
    "quality": 23,
    "resolution_scale": 1.0,
    "max_file_size_mb": 200,
    "max_duration_minutes": 60
  },
  "api": {
    "enabled": true,
    "base_url": "https://storage.company.com/api",
    "api_token": "your_secure_api_token_here",
    "auto_upload": true,
    "upload_timeout": 60,
    "max_retries": 3,
    "max_concurrent_uploads": 2,
    "delete_after_upload": false,
    "upload_older_recordings": true,
    "max_file_age_days": 30
  }
}
```

### 📋 Parâmetros de Configuração:

| Parâmetro                 | Tipo    | Padrão | Descrição                                 |
| ------------------------- | ------- | ------ | ----------------------------------------- |
| `enabled`                 | boolean | false  | Habilita/desabilita sistema de upload     |
| `base_url`                | string  | ""     | URL base da API de upload                 |
| `api_token`               | string  | ""     | Token de autenticação da API              |
| `auto_upload`             | boolean | false  | Upload automático após gravação           |
| `upload_timeout`          | integer | 60     | Timeout de upload em segundos             |
| `max_retries`             | integer | 3      | Máximo de tentativas de upload            |
| `max_concurrent_uploads`  | integer | 2      | Uploads simultâneos permitidos            |
| `delete_after_upload`     | boolean | false  | Excluir arquivos após upload bem-sucedido |
| `upload_older_recordings` | boolean | true   | Fazer upload de gravações anteriores      |
| `max_file_age_days`       | integer | 30     | Idade máxima de arquivos para upload      |

## 🚀 Como Usar

### 1. Configuração Inicial

```python
from wats_app.api import ApiIntegrationManager

# Inicializar com settings do WATS
api_manager = ApiIntegrationManager(settings)

# Verificar se inicializou corretamente
if api_manager.is_initialized:
    print("✅ API upload system ready")
else:
    print("❌ API upload system failed to initialize")
```

### 2. Upload Manual de Gravação

```python
from pathlib import Path

video_file = Path("session_123_ServerName_20241026_150000.mp4")
metadata_file = Path("session_123_metadata.json")

# Queue upload
task_id = api_manager.upload_recording(video_file, metadata_file)

if task_id:
    print(f"Upload queued: {task_id}")

    # Monitor status
    status = api_manager.get_upload_status(task_id)
    print(f"Status: {status['status']} - Progress: {status['progress']}%")
```

### 3. Upload de Gravações Antigas

```python
from pathlib import Path

recordings_dir = Path("C:/WATS_Recordings")

# Upload recordings up to 30 days old
task_ids = api_manager.upload_older_recordings(recordings_dir, max_age_days=30)

print(f"Queued {len(task_ids)} older recordings for upload")
```

### 4. Monitoramento de Status

```python
# Get overall queue status
queue_status = api_manager.get_queue_status()

print(f"Queue size: {queue_status['queue_size']}")
print(f"Active uploads: {queue_status['active_uploads']}")
print(f"Completed: {queue_status['completed_uploads']}")
print(f"Failed: {queue_status['failed_uploads']}")
```

### 5. Callbacks para UI

```python
def on_upload_started(task_id: str, filename: str):
    print(f"🚀 Upload started: {filename} ({task_id})")

def on_upload_progress(task_id: str, progress: int):
    print(f"📊 Upload progress: {task_id} - {progress}%")

def on_upload_completed(task_id: str, server_file_id: str):
    print(f"✅ Upload completed: {task_id} -> {server_file_id}")

def on_upload_failed(task_id: str, error: str):
    print(f"❌ Upload failed: {task_id} - {error}")

# Set callbacks
api_manager.on_upload_started = on_upload_started
api_manager.on_upload_progress = on_upload_progress
api_manager.on_upload_completed = on_upload_completed
api_manager.on_upload_failed = on_upload_failed
```

## 🌐 Endpoints da API

### Endpoints Esperados no Servidor:

1. **Health Check**

   - `GET /health`
   - Verifica se a API está funcionando

2. **Criar Sessão de Upload**

   - `POST /uploads/create-session`
   - Cria uma nova sessão de upload
   - Body: metadados da gravação

3. **Upload de Arquivo**

   - `POST /uploads/{session_id}/file`
   - Faz upload do arquivo de vídeo/metadados

4. **Finalizar Upload**

   - `POST /uploads/{session_id}/finalize`
   - Finaliza a sessão de upload

5. **Status do Upload**

   - `GET /uploads/{session_id}/status`
   - Consulta o status de um upload

6. **Listar Gravações**

   - `GET /recordings`
   - Lista gravações no servidor

7. **Excluir Gravação**
   - `DELETE /recordings/{file_id}`
   - Exclui uma gravação do servidor

### Exemplo de Requisição:

```http
POST /uploads/create-session
Authorization: Bearer your_api_token_here
Content-Type: application/json

{
  "session_id": "rdp_123_1729950022",
  "connection_info": {
    "con_codigo": 123,
    "ip": "192.168.1.100",
    "name": "Production Server",
    "user": "administrator",
    "connection_type": "RDP",
    "wats_user": "jefferson.silva",
    "wats_user_machine": "DESKTOP-ABC123",
    "wats_user_ip": "192.168.1.50"
  },
  "file_size": 15728640,
  "metadata": {
    "start_time": "2024-10-26T15:00:22.123456",
    "recorder_settings": {
      "fps": 10,
      "quality": 23,
      "resolution_scale": 1.0,
      "max_file_size_mb": 100,
      "max_duration_minutes": 30
    }
  }
}
```

### Resposta Esperada:

```json
{
  "session_id": "upload_session_xyz789",
  "metadata_upload_url": "https://storage.company.com/upload/metadata/xyz789",
  "video_upload_url": "https://storage.company.com/upload/video/xyz789",
  "expires_at": "2024-10-26T16:00:22.123456Z"
}
```

## 🔒 Segurança

### Autenticação:

- **Token Bearer**: Todas as requisições usam `Authorization: Bearer {token}`
- **Token Seguro**: Armazenado de forma criptografada no config
- **Timeout de Sessão**: Sessions de upload expiram automaticamente

### Validação:

- **Metadados**: Validação de estrutura e conteúdo
- **Tamanho de Arquivo**: Verificação de limites
- **Integridade**: Checksums e validação de transferência

## 📊 Monitoramento e Logs

### Logs Detalhados:

```
INFO - RecordingUploadClient initialized for https://storage.company.com/api
INFO - API connection test successful
INFO - UploadManager started with 2 workers
INFO - Recording queued for upload: session_123_ServerName.mp4 (task: upload_1729950022_session_123)
INFO - Upload completed: upload_1729950022_session_123
```

### Métricas Disponíveis:

- **Upload Queue Size**: Tamanho da fila de upload
- **Active Uploads**: Uploads em andamento
- **Completed Uploads**: Uploads concluídos
- **Failed Uploads**: Uploads falhados
- **Upload Progress**: Progresso individual por task
- **Retry Count**: Número de tentativas por upload

## 🚨 Tratamento de Erros

### Tipos de Erro:

1. **NetworkError**: Problemas de conectividade
2. **AuthenticationError**: Falhas de autenticação
3. **ServerError**: Erros do servidor (5xx)
4. **ValidationError**: Dados inválidos (4xx)
5. **UploadError**: Falhas específicas de upload

### Estratégia de Retry:

- **Backoff Exponencial**: 2^retry_count segundos (máx 60s)
- **Erros Retriáveis**: NetworkError, ServerError (500, 502, 503, 504)
- **Erros Não-Retriáveis**: AuthenticationError, ValidationError
- **Máximo de Tentativas**: Configurável (padrão: 3)

### Exemplo de Tratamento:

```python
try:
    task_id = api_manager.upload_recording(video_file, metadata_file)
except ApiError as e:
    if isinstance(e, AuthenticationError):
        print("❌ Authentication failed - check API token")
    elif isinstance(e, NetworkError):
        print("🌐 Network error - will retry automatically")
    else:
        print(f"💥 Upload error: {e.message}")
```

## 🧪 Testes

### Executar Testes:

```bash
# Execute o script de teste
python test_api_upload_system.py
```

### Cobertura de Testes:

- ✅ **Client Authentication**: Testa autenticação com API
- ✅ **Upload Flow**: Testa fluxo completo de upload
- ✅ **Error Handling**: Testa tratamento de erros
- ✅ **Retry Logic**: Testa lógica de retry
- ✅ **Progress Tracking**: Testa monitoramento de progresso
- ✅ **File Validation**: Testa validação de arquivos
- ✅ **Queue Management**: Testa gerenciamento de fila
- ✅ **State Persistence**: Testa persistência de estado

### Resultados Esperados:

```
🚀 WATS API Upload System - Test Suite
==================================================
test_connection_test_success (test_api_upload_system.TestRecordingUploadClient) ... ok
test_upload_recording_success (test_api_upload_system.TestRecordingUploadClient) ... ok
test_queue_upload (test_api_upload_system.TestUploadManager) ... ok
test_initialization_success (test_api_upload_system.TestApiIntegrationManager) ... ok

--------------------------------------------------
Ran 12 tests in 0.234s

OK

📊 Test Results Summary:
✅ Tests run: 12
❌ Failures: 0
💥 Errors: 0

🎉 ALL TESTS PASSED! API upload system is working correctly.
```

## 📈 Cenários de Uso

### 1. **Empresa com Backup Centralizado**

```json
{
  "api": {
    "enabled": true,
    "base_url": "https://backup.empresa.com/api",
    "auto_upload": true,
    "delete_after_upload": true,
    "max_concurrent_uploads": 3
  }
}
```

### 2. **Compliance e Auditoria**

```json
{
  "api": {
    "enabled": true,
    "base_url": "https://compliance-storage.empresa.com/api",
    "auto_upload": true,
    "delete_after_upload": false,
    "upload_older_recordings": true,
    "max_file_age_days": 365
  }
}
```

### 3. **Ambiente de Desenvolvimento**

```json
{
  "api": {
    "enabled": true,
    "base_url": "https://dev-storage.empresa.com/api",
    "auto_upload": false,
    "delete_after_upload": false,
    "upload_timeout": 30,
    "max_retries": 1
  }
}
```

## 🔮 Próximos Passos

### Funcionalidades Futuras:

1. **Compressão**: Compressão automática antes do upload
2. **Encryption**: Criptografia de arquivos em trânsito
3. **Bandwidth Throttling**: Controle de largura de banda
4. **Scheduling**: Agendamento de uploads fora do horário comercial
5. **Cloud Providers**: Integração direta com AWS S3, Azure Blob, Google Cloud
6. **Webhooks**: Notificações via webhook de eventos de upload

### Melhorias Planejadas:

1. **Interface Gráfica**: Painel de controle de uploads na UI
2. **Estatísticas**: Dashboard com métricas de upload
3. **Configuração Avançada**: Mais opções de configuração
4. **Performance**: Otimizações de velocidade e memória

---

## 📞 Suporte

Para questões sobre a API de upload:

1. **Logs**: Verificar logs do WATS em `wats_app.log`
2. **Configuração**: Validar configurações no `config.json`
3. **Conectividade**: Testar acesso à URL da API
4. **Autenticação**: Verificar validade do token da API

**Exemplo de Debug:**

```python
# Habilitar logs detalhados
import logging
logging.getLogger('wats_app.api').setLevel(logging.DEBUG)

# Testar conexão
if api_manager.upload_client:
    connection_ok = api_manager.upload_client.test_connection()
    print(f"API connection: {'✅ OK' if connection_ok else '❌ FAILED'}")
```
