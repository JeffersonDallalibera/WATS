# WATS - Windows Application and Terminal Server

![WATS Logo](assets/icons/ats.ico)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)](docs/BUILD_MULTIPLATFORM.md)

WATS é um sistema profissional para gerenciamento de conexões RDP com gravação, proteção de sessões e auditoria — projetado para ambientes corporativos e multiplataforma (Windows e Linux).

## 🎯 Visão Geral

O WATS foi desenvolvido para resolver os desafios de gerenciamento centralizado de conexões RDP em ambientes corporativos, oferecendo:

- **Gerenciamento Centralizado**: Controle todas as conexões RDP de uma interface única
- **Gravação de Sessões**: Sistema automático de gravação para auditoria e compliance
- **Proteção de Sessões**: Evita desconexões involuntárias entre usuários
- **Multiplataforma**: Funciona nativamente no Windows e Linux
- **Auditoria Completa**: Logs detalhados de todas as ações e conexões

## ✨ Principais recursos

### 🖥️ Gerenciamento de Conexões

- Interface intuitiva para organização de servidores e conexões
- Suporte a grupos para categorização de servidores
- Conexão automática com credenciais salvas de forma segura
- Monitoramento em tempo real do status das conexões

### 🎬 Sistema de Gravação

- Gravação automática de todas as sessões RDP
- Múltiplos formatos de vídeo (MP4, AVI)
- Rotação automática de arquivos baseada em tamanho/tempo
- Limites de espaço total/idade com limpeza automática
- Armazenamento local seguro com opções de compressão

### 🔒 Proteção de Sessões

- Sistema inovador que previne desconexões involuntárias
- Usuário conectado pode proteger sua sessão com senha
- Validação centralizada no servidor SQL (hash, SPs, auditoria)
- Logs de auditoria para todas as tentativas de acesso

### 👥 Gestão de Usuários e Permissões

- Painel administrativo completo
- Controle granular de permissões por usuário/grupo
- Sistema de autenticação integrado
- Auditoria de ações dos usuários

### �️ Integração com Banco de Dados

- Suporte nativo para SQL Server e PostgreSQL
- Estrutura de dados otimizada para performance
- Backup automático e recuperação de dados
- Sincronização em tempo real entre múltiplas instâncias

## 🧩 Plataforma e requisitos

### Windows

- Windows 10/11 ou Windows Server 2016+
- Python 3.11+ (para execução do código fonte)
- SQL Server 2017+ ou PostgreSQL 12+
- 4GB RAM mínimo, 8GB recomendado
- 10GB espaço livre para gravações

### Linux

- Ubuntu/Debian equivalentes
- Python 3.11+
- PostgreSQL 12+
- FreeRDP (RDP)
- 4GB RAM mínimo, 8GB recomendado

## 🚀 Início rápido (desenvolvimento)

Instalação e execução (Windows PowerShell):

```powershell
# Clonar e entrar no projeto
git clone https://github.com/JeffersonDallalibera/WATS.git
cd WATS

# Ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Dependências
pip install -r requirements.txt

# Executar
python run.py
```

Modo demo (sem banco), útil para explorar a UI:

```powershell
$env:WATS_DEMO_MODE = "true"; python run.py
```

## ⚙️ Configuração

### Banco de Dados

1. **SQL Server**: Execute os scripts em `scripts/create_wats_database.sql`
2. **PostgreSQL**: Configure conforme `docs/DATABASE_INSTALLATION.md`
3. Configure a string de conexão no arquivo `.env`

### Gravação de Sessões (config.json)

```json
{
  "recording": {
    "enabled": true,
    "auto_start": true,
    "mode": "rdp_window",
    "output_dir": "{VIDEOS}/WATS",
    "fps": 10,
    "quality": 23,
    "max_file_size_mb": 100,
    "max_duration_minutes": 30
  }
}
```

Variáveis de ambiente (exemplo):

