# test_main.py
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
from main import main


def test_main_sucesso(tmp_path):
    """Testa execução principal bem-sucedida."""
    # Cria arquivo de chaves temporário
    arquivo_chaves = tmp_path / "chaves.txt"
    arquivo_chaves.write_text("""35241123456789012345678901234567890123456789
35241123456789012345678901234567890123456788
""")
    
    with patch("main.ARQUIVO_CHAVES", arquivo_chaves), \
         patch("main.PASTA_XMLS", tmp_path / "xmls"), \
         patch("main.baixar_em_massa") as mock_baixar:
        
        # Executa
        main()
        
        # Verifica
        mock_baixar.assert_called_once()
        assert len(mock_baixar.call_args[0][0]) == 2  # 2 chaves válidas


def test_main_arquivo_nao_encontrado():
    """Testa quando o arquivo de chaves não existe."""
    with patch("main.ARQUIVO_CHAVES", Path("/caminho/inexistente/chaves.txt")):
        with pytest.raises(FileNotFoundError, match="Arquivo de chaves não encontrado"):
            main()


def test_main_chaves_invalidas(tmp_path):
    """Testa quando o arquivo de chaves contém apenas chaves inválidas."""
    arquivo_chaves = tmp_path / "chaves.txt"
    arquivo_chaves.write_text("""chave inválida
123
outra chave inválida
""")
    
    with patch("main.ARQUIVO_CHAVES", arquivo_chaves), \
         patch("main.PASTA_XMLS", tmp_path / "xmls"), \
         patch("main.baixar_em_massa") as mock_baixar:
        
        # Capture a saída
        with patch("builtins.print") as mock_print:
            main()
            
            # Verifica mensagem de aviso
            mock_print.assert_any_call("⚠️  Nenhuma chave válida encontrada.")
        
        # baixar_em_massa não deve ser chamado
        mock_baixar.assert_not_called()


def test_main_arquivo_vazio(tmp_path):
    """Testa quando o arquivo de chaves está vazio."""
    arquivo_chaves = tmp_path / "chaves.txt"
    arquivo_chaves.write_text("")
    
    with patch("main.ARQUIVO_CHAVES", arquivo_chaves), \
         patch("main.PASTA_XMLS", tmp_path / "xmls"), \
         patch("main.baixar_em_massa") as mock_baixar:
        
        with patch("builtins.print") as mock_print:
            main()
            mock_print.assert_any_call("⚠️  Nenhuma chave válida encontrada.")
        
        mock_baixar.assert_not_called()