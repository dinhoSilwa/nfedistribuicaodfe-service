# main.py
from pathlib import Path
from config import ARQUIVO_CHAVES, PASTA_XMLS
from convert_certificado import converter_pfx_para_pem
from download import baixar_em_massa

def main():
    # 1. Converte o certificado
    cert_pem, key_pem = converter_pfx_para_pem(
        pfx_path=ARQUIVO_CHAVES.parent / "certificado.pfx",
        senha=open(".env").read().split("CERT_PASSWORD=")[1].split("\n")[0]
    )
    # Melhor usar config.CERT_PASSWORD, mas evitamos import circular

    # 2. Lê as chaves
    with open(ARQUIVO_CHAVES, "r", encoding="utf-8") as f:
        chaves = [linha.strip() for linha in f if linha.strip()]

    if not chaves:
        print("❌ Nenhuma chave encontrada em chaves.txt")
        return

    print(f"🚀 Iniciando download de {len(chaves)} XMLs...")

    # 3. Baixa em massa
    baixar_em_massa(chaves, cert_pem, key_pem, PASTA_XMLS)

    print(f"\n🎉 Concluído! XMLs salvos em: {PASTA_XMLS}")

if __name__ == "__main__":
    main()