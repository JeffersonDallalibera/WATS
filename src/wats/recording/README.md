# WATS Smart Recording System

Sistema de gravação inteligente para janelas RDP com detecção automática de atividade e gerenciamento avançado de sessões.

## 🎯 Funcionalidades Principais

### ✨ Gravação Inteligente
- **Rastreamento de Janela RDP**: Detecta e acompanha automaticamente janelas RDP mesmo quando movidas entre monitores
- **Detecção de Atividade**: Monitora interações do usuário (mouse, teclado, foco) com timeout configurável
- **Pausa/Retomada Automática**: Para gravação baseado em critérios inteligentes
- **Segmentação de Arquivos**: Cria múltiplos arquivos baseado em critérios de duração, tamanho e eventos

### 🎮 Estados Automáticos de Gravação

| Estado | Descrição | Ação |
|--------|-----------|------|
| **Gravando** | Janela visível + usuário ativo | Grava normalmente |
| **Pausado** | Janela minimizada/coberta | Para gravação temporariamente |
| **Aguardando Atividade** | Sem interação por X minutos | Para até detectar atividade |
| **Aguardando Janela** | Janela RDP não encontrada | Para até janela aparecer |
| **Parado** | Sessão encerrada | Finaliza gravação |

### 🔧 Componentes do Sistema

#### 1. **WindowTracker**
- Rastreia estado da janela RDP (posição, tamanho, visibilidade)
- Detecta estados: normal, minimizada, maximizada, coberta
- Reacquisição automática de janelas perdidas
- Suporte multi-monitor

#### 2. **InteractivityMonitor**  
- Monitora atividade do usuário na janela específica
- Detecta: movimento do mouse, cliques, teclas pressionadas, foco
- Timeout configurável de inatividade
- Callbacks para eventos de atividade/inatividade

#### 3. **SmartSessionRecorder**
- Combina rastreamento de janela + monitoramento de atividade
- Gravação com pausa/retomada inteligente
- Criação automática de segmentos
- Gerenciamento de múltiplos arquivos por sessão

#### 4. **RecordingManager** (Atualizado)
- Coordenador central do sistema
- Interface simplificada para aplicação principal
- Callbacks para eventos de gravação
- Integração com compressão e upload

## 🚀 Como Usar

### Configuração Básica

```python
from recording_manager import RecordingManager
from smart_recording_config import get_smart_recording_config

# Configure settings
settings = YourSettingsClass()
settings.RECORDING_ENABLED = True
settings.RECORDING_OUTPUT_DIR = "/path/to/recordings"
settings.RECORDING_INACTIVITY_TIMEOUT_MINUTES = 10
settings.RECORDING_PAUSE_ON_MINIMIZED = True

# Initialize manager
recording_manager = RecordingManager(settings)
recording_manager.initialize()

# Set callbacks (opcional)
recording_manager.set_callbacks(
    on_started=lambda session_id: print(f"Started: {session_id}"),
    on_paused=lambda reason: print(f"Paused: {reason}"),
    on_resumed=lambda reason: print(f"Resumed: {reason}"),
    on_stopped=lambda session_id: print(f"Stopped: {session_id}")
)
```

### Iniciando uma Gravação

```python
# Informações da conexão RDP
connection_info = {
    'ip': '192.168.1.100:3389',
    'name': 'Servidor-Producao',
    'user': 'usuario.suporte',
    'con_codigo': 12345
}

session_id = f"session_{connection_info['con_codigo']}_{int(time.time())}"

# Inicia gravação inteligente
if recording_manager.start_session_recording(session_id, connection_info):
    print("Gravação iniciada com sucesso!")
    # A gravação agora será gerenciada automaticamente
```

### Monitoramento do Status

```python
# Verifica status da gravação
status = recording_manager.get_recording_status()

print(f"Gravando: {status['is_recording']}")
print(f"Estado: {status.get('state', 'unknown')}")
print(f"Duração: {status.get('total_duration', 0):.1f}s")
print(f"Segmentos: {status.get('segments_count', 0)}")

# Informações da janela
if 'window_info' in status:
    window = status['window_info']
    print(f"Janela: {window.get('state', 'unknown')}")

# Informações de atividade
if 'activity_info' in status:
    activity = status['activity_info']
    print(f"Usuário ativo: {activity.get('is_active', False)}")
```

