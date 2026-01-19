"""Testes para o módulo download.py"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Importa o módulo download
import download


# Testes básicos para começar
def test_detectar_uf_da_chave_valida():
    """Testa detecção de UF para chaves válidas."""
    test_cases = [
        ("35241123456789012345678901234567890123456789", "SP"),  # SP código 35
        ("43123456789012345678901234567890123456789012", "RS"),  # RS código 43
        ("33123456789012345678901234567890123456789012", "RJ"),  # RJ código 33
        ("41123456789012345678901234567890123456789012", "PR"),  # PR código 41
    ]

    for chave, uf_esperada in test_cases:
        assert download.detectar_uf_da_chave(chave) == uf_esperada


def test_detectar_uf_da_chave_codigo_invalido():
    """Testa comportamento com códigos de UF inválidos."""
    chave_invalida = "99123456789012345678901234567890123456789012"

    with pytest.raises(ValueError, match="Código de UF inválido na chave"):
        download.detectar_uf_da_chave(chave_invalida)


def test_uf_para_codigo_completo():
    """Testa se o mapa UF está completo."""
    assert len(download.UF_PARA_CODIGO) == 27  # 26 estados + DF
    assert download.UF_PARA_CODIGO["35"] == "SP"
    assert download.UF_PARA_CODIGO["33"] == "RJ"
    assert download.UF_PARA_CODIGO["53"] == "DF"


def test_urls_dfe_configuradas():
    """Testa se URLs estão configuradas para todas as UFs."""
    ufs_testadas = ["SP", "RJ", "MG", "RS", "PR"]
    for uf in ufs_testadas:
        assert uf in download.URLS_DFE
        assert download.URLS_DFE[uf]  # URL não vazia


def test_converter_pfx_para_pem_mock():
    """Testa conversão de certificado com mock."""
    with patch("download.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        cert_pem, key_pem = download.converter_pfx_para_pem(Path("teste.pfx"), "senha123")

        assert mock_run.call_count == 2
        assert cert_pem.suffix == ".cert.pem"
        assert key_pem.suffix == ".key.pem"
