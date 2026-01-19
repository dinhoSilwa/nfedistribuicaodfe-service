# test_download_conversao_certificado.py
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import subprocess
from download import converter_pfx_para_pem


@pytest.fixture
def mock_pfx_path(tmp_path):
    """Cria um caminho fictício para certificado PFX."""
    return tmp_path / "certificado.pfx"


def test_converter_pfx_para_pem_sucesso(mock_pfx_path):
    """Testa conversão bem-sucedida de PFX para PEM."""
    with patch("subprocess.run") as mock_run:
        # Configura o mock para simular sucesso
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock do conteúdo do certificado com múltiplos certificados
        cert_content = """-----BEGIN CERTIFICATE-----
        CERT1
        -----END CERTIFICATE-----
        -----BEGIN CERTIFICATE-----
        CERT2
        -----END CERTIFICATE-----
        """
        
        with patch("builtins.open", mock_open(read_data=cert_content)) as mock_file:
            cert_pem, key_pem = converter_pfx_para_pem(mock_pfx_path, "senha123")
            
            # Verifica se os comandos openssl foram chamados
            assert mock_run.call_count == 2
            
            # Verifica se os paths retornados são corretos
            assert cert_pem == mock_pfx_path.with_suffix(".cert.pem")
            assert key_pem == mock_pfx_path.with_suffix(".key.pem")


def test_converter_pfx_para_pem_erro_openssl(mock_pfx_path):
    """Testa tratamento de erro do OpenSSL."""
    with patch("subprocess.run") as mock_run:
        # Simula erro no subprocess
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["openssl", "..."],
            stderr=b"Erro no certificado"
        )
        
        with pytest.raises(subprocess.CalledProcessError):
            converter_pfx_para_pem(mock_pfx_path, "senha123")


def test_converter_pfx_para_pem_certificado_unico(mock_pfx_path):
    """Testa quando o certificado já tem apenas um certificado."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        
        # Conteúdo com apenas um certificado
        cert_content = """-----BEGIN CERTIFICATE-----
        APENAS UM CERT
        -----END CERTIFICATE-----
        """
        
        with patch("builtins.open", mock_open(read_data=cert_content)) as mock_file:
            cert_pem, key_pem = converter_pfx_para_pem(mock_pfx_path, "senha123")
            
            # O arquivo deve ser aberto para leitura e escrita
            assert mock_file.call_count >= 2