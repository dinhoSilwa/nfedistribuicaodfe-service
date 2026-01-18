# download.py
import time
from pathlib import Path
from pynfe.processamento.comunicacao import ComunicacaoSefaz
from pynfe.utils import extrair_dfe

def detectar_uf_da_chave(chave: str) -> str:
    """Extrai UF dos primeiros 2 dígitos da chave (ex: 23 → CE)."""
    codigos_uf = {
        "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
        "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
        "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
        "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
        "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
        "52": "GO", "53": "DF"
    }
    codigo = chave[:2]
    if codigo not in codigos_uf:
        raise ValueError(f"Código de UF inválido na chave: {codigo}")
    return codigos_uf[codigo]

def baixar_xml_por_chave(chave: str, cert_pem: Path, key_pem: Path, pasta_saida: Path):
    """Baixa um XML por chave usando PyNFe."""
    uf = detectar_uf_da_chave(chave)
    print(f"📥 Consultando chave {chave} (UF={uf})...")

    try:
        # Inicializa comunicação com a SEFAZ
        con = ComunicacaoSefaz(
            uf=uf,
            certificado=str(cert_pem),
            key=str(key_pem),
            homologacao=False
        )

        # Faz a consulta à distribuição DFe
        resposta = con.distribuicao_dfe(cnpj=None, chave=chave)

        # Extrai o XML da nota fiscal
        xml_nota = extrair_dfe(resposta, tipo="nfce") or extrair_dfe(resposta, tipo="nfe")
        
        if xml_nota:
            caminho_saida = pasta_saida / f"{chave}.xml"
            caminho_saida.write_text(xml_nota, encoding="utf-8")
            print(f"✅ Salvo: {caminho_saida.name}")
        else:
            print(f"⚠️  Nenhum XML encontrado para a chave {chave}")

    except Exception as e:
        print(f"❌ Erro na chave {chave}: {e}")

def baixar_em_massa(chaves: list[str], cert_pem: Path, key_pem: Path, pasta_saida: Path):
    """Baixa múltiplas chaves com pequeno delay entre requisições."""
    pasta_saida.mkdir(parents=True, exist_ok=True)

    for i, chave in enumerate(chaves, start=1):
        print(f"\n[{i}/{len(chaves)}]")
        if len(chave) != 44 or not chave.isdigit():
            print(f"⚠️  Chave inválida ignorada: {chave}")
            continue

        baixar_xml_por_chave(chave, cert_pem, key_pem, pasta_saida)
        time.sleep(1.5)  # Respeita limite de ~40 req/min