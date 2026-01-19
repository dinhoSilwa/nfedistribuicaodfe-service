# distribuicao/utils.py
from pathlib import Path

def detectar_uf_da_chave(chave: str) -> str:
    if len(chave) != 44 or not chave.isdigit():
        raise ValueError(f"Chave inválida: {chave}")
    codigo_uf = chave[:2]
    from .urls import UF_PARA_CODIGO
    if codigo_uf not in UF_PARA_CODIGO:
        raise ValueError(f"Código UF desconhecido: {codigo_uf}")
    return UF_PARA_CODIGO[codigo_uf]

def salvar_xml(chave: str, xml_bytes: bytes, pasta_saida: str):
    pasta = Path(pasta_saida)
    pasta.mkdir(exist_ok=True)
    caminho = pasta / f"{chave}.xml"
    caminho.write_bytes(xml_bytes)
    return caminho