### Parando a Gravação

```python
# Para a gravação (retorna lista de arquivos criados)
if recording_manager.stop_session_recording():
    print("Gravação finalizada com sucesso!")

# Cleanup
recording_manager.shutdown()
```

## ⚙️ Configurações Avançadas

### 📄 Configuração via config.json

O sistema de gravação inteligente se integra completamente com o sistema de configuração `config.json` do WATS. As configurações são carregadas na seguinte ordem de prioridade:

1. **config.json** (configurações do arquivo)
2. **Settings object** (sobrescreve config.json)
3. **Valores padrão** (fallback)

#### Estrutura do config.json

```json
{
  "recording": {
    "enabled": true,
    "output_dir": "./recordings",
    "fps": 30,
    "quality": 75,
    "resolution_scale": 1.0,
    "max_file_size_mb": 100,
    "max_duration_minutes": 30,
    "compression_enabled": true,
    "compression_crf": 28,
    
    "smart_recording": {
      "window_tracking_interval": 1.0,
      "inactivity_timeout_minutes": 10,
      "pause_on_minimized": true,
      "pause_on_covered": true,
      "pause_on_inactive": true,
      "create_new_file_after_pause": true,
      "debug_window_tracking": false,
      "debug_activity_monitoring": false
    }
  }
}
```

#### Configurações Específicas da Gravação Inteligente

| Configuração | Tipo | Padrão | Descrição |
|-------------|------|--------|-----------|
| `window_tracking_interval` | float | 1.0 | Intervalo em segundos entre verificações da janela |
| `inactivity_timeout_minutes` | int | 10 | Minutos de inatividade antes de pausar |
| `pause_on_minimized` | bool | true | Pausar quando janela minimizada |
| `pause_on_covered` | bool | true | Pausar quando janela coberta |
| `pause_on_inactive` | bool | true | Pausar por inatividade do usuário |
| `create_new_file_after_pause` | bool | true | Criar novo arquivo após retomar |
| `debug_window_tracking` | bool | false | Logs debug do rastreamento de janela |
| `debug_activity_monitoring` | bool | false | Logs debug do monitoramento de atividade |

### 🔧 Configurações Programáticas

Você também pode sobrescrever configurações via código:

```python
# Timeout de inatividade (em minutos)
settings.RECORDING_INACTIVITY_TIMEOUT_MINUTES = 10

# Pausar quando janela minimizada
settings.RECORDING_PAUSE_ON_MINIMIZED = True

# Pausar quando janela coberta por outras
settings.RECORDING_PAUSE_ON_COVERED = True

# Criar novo arquivo após retomar gravação
settings.RECORDING_CREATE_NEW_FILE_AFTER_PAUSE = True

# Intervalo de verificação da janela (segundos)
settings.RECORDING_WINDOW_TRACKING_INTERVAL = 1.0
```

### Configurações de Arquivo

```python
# Duração máxima por arquivo (minutos)
settings.RECORDING_MAX_DURATION_MINUTES = 30

# Tamanho máximo por arquivo (MB)
settings.RECORDING_MAX_FILE_SIZE_MB = 100

# FPS da gravação
settings.RECORDING_FPS = 30

# Qualidade da gravação (0-100)
settings.RECORDING_QUALITY = 75

# Escala de resolução (1.0 = original)
settings.RECORDING_RESOLUTION_SCALE = 1.0
```

### Configurações de Compressão

```python
# Habilitar compressão pós-gravação
settings.RECORDING_COMPRESSION_ENABLED = True

# Valor CRF do H.264 (0-51, menor = melhor qualidade)
settings.RECORDING_COMPRESSION_CRF = 28
```

## 📁 Estrutura de Arquivos

### Nomenclatura dos Arquivos

Os arquivos de gravação seguem o padrão:
```
{session_id}_seg{numero:03d}_{timestamp}.mp4
```

Exemplo:
```
session_12345_1698765432_seg001_20241029_143052.mp4
session_12345_1698765432_seg002_20241029_143612.mp4
session_12345_1698765432_seg003_20241029_144205.mp4
```

### Segmentação Automática

Novos arquivos são criados automaticamente quando:
- ✅ Duração máxima é atingida
- ✅ Tamanho máximo é atingido  
- ✅ Gravação é retomada após pausa
- ✅ Janela é reacquirida após perda
- ✅ Atividade é retomada após inatividade

