# test_config.py
import os
from unittest.mock import patch
from pathlib import Path
from config import ARQUIVO_CHAVES, PASTA_XMLS, CERT_PFX_PATH, CERT_PASSWORD, CNPJ


def test_config_paths_exist():
    """Testa se os caminhos de configuração são Path objects válidos."""
    assert isinstance(ARQUIVO_CHAVES, Path)
    assert isinstance(PASTA_XMLS, Path)
    assert isinstance(CERT_PFX_PATH, Path)
    
    # Verifica se os paths são absolutos (resolve() foi aplicado)
    assert ARQUIVO_CHAVES.is_absolute()
    assert PASTA_XMLS.is_absolute()
    assert CERT_PFX_PATH.is_absolute()


def test_config_from_env():
    """Testa se as variáveis de ambiente são carregadas."""
    # Testa com valores padrão quando variáveis não existem
    with patch.dict(os.environ, {}, clear=True):
        from importlib import reload
        import config
        reload(config)
        
        # Valores padrão devem ser usados
        assert config.CERT_PASSWORD is None
        assert config.CNPJ is None
        # O path do certificado deve ser o padrão
        assert "certificado.pfx" in str(config.CERT_PFX_PATH)


def test_config_with_env_vars():
    """Testa carregamento com variáveis de ambiente definidas."""
    with patch.dict(os.environ, {
        "CERT_PFX_PATH": "custom_cert.pfx",
        "CERT_PASSWORD": "test_password",
        "CNPJ": "12345678000199"
    }, clear=True):
        from importlib import reload
        import config
        reload(config)
        
        assert config.CERT_PASSWORD == "test_password"
        assert config.CNPJ == "12345678000199"
        assert "custom_cert.pfx" in str(config.CERT_PFX_PATH)