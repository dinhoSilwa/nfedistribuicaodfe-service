# sistema_de_download_nf_ce/main.py
import time
from pathlib import Path
from .config import (
    CNPJ_INTERESSADO,
    CERT_PFX_PATH,
    CERT_PASSWORD,
    AMBIENTE,
    TIMEOUT,
    PASTA_XML
)
from .distribuicao.soap import distribuicao_dfe_por_chave
from .distribuicao.utils import salvar_xml

CHAVES_DESEJADAS = [
    "23250834683891000140650220000200441904557410",
    # ...
]

def main():
    print(f"📥 Consultando {len(CHAVES_DESEJADAS)} chaves...")
    for i, chave in enumerate(CHAVES_DESEJADAS, 1):
        print(f"[{i}/{len(CHAVES_DESEJADAS)}] {chave}")
        
        xml_bytes = distribuicao_dfe_por_chave(
            chave=chave,
            cnpj_interessado=CNPJ_INTERESSADO,
            cert_pfx=str(CERT_PFX_PATH),
            cert_password=CERT_PASSWORD,
            ambiente=AMBIENTE,
            timeout=TIMEOUT
        )
        
        if xml_bytes:
            caminho = salvar_xml(chave, xml_bytes, PASTA_XML)
            print(f"✅ Salvo: {caminho.name}")
        else:
            print(f"⚠️ Não encontrado: {chave}")
        
        if i < len(CHAVES_DESEJADAS):
            time.sleep(6.0)  # respeita limite da SEFAZ

if __name__ == "__main__":
    main()