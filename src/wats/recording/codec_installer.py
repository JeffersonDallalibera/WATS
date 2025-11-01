# WATS_Project/wats_app/recording/codec_installer.py

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import requests


class CodecInstaller:
    """
    Instala automaticamente codecs necessários para gravação de vídeo.
    """

    # URLs dos codecs
    OPENH264_RELEASES = {
        "2.3.1": {
            "win64": "https://github.com/cisco/openh264/releases/download/v2.3.1/openh264-2.3.1-win64.dll.bz2",
            "win32": "https://github.com/cisco/openh264/releases/download/v2.3.1/openh264-2.3.1-win32.dll.bz2",
        },
        "2.4.1": {
            "win64": "https://github.com/cisco/openh264/releases/download/v2.4.1/openh264-2.4.1-win64.dll.bz2",
            "win32": "https://github.com/cisco/openh264/releases/download/v2.4.1/openh264-2.4.1-win32.dll.bz2",
        },
    }

    def __init__(self, install_dir: Optional[str] = None):
        """
        Initialize codec installer.

        Args:
            install_dir: Diretório para instalar os codecs. Se None, usa o diretório do script.
        """
        if install_dir:
            self.install_dir = Path(install_dir)
        else:
            # Usa o diretório onde o Python está executando
            self.install_dir = Path.cwd()

        self.install_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"CodecInstaller: Diretório de instalação: {self.install_dir}")

    def check_openh264_installed(self) -> bool:
        """
        Verifica se o OpenH264 está instalado e funcionando.

        Returns:
            True se estiver instalado corretamente
        """
        try:
            import cv2

            # Tenta criar um VideoWriter com H264
            test_path = self.install_dir / "test_h264.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"H264")
            writer = cv2.VideoWriter(str(test_path), fourcc, 10.0, (640, 480))

            if writer.isOpened():
                writer.release()
                # Remove arquivo de teste
                if test_path.exists():
                    test_path.unlink()
                logging.info("✅ OpenH264 está funcionando corretamente")
                return True
            else:
                logging.warning("⚠️ OpenH264 não está funcionando")
                return False

        except Exception as e:
            logging.warning(f"⚠️ Erro testando OpenH264: {e}")
            return False

    def install_openh264(self, version: str = "2.4.1", force: bool = False) -> bool:
        """
        Instala o codec OpenH264.

        Args:
            version: Versão do OpenH264 para instalar
            force: Se True, reinstala mesmo se já estiver instalado

        Returns:
            True se instalação foi bem-sucedida
        """
        if not force and self.check_openh264_installed():
            logging.info("OpenH264 já está instalado e funcionando")
            return True

        try:
            # Determina arquitetura
            import platform

            arch = "win64" if platform.machine().endswith("64") else "win32"

            if version not in self.OPENH264_RELEASES:
                logging.error(f"Versão {version} não suportada")
                return False

            if arch not in self.OPENH264_RELEASES[version]:
                logging.error(f"Arquitetura {arch} não suportada para versão {version}")
                return False

            url = self.OPENH264_RELEASES[version][arch]
            logging.info(f"📥 Baixando OpenH264 {version} ({arch}) de: {url}")

            # Baixa o arquivo
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Salva em arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=".bz2") as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_path = temp_file.name

            # Descompacta o arquivo .bz2
            import bz2

            with bz2.open(temp_path, "rb") as compressed_file:
                dll_content = compressed_file.read()

            # Salva a DLL no diretório de instalação
            dll_name = f"openh264-{version}-{arch}.dll"
            dll_path = self.install_dir / dll_name

            with open(dll_path, "wb") as dll_file:
                dll_file.write(dll_content)

            # Remove arquivo temporário
            os.unlink(temp_path)

            # Cria link simbólico ou cópia para nome padrão
            standard_name = "openh264-1.8.0-win64.dll"  # Nome que o OpenCV procura
            standard_path = self.install_dir / standard_name

            if standard_path.exists():
                standard_path.unlink()

            # Copia para o nome padrão
            import shutil

            shutil.copy2(dll_path, standard_path)

            logging.info(f"✅ OpenH264 instalado com sucesso: {dll_path}")
            logging.info(f"✅ Link criado: {standard_path}")

            # Testa a instalação
            if self.check_openh264_installed():
                logging.info("✅ OpenH264 instalado e testado com sucesso!")
                return True
            else:
                logging.warning("⚠️ OpenH264 instalado mas não está funcionando corretamente")
                return False

        except Exception as e:
            logging.error(f"❌ Erro instalando OpenH264: {e}")
            return False

    def install_all_codecs(self) -> bool:
        """
        Instala todos os codecs necessários.

        Returns:
            True se todos os codecs foram instalados com sucesso
        """
        success = True

        logging.info("🔧 Instalando codecs necessários...")

        # Instala OpenH264
        if not self.install_openh264():
            success = False

        if success:
            logging.info("✅ Todos os codecs instalados com sucesso!")
        else:
            logging.error("❌ Falha na instalação de alguns codecs")

        return success

    def get_recommended_codec_fallback(self) -> list:
        """
        Retorna lista de codecs em ordem de preferência para fallback.

        Returns:
            Lista de fourcc codes para tentar
        """
        import cv2

        codecs = []

        # Se OpenH264 está funcionando, usa primeiro
        if self.check_openh264_installed():
            codecs.append(cv2.VideoWriter_fourcc(*"H264"))

        # Fallbacks
        codecs.extend(
            [
                cv2.VideoWriter_fourcc(*"XVID"),  # Xvid
                cv2.VideoWriter_fourcc(*"MP4V"),  # MPEG-4
                cv2.VideoWriter_fourcc(*"MJPG"),  # Motion JPEG
                cv2.VideoWriter_fourcc(*"X264"),  # x264
            ]
        )

        return codecs


def ensure_codecs_installed(install_dir: Optional[str] = None) -> CodecInstaller:
    """
    Função utilitária para garantir que os codecs estejam instalados.

    Args:
        install_dir: Diretório para instalar codecs

    Returns:
        Instância do CodecInstaller
    """
    installer = CodecInstaller(install_dir)

    if not installer.check_openh264_installed():
        logging.info("🔧 OpenH264 não encontrado, instalando automaticamente...")
        installer.install_openh264()

    return installer


if __name__ == "__main__":
    # Teste do instalador
    logging.basicConfig(level=logging.INFO)

    installer = CodecInstaller()
    installer.install_all_codecs()
