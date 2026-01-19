"""Testes para o módulo convert_certificado.py"""

from pathlib import Path
from unittest.mock import MagicMock, patch

# Importa o módulo convert_certificado
import convert_certificado


def test_converter_pfx_para_pem_sucesso():
    """Testa conversão bem-sucedida do certificado."""
    with patch("convert_certificado.subprocess.run") as mock_run:
        # Configura mocks
        mock_run.return_value = MagicMock(returncode=0)

        # Mock do conteúdo do arquivo com múltiplos certificados
        mock_file_content = """-----BEGIN CERTIFICATE-----
CERTIFICADO1
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
CERTIFICADO2
-----END CERTIFICATE-----
"""

        with patch("builtins.open", MagicMock()) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = mock_file_content

            # Executa função
            cert_pem, key_pem = convert_certificado.converter_pfx_para_pem(Path("teste.pfx"), "senha123")

            # Verifica
            assert mock_run.call_count == 2
            assert cert_pem.name == "cert.pem"
            assert key_pem.name == "key.pem"


def test_converter_pfx_para_pem_erro_openssl():
    """Testa tratamento de erro do OpenSSL."""
    with patch("convert_certificado.subprocess.run") as mock_run:
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["openssl", "..."], stderr=b"Erro no certificado"
        )

        try:
            convert_certificado.converter_pfx_para_pem(Path("teste.pfx"), "senha123")
            assert False, "Deveria ter lançado exceção"
        except subprocess.CalledProcessError:
            pass  # Esperado
