# test_download_requisicoes.py
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import requests
from lxml import etree
from download import criar_sessao_sefaz, distribuicao_dfe


@pytest.fixture
def mock_cert_files(tmp_path):
    """Cria arquivos de certificado mock."""
    cert_pem = tmp_path / "cert.pem"
    key_pem = tmp_path / "key.pem"
    
    cert_pem.write_text("-----BEGIN CERTIFICATE-----\nCERT\n-----END CERTIFICATE-----")
    key_pem.write_text("-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----")
    
    return cert_pem, key_pem


@pytest.fixture
def mock_session():
    """Cria uma sessão mock."""
    return MagicMock(spec=requests.Session)


def test_criar_sessao_sefaz(mock_cert_files):
    """Testa criação de sessão com autenticação mTLS."""
    cert_pem, key_pem = mock_cert_files
    
    with patch("requests.Session") as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        session = criar_sessao_sefaz(cert_pem, key_pem)
        
        # Verifica configurações da sessão
        assert session.cert == (str(cert_pem), str(key_pem))
        assert session.verify is False
        mock_session_class.assert_called_once()


def test_distribuicao_dfe_sucesso(mock_cert_files, mock_session):
    """Testa chamada ao serviço de distribuição DFe."""
    cert_pem, key_pem = mock_cert_files
    
    with patch("download.URLS_DFE", {"SP": "https://teste.sefaz.sp.gov.br/ws"}), \
         patch("signxml.XMLSigner") as mock_signer, \
         patch("builtins.open", mock_open(read_data="cert content")), \
         patch("etree.fromstring") as mock_fromstring, \
         patch("etree.tostring") as mock_tostring:
        
        # Mock da resposta assinada
        mock_signed_root = MagicMock()
        mock_signer_instance = MagicMock()
        mock_signer_instance.sign.return_value = mock_signed_root
        mock_signer.return_value = mock_signer_instance
        
        # Mock do XML
        mock_root = MagicMock()
        mock_fromstring.return_value = mock_root
        mock_tostring.return_value = "<signed>XML</signed>"
        
        # Mock da resposta HTTP
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <soap:Envelope>
            <soap:Body>
                <loteDistDFeZip>ZmFrZV9iYXNlNjRfZGF0YQ==</loteDistDFeZip>
            </soap:Body>
        </soap:Envelope>
        """
        mock_session.post.return_value = mock_response
        
        # Mock para base64 e gzip
        with patch("base64.b64decode") as mock_b64decode, \
             patch("gzip.decompress") as mock_gzip:
            
            mock_b64decode.return_value = b"compressed"
            mock_gzip.return_value = b"<?xml><nfeProc>conteudo</nfeProc>"
            
            # Chama a função
            result = distribuicao_dfe(
                "35241123456789012345678901234567890123456789",
                "SP",
                cert_pem,
                key_pem,
                mock_session
            )
            
            # Verificações
            assert result == "<?xml><nfeProc>conteudo</nfeProc>"
            mock_session.post.assert_called_once()
            
            # Verifica se o arquivo de debug foi "salvo"
            # (na realidade, mock_open captura a chamada)


def test_distribuicao_dfe_uf_nao_configurada(mock_cert_files, mock_session):
    """Testa comportamento quando UF não está configurada."""
    cert_pem, key_pem = mock_cert_files
    
    with pytest.raises(ValueError, match="URL não configurada para UF"):
        distribuicao_dfe(
            "99999999999999999999999999999999999999999999",
            "XX",  # UF não existente
            cert_pem,
            key_pem,
            mock_session
        )


def test_distribuicao_dfe_resposta_vazia(mock_cert_files, mock_session):
    """Testa quando a resposta não contém loteDistDFeZip."""
    cert_pem, key_pem = mock_cert_files
    
    with patch("download.URLS_DFE", {"SP": "https://teste.sefaz.sp.gov.br/ws"}), \
         patch("signxml.XMLSigner") as mock_signer, \
         patch("builtins.open", mock_open()), \
         patch("etree.fromstring") as mock_fromstring, \
         patch("etree.tostring") as mock_tostring:
        
        mock_signer_instance = MagicMock()
        mock_signer.return_value = mock_signer_instance
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <soap:Envelope>
            <soap:Body>
                <cStat>138</cStat>
                <xMotivo>Documento localizado</xMotivo>
            </soap:Body>
        </soap:Envelope>
        """
        mock_session.post.return_value = mock_response
        
        result = distribuicao_dfe(
            "35241123456789012345678901234567890123456789",
            "SP",
            cert_pem,
            key_pem,
            mock_session
        )
        
        assert result is None