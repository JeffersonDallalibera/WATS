# Changelog

Todas as mudanças notáveis do projeto WATS serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/spec/v2.0.0.html).

## [4.2.0] - 2025-10-26

### Adicionado

- **Sistema de Gravação de Sessões**

  - Múltiplos modos de gravação: tela cheia, específico da janela RDP, janela ativa
  - Captura de tela leve usando MSS com uso mínimo de CPU/memória
  - Compressão de vídeo H.264 para armazenamento eficiente
  - Rotação automática de arquivos baseada em limites de tamanho e tempo
  - Gerenciamento de cota de armazenamento com limpeza automática
  - Exclusão baseada em idade de gravações antigas
  - Indicadores de status de gravação em tempo real na UI

- **Configuração de Gravação**

  - Configuração por variáveis de ambiente via arquivo .env
  - Configurações de frame rate, qualidade e resolução configuráveis
  - Seleção de modo de gravação (full_screen, rdp_window, active_window)
  - Configurações de gerenciamento de armazenamento (tamanho máximo, duração, intervalos de limpeza)

- **Integração com Windows**

  - Detecção e rastreamento de janela RDP
  - Seguimento automático de janela para sessões RDP
  - Identificação de janela baseada em processo
  - Mecanismos de fallback para gravação confiável

- **Gerenciamento de Arquivos**
  - Rotação automática de arquivos baseada em limites configuráveis
  - Processos de limpeza em segundo plano
  - Rastreamento de metadados para cada sessão de gravação
  - Estatísticas e monitoramento de armazenamento

### Aprimorado

- **Otimizações de Performance**

  - Inicialização adiada para startup mais rápido
  - Inicialização de banco de dados em segundo plano
  - Processo de criação de UI otimizado
  - Pegada de memória reduzida

- **Tratamento de Erros**

  - Tratamento abrangente de erros para operações de gravação
  - Fallbacks elegantes quando componentes de gravação falham
  - Log detalhado para resolução de problemas
  - Mensagens de erro amigáveis ao usuário

- **Gerenciamento de Configuração**
  - Classe Settings estendida com preferências de gravação
  - Validação para todas as opções de configuração de gravação
  - Melhor tratamento de variáveis de ambiente
  - Suporte a arquivo .env embarcado em executáveis

### Corrigido

- Carregamento de variáveis de ambiente em executáveis PyInstaller
- Persistência de tema entre reinicializações da aplicação
- Validação de configuração de banco de dados
- Limpeza de recursos ao fechar a aplicação

### Dependências

- Adicionado `opencv-python` para codificação de vídeo
- Adicionado `mss` para captura de tela
- Adicionado `numpy` para processamento de arrays
- Adicionado `pywin32` para integração com API do Windows
- Adicionado `psutil` para gerenciamento de processos

## [4.1.0] - Versão Anterior

### Adicionado

- Gerenciamento central de conexões RDP
- Integração com banco de dados (PostgreSQL e SQL Server)
- Gerenciamento de usuários com painel administrativo
- Organização de conexões baseada em grupos
- UI moderna baseada em CustomTkinter
- Suporte a temas claro/escuro
- Monitoramento de conexão em tempo real
- Sistema de heartbeat para status de conexão
- Criação de executável com PyInstaller

### Funcionalidades

- Gerenciamento centralizado de conexões RDP
- Suporte a backend de banco de dados
- Painel administrativo para gerenciamento de usuários/conexões
- Agrupamento e organização de conexões
- UI moderna com suporte a temas
- Monitoramento de status em tempo real
- Log de auditoria
- Criação de executável standalone

---

## Numeração de Versões

- **Versão principal** (X.0.0): Mudanças que quebram compatibilidade ou adições de recursos principais
- **Versão menor** (0.X.0): Novos recursos que são compatíveis com versões anteriores
- **Versão de correção** (0.0.X): Correções de bugs e melhorias menores

## Categorias

- **Adicionado**: Novos recursos
- **Alterado**: Mudanças em funcionalidades existentes
- **Depreciado**: Recursos que serão removidos em breve
- **Removido**: Recursos removidos
- **Corrigido**: Correções de bugs
- **Segurança**: Melhorias de segurança
