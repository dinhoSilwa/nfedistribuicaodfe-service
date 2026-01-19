"""Testes para o módulo main.py"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Importa o módulo main
import main


def test_main_sucesso_com_mock():
    """Testa execução principal bem-sucedida com mocks."""
    # Cria conteúdo de chaves válidas
    chaves_conteudo = """35241123456789012345678901234567890123456789
35241123456789012345678901234567890123456788
"""

    with patch("main.ARQUIVO_CHAVES") as mock_arquivo_chaves:
        # Mock do arquivo de chaves
        mock_arquivo_chaves.exists.return_value = True

        with patch("builtins.open", mock_open(read_data=chaves_conteudo)):
            with patch("main.baixar_em_massa") as mock_baixar:
                # Mock da função baixar_em_massa
                mock_baixar.return_value = None

                with patch("main.PASTA_XMLS", Path("xmls_test")):
                    # Executa main
                    main.main()

                    # Verifica se baixar_em_massa foi chamado
                    mock_baixar.assert_called_once()

                    # Verifica que recebeu 2 chaves
                    args, _ = mock_baixar.call_args
                    chaves = args[0]
                    assert len(chaves) == 2
                    assert all(len(chave) == 44 for chave in chaves)


def test_main_arquivo_nao_encontrado():
    """Testa quando o arquivo de chaves não existe."""
    with patch("main.ARQUIVO_CHAVES") as mock_arquivo_chaves:
        mock_arquivo_chaves.exists.return_value = False

        # Deve lançar FileNotFoundError
        try:
            main.main()
            assert False, "Deveria ter lançado FileNotFoundError"
        except FileNotFoundError as e:
            assert "Arquivo de chaves não encontrado" in str(e)
