# MODO DEMO - WATS

## O que é o Modo Demo?

O modo demo permite testar as telas do Admin Panel do WATS sem necessidade de conexão com banco de dados. Útil para desenvolvimento, demonstrações e testes.

## Como Ativar o Modo Demo

### Método 1: Variável de Ambiente

```cmd
# Windows PowerShell
$env:WATS_DEMO_MODE = "true"
python run.py

# Windows CMD
set WATS_DEMO_MODE=true
python run.py

# Linux/Mac
export WATS_DEMO_MODE=true
python run.py
```

### Método 2: Arquivo .env

Crie um arquivo `.env` na raiz do projeto:

```
WATS_DEMO_MODE=true
```

### Método 3: Temporário para Teste

No código, você pode forçar o modo demo editando `wats_app/config.py`:

```python
def is_demo_mode() -> bool:
    return True  # Força modo demo
```

## Funcionalidades Disponíveis em Modo Demo

### 🔐 **CREDENCIAIS DE ACESSO EM MODO DEMO**

- **Usuário Admin**: admin
- **Senha Admin**: **admin123**

### ✅ Admin Panel - Usuários

- Visualizar lista de usuários simulados
- Ver detalhes de usuários
- Criar novos usuários (simulado)
- Editar usuários existentes (simulado)
- Excluir usuários (simulado)

### ✅ Admin Panel - Grupos

- Visualizar grupos simulados
- Gerenciar grupos (simulado)

### ✅ Admin Panel - Conexões

- Visualizar conexões simuladas
- Gerenciar conexões (simulado)

### ✅ Admin Panel - Logs

- Visualizar logs simulados de atividades

## Dados Simulados Incluídos

### Usuários

- **admin** - Administrador (admin@empresa.com)
- **usuario1** - João Silva (joao.silva@empresa.com)
- **usuario2** - Maria Santos (maria.santos@empresa.com)
- **suporte** - Equipe Suporte (suporte@empresa.com)

### Grupos

- **Administradores** - Grupo de administradores do sistema
- **Usuários Finais** - Grupo de usuários finais
- **Suporte Técnico** - Equipe de suporte técnico

### Conexões

- **Servidor Produção** (192.168.1.100)
- **Servidor Desenvolvimento** (192.168.1.101)
- **Servidor Backup** (192.168.1.102)

## Como Identificar que Está em Modo Demo

1. **Log de Inicialização**: Procure por mensagens `[DEMO]` nos logs
2. **Console**: Mensagens indicando uso do mock service
3. **Tela**: Pode exibir indicador visual (se implementado)

## Limitações do Modo Demo

- Dados não são persistidos (resetam a cada execução)
- Não há validação real de credenciais
- Conexões RDP não funcionam
- Logs são simulados

## Desenvolvimento - Adicionando Novos Recursos Demo

Para adicionar suporte demo a novos recursos:

1. **Adicione dados mock** em `wats_app/mock_data_service.py`
2. **Use o DemoAdapter** nos repositórios:

```python
mock_result = self.demo_adapter.execute_with_fallback(
    "operation_name",
    "mock_method_name",
    *args
)
```

3. **Converta dados** do formato mock para o formato esperado

## Solução de Problemas

### Modo demo não ativa

- Verifique se `WATS_DEMO_MODE=true` está definido
- Confirme que não há erros na importação de `is_demo_mode()`

### Erros de importação

- Verifique se `mock_data_service.py` está no local correto
- Confirme que `demo_adapter.py` foi criado

### Dados não aparecem

- Verifique logs para mensagens `[DEMO]`
- Confirme que o repositório usa `DemoAdapter`

## Desativando o Modo Demo

Para voltar ao modo normal:

```cmd
# PowerShell
$env:WATS_DEMO_MODE = $null

# CMD
set WATS_DEMO_MODE=

# Linux/Mac
unset WATS_DEMO_MODE
```

Ou remova/comente a linha no arquivo `.env`.
