#!/bin/bash
# Build script para Linux - WATS
# Cria executável Linux e pacote .deb

set -e  # Para na primeira falha

echo "========================================"
echo "   WATS BUILD SCRIPT - LINUX V1.0"
echo "========================================"
echo

# Verifica se está no diretório correto
if [ ! -d "src/wats" ]; then
    echo "ERRO: Execute este script na pasta raiz do projeto WATS"
    echo "Pasta atual: $(pwd)"
    exit 1
fi

# Verifica se Python está disponível
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 não encontrado!"
    exit 1
fi

echo "🔧 Configurando ambiente virtual..."
# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
source venv/bin/activate
echo "✅ Ambiente virtual ativado"

echo
echo "🧹 LIMPANDO CACHE E ARQUIVOS TEMPORÁRIOS..."
echo "=========================================="

# Remove cache Python
echo "Removendo cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove builds anteriores
echo "Removendo builds anteriores..."
rm -rf dist/ build/ *.spec

# Remove logs antigos
echo "Removendo logs antigos..."
rm -f wats_app.log *.log

echo
echo "📦 INSTALANDO DEPENDÊNCIAS..."
echo "=============================="

# Verifica se FreeRDP está instalado (recomendado)
if ! command -v xfreerdp &> /dev/null; then
    echo "⚠️  FreeRDP não encontrado. Recomendamos instalar para melhor funcionalidade RDP:"
    echo "   Ubuntu/Debian: sudo apt-get install freerdp2-x11"
    echo "   CentOS/RHEL:   sudo yum install freerdp"
    echo "   Arch Linux:    sudo pacman -S freerdp"
    echo
    echo "O sistema funcionará com clientes RDP alternativos se disponíveis."
    echo
fi

# Instala dependências do Linux
pip install --upgrade pip
pip install -r requirements-linux.txt

echo
echo "🏗️  CONSTRUINDO EXECUTÁVEL..."
echo "============================="

# Usa o spec file multiplataforma
pyinstaller --clean --noconfirm WATS-multiplatform.spec

if [ $? -eq 0 ]; then
    echo "✅ Executável criado com sucesso!"
    echo "Localização: dist/wats/"
else
    echo "❌ Erro ao criar executável!"
    exit 1
fi

echo
echo "📦 CRIANDO PACOTE .DEB..."
echo "========================"

# Cria estrutura do pacote .deb
PACKAGE_DIR="wats-package"
rm -rf $PACKAGE_DIR

mkdir -p $PACKAGE_DIR/DEBIAN
mkdir -p $PACKAGE_DIR/opt/wats
mkdir -p $PACKAGE_DIR/usr/share/applications
mkdir -p $PACKAGE_DIR/usr/share/pixmaps

# Copia executável e arquivos
cp -r dist/wats/* $PACKAGE_DIR/opt/wats/
cp assets/ats.ico $PACKAGE_DIR/usr/share/pixmaps/wats.ico 2>/dev/null || echo "Ícone não encontrado, continuando..."

# Cria arquivo de controle do .deb
cat > $PACKAGE_DIR/DEBIAN/control << EOF
Package: wats
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Depends: python3, python3-tk
Maintainer: ATS Team <contato@ats.com>
Description: WATS - Sistema de Monitoramento e Auditoria
 Sistema completo de monitoramento, gravação e auditoria
 de sessões para segurança corporativa.
EOF

# Cria script pós-instalação
cat > $PACKAGE_DIR/DEBIAN/postinst << 'EOF'
#!/bin/bash
set -e

# Torna o executável executável
chmod +x /opt/wats/wats

# Cria link simbólico
ln -sf /opt/wats/wats /usr/local/bin/wats

echo "WATS instalado com sucesso!"
echo "Execute 'wats' no terminal ou procure por 'WATS' no menu de aplicações."
EOF

chmod 755 $PACKAGE_DIR/DEBIAN/postinst

# Cria script de remoção
cat > $PACKAGE_DIR/DEBIAN/prerm << 'EOF'
#!/bin/bash
set -e

# Remove link simbólico
rm -f /usr/local/bin/wats
EOF

chmod 755 $PACKAGE_DIR/DEBIAN/prerm

# Cria arquivo .desktop para o menu
cat > $PACKAGE_DIR/usr/share/applications/wats.desktop << EOF
[Desktop Entry]
Name=WATS
Comment=Sistema de Monitoramento e Auditoria
Exec=/opt/wats/wats
Icon=/usr/share/pixmaps/wats.ico
Terminal=false
Type=Application
Categories=Utility;Security;
EOF

# Constrói o pacote .deb
echo "Construindo pacote .deb..."
dpkg-deb --build $PACKAGE_DIR wats_1.0.0_amd64.deb

if [ $? -eq 0 ]; then
    echo "✅ Pacote .deb criado com sucesso: wats_1.0.0_amd64.deb"
else
    echo "❌ Erro ao criar pacote .deb!"
    exit 1
fi

# Limpa arquivos temporários
rm -rf $PACKAGE_DIR

echo
echo "🎉 BUILD COMPLETO!"
echo "=================="
echo "Executável: dist/wats/wats"
echo "Pacote .deb: wats_1.0.0_amd64.deb"
echo
echo "Para instalar o .deb:"
echo "sudo dpkg -i wats_1.0.0_amd64.deb"
echo
echo "Para executar diretamente:"
echo "./dist/wats/wats"