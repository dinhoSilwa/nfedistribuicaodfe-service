import time
from pathlib import Path

from sistema_de_download_nf_ce import config
from sistema_de_download_nf_ce.distribuicao import distribuicao_dfe_por_chave
from sistema_de_download_nf_ce.distribuicao.utils import salvar_xml

# Carrega chaves do arquivo
with open(config.ARQUIVO_CHAVES) as f:
    CHAVES_DESEJADAS = [linha.strip() for linha in f if linha.strip().isdigit() and len(linha.strip()) == 44]


def main():
    print(f"📥 Consultando {len(CHAVES_DESEJADAS)} chaves...")
    for i, chave in enumerate(CHAVES_DESEJADAS, 1):
        print(f"[{i}/{len(CHAVES_DESEJADAS)}] {chave}")
        xml_bytes = distribuicao_dfe_por_chave(
            chave=chave,
            cnpj_interessado=config.CNPJ_INTERESSADO,
            cert_pfx=str(config.CERT_PFX_PATH),
            cert_password=config.CERT_PASSWORD,
            ambiente=config.AMBIENTE,
            timeout=config.TIMEOUT,
        )
        if xml_bytes:
            salvar_xml(chave, xml_bytes, config.PASTA_XML)
            print(f"✅ Salvo: {chave}.xml")
        else:
            print(f"⚠️ Falha ou não encontrado: {chave}")
        time.sleep(1.5)


if __name__ == "__main__":
    main()
