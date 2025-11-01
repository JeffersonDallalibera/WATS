# 📋 Exemplos de Configuração - WATS

## 🎯 Configurações Mais Comuns

### 1. **Gravação na Pasta de Vídeos do Usuário**
```json
{
  "recording": {
    "output_dir": "{VIDEOS}/WATS"
  }
}
```
**Resultado:** `C:/Users/[usuario]/Videos/WATS`

### 2. **Gravação em Pasta Personalizada no Desktop**
```json
{
  "recording": {
    "output_dir": "{DESKTOP}/Gravacoes_RDP"
  }
}
```
**Resultado:** `C:/Users/[usuario]/Desktop/Gravacoes_RDP`

### 3. **Gravação em Documentos por Projeto**
```json
{
  "recording": {
    "output_dir": "{DOCUMENTS}/Empresa/WATS_Sessions"
  }
}
```
**Resultado:** `C:/Users/[usuario]/Documents/Empresa/WATS_Sessions`

### 4. **Configuração para Servidor/Rede**
```json
{
  "recording": {
    "output_dir": "D:/Shared/WATS_Recordings"
  }
}
```
**Resultado:** `D:/Shared/WATS_Recordings` (caminho fixo)

### 5. **Configuração Temporária**
```json
{
  "recording": {
    "output_dir": "{TEMP}/WATS_Temp"
  }
}
```
**Resultado:** `C:/Users/[usuario]/AppData/Local/Temp/WATS_Temp`

## ✅ **Vantagens das Variáveis de Sistema:**

- 🔄 **Portabilidade:** Funciona em qualquer computador
- 👥 **Multi-usuário:** Cada usuário tem sua pasta própria
- 🔐 **Segurança:** Respeita permissões do usuário
- 🎯 **Organização:** Usa pastas padrão do Windows
- 🛠️ **Automação:** Pastas são criadas automaticamente

## 📁 **O que acontece quando você configura:**

1. **WATS lê** o `config.json`
2. **Expande** as variáveis (ex: `{VIDEOS}` → `C:/Users/usuario/Videos`)
3. **Verifica** se a pasta existe
4. **Cria automaticamente** se não existir
5. **Testa** se é possível gravar na pasta
6. **Informa** no log se tudo está OK

## 🚨 **Importante:**

- ✅ Pastas são criadas **automaticamente**
- ✅ Sistema verifica **permissões** de escrita
- ✅ Logs informam **status** da criação
- ⚠️ Use `DEBUG` no log_level para ver detalhes da criação