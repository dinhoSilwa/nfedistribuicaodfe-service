# test_download_integracao.py
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from download import baixar_xml_por_chave, baixar_em_massa


@pytest.fixture
def mock_environment():
    """Configura ambiente mock para testes."""
    with patch("download.CERT_PFX_PATH", Path("certificado.pfx")), \
         patch("download.CERT_PASSWORD", "senha123"), \
         patch("download.CNPJ", "12345678000199"):
        yield


def test_baixar_xml_por_chave_sucesso(mock_environment, tmp_path):
    """Testa download bem-sucedido de um XML por chave."""
    chave = "35241123456789012345678901234567890123456789"
    pasta_saida = tmp_path / "xmls"
    pasta_saida.mkdir()
    
    with patch("download.detectar_uf_da_chave") as mock_detectar, \
         patch("download.distribuicao_dfe") as mock_distribuicao, \
         patch("download.converter_pfx_para_pem") as mock_converter, \
         patch("download.criar_sessao_sefaz") as mock_sessao:
        
        # Configura mocks
        mock_detectar.return_value = "SP"
        mock_distribuicao.return_value = "<?xml><nfeProc>conteudo</nfeProc>"
        mock_converter.return_value = (Path("cert.pem"), Path("key.pem"))
        mock_sessao.return_value = MagicMock()
        
        # Executa
        resultado = baixar_xml_por_chave(
            chave, 
            pasta_saida,
            Path("cert.pem"),
            Path("key.pem"),
            mock_sessao.return_value
        )
        
        # Verifica
        assert resultado is True
        arquivo_esperado = pasta_saida / f"{chave}.xml"
        assert arquivo_esperado.exists()
        assert arquivo_esperado.read_text() == "<?xml><nfeProc>conteudo</nfeProc>"


def test_baixar_xml_por_chave_nao_encontrado(mock_environment, tmp_path):
    """Testa quando o XML não é encontrado."""
    chave = "35241123456789012345678901234567890123456789"
    pasta_saida = tmp_path / "xmls"
    
    with patch("download.detectar_uf_da_chave") as mock_detectar, \
         patch("download.distribuicao_dfe") as mock_distribuicao, \
         patch("download.converter_pfx_para_pem"), \
         patch("download.criar_sessao_sefaz"):
        
        mock_detectar.return_value = "SP"
        mock_distribuicao.return_value = None  # Nenhum XML retornado
        
        resultado = baixar_xml_por_chave(
            chave,
            pasta_saida,
            Path("cert.pem"),
            Path("key.pem"),
            MagicMock()
        )
        
        assert resultado is False
        assert not list(pasta_saida.glob("*.xml"))  # Nenhum arquivo criado


def test_baixar_xml_por_chave_erro(mock_environment, tmp_path):
    """Testa tratamento de erro durante download."""
    chave = "35241123456789012345678901234567890123456789"
    pasta_saida = tmp_path / "xmls"
    
    with patch("download.detectar_uf_da_chave") as mock_detectar, \
         patch("download.distribuicao_dfe") as mock_distribuicao, \
         patch("download.converter_pfx_para_pem"), \
         patch("download.criar_sessao_sefaz"):
        
        mock_detectar.return_value = "SP"
        mock_distribuicao.side_effect = Exception("Erro de conexão")
        
        resultado = baixar_xml_por_chave(
            chave,
            pasta_saida,
            Path("cert.pem"),
            Path("key.pem"),
            MagicMock()
        )
        
        assert resultado is False


def test_baixar_em_massa(mock_environment, tmp_path):
    """Testa download em massa de múltiplas chaves."""
    chaves = [
        "35241123456789012345678901234567890123456789",
        "35241123456789012345678901234567890123456788",
        "inválida123",  # Chave inválida
    ]
    pasta_saida = tmp_path / "xmls"
    
    with patch("download.converter_pfx_para_pem") as mock_converter, \
         patch("download.criar_sessao_sefaz") as mock_sessao, \
         patch("download.baixar_xml_por_chave") as mock_baixar:
        
        mock_converter.return_value = (Path("cert.pem"), Path("key.pem"))
        mock_sessao.return_value = MagicMock()
        
        # Primeira chave: sucesso, segunda: não encontrada
        mock_baixar.side_effect = [True, False, False]
        
        # Executa
        baixar_em_massa(chaves, pasta_saida)
        
        # Verifica se os arquivos temporários seriam removidos
        assert mock_converter.called
        # A função baixar_xml_por_chave deve ser chamada 3 vezes
        assert mock_baixar.call_count == 3


def test_baixar_em_massa_chaves_invalidas(mock_environment, tmp_path):
    """Testa download em massa com chaves inválidas."""
    chaves = [
        "123",  # Muito curta
        "abcdefghijklmnopqrstuvwxyzabcdefghijklmnop",  # Não numérica
        "35241123456789012345678901234567890123456789",  # Válida
    ]
    pasta_saida = tmp_path / "xmls"
    
    with patch("download.converter_pfx_para_pem") as mock_converter, \
         patch("download.criar_sessao_sefaz") as mock_sessao, \
         patch("download.baixar_xml_por_chave") as mock_baixar:
        
        mock_converter.return_value = (Path("cert.pem"), Path("key.pem"))
        mock_sessao.return_value = MagicMock()
        mock_baixar.return_value = True  # A válida terá sucesso
        
        baixar_em_massa(chaves, pasta_saida)
        
        # Apenas a chave válida deve ser processada
        assert mock_baixar.call_count == 1