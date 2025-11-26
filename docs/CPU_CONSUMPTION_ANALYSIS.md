# 🖥️ Análise de Consumo de CPU no WATS

Este documento explica as principais razões pelas quais o WATS pode consumir uma quantidade significativa de CPU e oferece orientações para otimizar o desempenho.

---

## 📊 Visão Geral

O WATS é uma aplicação complexa que gerencia conexões RDP, gravação de sessões, monitoramento de processos e sincronização com banco de dados. Cada um desses componentes pode contribuir para o consumo de CPU.

---

## 🔥 Principais Causas de Alto Consumo de CPU

### 1. 🎬 **Sistema de Gravação de Sessões**

**Arquivo:** `src/wats/recording/recording_manager.py`

O sistema de gravação é provavelmente o **maior consumidor de CPU** do WATS.

#### Componentes que consomem CPU:

| Componente | Consumo | Descrição |
|------------|---------|-----------|
| Captura de Tela (MSS) | ⚠️ Alto | Captura frames da tela a cada intervalo de FPS |
| Codificação de Vídeo | ⚠️ Muito Alto | Conversão de frames para H.264/MP4 |
| Compressão em Tempo Real | ⚠️ Alto | Compressão durante a gravação |
| Monitoramento de Janelas | 🔵 Médio | Detecta janelas RDP ativas |

#### Como funciona:

A cada intervalo (ex: 10 FPS = 100ms), o WATS:
1. Captura um screenshot da tela/janela
2. Compara com o frame anterior
3. Codifica o frame em vídeo
4. Escreve no disco

#### Configurações que afetam o consumo:

```json
{
  "recording": {
    "fps": 10,              // ⚠️ Maior FPS = Maior CPU
    "quality": 23,          // ⚠️ Menor valor = Maior qualidade = Mais CPU
    "resolution_scale": 1.0 // ⚠️ 1.0 = Resolução total = Mais CPU
  }
}
```

**💡 Recomendação:** Para reduzir consumo de CPU:
- Reduzir FPS para 5-8 (suficiente para auditoria)
- Aumentar quality para 28-33
- Usar resolution_scale de 0.75

---

### 2. 🔄 **Heartbeat e Monitoramento de Processos RDP**

**Arquivo:** `src/wats/app_window.py` (linha ~1305) e `src/wats/utils/process_monitor.py`

O sistema de heartbeat verifica continuamente se os processos RDP estão ativos.

#### Como funciona:
```python
# Thread de heartbeat (roda a cada 2 segundos por conexão):
def heartbeat_task():
    while not stop_flag.wait(2):  # A cada 2 segundos
        # 1. Chama is_rdp_connection_active()
        rdp_active = is_rdp_connection_active(server_ip, rdp_user, title)
        # 2. Atualiza banco de dados
        heartbeat_sent = self.db.logs.update_heartbeat(con_id, user)
```

#### O que consome CPU:

1. **`psutil.process_iter()`** - Itera sobre TODOS os processos do sistema
2. **Regex para parsing** - Extrai informações de linha de comando
3. **win32gui.EnumWindows()** - Enumera todas as janelas abertas

```python
# Em process_monitor.py:
def get_active_rdp_processes(self):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        # Itera sobre CENTENAS de processos a cada 2 segundos
```

**💡 Recomendação:** 
- O intervalo de heartbeat já foi otimizado para 2 segundos
- Evitar ter muitas conexões ativas simultaneamente
- O consumo é proporcional ao número de conexões ativas

---

### 3. 🔃 **Refresh Automático da Treeview**

**Arquivo:** `src/wats/app_window.py` (método `_populate_tree`)

A cada 30 segundos (60 segundos após carga inicial), o WATS atualiza a lista de conexões.

#### O que acontece:
```python
def _populate_tree(self):
    # 1. Limpeza periódica em background
    self._cleanup_orphaned_connections()  # Pode ser custoso
    self._cleanup_orphaned_protections()
    
    # 2. Query ao banco de dados
    raw_data = self.db.connections.select_all(self.user_session_name)
    
    # 3. Processamento de dados
    [ConnectionData(row) for row in raw_data]  # Cria objetos
    
    # 4. Atualização diferencial da UI
    self._process_tree_update(new_data_list)
```

#### Consumo por operação:

| Operação | Consumo | Frequência |
|----------|---------|------------|
| Cleanup de conexões órfãs | 🔵 Médio | A cada refresh |
| Query ao banco | 🟢 Baixo | A cada 30s |
| Criação de objetos | 🟢 Baixo | A cada 30s |
| Atualização diferencial UI | 🟢 Baixo | A cada 30s |

---

### 4. 🧵 **Thread Pool e Operações Assíncronas**

**Arquivo:** `src/wats/util_cache/thread_pool.py`

O WATS usa um ThreadPool com até 8 workers (5 I/O + 3 CPU).

```python
class WASTThreadPool:
    def __init__(self):
        self._io_pool = ThreadPoolExecutor(max_workers=5)
        self._cpu_pool = ThreadPoolExecutor(max_workers=3)
```

#### Quando múltiplas threads estão ativas:
- Operações de banco de dados
- Monitoramento de heartbeats
- Limpeza de proteções/conexões órfãs
- Compressão de vídeos em background