```powershell
# Banco de Dados
$env:DB_TYPE = "sqlserver"
$env:DB_SERVER = "seu-servidor"; $env:DB_DATABASE = "WATS_DB"
$env:DB_UID = "usuario"; $env:DB_PWD = "senha"; $env:DB_PORT = "1433"

# Gravação
$env:RECORDING_ENABLED = "true"; $env:RECORDING_MODE = "rdp_window"
$env:RECORDING_AUTO_START = "true"; $env:RECORDING_FPS = "10"
$env:RECORDING_QUALITY = "23"; $env:RECORDING_MAX_FILE_SIZE_MB = "100"
$env:RECORDING_MAX_DURATION_MINUTES = "30"
```

## 📚 Documentação

### Documentos Essenciais

- **[Configuração Completa](docs/CONFIGURACAO.md)** - Guia completo de configuração
- **[Sistema de Proteção de Sessões](docs/SISTEMA_PROTECAO_SESSOES.md)** - Como funciona a proteção
- **[Build Multiplataforma](docs/BUILD_MULTIPLATFORM.md)** - Compilação para diferentes sistemas
- **[API e Integração](docs/api_upload_system.md)** - Sistema de API para integrações
- **[Banco de Dados](docs/DATABASE_INSTALLATION.md)** - Configuração do banco
- **[RDP System](docs/RDP_SYSTEM.md)** - Funcionamento do sistema RDP

Para um índice simples dos documentos, consulte `docs/README.md`.

## 🎮 Como Usar

### Primeira Execução

1. **Configuração Inicial**: Configure banco de dados e diretórios
2. **Cadastro de Servidores**: Adicione seus servidores RDP
3. **Usuários**: Configure usuários e permissões
4. **Teste de Conexão**: Verifique se tudo está funcionando

### Conectando a um Servidor

1. Selecione o servidor na lista
2. Clique em "Conectar" ou use duplo-clique
3. A sessão será gravada automaticamente
4. Use o menu de contexto para opções avançadas

### Proteção de Sessões

1. Clique com botão direito em uma conexão ativa
2. Selecione "Proteger Sessão"
3. Defina uma senha temporária
4. Outros usuários precisarão da senha para conectar

## 📁 Estrutura do Projeto

```
WATS/
├── src/wats/                   # Código fonte principal
│   ├── app_window.py          # Interface principal
│   ├── main.py                # Ponto de entrada
│   ├── config.py              # Configurações
│   ├── admin_panels/          # Painéis administrativos
│   ├── db/                    # Camada de banco de dados
│   ├── recording/             # Sistema de gravação
│   └── session_protection.py  # Proteção de sessões
├── docs/                      # Documentação
├── scripts/                   # Scripts de build e deploy
├── tests/                     # Testes automatizados
├── assets/                    # Recursos estáticos
└── config/                    # Arquivos de configuração
```

## 🧪 Testes

```powershell
python -m pytest -q
# Teste específico
python -m pytest tests/test_session_protection.py -q
```

---

## 🔧 Desenvolvimento

### Executando Testes

```bash
# Todos os testes
python -m pytest tests/

# Testes específicos
python -m pytest tests/test_session_protection.py
```

### Build do Executável

```powershell
# Script universal
python build.py --platform windows
# Linux (ver docs)
python build.py --platform linux
```

## � Segurança e conformidade

### Proteção de Dados

- Variáveis de ambiente para configuração sensível
- Conexões de banco de dados criptografadas
- Armazenamento seguro de arquivos de gravação
- Trilha de auditoria para todas as ações

### Privacidade de Gravação

- Antes de iniciar, o WATS exibe um diálogo de consentimento de gravação
- Consentimentos/recusas são registrados em `wats_app.log`
- Defina políticas de retenção (limites de tamanho/idade) conforme sua empresa

## 📚 Documentação

### Documentos Essenciais

