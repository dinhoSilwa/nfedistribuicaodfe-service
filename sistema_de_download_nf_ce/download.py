# # download.py - VERSÃO CORRETA E MINIMAL
# import time
# from pathlib import Path
# from typing import List

# from sistema_de_download_nf_ce.config import (
#     AMBIENTE,
#     CERT_PASSWORD,
#     CERT_PFX_PATH,
#     CNPJ_INTERESSADO,
#     PASTA_XML,
#     TIMEOUT,
# )
# from sistema_de_download_nf_ce.distribuicao.soap import distribuicao_dfe_por_chave
# from sistema_de_download_nf_ce.distribuicao.utils import salvar_xml


# def baixar_xml_por_chave(chave: str) -> bool:
#     """Baixa uma única chave e salva na pasta configurada."""
#     xml_bytes = distribuicao_dfe_por_chave(
#         chave=chave,
#         cnpj_interessado=CNPJ_INTERESSADO,
#         cert_pfx=str(CERT_PFX_PATH),
#         cert_password=CERT_PASSWORD,
#         ambiente=AMBIENTE,
#         timeout=TIMEOUT,
#     )

#     if xml_bytes:
#         salvar_xml(chave, xml_bytes, PASTA_XML)
#         return True
#     return False


# def baixar_em_massa(chaves: List[str]) -> dict:
#     """Baixa múltiplas chaves com controle de taxa."""
#     Path(PASTA_XML).mkdir(exist_ok=True)
#     resultados = {"sucesso": 0, "falhas": 0, "nao_encontrados": 0}

#     for i, chave in enumerate(chaves, 1):
#         print(f"[{i}/{len(chaves)}] Processando {chave}...")

#         if len(chave) != 44 or not chave.isdigit():
#             print(f"⚠️ Chave inválida: {chave}")
#             resultados["falhas"] += 1
#             continue

#         if baixar_xml_por_chave(chave):
#             resultados["sucesso"] += 1
#             print(f"✅ Salvo: {chave}.xml")
#         else:
#             resultados["nao_encontrados"] += 1
#             print(f"⚠️ Não encontrado: {chave}")

#         if i < len(chaves):
#             time.sleep(1.5)  # Respeita limite da SEFAZ

#     return resultados