### Metadados

Cada arquivo de gravação pode ter um arquivo `.json` associado com metadados:

```json
{
  "session_id": "session_12345_1698765432",
  "segment_number": 1,
  "start_time": "2024-10-29T14:30:52Z",
  "end_time": "2024-10-29T14:36:12Z",
  "duration_seconds": 320,
  "reason_started": "session_start",
  "reason_ended": "window_minimized",
  "window_info": {
    "title": "Servidor-Producao - Conexão de Área de Trabalho Remota",
    "initial_rect": [100, 50, 1200, 800]
  },
  "activity_summary": {
    "total_events": 45,
    "mouse_events": 23,
    "keyboard_events": 18,
    "focus_events": 4
  }
}
```

## 🔍 Debug e Monitoramento

### Logs Detalhados

```python
# Habilitar logs debug
settings.RECORDING_DEBUG_WINDOW_TRACKING = True
settings.RECORDING_DEBUG_ACTIVITY_MONITORING = True

# Salvar logs de atividade em arquivo
settings.RECORDING_SAVE_ACTIVITY_LOG = True
settings.RECORDING_SAVE_WINDOW_STATE_LOG = True
```

### Callbacks de Eventos

```python
def on_window_state_changed(old_state, new_state):
    print(f"Janela: {old_state} -> {new_state}")

def on_activity_detected(event):
    print(f"Atividade: {event.activity_type} em {event.timestamp}")

def on_new_segment_created(segment):
    print(f"Novo segmento: {segment.file_path} (motivo: {segment.reason})")

# Configurar callbacks no SmartSessionRecorder
smart_recorder.window_tracker.set_callbacks(on_state_changed=on_window_state_changed)
smart_recorder.interactivity_monitor.set_callbacks(on_activity=on_activity_detected)
smart_recorder.set_callbacks(on_new_segment=on_new_segment_created)
```

## 🛠️ Solução de Problemas

### Janela RDP Não Encontrada

```python
# Verificar se existem janelas RDP abertas
connection_info = {
    'name': '',  # Nome vazio para detectar qualquer janela RDP
    'ip': ''     # IP vazio para detectar qualquer janela RDP
}

# Aumentar tentativas de reacquisição
settings.RECORDING_WINDOW_REACQUISITION_ATTEMPTS = 10
settings.RECORDING_WINDOW_REACQUISITION_DELAY = 3.0
```

### Gravação Pausando Frequentemente

```python
# Ajustar sensibilidade de atividade
settings.RECORDING_INACTIVITY_TIMEOUT_MINUTES = 30  # Aumentar timeout

# Desabilitar pausa por cobertura se necessário
settings.RECORDING_PAUSE_ON_COVERED = False

# Ajustar intervalo de verificação
settings.RECORDING_WINDOW_TRACKING_INTERVAL = 2.0  # Verificar menos frequentemente
```

### Performance

```python
# Reduzir FPS para melhor performance
settings.RECORDING_FPS = 15

# Reduzir resolução
settings.RECORDING_RESOLUTION_SCALE = 0.8

# Qualidade menor
settings.RECORDING_QUALITY = 50
```

## 📋 Exemplo Completo

Veja o arquivo `smart_recording_example.py` para um exemplo completo de uso do sistema.

```bash
# Executar exemplo
python smart_recording_example.py

# Ver opções de configuração
python smart_recording_example.py config
```

## 🔄 Migração do Sistema Antigo

Para migrar do sistema de gravação antigo:

1. **Substituir SessionRecorder por SmartSessionRecorder**
2. **Atualizar RecordingManager** (já feito)
3. **Adicionar configurações** específicas do sistema inteligente
4. **Ajustar callbacks** para incluir eventos de pausa/retomada
5. **Testar detecção** de janelas RDP existentes

## 🚀 Próximos Passos

- [ ] Suporte para múltiplas sessões simultâneas
- [ ] Interface gráfica para monitoramento
- [ ] Relatórios de atividade detalhados
- [ ] Integração com sistema de notificações
- [ ] Detecção automática de aplicações críticas
- [ ] Backup automático de gravações importantes

---

## 📝 Licença

Este sistema faz parte do projeto WATS e segue a mesma licença do projeto principal.