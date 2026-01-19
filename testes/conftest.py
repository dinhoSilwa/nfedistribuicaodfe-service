# conftest.py
"""
Configurações globais do pytest.
"""
import pytest
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture
def sample_chave_nfe():
    """Fornece uma chave de NFe de exemplo válida."""
    return "35241123456789012345678901234567890123456789"


@pytest.fixture
def temp_dir_structure(tmp_path):
    """Cria estrutura de diretórios temporária para testes."""
    # Cria arquivos de exemplo
    chaves_file = tmp_path / "chaves.txt"
    chaves_file.write_text("35241123456789012345678901234567890123456789\n")
    
    cert_file = tmp_path / "certificado.pfx"
    cert_file.write_bytes(b"fake pfx content")
    
    return {
        "root": tmp_path,
        "chaves": chaves_file,
        "certificado": cert_file
    }