- **[Configuração Completa](docs/CONFIGURACAO.md)** - Guia completo de configuração
- **[Sistema de Proteção de Sessões](docs/SISTEMA_PROTECAO_SESSOES.md)** - Como funciona a proteção
- **[Build Multiplataforma](docs/BUILD_MULTIPLATFORM.md)** - Compilação para diferentes sistemas
- **[API e Integração](docs/api_upload_system.md)** - Sistema de API para integrações
- **[Banco de Dados](docs/DATABASE_INSTALLATION.md)** - Configuração do banco
- **[RDP System](docs/RDP_SYSTEM.md)** - Funcionamento do sistema RDP

Para um índice simples dos documentos, consulte `docs/README.md`.

## � Solução de Problemas

### Problemas Comuns

1. **Erro de Conexão com Banco**: Verifique as credenciais no `.env`
2. **Gravação não Funciona**: Verifique permissões do diretório
3. **RDP não Conecta**: Verifique firewall e credenciais
4. **Performance Lenta**: Ajuste configurações de gravação

### Logs e Diagnóstico

- Log da aplicação: `wats_app.log` (na pasta do executável em produção; na raiz do projeto em desenvolvimento)

## 📈 Performance e Otimização

### Configurações Recomendadas

- **Pequenas Empresas** (1-10 usuários): 4GB RAM, HD padrão
- **Médias Empresas** (11-50 usuários): 8GB RAM, SSD recomendado
- **Grandes Empresas** (50+ usuários): 16GB+ RAM, SSD obrigatório

### Monitoramento

- CPU: Máximo 80% de uso sustentado
- Memória: Máximo 70% de uso
- Disco: Mínimo 5GB livres para gravações

## 🔐 Segurança

### Recursos de Segurança

- Criptografia de senhas MD5 no banco
- Proteção contra acesso não autorizado
- Logs de auditoria completos
- Sanitização automática de dados sensíveis

### Boas Práticas

- Mantenha o sistema sempre atualizado
- Use senhas fortes para proteção de sessões
- Monitore logs regularmente
- Faça backup regular do banco de dados

## 📊 Modo Demo

Para testar o sistema sem configurar banco de dados:

```powershell
# Ativar temporariamente o modo demo
$env:WATS_DEMO_MODE = "true"; python run.py
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Changelog

### Versão 4.2 (2025)

- ✅ Sistema de proteção de sessões com validação no servidor
- ✅ Suporte multiplataforma (Windows/Linux)
- ✅ Interface modernizada com CustomTkinter
- ✅ Sistema de gravação otimizado
- ✅ API de integração melhorada

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Equipe

- **Jefferson Dallalibera** - Desenvolvimento Principal
- **Contribuidores** - Veja [CONTRIBUTORS.md](CONTRIBUTORS.md)

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/JeffersonDallalibera/WATS/issues)
- **Documentação**: `docs/`
- **Email**: [Criar issue no GitHub]

---

**WATS V4.2** - Sistema Profissional de Gerenciamento RDP 6. Push para a branch: `git push origin nome-da-feature` 7. Submeta um pull request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Autores

- **Equipe de Desenvolvimento** - Trabalho inicial e manutenção contínua

## 🙏 Agradecimentos

- CustomTkinter por componentes modernos de UI
- MSS por captura eficiente de tela
- OpenCV por processamento de vídeo
- PyInstaller por criação de executáveis

## 📊 Histórico de Versões

- **V4.2** (2025-10-26)

  - Adicionado sistema abrangente de gravação de sessões
  - Múltiplos modos de gravação (tela cheia, janela RDP, janela ativa)
  - Rotação automática de arquivos e limpeza
  - Otimizações de performance
  - Tratamento de erros aprimorado

- **V4.1** (Anterior)
  - Gerenciamento central de conexões RDP
  - Integração com banco de dados
  - Funcionalidade de painel administrativo
  - Framework básico de UI

---

Para documentação detalhada e opções avançadas de configuração, consulte os arquivos de documentação na raiz do projeto.
