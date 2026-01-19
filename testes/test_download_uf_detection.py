# test_download_uf_detection.py
import pytest
from download import detectar_uf_da_chave, UF_PARA_CODIGO


def test_detectar_uf_da_chave_valida():
    """Testa detecção de UF para chaves válidas."""
    # Testa algumas UFs conhecidas
    test_cases = [
        ("35241123456789012345678901234567890123456789", "SP"),  # SP código 35
        ("43123456789012345678901234567890123456789012", "RS"),  # RS código 43
        ("33123456789012345678901234567890123456789012", "RJ"),  # RJ código 33
        ("41123456789012345678901234567890123456789012", "PR"),  # PR código 41
    ]
    
    for chave, uf_esperada in test_cases:
        assert detectar_uf_da_chave(chave) == uf_esperada


def test_detectar_uf_da_chave_codigo_invalido():
    """Testa comportamento com códigos de UF inválidos."""
    chave_invalida = "99123456789012345678901234567890123456789012"
    
    with pytest.raises(ValueError, match="Código de UF inválido na chave"):
        detectar_uf_da_chave(chave_invalida)


def test_detectar_uf_da_chave_comprimento_curto():
    """Testa comportamento com chave muito curta."""
    chave_curta = "35"
    
    with pytest.raises(KeyError):
        detectar_uf_da_chave(chave_curta)


def test_mapa_uf_completo():
    """Testa se o mapa UF está completo para todos os códigos."""
    assert len(UF_PARA_CODIGO) == 27  # 26 estados + DF
    # Verifica alguns códigos específicos
    assert UF_PARA_CODIGO["35"] == "SP"
    assert UF_PARA_CODIGO["33"] == "RJ"
    assert UF_PARA_CODIGO["53"] == "DF"