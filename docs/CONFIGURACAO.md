# 📋 Configuração do WATS - Sistema de Gravação RDP

## 🎯 Como Configurar o Nível de Logging

O WATS usa o arquivo `config.json` localizado **na mesma pasta do executável** para todas as configurações.

### 📍 Localização do Arquivo de Configuração

**Para o executável:** `dist/WATS/config.json`
**Para desenvolvimento:** `config.json` na raiz do projeto

### 🔧 Configurações de Logging

No arquivo `config.json`, seção `application`:

```json
{
  "application": {
    "log_level": "DEBUG"
  }
}
```

**Níveis Disponíveis:**

- `DEBUG` - Logs muito detalhados (recomendado para debugging)
- `INFO` - Logs informativos (padrão recomendado)
- `WARNING` - Apenas warnings e erros
- `ERROR` - Apenas erros críticos

### 📁 Onde os Logs são Salvos

- Executável (PyInstaller): `dist/WATS/wats_app.log` (na mesma pasta do executável)
- Desenvolvimento: `<pasta do projeto>/wats_app.log`
- Console: durante a execução do aplicativo

Observação: o caminho é resolvido pelo WATS automaticamente usando a pasta de execução (ver `get_user_data_dir()` em `src/wats/config.py`).

### 🎛️ Configurações Principais Disponíveis

#### 1. **Banco de Dados**

```json
{
  "database": {
    "type": "sqlserver",
    "server": "seu-servidor",
    "database": "nome-database",
    "username": "usuario",
    "password": "senha",
    "port": "1433"
  }
}
```

#### 2. **Sistema de Gravação**

```json
{
  "recording": {
    "enabled": true,
    "auto_start": true,
    "mode": "rdp_window",
    "output_dir": "{USERPROFILE}/Videos/Wats",
    "fps": 10,
    "quality": 23,
    "max_file_size_mb": 100,
    "max_duration_minutes": 30
  }
}
```

**🔧 Variáveis de Sistema Suportadas no `output_dir`:**

- `{USERPROFILE}` - Pasta do usuário (C:/Users/username)
- `{VIDEOS}` - Pasta de vídeos do usuário
- `{DOCUMENTS}` - Pasta de documentos do usuário
- `{DESKTOP}` - Área de trabalho do usuário
- `{APPDATA}` - AppData/Roaming do usuário
- `{LOCALAPPDATA}` - AppData/Local do usuário
- `{DOWNLOADS}` - Pasta de downloads do usuário
- `{PICTURES}` - Pasta de imagens do usuário
- `{TEMP}` - Pasta temporária do sistema

**📁 Criação Automática de Pastas:**

- ✅ O WATS **cria automaticamente** as pastas que não existem
- ✅ Valida se a pasta é **gravável** antes de iniciar
- ✅ Exibe **logs informativos** sobre a criação das pastas

**Exemplos de uso:**

- `{VIDEOS}/WATS` → `C:/Users/username/Videos/WATS` (criada automaticamente)
- `{DOCUMENTS}/Gravacoes` → `C:/Users/username/Documents/Gravacoes` (criada automaticamente)
- `{USERPROFILE}/MeusVideos` → `C:/Users/username/MeusVideos` (criada automaticamente)

#### 3. **Interface e Aplicação**

```json
{
  "application": {
    "log_level": "INFO",
    "theme": "Dark",
    "window_title": "WATS - Sistema de Gravação RDP",
    "window_geometry": "1200x800"
  }
}
```

#### 4. **Configurações de Performance**

```json
{
  "performance": {
    "max_cpu_usage_percent": 80,
    "memory_limit_mb": 1024,
    "min_free_space_gb": 5
  }
}
```

#### 5. **Segurança**

```json
{
  "security": {
    "encrypt_recordings": false,
    "require_password": false,
    "audit_log_enabled": true
  }
}
```

### 🔄 Como Aplicar Mudanças

1. **Edite** o arquivo `config.json` na pasta do executável
2. **Reinicie** o WATS
3. **Verifique** os logs para confirmar as mudanças

### ⚠️ Observações Importantes

- **Backup:** Sempre faça backup do `config.json` antes de modificar
- **Formato:** Mantenha a sintaxe JSON válida (use aspas duplas, vírgulas corretas)
- **Caminhos:** Use barras normais `/` ou duplas barras `\\` nos caminhos do Windows
- **Prioridade:** Variáveis de ambiente têm prioridade sobre `config.json`

### 🚀 Exemplo de Configuração Completa para Produção

```json
{
  "application": {
    "log_level": "INFO",
    "theme": "Dark"
  },
  "recording": {
    "enabled": true,
    "auto_start": true,
    "output_dir": "D:/Gravacoes/WATS",
    "fps": 15,
    "quality": 20,
    "max_file_size_mb": 200
  },
  "performance": {
    "max_cpu_usage_percent": 70,
    "memory_limit_mb": 2048
  }
}
```

---

**💡 Dica:** Para debugging, use `"log_level": "DEBUG"` e verifique o arquivo de log em `%APPDATA%\WATS\wats_app.log`

## 📦 Onde o WATS procura o `config.json`

- Executável: primeiro em `dist/WATS/config.json`; fallback para arquivo embutido no executável
- Desenvolvimento: primeiro em `config/config.json`; fallback para `./config.json` na raiz do projeto

Essa ordem garante que você possa distribuir um executável com um `config.json` ao lado, e em desenvolvimento manter os arquivos de configuração versionados em `config/`.

## 🌐 Variáveis de Ambiente Suportadas (além do config.json)

As variáveis de ambiente têm prioridade sobre o `config.json` quando presentes:

Banco de Dados:

- `DB_TYPE`, `DB_SERVER`, `DB_DATABASE`, `DB_UID`, `DB_PWD`, `DB_PORT`

Gravação:

- `RECORDING_ENABLED`, `RECORDING_AUTO_START`, `RECORDING_MODE`
- `RECORDING_OUTPUT_DIR`, `RECORDING_FPS`, `RECORDING_QUALITY`, `RECORDING_RESOLUTION_SCALE`
- `RECORDING_MAX_FILE_SIZE_MB`, `RECORDING_MAX_DURATION_MINUTES`
- `RECORDING_MAX_TOTAL_SIZE_GB`, `RECORDING_MAX_FILE_AGE_DAYS`, `RECORDING_CLEANUP_INTERVAL_HOURS`

API de Upload:

- `API_ENABLED`, `API_BASE_URL`, `API_TOKEN`, `API_AUTO_UPLOAD`
- `API_UPLOAD_TIMEOUT`, `API_MAX_RETRIES`, `API_MAX_CONCURRENT_UPLOADS`
- `API_DELETE_AFTER_UPLOAD`, `API_UPLOAD_OLDER_RECORDINGS`, `API_MAX_FILE_AGE_DAYS`
