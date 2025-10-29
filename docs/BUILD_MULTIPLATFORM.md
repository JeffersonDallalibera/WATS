# WATS - Build Multiplataforma

Este documento explica como gerar executáveis do WATS para Windows (.exe) e Linux (.deb).

## 📋 Requisitos

### Windows

- Python 3.11+
- pip
- PyInstaller
- Todas as dependências do `requirements.txt`
- **FreeRDP** (opcional, para melhor compatibilidade): `winget install FreeRDP.FreeRDP`

### Linux

- Python 3.11+
- pip
- PyInstaller
- python3-tk (para interface gráfica)
- dpkg-dev (para criar pacotes .deb)
- **FreeRDP** (recomendado): `sudo apt-get install freerdp2-x11`
- Todas as dependências do `requirements-linux.txt`

### Docker (Opcional)

- Docker Desktop ou Docker Engine
- Para builds cross-platform

## 🚀 Como Fazer Build

### Método 1: Script Universal (Recomendado)

```bash
# Build automático (detecta plataforma)
python build.py

# Build específico para Windows
python build.py --platform windows

# Build específico para Linux
python build.py --platform linux

# Build usando Docker
python build.py --platform docker

# Limpar builds anteriores
python build.py --clean
```

### Método 2: Scripts Específicos

#### Windows
```cmd
# Execute no prompt de comando
scripts\build_windows.bat
```

#### Linux
```bash
# Execute no terminal
chmod +x scripts/build_linux.sh
./scripts/build_linux.sh
```

### Método 3: Makefile

```bash
# Build automático
make build

# Windows específico
make build-windows

# Linux específico
make build-linux

# Docker
make build-docker

# Todas as plataformas
make build-all

# Apenas pacote .deb
make package-deb
```

## 📦 Arquivos Gerados

### Windows
- `dist/WATS/WATS.exe` - Executável principal
- `dist/WATS/` - Pasta com todas as dependências
- Arquivo ZIP (opcional) - Para distribuição

### Linux
- `dist/wats/wats` - Executável principal
- `dist/wats/` - Pasta com todas as dependências
- `wats_1.0.0_amd64.deb` - Pacote Debian para instalação

## 🔧 Configuração Multiplataforma

### Dependências por Plataforma

**Windows** (`requirements.txt`):
- Inclui `pywin32` para APIs específicas do Windows
- Suporte completo a todas as funcionalidades

**Linux** (`requirements-linux.txt`):
- Remove `pywin32` (não compatível)
- Adiciona dependências específicas do Linux

### Código Multiplataforma

O arquivo `src/wats/utils/platform_utils.py` lida com:
- Detecção automática de plataforma
- Importações condicionais
- Mocks para funções não disponíveis
- Caminhos específicos por SO

### Exemplo de Uso no Código

```python
from src.wats.utils.platform_utils import (
    IS_WINDOWS, IS_LINUX, HAS_WIN32,
    get_platform_info, ensure_platform_dirs
)

# Verificar plataforma
if IS_WINDOWS and HAS_WIN32:
    # Código específico do Windows
    import win32gui
    windows = win32gui.EnumWindows(...)
elif IS_LINUX:
    # Código específico do Linux
    import subprocess
    windows = subprocess.run(['wmctrl', '-l'])

# Configurar diretórios
paths = ensure_platform_dirs()
```

## 🏗️ CI/CD Automático

O arquivo `.github/workflows/build.yml` configura builds automáticos:

- **Push para main/develop**: Build de teste
- **Tags (v*)**: Build de release com artifacts
- **Pull Requests**: Validação

### Artifacts Gerados
- `wats-windows.zip` - Executável Windows
- `wats_1.0.0_amd64.deb` - Pacote Linux

## 📋 Instalação

### Windows
1. Baixe `wats-windows.zip`
2. Extraia em uma pasta
3. Execute `WATS.exe`

### Linux (Ubuntu/Debian)
```bash
# Instalação via .deb
sudo dpkg -i wats_1.0.0_amd64.deb

# Resolver dependências se necessário
sudo apt-get install -f

# Executar
wats
```

### Linux (Outras Distribuições)
```bash
# Executável direto
chmod +x dist/wats/wats
./dist/wats/wats
```

## 🐳 Build com Docker

### Windows Container
```dockerfile
FROM python:3.11-windowsservercore
# ... (ver build.py para Dockerfile completo)
```

### Linux Container
```dockerfile
FROM python:3.11-slim
# ... (ver build.py para Dockerfile completo)
```

### Comandos Docker
```bash
# Build Windows
docker build -f Dockerfile.windows -t wats:windows .

# Build Linux  
docker build -f Dockerfile.linux -t wats:linux .

# Extrair executáveis
docker create --name temp wats:linux
docker cp temp:/app/dist ./dist-linux
docker rm temp
```

## 🔍 Troubleshooting

### Erro: "pywin32 não encontrado" no Linux
**Solução**: Use `requirements-linux.txt` em vez de `requirements.txt`

### Erro: "python3-tk não instalado" no Linux
```bash
sudo apt-get install python3-tk
```

### Erro: "dpkg-deb não encontrado"
```bash
sudo apt-get install dpkg-dev
```

### Executável não inicia no Linux
```bash
# Verificar dependências
ldd dist/wats/wats

# Instalar bibliotecas necessárias
sudo apt-get install libc6 libgcc1
```

### Tamanho grande do executável
- Use `--exclude-module` no PyInstaller
- Remova dependências desnecessárias
- Use UPX para compressão (já habilitado)

## 📊 Comparação de Funcionalidades

| Funcionalidade | Windows | Linux | Observações |
|---|---|---|---|
| Interface Gráfica | ✅ | ✅ | CustomTkinter multiplataforma |
| Gravação de Tela | ✅ | ✅ | MSS funciona em ambos |
| APIs do Windows | ✅ | ❌ | Funções mockadas no Linux |
| Banco de Dados | ✅ | ✅ | PostgreSQL e SQLite |
| Monitoramento | ✅ | ⚠️ | Limitado no Linux |
| Instalação | Manual | .deb | Pacote oficial para Linux |

## 🎯 Próximos Passos

1. **Testar em ambientes reais**
2. **Adicionar suporte ao macOS**
3. **Criar instalador MSI para Windows**
4. **Implementar auto-update**
5. **Otimizar tamanho dos executáveis**

---

Para mais informações, consulte a documentação específica de cada plataforma ou abra uma issue no repositório.