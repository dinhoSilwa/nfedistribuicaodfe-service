# main_simples.py - BAIXAR 10 CHAVES ESPECÍFICAS

import base64
import time
from pathlib import Path

from lxml import etree
from requests import Session
from requests_pkcs12 import Pkcs12Adapter
from zeep import Client
from zeep.transports import Transport

import config


NS = "http://www.portalfiscal.inf.br/nfe"

# ✅ LISTA DAS 10 CHAVES QUE VOCÊ QUER
CHAVES_DESEJADAS = {
    "23250834683891000140650220000200441904557410",
    "23250834683891000140650220000200461119674581",
    "23250834683891000140650220000200481492423879",
    "23250834683891000140650220000201471078586171",
    "23250834683891000140650220000201671838266750",
    "23250834683891000140650220000201861478672758",
    "23250834683891000140650220000202821514530209",
    "23250834683891000140650220000203181498769340",
    "23250834683891000140650220000206171126786056",
    "23250834683891000140650220000206901800272082",
    "23250834683891000140650220000207061299677609",
}


def extrair_status_de_xml(response_element):
    """Extrai cStat e xMotivo"""
    if response_element is None:
        return None, "Resposta vazia"

    try:
        cstat_elem = response_element.find(".//{http://www.portalfiscal.inf.br/nfe}cStat")
        if cstat_elem is None:
            cstat_elem = response_element.find(".//cStat")

        xmotivo_elem = response_element.find(".//{http://www.portalfiscal.inf.br/nfe}xMotivo")
        if xmotivo_elem is None:
            xmotivo_elem = response_element.find(".//xMotivo")

        if cstat_elem is None:
            return None, "cStat não encontrado"

        return str(cstat_elem.text), xmotivo_elem.text if xmotivo_elem is not None else ""
    except Exception as e:
        return None, f"Erro: {e}"


def extrair_documentos(response_element):
    """Extrai documentos do lote"""
    try:
        docs = []
        doc_zips = response_element.findall(".//{http://www.portalfiscal.inf.br/nfe}docZip")

        if not doc_zips:
            doc_zips = response_element.findall(".//docZip")

        for doc_zip in doc_zips:
            nsu_elem = doc_zip.get("NSU") or doc_zip.findtext(".//NSU")
            value = doc_zip.text or ""

            if nsu_elem and value:
                docs.append({"NSU": nsu_elem, "value": value})

        return docs
    except Exception as e:
        print(f"⚠️ Erro ao extrair: {e}")
        return []


