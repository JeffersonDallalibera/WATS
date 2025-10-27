# 🔒 Sistema de Proteção de Sessões Temporárias - WATS

## 📋 Visão Geral

O sistema de **proteção de sessões temporárias** permite que um usuário conectado a um servidor crie uma "barreira" temporária que impede outros usuários de acessar o mesmo servidor sem uma senha específica.

### 🎯 **Objetivo Principal**

Resolver conflitos quando múltiplos usuários querem acessar o mesmo servidor simultaneamente, dando controle ao usuário que já está conectado.

### 🔄 **Validação no Servidor** ✅

**IMPORTANTE:** A partir desta versão, toda validação de senhas é feita no servidor SQL Server, não mais localmente. Isso garante:

- ✅ **Segurança**: Senhas nunca trafegam em texto plano
- ✅ **Centralização**: Todas as instâncias WATS compartilham as mesmas proteções
- ✅ **Auditoria**: Logs completos de todas as tentativas no banco
- ✅ **Sincronização**: Proteções são visíveis em tempo real entre máquinas

## 🔄 **Funcionamento Completo**

### **Cenário Típico:**

1. **João** está trabalhando no "Servidor de Produção"
2. **Maria** tenta conectar no mesmo servidor
3. **João** recebe notificação e pode criar uma proteção temporária no servidor
4. **Maria** precisa da senha que é validada no servidor SQL Server
5. Proteção expira automaticamente ou João remove manualmente

### **Fluxo de Validação no Servidor:**

```
Usuário tenta conectar
       ↓
WATS verifica se servidor está protegido (consulta SQL Server)
       ↓
Se protegido: Solicita senha
       ↓
Senha enviada para stored procedure no SQL Server
       ↓
Servidor valida hash SHA-256 e registra tentativa
       ↓
Retorna resultado: SUCESSO ou NEGADO
```

## 🗄️ **Estrutura no Banco de Dados**

### **Tabela Principal: `Sessao_Protecao_WTS`**

```sql
-- Armazena as proteções ativas
Prot_Id                  -- ID único da proteção
Con_Codigo              -- Servidor protegido
Usu_Nome_Protetor       -- Usuário que criou a proteção
Usu_Maquina_Protetor    -- Máquina do protetor
Prot_Senha_Hash         -- Hash SHA-256 da senha
Prot_Observacoes        -- Motivo da proteção
Prot_Data_Criacao       -- Quando foi criada
Prot_Data_Expiracao     -- Quando expira
Prot_Duracao_Minutos    -- Duração em minutos
Prot_Status             -- ATIVA, EXPIRADA, REMOVIDA
```

### **Tabela de Auditoria: `Log_Tentativa_Protecao_WTS`**

```sql
-- Registra todas as tentativas de acesso
LTent_Id                -- ID da tentativa
Prot_Id                 -- Proteção relacionada
Usu_Nome_Solicitante    -- Quem tentou acessar
LTent_Resultado         -- SUCESSO, SENHA_INCORRETA, etc.
LTent_Data_Hora         -- Quando tentou
LTent_IP_Solicitante    -- IP da máquina solicitante
```

## 🚀 **Como Funciona na Prática**

### **1. Criação de Proteção**

```python
# Usuário conectado cria proteção
sp_Criar_Protecao_Sessao(
    @Con_Codigo = 123,
    @Usu_Nome_Protetor = 'joao.silva',
    @Prot_Senha_Hash = 'hash_sha256_da_senha',
    @Prot_Duracao_Minutos = 60,
    @Prot_Observacoes = 'Manutenção crítica em andamento'
)
```

### **2. Tentativa de Acesso**

```python
# Outro usuário tenta acessar
sp_Validar_Protecao_Sessao(
    @Con_Codigo = 123,
    @Prot_Senha_Hash = 'hash_tentativa',
    @Usu_Nome_Solicitante = 'maria.santos',
    @Resultado = OUTPUT  -- SUCESSO ou SENHA_INCORRETA
)
```

### **3. Limpeza Automática**

```python
# Executado periodicamente
sp_Limpar_Protecoes_Expiradas()
```

## 🖥️ **Interface do Usuário**

### **Fluxo para Usuário Conectado (Protetor):**

1. **Clique direito** na conexão ativa
2. **"Proteger Sessão"** no menu de contexto
3. **Definir senha** (6-20 caracteres ou auto-gerada)
4. **Escolher duração** (30 min, 1h, 2h)
5. **Adicionar observações** (opcional)
6. **Confirmar proteção**

### **Fluxo para Usuário Solicitante:**

1. **Tentar conectar** ao servidor protegido
2. **Diálogo de senha** aparece automaticamente
3. **Digitar senha** fornecida pelo protetor
4. **Acessar servidor** se senha correta

## 🔧 **Stored Procedures Principais**

### **sp_Criar_Protecao_Sessao**

- Cria nova proteção para um servidor
- Remove proteção anterior se existir
- Calcula data de expiração automática

### **sp_Validar_Protecao_Sessao**

- Verifica se servidor está protegido
- Valida senha fornecida
- Registra tentativa de acesso
- Retorna resultado (sucesso/falha)

### **sp_Remover_Protecao_Sessao**

- Remove proteção ativa
- Apenas protetor ou admin pode remover
- Marca como "REMOVIDA" (não exclui)

