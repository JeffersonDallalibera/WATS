#!/usr/bin/env python3
"""
Script universal de build para WATS
Detecta a plataforma e executa o build apropriado
"""

import os
import sys
import platform
import subprocess
import argparse


def run_command(command, shell=True):
    """Executa comando e retorna resultado"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Erro ao executar: {command}")
            print(f"Stderr: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Erro ao executar comando: {e}")
        return False


def build_windows():
    """Build para Windows"""
    print("🪟 Building para Windows...")

    script_path = os.path.join("scripts", "build_windows.bat")
    if os.path.exists(script_path):
        return run_command(script_path)
    else:
        print("❌ Script build_windows.bat não encontrado!")
        return False


def build_linux():
    """Build para Linux"""
    print("🐧 Building para Linux...")

    script_path = os.path.join("scripts", "build_linux.sh")
    if os.path.exists(script_path):
        # Torna o script executável
        run_command(f"chmod +x {script_path}")
        return run_command(f"bash {script_path}")
    else:
        print("❌ Script build_linux.sh não encontrado!")
        return False


def build_docker():
    """Build usando Docker (multiplataforma)"""
    print("🐳 Building com Docker...")

    # Dockerfile para Windows
    dockerfile_windows = """
FROM python:3.11-windowsservercore

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pyinstaller --clean --noconfirm WATS-multiplatform.spec
"""

    # Dockerfile para Linux
    dockerfile_linux = """
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \\
    python3-tk \\
    dpkg-dev \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-linux.txt .
RUN pip install -r requirements-linux.txt

COPY . .
RUN pyinstaller --clean --noconfirm WATS-multiplatform.spec

# Criar pacote .deb
RUN bash scripts/build_linux.sh
"""

    current_platform = platform.system().lower()

    if current_platform == "windows":
        with open("Dockerfile.windows", "w") as f:
            f.write(dockerfile_windows)

        return run_command("docker build -f Dockerfile.windows -t wats:windows .")

    else:  # Linux
        with open("Dockerfile.linux", "w") as f:
            f.write(dockerfile_linux)

        return run_command("docker build -f Dockerfile.linux -t wats:linux .")


def main():
    parser = argparse.ArgumentParser(description="Build WATS para múltiplas plataformas")
    parser.add_argument("--platform", choices=["auto", "windows", "linux", "docker"],
                        default="auto", help="Plataforma alvo")
    parser.add_argument("--clean", action="store_true", help="Limpa builds anteriores")

    args = parser.parse_args()

    print("🚀 WATS Universal Build Script")
    print("=" * 40)

    current_platform = platform.system().lower()
    print(f"Plataforma atual: {current_platform}")

    if args.clean:
        print("🧹 Limpando builds anteriores...")
        if current_platform == "windows":
            run_command("if exist dist rd /s /q dist")
            run_command("if exist build rd /s /q build")
        else:
            run_command("rm -rf dist/ build/")

    success = False

    if args.platform == "auto":
        # Detecta automaticamente
        if current_platform == "windows":
            success = build_windows()
        elif current_platform == "linux":
            success = build_linux()
        else:
            print(f"❌ Plataforma {current_platform} não suportada diretamente")
            print("💡 Tente usar --platform docker")

    elif args.platform == "windows":
        if current_platform == "windows":
            success = build_windows()
        else:
            print("❌ Build Windows só pode ser executado no Windows")
            print("💡 Use Docker para cross-compilation")

    elif args.platform == "linux":
        if current_platform == "linux":
            success = build_linux()
        else:
            print("❌ Build Linux só pode ser executado no Linux")
            print("💡 Use Docker para cross-compilation")

    elif args.platform == "docker":
        success = build_docker()

    if success:
        print("✅ Build concluído com sucesso!")

        # Lista arquivos gerados
        print("\n📦 Arquivos gerados:")
        if os.path.exists("dist"):
            for root, dirs, files in os.walk("dist"):
                for file in files:
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)
                    print(f"  - {file_path} ({size:,} bytes)")

        # Lista pacotes .deb se existirem
        for file in os.listdir("."):
            if file.endswith(".deb"):
                size = os.path.getsize(file)
                print(f"  - {file} ({size:,} bytes)")

    else:
        print("❌ Build falhou!")
        sys.exit(1)


if __name__ == "__main__":
    main()
