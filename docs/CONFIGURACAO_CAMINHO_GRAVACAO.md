# Configuração Personalizável de Caminho de Gravação - WATS

## 📁 Como Configurar o Caminho de Gravação

O WATS agora permite que administradores configurem onde as sessões gravadas serão armazenadas através do arquivo `config.json`.

### Exemplo de Configuração

```json
{
  "database": {
    "type": "sqlserver",
    "server": "192.168.1.100",
    "database": "WATS_DB",
    "username": "wats_user",
    "password": "senha_segura",
    "port": "1433"
  },
  "recording": {
    "enabled": true,
    "auto_start": true,
    "mode": "rdp_window",
    "output_dir": "D:\\WATS_Recordings",
    "fps": 15,
    "quality": 23,
    "resolution_scale": 1.0,
    "max_file_size_mb": 200,
    "max_duration_minutes": 60,
    "max_total_size_gb": 50.0,
    "max_file_age_days": 90,
    "cleanup_interval_hours": 12
  },
  "application": {
    "log_level": "INFO",
    "theme": "Dark"
  }
}
```

## ⚙️ Configurações de Gravação

### Campo `output_dir`

- **Propósito**: Define onde as gravações serão armazenadas
- **Tipo**: String (caminho do diretório)
- **Padrão**: Se vazio ou não especificado, usa `<pasta_do_executavel>/recordings`

### Exemplos de Caminhos

#### Windows

```json
"output_dir": "D:\\WATS_Recordings"
"output_dir": "C:\\ProgramData\\WATS\\Sessions"
"output_dir": "\\\\servidor\\compartilhamento\\WATS"
```

#### Linux/Unix (se aplicável)

```json
"output_dir": "/var/wats/recordings"
"output_dir": "/home/wats/sessions"
"output_dir": "/mnt/storage/wats"
```

## 🔧 Comportamento do Sistema

### Criação Automática de Diretórios

- O WATS criará automaticamente o diretório especificado se ele não existir
- Cria diretórios aninhados conforme necessário
- Exemplo: `D:\\WATS\\Recordings\\2024\\01` será criado automaticamente

### Fallback de Configuração

1. **Prioridade 1**: Valor definido em `config.json` → `recording.output_dir`
2. **Prioridade 2**: Variável de ambiente `RECORDING_OUTPUT_DIR`
3. **Prioridade 3**: Padrão do sistema `<pasta_executavel>/recordings`

### Validação

- O sistema valida se o caminho pode ser criado durante a inicialização
- Logs de erro são gerados se o diretório não puder ser acessado
- Validação acontece apenas quando `recording.enabled = true`

## 📋 Cenários de Uso

### 1. Armazenamento em Disco Dedicado

```json
"recording": {
  "enabled": true,
  "output_dir": "D:\\WATS_Sessions",
  "max_total_size_gb": 100.0
}
```

### 2. Compartilhamento de Rede

```json
"recording": {
  "enabled": true,
  "output_dir": "\\\\servidor-storage\\wats\\recordings",
  "max_file_size_mb": 500
}
```

### 3. Organização por Data (manual)

```json
"recording": {
  "enabled": true,
  "output_dir": "C:\\WATS_Data\\2024\\Sessions",
  "max_file_age_days": 365
}
```

### 4. Ambiente de Desenvolvimento (local)

```json
"recording": {
  "enabled": true,
  "output_dir": "",
  "max_total_size_gb": 5.0
}
```

## 🚨 Considerações Importantes

### Permissões

- O usuário que executa o WATS deve ter permissões de **escrita** no diretório
- Para compartilhamentos de rede, configure as credenciais adequadas
- Teste as permissões antes de colocar em produção

### Espaço em Disco

- Configure `max_total_size_gb` adequadamente para o espaço disponível
- Use `max_file_age_days` para limpeza automática
- Monitore o uso de espaço regularmente

### Performance

- SSDs oferecem melhor performance para gravação
- Evite caminhos de rede lentos para melhor experiência
- Configure `cleanup_interval_hours` baseado no volume de uso

### Backup

- As gravações são críticas para auditoria
- Configure backup automático do diretório de gravações
- Considere replicação para recuperação de desastres

## 🔍 Troubleshooting

### Problema: Diretório não é criado

**Solução**: Verifique permissões e espaço em disco

### Problema: Gravações não aparecem no local configurado

**Solução**:

1. Verifique se `recording.enabled = true`
2. Verifique logs em `wats_app.log`
3. Confirme sintaxe do JSON

### Problema: Performance ruim

**Solução**:

1. Use discos locais quando possível
2. Ajuste `fps` e `quality` conforme necessário
3. Monitore uso de CPU durante gravação

## 📝 Logs Relacionados

Procure por estas mensagens nos logs:

```
INFO - Recording settings: ... output_dir=<caminho>
INFO - Recording system initialized successfully
ERROR - Failed to create output directory: <erro>
```

## ✅ Checklist de Implementação

- [ ] Configurar `output_dir` no config.json
- [ ] Testar criação de diretório
- [ ] Verificar permissões de escrita
- [ ] Configurar limites de espaço
- [ ] Testar gravação real
- [ ] Configurar backup/arquivamento
- [ ] Documentar para equipe

---

**Versão**: 1.0  
**Data**: Janeiro 2024  
**Responsável**: Sistema de Auditoria WATS