### **sp_Limpar_Protecoes_Expiradas**

- Marca proteções expiradas
- Executado automaticamente
- Mantém histórico para auditoria

## 📊 **Relatórios e Monitoramento**

### **Proteções Ativas**

```sql
EXEC sp_Relatorio_Protecoes_Ativas;
-- Mostra todas as proteções ativas no momento
```

### **Tentativas de Acesso**

```sql
EXEC sp_Relatorio_Tentativas_Protecao
    @DataInicio = '2024-01-01',
    @DataFim = '2024-01-31';
-- Histórico de tentativas por período
```

### **Conexões com Status**

```sql
SELECT * FROM vw_Conexoes_Completas;
-- Mostra conexões e se estão protegidas
```

## 🔐 **Segurança e Auditoria**

### **Hash de Senhas**

- Senhas são armazenadas como **SHA-256**
- Nunca em texto plano
- Comparação segura no banco

### **Log Completo**

- **Todas as tentativas** são registradas
- **IP e máquina** do solicitante
- **Resultado** da validação
- **Timestamp** preciso

### **Expiração Automática**

- Proteções **expiram automaticamente**
- Trigger remove ao desconectar
- Limpeza periódica via job

## 🚨 **Tratamento de Cenários**

### **Usuário Desconecta**

- **Trigger automático** remove proteções
- Log registra remoção por "SISTEMA_DESCONEXAO"
- Outros usuários podem acessar imediatamente

### **Proteção Expira**

- Status muda para "EXPIRADA"
- Novas tentativas são liberadas
- Histórico mantido para auditoria

### **Admin Override**

- **Administradores** podem remover qualquer proteção
- **Log registra** quem removeu
- **Notificação** pode ser enviada ao protetor

### **Múltiplas Tentativas**

- **Todas registradas** no log
- **Sem bloqueio** por tentativas incorretas
- **Relatório** de tentativas suspeitas

## ⚙️ **Configurações do Sistema**

### **Parâmetros Configuráveis**

```sql
-- No Config_Sistema_WTS
INSERT INTO Config_Sistema_WTS VALUES
('PROTECAO_DURACAO_MAX', '480', 'Máxima duração em minutos (8h)'),
('PROTECAO_SENHA_MIN', '6', 'Tamanho mínimo da senha'),
('PROTECAO_AUTO_CLEANUP', '300', 'Intervalo de limpeza em segundos'),
('PROTECAO_LOG_RETENTION', '90', 'Dias para manter logs');
```

### **Jobs Automáticos**

- **Limpeza de proteções expiradas** (a cada 5 minutos)
- **Limpeza de logs antigos** (diário)
- **Relatório de proteções** (semanal)

## 📈 **Benefícios do Sistema**

### **Para Usuários**

- ✅ **Controle total** sobre sua sessão
- ✅ **Evita interrupções** durante trabalho crítico
- ✅ **Compartilhamento seguro** da senha
- ✅ **Expiração automática** - não esquece de liberar

### **Para Administradores**

- ✅ **Auditoria completa** de acessos
- ✅ **Relatórios detalhados** de uso
- ✅ **Override administrativo** quando necessário
- ✅ **Automação** de limpeza e manutenção

### **Para a Empresa**

- ✅ **Segurança** aprimorada
- ✅ **Rastreabilidade** total
- ✅ **Eficiência** operacional
- ✅ **Conformidade** com políticas

## 🔄 **Ambiente Distribuído**

### **Sincronização Entre Máquinas**

- Cada WATS consulta o **banco central**
- Proteções são **compartilhadas** entre todas as máquinas
- **Real-time** - mudanças visíveis imediatamente

### **Identificação Única**

- **Nome do usuário** + **nome da máquina**
- **IP da máquina** para auditoria
- **Timestamp** para resolução de conflitos

### **Tolerância a Falhas**

- **Conexão perdida** - proteções mantidas
- **Crash da aplicação** - trigger limpa automaticamente
- **Backup/restore** - histórico preservado

## 📝 **Exemplo Prático**

### **Cenário Real:**

```
1. João conecta no "Servidor-Producao" às 14:00
2. João precisa fazer deploy crítico (2 horas)
3. João clica direito → "Proteger Sessão"
4. Define senha "deploy2024" e duração 2h
5. Sistema cria proteção válida até 16:00

6. Maria tenta conectar às 14:30
7. Sistema mostra: "Servidor protegido por João"
8. Maria digita "deploy2024"
9. Acesso liberado - ambos podem trabalhar

10. Pedro tenta às 15:00 com senha errada
11. Sistema nega acesso e registra tentativa
12. Pedro pede senha para João

13. Às 16:00 proteção expira automaticamente
14. Qualquer um pode conectar livremente
```

### **Logs Gerados:**

```sql
-- Proteção criada
Prot_Id: 1, Protetor: joao.silva, Servidor: Servidor-Producao
Criado: 14:00, Expira: 16:00, Status: ATIVA

-- Tentativas registradas
Maria: 14:30 - SUCESSO
Pedro: 15:00 - SENHA_INCORRETA
Pedro: 15:15 - SUCESSO (após pedir senha)

-- Expiração automática
16:00 - Status: EXPIRADA
```

---

**🎯 Este sistema oferece controle granular, auditoria completa e automação inteligente para gerenciar conflitos de acesso em ambientes corporativos!**
