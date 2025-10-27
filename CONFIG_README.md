# Configuração do WATS - config.json

Este arquivo permite configurar o WATS de forma fácil e intuitiva. As configurações neste arquivo têm prioridade sobre as variáveis de ambiente (.env).

## Estrutura do Arquivo

### Database (Banco de Dados)

**⚠️ IMPORTANTE - SEGURANÇA:**

- Para **ambientes de produção**, deixe os campos vazios ("") e use arquivo `.env` separado
- Para **testes locais**, pode preencher diretamente no config.json

- `type`: Tipo do banco (atualmente apenas "sqlserver")
- `server`: Endereço do servidor SQL Server (deixe "" para usar .env)
- `database`: Nome da base de dados (deixe "" para usar .env)
- `username`: Usuário para conexão (deixe "" para usar .env)
- `password`: Senha para conexão (deixe "" para usar .env) - **NUNCA compartilhe este arquivo se preenchido**
- `port`: Porta do servidor (padrão: 1433)

### Recording (Gravação de Sessão)

- `enabled`: true/false - Habilita ou desabilita gravação
- `auto_start`: true/false - Inicia gravação automaticamente ao conectar
- `mode`: Modo de gravação:
  - "full_screen": Grava tela inteira
  - "rdp_window": Grava apenas janela RDP (recomendado)
  - "active_window": Grava janela ativa
- `fps`: Frames por segundo (1-60, padrão: 10)
- `quality`: Qualidade do vídeo (0-51, menor = melhor, padrão: 23)
- `resolution_scale`: Escala da resolução (0.1-2.0, padrão: 1.0)
- `max_file_size_mb`: Tamanho máximo do arquivo em MB (padrão: 100)
- `max_duration_minutes`: Duração máxima em minutos (padrão: 30)
- `max_total_size_gb`: Tamanho total máximo em GB (padrão: 10.0)
- `max_file_age_days`: Idade máxima dos arquivos em dias (padrão: 30)
- `cleanup_interval_hours`: Intervalo de limpeza em horas (padrão: 6)

### Application (Aplicação)

- `log_level`: Nível de log (DEBUG, INFO, WARNING, ERROR)
- `theme`: Tema da interface (Dark, Light)

## Localização dos Arquivos

### Logs

Os logs são salvos na mesma pasta onde o WATS está instalado:

- `wats_app.log`: Log principal da aplicação

### Gravações

As gravações são salvas por padrão em:

- `recordings/`: Pasta de gravações (criada automaticamente)

## Exemplo de Configuração

### Opção 1: Configuração Segura (Recomendada para Produção)

```json
{
  "database": {
    "type": "sqlserver",
    "server": "",
    "database": "",
    "username": "",
    "password": "",
    "port": "1433"
  },
  "recording": {
    "enabled": true,
    "auto_start": true,
    "mode": "rdp_window",
    "fps": 10,
    "quality": 23
  }
}
```

_Crie um arquivo `.env` separado com as credenciais do banco_

### Opção 2: Configuração Direta (Apenas para Testes Locais)

```json
{
  "database": {
    "type": "sqlserver",
    "server": "seu-servidor.com",
    "database": "WATS_DB",
    "username": "wats_user",
    "password": "sua_senha_aqui",
    "port": "1433"
  },
  "recording": {
    "enabled": true,
    "auto_start": true,
    "mode": "rdp_window",
    "fps": 10,
    "quality": 23
  }
}
```

**⚠️ ATENÇÃO: Nunca compartilhe este arquivo se contiver senha real**

## Dicas de Configuração

1. **🔒 Segurança**: Para produção, use sempre a Opção 1 (campos vazios + arquivo .env)
2. **🏠 Ambiente local**: Opção 2 é aceitável apenas para desenvolvimento/testes
3. **📝 Primeira instalação**: Comece com a Opção 1 e crie o .env separadamente
4. **🎬 Teste de gravação**: Comece com `enabled: false` e teste manualmente
5. **⚡ Performance**: Para melhor performance, use `fps: 5-10` e `quality: 25-30`
6. **💾 Espaço em disco**: Monitore `max_total_size_gb` conforme necessário
7. **🐛 Logs**: Use `log_level: DEBUG` apenas para diagnóstico

## Fallback para .env

Se alguma configuração não estiver presente no config.json, o sistema tentará ler do arquivo .env correspondente.

## 🔐 Boas Práticas de Segurança

### ✅ Recomendado:

- **Produção**: Mantenha credenciais no arquivo `.env` separado
- **Controle de acesso**: Defina permissões apropriadas nos arquivos
- **Backup seguro**: Não inclua credenciais em backups compartilhados
- **Versionamento**: Adicione `config.json` ao `.gitignore` se contiver senhas

### ❌ Evite:

- Colocar senhas reais no `config.json` em ambiente de produção
- Compartilhar arquivos de configuração com credenciais
- Fazer commit de credenciais no controle de versão
- Deixar arquivos de configuração com permissões muito abertas

### 📁 Estrutura de Arquivos Sugerida:

```
WATS_App.exe
config.json          # Configurações gerais (sem credenciais)
.env                  # Credenciais do banco (protegido)
wats_app.log         # Logs da aplicação
wats_settings.json   # Configurações de UI (tema, etc.)
recordings/          # Pasta de gravações
```

## 🔧 Criando Arquivo .env

Crie um arquivo `.env` na mesma pasta do executável:

```bash
# Configurações do Banco de Dados
DB_TYPE=sqlserver
DB_SERVER=seu-servidor.com
DB_DATABASE=WATS_DB
DB_UID=usuario_banco
DB_PWD=senha_super_secreta
DB_PORT=1433

# Configurações de Gravação (opcionais)
RECORDING_ENABLED=true
RECORDING_MODE=rdp_window
LOG_LEVEL=INFO
```

**Dica**: Use o arquivo `.env` para credenciais e o `config.json` para configurações que podem ser compartilhadas.
