"""Testes para o módulo config.py"""

from pathlib import Path

from config import ARQUIVO_CHAVES, CERT_PASSWORD, CERT_PFX_PATH, CNPJ, PASTA_XMLS


def test_config_paths_exist():
    """Testa se os caminhos de configuração são Path objects válidos."""
    assert isinstance(ARQUIVO_CHAVES, Path)
    assert isinstance(PASTA_XMLS, Path)
    assert isinstance(CERT_PFX_PATH, Path)

    # Verifica se os paths são absolutos (resolve() foi aplicado)
    assert ARQUIVO_CHAVES.is_absolute()
    assert PASTA_XMLS.is_absolute()
    assert CERT_PFX_PATH.is_absolute()


def test_config_paths_correct():
    """Testa se os caminhos estão apontando para os locais corretos."""
    # ARQUIVO_CHAVES deve apontar para chaves.txt
    assert ARQUIVO_CHAVES.name == "chaves.txt"

    # PASTA_XMLS deve apontar para xmls_baixados
    assert PASTA_XMLS.name == "xmls_baixados"

    # CERT_PFX_PATH deve apontar para certificado.pfx
    assert CERT_PFX_PATH.name == "certificado.pfx"


def test_config_values_can_be_none():
    """Testa se CERT_PASSWORD e CNPJ podem ser None (dependem de .env)."""
    # Estes valores vêm de variáveis de ambiente, podem ser None
    assert CERT_PASSWORD is None or isinstance(CERT_PASSWORD, str)
    assert CNPJ is None or isinstance(CNPJ, str)


def test_config_paths_resolved():
    """Testa se os paths estão resolvidos corretamente."""
    # Importa para obter o project_root
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent

    # Verifica se os caminhos apontam para os arquivos na raiz
    assert ARQUIVO_CHAVES == (project_root / "chaves.txt").resolve()
    assert PASTA_XMLS == (project_root / "xmls_baixados").resolve()
    assert CERT_PFX_PATH == (project_root / "certificado.pfx").resolve()
