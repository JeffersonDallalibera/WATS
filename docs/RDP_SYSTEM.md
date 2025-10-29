# Sistema RDP Multiplataforma - WATS

## 🎯 Visão Geral

O WATS agora possui um sistema RDP completamente multiplataforma que funciona tanto no Windows quanto no Linux, substituindo a dependência do `rdp.exe` específico do Windows.

## 🏗️ Arquitetura

### Componentes Principais

1. **RDPConnector** (`rdp_connector.py`)
   - Gerenciador principal de conexões RDP
   - Detecta automaticamente a melhor opção disponível
   - Fallback inteligente entre diferentes métodos

2. **FreeRDP Wrapper** (`freerdp_wrapper.py`)
   - Wrapper Python para FreeRDP
   - Controle de sessões ativas
   - Geração de arquivos .rdp
   - Execução em background com logs

3. **Platform Utils** (`platform_utils.py`)
   - Detecção automática de plataforma
   - Mocks para funções específicas do Windows
   - Caminhos e configurações por SO

## 🔄 Prioridade de Métodos

O sistema escolhe automaticamente o melhor método disponível:

1. **FreeRDP Wrapper** (Preferido)
   - ✅ Multiplataforma (Windows/Linux)
   - ✅ Controle total via Python
   - ✅ Logs detalhados
   - ✅ Gerenciamento de sessões

2. **RDP.exe Customizado** (Windows)
   - ✅ Funcionalidades específicas
   - ❌ Apenas Windows

3. **MSTSC Nativo** (Windows)
   - ✅ Sempre disponível no Windows
   - ❌ Menos controle

4. **Clientes Linux Nativos**
   - ✅ xfreerdp (FreeRDP nativo)
   - ✅ rdesktop (cliente clássico)
   - ✅ remmina (interface gráfica)

## 📦 Instalação

### Windows

```powershell
# FreeRDP (Recomendado)
winget install FreeRDP.FreeRDP

# Ou via Chocolatey
choco install freerdp
```

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install freerdp2-x11

# CentOS/RHEL/Fedora
sudo yum install freerdp
# ou: sudo dnf install freerdp

# Arch Linux
sudo pacman -S freerdp
```

## 🚀 Como Usar

### Uso Básico

```python
from src.wats.utils.rdp_connector import rdp_connector

# Dados da conexão
connection_data = {
    'ip': '192.168.1.100',
    'user': 'usuario',
    'pwd': 'senha',
    'title': 'Servidor de Teste',
    'port': '3389'  # Opcional
}

# Conecta automaticamente
success = rdp_connector.connect(connection_data)
if success:
    print("Conexão RDP iniciada com sucesso!")
else:
    print("Falha ao conectar")
```

### Verificação de Disponibilidade

```python
# Verifica se RDP está disponível
is_available, status_msg = rdp_connector.is_rdp_available()
print(f"RDP disponível: {is_available}")
print(f"Status: {status_msg}")

# Mostra método preferido
print(f"Método preferido: {rdp_connector.preferred_method}")
```

### Uso Avançado com FreeRDP Wrapper

```python
from src.wats.utils.freerdp_wrapper import freerdp_wrapper

# Conecta com controle de sessão
session_id = "minha_sessao_rdp"
success = freerdp_wrapper.connect(
    connection_data=connection_data,
    session_id=session_id,
    background=True
)

# Lista sessões ativas
active_sessions = freerdp_wrapper.get_active_sessions()
for session_id, info in active_sessions.items():
    print(f"Sessão {session_id}: {info['server']} (PID: {info['pid']})")

# Desconecta sessão específica
freerdp_wrapper.disconnect(session_id)

# Desconecta todas as sessões
count = freerdp_wrapper.disconnect_all()
print(f"Desconectadas {count} sessões")
```

## 🧪 Testes

Execute os testes para verificar o sistema:

```bash
# Teste geral multiplataforma
python test_multiplatform.py

# Teste específico do sistema RDP
python test_rdp_system.py
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Força uso de um cliente específico (opcional)
export WATS_RDP_CLIENT=xfreerdp

# Diretório personalizado para arquivos RDP temporários
export WATS_RDP_TEMP_DIR=/tmp/wats-rdp

