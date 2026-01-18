# download.py
import time
from pathlib import Path
from pynfe.processamento.comunicacao import ComunicacaoSefaz

def extrair_dfe(resposta_xml, tipo="nfe"):
    """
    Extrai o XML da nota fiscal (NF-e ou NFC-e) da resposta do serviço NFeDistribuicaoDFe.
    
    :param resposta_xml: Elemento XML da resposta SOAP (lxml.etree._Element)
    :param tipo: "nfe" ou "nfce"
    :return: str com o XML da nota fiscal, ou None se não encontrado
    """
    # Namespace da resposta
    ns = {"ns": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"}

    # Localiza o campo com o documento compactado
    lote = resposta_xml.xpath("//ns:retDistDFeInt/ns:loteDistDFeZip", namespaces=ns)
    if not lote:
        return None

    # Decodifica base64
    conteudo_base64 = lote[0].text
    if not conteudo_base64:
        return None

    try:
        dados_zip = base64.b64decode(conteudo_base64)
        xml_descomprimido = gzip.decompress(dados_zip).decode("utf-8")
    except Exception:
        return None

    # Parseia o XML resultante
    root = etree.fromstring(xml_descomprimido)

    # Determina a tag esperada
    if tipo == "nfce":
        xpath_expr = ".//ns:NFe[ns:infNFe/@mod='65']"
    else:
        xpath_expr = ".//ns:NFe[ns:infNFe/@mod='55']"

    notas = root.xpath(xpath_expr, namespaces={"ns": "http://www.portalfiscal.inf.br/nfe"})
    if notas:
        return etree.tostring(notas[0], encoding="unicode", pretty_print=True)

    # Fallback: retorna qualquer NFe se não encontrar por modelo
    qualquer_nfe = root.xpath(".//ns:NFe", namespaces={"ns": "http://www.portalfiscal.inf.br/nfe"})
    if qualquer_nfe:
        return etree.tostring(qualquer_nfe[0], encoding="unicode", pretty_print=True)

    return None

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
            certificado=(str(cert_pem), str(key_pem)),  # Tupla (cert, key)
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