# test_convert_certificado.py
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from convert_certificado import converter_pfx_para_pem


def test_converter_pfx_para_pem_sucesso():
    """Testa conversão bem-sucedida do certificado."""
    with patch("subprocess.run") as mock_run, patch("builtins.open") as mock_open_file:

        # Mock do subprocess
        mock_run.return_value = MagicMock(returncode=0)

        # Mock do conteúdo do arquivo
        mock_file = MagicMock()
        mock_file.read.return_value = """-----BEGIN CERTIFICATE-----
        CERT1
        -----END CERTIFICATE-----
        -----BEGIN CERTIFICATE-----
        CERT2
        -----END CERTIFICATE-----
        """
        mock_open_file.return_value.__enter__.return_value = mock_file

        # Executa
        cert_pem, key_pem = converter_pfx_para_pem(Path("test.pfx"), "senha")

        # Verifica
        assert mock_run.call_count == 2
        assert cert_pem.name == "cert.pem"
        assert key_pem.name == "key.pem"


def test_converter_pfx_para_pem_erro_openssl():
    """Testa tratamento de erro do OpenSSL."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Erro OpenSSL")

        with pytest.raises(Exception):
            converter_pfx_para_pem(Path("test.pfx"), "senha")


def test_converter_pfx_para_pem_openssl_nao_encontrado():
    """Testa quando OpenSSL não está instalado."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("openssl não encontrado")

        with pytest.raises(SystemExit) as exc_info:
            converter_pfx_para_pem(Path("test.pfx"), "senha")

        assert exc_info.value.code == 1
