from sistema_de_download_nf_ce.config import ARQUIVO_CHAVES, PASTA_XMLS
from sistema_de_download_nf_ce.download import baixar_em_massa

def main():
    if not ARQUIVO_CHAVES.exists():
        raise FileNotFoundError(f"Arquivo de chaves não encontrado: {ARQUIVO_CHAVES}")

    with open(ARQUIVO_CHAVES, "r", encoding="utf-8") as f:
        chaves = [linha.strip() for linha in f if linha.strip().isdigit() and len(linha.strip()) == 44]

    if not chaves:
        print("⚠️  Nenhuma chave válida encontrada.")
        return

    print(f"🚀 Iniciando download de {len(chaves)} XMLs...")
    baixar_em_massa(chaves, PASTA_XMLS)
    print(f"🎉 Concluído! XMLs salvos em: {PASTA_XMLS}")

if __name__ == "__main__":
    main()