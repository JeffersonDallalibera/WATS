# WATS - Gerenciador de Conexões Windows Terminal Server

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://microsoft.com/windows)

**WATS V4.2** é um Gerenciador de Conexões Windows Terminal Server abrangente com recursos avançados de gravação de sessões para monitoramento e auditoria de conexões RDP.

## 🚀 Recursos

### Funcionalidades Principais

- **Gerenciamento de Conexões RDP**: Gestão centralizada de conexões de área de trabalho remota
- **Integração com Banco de Dados**: Suporte otimizado para SQL Server
- **Gerenciamento de Usuários**: Painel administrativo para gestão de usuários e conexões
- **Organização por Grupos**: Organize conexões por grupos para melhor gerenciamento

### Sistema de Gravação de Sessões _(NOVO)_

- **Múltiplos Modos de Gravação**: Tela cheia, janela RDP específica ou gravação da janela ativa
- **Performance Leve**: Captura de tela otimizada com uso mínimo de CPU/memória
- **Compressão H.264**: Compressão de vídeo eficiente para redução do tamanho dos arquivos
- **Gerenciamento Automático de Arquivos**: Rotação de arquivos baseada em tamanho e tempo com limpeza
- **Conformidade com Privacidade**: Escopo de gravação configurável para requisitos de privacidade

### Recursos Avançados

- **Interface Moderna**: Interface baseada em CustomTkinter com suporte a temas escuro/claro
- **Monitoramento em Tempo Real**: Status de conexão ao vivo e monitoramento de heartbeat
- **Trilha de Auditoria**: Logging abrangente e metadados de sessão
- **Compilação de Executável**: Executável standalone com PyInstaller

## 📋 Requisitos

### Requisitos do Sistema

- **SO**: Windows 10/11
- **Python**: 3.11+
- **Memória**: 4GB RAM mínimo
- **Disco**: 2GB de espaço livre (mais para gravações)

### Dependências

```txt
customtkinter>=5.0.0
pyodbc>=4.0.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.0
opencv-python>=4.8.0
mss>=9.0.0
numpy>=1.24.0
pywin32>=306
psutil>=5.9.0
```

## 🛠️ Instalação

### 1. Clonar Repositório

```bash
git clone <repository-url>
cd wats
```

### 2. Criar Ambiente Virtual

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Ambiente

```bash
# Copiar configuração de exemplo
copy .env.recording.sample .env

# Editar arquivo .env com configurações do banco de dados e gravação
notepad .env
```

### 5. Executar Aplicação

```bash
python run.py
```

## ⚙️ Configuração

### Configuração do Banco de Dados

```env
# Configurações do Banco de Dados
DB_TYPE=sqlserver           # Tipo do banco (sqlserver ou sqlite)
DB_SERVER=seu_servidor
DB_DATABASE=seu_banco_de_dados
DB_UID=seu_usuario
DB_PWD=sua_senha
DB_PORT=5432               # ou 1433 para SQL Server
```

### Configuração de Gravação

```env
# Configurações de Gravação
RECORDING_ENABLED=true
RECORDING_MODE=rdp_window           # full_screen, rdp_window, active_window
RECORDING_AUTO_START=true
RECORDING_FPS=10
RECORDING_QUALITY=23
RECORDING_MAX_FILE_SIZE_MB=100
RECORDING_MAX_DURATION_MINUTES=30
```

## 📚 Documentação

- **[Documentação do Sistema de Gravação](RECORDING_SYSTEM_DOCUMENTATION.md)** - Guia abrangente para gravação de sessões
- **[Otimização de Performance](PERFORMANCE_OPTIMIZATION.md)** - Guia de ajuste de performance
- **[Configuração de Temas](THEME_FIX_README.md)** - Personalização de temas da interface
- **[Instruções de Build](BUILD_README.md)** - Criando executáveis standalone

## 🎯 Modos de Gravação

### Gravação de Janela RDP _(Recomendado)_

- Grava apenas a janela de conexão RDP
- Arquivos 60-80% menores
- Melhor privacidade e performance
- Rastreamento automático da janela

### Gravação de Tela Cheia

- Grava toda a área de trabalho
- Trilha de auditoria completa
- Maiores tamanhos de arquivo e uso de CPU

### Gravação de Janela Ativa

- Grava a janela atualmente em foco
- Gravação dinâmica baseada na interação do usuário

## 🔧 Compilando Executável

```bash
# Compilar executável standalone
python -m PyInstaller build_executable.spec --clean

# Executável será criado em dist/WATS_App.exe
```

## 📁 Estrutura do Projeto

```
wats/
├── run.py                          # Ponto de entrada da aplicação
├── requirements.txt                # Dependências Python
├── build_executable.spec           # Configuração PyInstaller
├── .env.recording.sample           # Template de configuração
├── wats_app/                       # Pacote principal da aplicação
│   ├── __init__.py
│   ├── main.py                     # Lógica principal da aplicação
│   ├── app_window.py               # Janela principal da UI
│   ├── config.py                   # Gerenciamento de configuração
│   ├── utils.py                    # Funções utilitárias
│   ├── dialogs.py                  # Diálogos da UI
│   ├── admin_panels/               # Interface administrativa
│   ├── db/                         # Camada de banco de dados
│   │   ├── db_service.py          # Serviço de banco de dados
│   │   ├── database_manager.py    # Gerenciamento de conexão
│   │   └── repositories/          # Camada de acesso a dados
│   └── recording/                  # Sistema de gravação de sessões
│       ├── session_recorder.py    # Funcionalidade principal de gravação
│       ├── recording_manager.py   # Coordenação de gravação
│       └── file_rotation_manager.py # Gerenciamento de arquivos
├── assets/                         # Assets da aplicação
│   ├── ats.ico                    # Ícone da aplicação
│   └── rdp.exe                    # Executável RDP
└── docs/                          # Documentação
```

## 🔒 Considerações de Segurança

### Proteção de Dados

- Variáveis de ambiente para configuração sensível
- Conexões de banco de dados criptografadas
- Armazenamento seguro de arquivos de gravação
- Trilha de auditoria para todas as ações

### Privacidade de Gravação

- Escopo de gravação configurável
- Políticas de limpeza automática
- Controle de acesso para gravações

### Performance

- Gravação leve em segundo plano
- Otimização automática de qualidade
- Uso mínimo de recursos do sistema
- Interface responsiva

## 🐛 Solução de Problemas

### Problemas Comuns

**Aplicação não inicia**

```bash
# Verificar versão do Python
python --version

# Verificar dependências
pip check

# Verificar configuração do ambiente
python -c "from wats_app.config import load_environment_variables; load_environment_variables()"
```

**Gravação não está funcionando**

```bash
# Verificar dependências de gravação
pip install opencv-python mss numpy pywin32 psutil

# Verificar configuração de gravação
python -c "from wats_app.config import Settings; s=Settings(); print(s.get_recording_config())"
```

**Problemas de conexão com banco de dados**

- Verificar acessibilidade do servidor de banco de dados
- Verificar credenciais no arquivo .env
- Garantir que o banco de dados existe e o usuário tem permissões

## 🤝 Contribuindo

1. Fork o repositório
2. Crie uma branch para sua feature: `git checkout -b nome-da-feature`
3. Faça suas mudanças
4. Adicione testes se aplicável
5. Commit suas mudanças: `git commit -am 'Adicionar feature'`
6. Push para a branch: `git push origin nome-da-feature`
7. Submeta um pull request

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
