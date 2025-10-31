# Manual do Painel de Permissões Individuais - WATS

## Como Acessar

1. **Abrir o Sistema WATS**
2. **Entrar como Administrador**
3. **Acessar Painel de Administração**
4. **Clicar em "🔐 Gerenciar Permissões de Acesso"**

## Interface do Sistema de Abas

O painel "🔐 Gerenciar Permissões de Acesso" possui **2 abas**:

### 📁 **Aba 1: Permissões de Grupo**

- Funcionalidade atual do sistema
- Gerencia permissões baseadas em grupos
- Mantém compatibilidade total

### 👤 **Aba 2: Permissões Individuais** ⭐ NOVA

- **Nova funcionalidade** para conceder acessos específicos
- Layout de 3 colunas: Usuários | Conexões | Permissões Ativas

## Permissões Temporárias

### 🕐 **Painel Separado** (próxima implementação)

- Será um **botão separado** no Painel de Administração
- **Não faz parte** do painel de permissões de acesso
- Terá sua própria interface dedicada
- Permitirá acessos com data de expiração automática

---

## Como Usar: Permissões Individuais

### **Coluna 1: USUÁRIOS**
```
👤 USUÁRIOS
🔍 [Buscar usuário...]
┌─────────────────┐
│ • João Silva    │
│ • Maria Santos  │
│ • Pedro Oliveira│
│ • Ana Costa     │
└─────────────────┘
```

**Funcionalidades:**
- ✅ **Filtro de busca**: Digite para filtrar usuários
- ✅ **Lista de usuários ativos**: Mostra todos os usuários do sistema
- ✅ **Seleção**: Clique em um usuário para selecioná-lo

### **Coluna 2: CONEXÕES DISPONÍVEIS**
```
🖥️ CONEXÕES DISPONÍVEIS
🔍 [Buscar conexão...]
[Observações (opcional)...]
┌─────────────────┐
│ ☐ ats-bd 01     │
│ ☐ ats-app 01    │
│ ☐ srv-web       │
│ ☐ db-prod       │
└─────────────────┘
  [✅ Conceder Acesso]
```

**Funcionalidades:**
- ✅ **Filtro de busca**: Digite para filtrar conexões
- ✅ **Lista de conexões**: Mostra todas as conexões disponíveis
- ✅ **Campo observações**: Adicione motivo/observação
- ✅ **Botão conceder**: Concede acesso à conexão selecionada

### **Coluna 3: PERMISSÕES ATIVAS**
```
🔑 PERMISSÕES ATIVAS
Usuário: João Silva
┌─────────────────┐
│ ✓ ats-app01     │
│ ✓ srv-web       │
│                 │
└─────────────────┘
[❌ Revogar] [🔄 Atualizar]
```

**Funcionalidades:**
- ✅ **Mostra usuário selecionado**
- ✅ **Lista permissões ativas**: Só do usuário selecionado
- ✅ **Botão revogar**: Remove permissão selecionada
- ✅ **Botão atualizar**: Recarrega todas as listas

---

## Passo a Passo: Conceder Acesso Individual

### **Exemplo Prático:**
*Quero dar acesso apenas ao "ats-app 01" para o usuário "João Silva"*

1. **Selecionar Usuário:**
   - Na coluna 1, digite "João" no filtro
   - Clique em "João Silva (ID: 5)"

2. **Escolher Conexão:**
   - Na coluna 2, digite "ats-app" no filtro
   - Clique na linha "ats-app 01"
   - (Opcional) Digite observação: "Acesso para projeto X"

3. **Conceder Acesso:**
   - Clique no botão "✅ Conceder Acesso"
   - Confirme na dialog que aparece

4. **Verificar Resultado:**
   - Na coluna 3, aparecerá "ats-app 01" nas permissões ativas
   - João Silva agora pode acessar apenas esta conexão

---

## Passo a Passo: Revogar Acesso Individual

1. **Selecionar Usuário:**
   - Clique no usuário na coluna 1

2. **Selecionar Permissão:**
   - Na coluna 3, clique na permissão que quer revogar

3. **Revogar:**
   - Clique no botão "❌ Revogar Acesso"
   - Confirme na dialog

4. **Verificar:**
   - A permissão desaparece da lista
   - Usuário perde acesso à conexão

---

## Vantagens do Sistema

### **Flexibilidade Total:**
- ✅ **Usuário pode ter AMBOS**: acesso de grupo + permissões individuais
- ✅ **Usuário pode ter APENAS**: permissões individuais (sem grupo)
- ✅ **Granularidade**: Acesso específico a conexões individuais

### **Exemplos de Uso:**

**Cenário 1: Acesso Específico**
```
Problema: Grupo "Saphir" tem ats-bd 01 + ats-app 01
Solução: Dar acesso individual apenas ao ats-app 01
Resultado: Usuário vê SÓ o ats-app 01
```

**Cenário 2: Acesso Adicional**
```
Situação: Usuário já tem grupo "Desenvolvimento"
Necessidade: Precisa de UMA conexão de "Produção"
Solução: Manter grupo + dar acesso individual à conexão específica
Resultado: Usuário vê grupo Desenvolvimento + conexão específica de Produção
```

**Cenário 3: Acesso Temporário (futuro)**
```
Necessidade: Acesso por 2 horas apenas
Solução: Usar aba "Permissões Temporárias" (próxima implementação)
```

---

## Filtros de Busca

### **Busca de Usuários:**
- Digite parte do nome: `joão` → encontra "João Silva"
- Digite ID: `5` → encontra usuário com ID 5
- Busca é **case-insensitive** (não importa maiúscula/minúscula)

### **Busca de Conexões:**
- Por nome: `ats` → encontra "ats-bd 01", "ats-app 01"
- Por IP: `192.168` → encontra conexões com esse IP
- Por grupo: `saphir` → encontra conexões do grupo Saphir

---

## Compatibilidade

✅ **100% Compatível** com sistema existente  
✅ **Não quebra** funcionalidades atuais  
✅ **Adiciona** nova capacidade sem modificar o que já funciona  
✅ **Usuários admin** continuam vendo tudo  
✅ **Usuários comuns** veem: permissões de grupo + permissões individuais  

---

## Troubleshooting

### **Problema: Não vejo o botão "Gerenciar Permissões de Acesso"**
- **Solução**: Certifique-se de estar logado como administrador

### **Problema: Lista de usuários vazia**
- **Solução**: Verifique se há usuários ativos no sistema

### **Problema: Erro ao conceder acesso**
- **Solução**: 
  1. Verifique se a tabela `Permissao_Conexao_Individual_WTS` foi criada
  2. Execute o script SQL: `scripts/create_individual_permissions_table.sql`

### **Problema: Permissões não aparecem na lista principal**
- **Solução**: 
  1. Clique em "🔄 Atualizar" 
  2. Feche e reabra a aplicação principal

---

## Próximos Passos

### **Implementado ✅**

- Permissões individuais permanentes
- Interface com filtros de busca  
- Sistema de 2 abas organizado (Grupo + Individual)
- Botão dedicado no Admin Hub

### **Próximo: Painel de Permissões Temporárias 🔄**

- **Novo painel separado** no Admin Hub
- Botão próprio: "🕐 Permissões Temporárias"
- Funcionalidades:
  - Acessos com data de expiração
  - Notificações de vencimento
  - Limpeza automática de acessos expirados
  - Interface específica para gerenciar prazos

### **Futuro: Melhorias 📋**

- Relatórios de permissões
- Auditoria de concessões/revogações  
- Notificações por email
- Dashboard de resumo de acessos