def main():
    CERT_PFX = config.CERT_PFX
    CERT_PASSWORD = config.CERT_PASSWORD
    CNPJ_INTERESSADO = config.CNPJ_INTERESSADO
    PASTA_XML = Path(__file__).parent / config.PASTA_XML
    ARQ_ULT_NSU = Path(__file__).parent / "ult_nsu.txt"

    PASTA_XML.mkdir(exist_ok=True)

    print("=" * 60)
    print("🎯 BUSCANDO 10 CHAVES ESPECÍFICAS")
    print("=" * 60)
    print(f"📁 Salvando em: {PASTA_XML.resolve()}\n")

    # Criar sessão
    session = Session()
    session.mount(
        "https://",
        Pkcs12Adapter(
            pkcs12_filename=CERT_PFX,
            pkcs12_password=CERT_PASSWORD,
        ),
    )

    client = Client(
        "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl",
        transport=Transport(session=session),
    )

    # Ler último NSU
    if ARQ_ULT_NSU.exists():
        nsu = ARQ_ULT_NSU.read_text().strip()
    else:
        nsu = "000000000000000"

    print(f"🔁 Começando do NSU: {nsu}\n")

    # ✅ CONTROLE SIMPLES
    chaves_encontradas = set()
    total_consultado = 0
    max_consultas = 500  # Limite de segurança

    while len(chaves_encontradas) < len(CHAVES_DESEJADAS):
        total_consultado += 1

        # ⚠️ SEGURANÇA: Não consultar infinitamente
        if total_consultado > max_consultas:
            print(f"\n⚠️ Atingiu limite de {max_consultas} consultas")
            break

        print(f"🔍 Consulta #{total_consultado} - NSU: {nsu}")

        try:
            # Montar requisição
            header_element = etree.Element("{http://www.portalfiscal.inf.br/nfe}nfeCabecMsg")
            etree.SubElement(header_element, "{http://www.portalfiscal.inf.br/nfe}cUF").text = "23"
            etree.SubElement(header_element, "{http://www.portalfiscal.inf.br/nfe}versaoDados").text = "1.01"

            distDFeInt = etree.Element("distDFeInt", versao="1.01", nsmap={None: NS})
            etree.SubElement(distDFeInt, "tpAmb").text = "1"
            etree.SubElement(distDFeInt, "CNPJ").text = CNPJ_INTERESSADO
            distNSU = etree.SubElement(distDFeInt, "distNSU")
            etree.SubElement(distNSU, "ultNSU").text = nsu

            response = client.service.nfeDistDFeInteresse(nfeDadosMsg=distDFeInt, _soapheaders=[header_element])

        except Exception as e:
            print(f"❌ Erro: {e}")
            break

        if response is None:
            print("❌ Resposta vazia")
            break

        cStat, xMotivo = extrair_status_de_xml(response)

        # ⏳ RATE LIMIT
        if cStat == "656":
            print(f"⏳ Rate limit! Esperando 1 hora...")
            time.sleep(3600)
            continue

        # ✅ FIM DA FILA
        if cStat == "137":
            print("ℹ️ Sem mais documentos")
            break

        # ❌ ERRO
        if cStat != "138":
            print(f"❌ Erro SEFAZ: {cStat} - {xMotivo}")
            break

        # ✅ PROCESSAR DOCUMENTOS
        docs = extrair_documentos(response)

        if not docs:
            print("⚠️ Lote vazio")
            break

        print(f"   📦 {len(docs)} documentos neste lote")

        # ✅ VERIFICAR CADA DOCUMENTO
        for doc in docs:
            nsu = doc["NSU"]
            ARQ_ULT_NSU.write_text(nsu)

            try:
                xml_bytes = base64.b64decode(doc["value"])
                root = etree.fromstring(xml_bytes)

                inf_nfe = root.find(".//{http://www.portalfiscal.inf.br/nfe}infNFe")
                if inf_nfe is None:
                    continue

                chave_xml = inf_nfe.get("Id", "")[3:]

                # ✅ É UMA DAS 10 CHAVES?
                if chave_xml in CHAVES_DESEJADAS:

                    # ✅ JÁ FOI BAIXADA?
                    if chave_xml in chaves_encontradas:
                        print(f"   🔁 Duplicada: {chave_xml[:10]}...")
                        continue

                    # ✅ SALVAR!
                    caminho = PASTA_XML / f"{chave_xml}.xml"
                    with open(caminho, "wb") as f:
                        f.write(xml_bytes)

                    chaves_encontradas.add(chave_xml)

                    print(f"   ✅ [{len(chaves_encontradas)}/11] {chave_xml[:10]}...{chave_xml[-4:]}")

            except Exception as e:
                print(f"   ⚠️ Erro NSU {nsu}: {e}")

        # ✅ ENCONTROU TODAS?
        if len(chaves_encontradas) == len(CHAVES_DESEJADAS):
            print(f"\n🎉 Todas as {len(CHAVES_DESEJADAS)} chaves encontradas!")
            break

        # ⏱️ DELAY (evitar rate limit)
        time.sleep(2)

    # ✅ RELATÓRIO FINAL
    print("\n" + "=" * 60)
    print("📊 RESULTADO")
    print("=" * 60)
    print(f"✅ Encontradas: {len(chaves_encontradas)}/11")
    print(f"🔍 Consultas: {total_consultado}")
    print(f"💾 Último NSU: {nsu}")
    print(f"📁 Pasta: {PASTA_XML.resolve()}")

    if len(chaves_encontradas) < len(CHAVES_DESEJADAS):
        print("\n❌ CHAVES NÃO ENCONTRADAS:")
        faltando = CHAVES_DESEJADAS - chaves_encontradas
        for chave in faltando:
            print(f"   • {chave}")

    print("=" * 60)


if __name__ == "__main__":
    main()
