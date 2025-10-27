# ✅ Checklist de Migração - Validação de Senhas no Servidor

## 🎯 **Objetivo**

Migrar a validação de senhas de proteção de sessão do modo local para validação no servidor SQL Server.

## 📝 **Status Atual**

### ✅ **Já Implementado:**

1. **Repositório no Servidor**

   - ✅ `SessionProtectionRepository` criado
   - ✅ Stored procedures no SQL Server implementadas
   - ✅ Hash SHA-256 das senhas
   - ✅ Auditoria completa de tentativas

2. **Interface Atualizada**

   - ✅ `SessionProtectionManager` modificado para usar servidor
   - ✅ Fallback para modo local mantido
   - ✅ Configuração automática com DBService

3. **Documentação**
   - ✅ Exemplo de integração criado
   - ✅ Documentação atualizada

### 🔄 **Pendente de Implementação:**

4. **Integração no Código Principal** ✅ **CONCLUÍDO**

   - ✅ Modificar `app_window.py` para configurar sistema com DBService
   - ✅ Adicionar verificação de proteção antes das conexões RDP/MSTSC
   - ✅ Adicionar opções de proteção no menu de contexto
   - ✅ Implementar funções `_protect_session` e `_remove_session_protection`

5. **Configuração Inicial** ⏳ **PENDENTE**
   - ❌ Executar scripts SQL para criar tabelas e procedures
   - ❌ Testar conectividade com SQL Server
   - ❌ Verificar permissões de usuário no banco

## 🚀 **Próximos Passos**

### **1. Executar Scripts no Banco de Dados** ⚠️ **OBRIGATÓRIO**

```sql
-- 1. Abra SQL Server Management Studio
-- 2. Conecte ao seu servidor SQL Server
-- 3. Execute o script atualizado:
USE [WATS_Database]
GO

-- Verificar se tabelas foram criadas
SELECT name FROM sys.tables WHERE name LIKE '%Protecao%'

-- Verificar se procedures foram criadas
SELECT name FROM sys.procedures WHERE name LIKE '%Protecao%'

-- Testar procedure de validação
EXEC sp_Validar_Protecao_Sessao
    @Con_Codigo = 1,
    @Prot_Senha_Hash = 'hash_teste',
    @Usu_Nome_Solicitante = 'usuario_teste',
    @Usu_Maquina_Solicitante = 'PC-TESTE',
    @LTent_IP_Solicitante = '192.168.1.100'
```

### **2. Validar Integração no WATS** ✅ **IMPLEMENTADO**

```python
# O código já foi modificado em app_window.py
# - Sistema configurado automaticamente na inicialização
# - Verificação de proteção antes de todas as conexões
# - Menu de contexto com opções de proteção
# - Logs detalhados de todas as operações
```

### **3. Testar Funcionalidades**

1. **Teste Básico de Proteção:**

   - Conectar ao WATS
   - Clicar com botão direito em um servidor
   - Selecionar "🔒 Proteger Sessão"
   - Definir senha e duração
   - Verificar se proteção foi criada no banco

2. **Teste de Validação:**

   - Em outra máquina/usuário, tentar conectar ao mesmo servidor
   - Verificar se pede senha de proteção
   - Testar senha incorreta (deve negar)
   - Testar senha correta (deve permitir)

3. **Teste de Remoção:**
   - Usuário que criou a proteção deve conseguir removê-la
   - Outros usuários não devem conseguir remover

### **2. Modificar Código Principal WATS**

**Arquivo:** `src/wats/main.py` (ou equivalente)

```python
# Adicionar configuração do sistema de proteção
from docs.session_protection import configure_session_protection_with_db

def main():
    # ... código existente ...

    # Configurar proteção de sessão com banco
    configure_session_protection_with_db(db_service)

    # ... resto da aplicação ...
```

**Arquivo:** `src/wats/admin_panels/connection_manager.py`

```python
# Adicionar verificação antes de conectar
from docs.session_protection import session_protection_manager

def connect_to_server(self, connection_data):
    connection_id = connection_data.get('db_id')
    current_user = get_current_user()  # Implementar

    # Verificar se está protegido
    if session_protection_manager.is_session_protected(connection_id):
        # Mostrar diálogo de senha
        # Validar no servidor
        # Prosseguir ou negar acesso
```

### **3. Testes de Validação**

1. **Teste Básico:**

   - ✅ Criar proteção via interface
   - ✅ Verificar se foi salva no SQL Server
   - ✅ Tentar validar senha correta
   - ✅ Tentar validar senha incorreta

2. **Teste Distribuído:**

   - ❌ Criar proteção em WATS Máquina A
   - ❌ Tentar acessar de WATS Máquina B
   - ❌ Verificar sincronização em tempo real

3. **Teste de Performance:**
   - ❌ Validar múltiplas senhas simultaneamente
   - ❌ Verificar tempo de resposta do servidor
   - ❌ Testar fallback para modo local

## 📋 **Comandos para Execução**

### **1. Executar Scripts SQL**

```sql
-- Conectar no SQL Server Management Studio
-- Executar: scripts/create_wats_database.sql
-- Verificar criação das tabelas:
SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Protecao%'
```

### **2. Testar Procedures**

```sql
-- Teste de criação
EXEC sp_Criar_Protecao_Sessao
    @Con_Codigo = 1,
    @Usu_Nome_Protetor = 'teste',
    @Usu_Maquina_Protetor = 'DESKTOP-TEST',
    @Prot_Senha_Hash = 'hash_teste',
    @Prot_Duracao_Minutos = 60;

-- Teste de validação
EXEC sp_Validar_Protecao_Sessao
    @Con_Codigo = 1,
    @Prot_Senha_Hash = 'hash_teste',
    @Usu_Nome_Solicitante = 'user_test';
```

### **3. Integrar no WATS**

```python
# No arquivo main da aplicação
from docs.session_protection import configure_session_protection_with_db

# Após inicializar DBService
configure_session_protection_with_db(self.db_service)
```

## 🔍 **Verificação Final**

- [ ] Senhas são validadas no servidor SQL Server
- [ ] Logs de tentativas aparecem na tabela de auditoria
- [ ] Proteções são sincronizadas entre máquinas
- [ ] Fallback local funciona se servidor não disponível
- [ ] Performance é aceitável para validações
- [ ] Documentação está atualizada

## 🎯 **Resultado Esperado**

Após a implementação completa:

1. **Usuário A** conecta no servidor e cria proteção com senha "123456"
2. **Usuário B** em outra máquina tenta conectar ao mesmo servidor
3. WATS consulta SQL Server e detecta proteção ativa
4. Usuário B digita senha "123456"
5. WATS envia hash para stored procedure no SQL Server
6. Servidor valida hash e registra acesso autorizado
7. Usuário B conecta com sucesso

**✅ Validação 100% no servidor SQL Server!**