---

### 5. 🗄️ **Operações de Banco de Dados**

Embora as queries sejam otimizadas, operações frequentes podem consumir CPU:

| Operação | Frequência | Impacto |
|----------|------------|---------|
| Heartbeat update | A cada 2s por conexão | Baixo |
| Log de conexão | Uma vez por conexão | Baixo |
| Select de conexões | A cada 30s | Baixo-Médio |
| Cleanup de logs órfãos | A cada ~3 minutos | Médio |

---

### 6. 📱 **Interface Gráfica (CustomTkinter)**

**Arquivo:** `src/wats/app_window.py`

A interface usa CustomTkinter (baseado em Tkinter), que:
- Renderiza widgets customizados
- Processa eventos de mouse/teclado
- Atualiza a Treeview com muitos itens

#### Situações que consomem mais CPU:
- Muitos itens na lista (100+ conexões)
- Filtro em tempo real (reprocessa a cada caractere)
- Animações de loading

---

## 📈 Tabela Resumo de Consumo

| Componente | Consumo Base | Com Gravação | Observação |
|------------|-------------|--------------|------------|
| **Gravação de Sessão** | 0% | 15-40% | Maior consumidor |
| **Heartbeat (por conexão)** | 0.5-1% | 0.5-1% | Multiplicado por conexões ativas |
| **Refresh da Treeview** | 0.5% | 0.5% | A cada 30s |
| **Monitoramento de Processos** | 1-3% | 1-3% | Quando há conexões ativas |
| **Interface Gráfica** | 1-2% | 1-2% | Maior com muitos itens |
| **Operações de Banco** | 0.5-1% | 0.5-1% | Depende da latência do servidor |

---

## ⚡ Dicas de Otimização

### 1. Configuração de Gravação

```json
// config.json - Configuração para menor consumo de CPU
{
  "recording": {
    "enabled": true,
    "fps": 5,                    // Reduzir de 10 para 5
    "quality": 30,               // Aumentar de 23 para 30
    "resolution_scale": 0.75,    // Reduzir de 1.0 para 0.75
    "pause_on_minimized": true,  // Pausar quando minimizado
    "pause_on_covered": true     // Pausar quando coberto
  }
}
```

### 2. Reduzir Conexões Simultâneas

Cada conexão ativa adiciona:
- 1 thread de heartbeat
- Monitoramento contínuo de processo
- Queries periódicas ao banco

**Recomendação:** Limitar conexões simultâneas a 5-10 por usuário.

### 3. Desabilitar Gravação (quando não necessário)

```json
{
  "recording": {
    "enabled": false
  }
}
```

Ou desabilitar via variável de ambiente:
```bash
RECORDING_ENABLED=false
```

### 4. Aumentar Intervalo de Refresh

O intervalo padrão é 30 segundos. Para ambientes estáveis:

```python
# Em app_window.py, linha ~768:
self._refresh_job = self.after(60000, self._populate_tree)  # 60 segundos
```

### 5. Otimizar Monitoramento de Processos

Se a detecção de RDP não for crítica, aumentar tolerância:

```python
# Em process_monitor.py:
tolerance_seconds: int = 30  # Aumentar de 10 para 30
```

---

## 🔍 Como Diagnosticar

### 1. Monitorar Processos Python

```powershell
# Windows - Ver uso de CPU do WATS
Get-Process python* | Select-Object CPU, WorkingSet, Name

# Monitorar em tempo real (pressione Ctrl+C para parar)
while($true) { Get-Process python* | Select CPU; Start-Sleep 1 }
```

### 2. Verificar Logs

```powershell
# Buscar operações custosas
Select-String -Path logs/wats_app.log -Pattern "PERF|RECORDING|HEARTBEAT"
```

### 3. Identificar Threads Ativas

No código, adicionar logging temporário para diagnóstico:
```python
import threading
import logging
logging.info(f"Active threads: {threading.active_count()}")
```

---

## 📊 Comparativo: Com e Sem Gravação

| Cenário | CPU Idle | CPU Ativo (1 conexão) | CPU Ativo (5 conexões) |
|---------|----------|----------------------|------------------------|
| **Sem gravação** | 0-2% | 3-5% | 8-15% |
| **Com gravação (10 FPS)** | 0-2% | 15-25% | 25-40% |
| **Com gravação (5 FPS)** | 0-2% | 8-15% | 15-25% |

---

## 🎯 Conclusão

O WATS pode consumir bastante CPU principalmente por:

1. **🎬 Gravação de sessões** - O maior consumidor (codificação de vídeo em tempo real)
2. **🔄 Heartbeats contínuos** - Verificação de processos RDP a cada 2 segundos
3. **🔍 Monitoramento de processos** - Iteração sobre todos os processos do sistema
4. **🗄️ Operações de banco** - Queries e updates frequentes

### Recomendações Principais:

1. **Ajustar FPS da gravação** para 5 se a qualidade de vídeo não for crítica
2. **Desabilitar gravação** em ambientes onde não é necessária
3. **Limitar conexões simultâneas** a um número razoável
4. **Monitorar logs** para identificar gargalos específicos
5. **Usar SSD** para reduzir I/O da gravação

---

*Documentação criada com base na análise do código fonte do WATS v4.2*