# Nível de log para RDP
export WATS_RDP_LOG_LEVEL=DEBUG
```

### Arquivo de Configuração

```json
{
  "rdp": {
    "preferred_client": "freerdp_wrapper",
    "connection_timeout": 30,
    "auto_reconnect": true,
    "fullscreen": true,
    "compression": true,
    "clipboard_sharing": true
  }
}
```

## 🐛 Troubleshooting

### Windows

**Problema**: "FreeRDP não encontrado"
```powershell
# Solução: Instalar FreeRDP
winget install FreeRDP.FreeRDP

# Verificar se está no PATH
where wfreerdp
```

**Problema**: "rdp.exe não encontrado"
```
# Solução: O sistema usa automaticamente MSTSC como fallback
# Verifique se os arquivos estão na pasta assets/
```

### Linux

**Problema**: "Nenhum cliente RDP encontrado"
```bash
# Solução: Instalar FreeRDP
sudo apt-get install freerdp2-x11

# Verificar instalação
which xfreerdp
xfreerdp --version
```

**Problema**: "Erro de permissão X11"
```bash
# Solução: Configurar X11 forwarding
export DISPLAY=:0
xhost +local:
```

### Geral

**Problema**: "Conexão falha com erro de certificado"
```python
# Solução: O sistema já ignora certificados por padrão
# Se necessário, configure manualmente:
connection_data['cert_ignore'] = True
```

**Problema**: "Processo RDP não inicia"
```bash
# Debug: Execute teste específico
python test_rdp_system.py

# Verifique logs
tail -f wats_app.log | grep RDP
```

## 📊 Comparação de Funcionalidades

| Recurso | Windows (rdp.exe) | Windows (FreeRDP) | Linux (FreeRDP) | Linux (rdesktop) |
|---------|-------------------|-------------------|------------------|------------------|
| Fullscreen | ✅ | ✅ | ✅ | ✅ |
| Clipboard | ✅ | ✅ | ✅ | ❌ |
| Drive Sharing | ✅ | ✅ | ✅ | ❌ |
| Audio | ✅ | ✅ | ✅ | ❌ |
| Multi-monitor | ✅ | ✅ | ✅ | ❌ |
| Auto-reconnect | ✅ | ✅ | ✅ | ❌ |
| Session Control | ❌ | ✅ | ✅ | ❌ |

## 🔮 Próximas Funcionalidades

- [ ] **Suporte ao macOS** com Microsoft Remote Desktop
- [ ] **Configurações por usuário** para preferências de cliente
- [ ] **Gravação de sessão integrada** com controle de início/fim
- [ ] **Reconexão automática** em caso de falha
- [ ] **Load balancing** entre múltiplos servidores RDP
- [ ] **Criptografia adicional** para conexões sensíveis
- [ ] **Métricas de conexão** (latência, qualidade, etc.)

## 📝 Logs e Debug

### Estrutura de Logs

```
[2025-10-29 10:30:15] INFO: RDPConnector: Método preferido: freerdp_wrapper
[2025-10-29 10:30:15] INFO: FreeRDP Wrapper: Conectando via FreeRDP...
[2025-10-29 10:30:15] INFO: FreeRDP Wrapper: Executando FreeRDP [wats_rdp_192.168.1.100_1730203815]: xfreerdp /v:192.168.1.100 /u:usuario /p:*** /f /cert:ignore +clipboard
[2025-10-29 10:30:16] INFO: FreeRDP Wrapper: Conexão iniciada com PID: 12345
```

### Debug Avançado

```python
import logging
logging.getLogger('wats.utils.rdp_connector').setLevel(logging.DEBUG)
logging.getLogger('wats.utils.freerdp_wrapper').setLevel(logging.DEBUG)
```

---

## 🤝 Contribuição

Para contribuir com melhorias no sistema RDP:

1. Teste em diferentes distribuições Linux
2. Implemente suporte a novos clientes RDP
3. Adicione testes para cenários específicos
4. Documente problemas e soluções encontradas

---

**Desenvolvido pela equipe ATS**  
*Sistema RDP Multiplataforma para WATS v1.0*