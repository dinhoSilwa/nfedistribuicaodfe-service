# main.py (CORRIGIDO - SEM PREFIXOS)

import base64
from pathlib import Path

from lxml import etree
from requests import Session
from requests_pkcs12 import Pkcs12Adapter
from zeep import Client
from zeep.exceptions import Fault
from zeep.transports import Transport

import config

NS = "http://www.portalfiscal.inf.br/nfe"

STATUS_MAP = {
    "137": "Nenhum documento disponível",
    "138": "Documentos localizados",
    "656": "Consumo indevido",
    "217": "Rejeição: Falha no schema XML",
    "225": "Rejeição: Falha no Schema XML da NFe",
    "214": "Tamanho da mensagem excedeu o limite",
    "404": "Rejeição: Uso de prefixo de namespace não permitido",
    "999": "Erro interno SEFAZ",
}


def extrair_status_de_xml(response_element):
    """Extrai cStat e xMotivo do elemento XML da resposta"""
    if response_element is None:
        return None, "Resposta vazia"

    try:
        # Procurar cStat com e sem namespace
        cstat_elem = response_element.find(".//{http://www.portalfiscal.inf.br/nfe}cStat")
        if cstat_elem is None:
            cstat_elem = response_element.find(".//cStat")

        xmotivo_elem = response_element.find(".//{http://www.portalfiscal.inf.br/nfe}xMotivo")
        if xmotivo_elem is None:
            xmotivo_elem = response_element.find(".//xMotivo")

        if cstat_elem is None:
            print("\n🔍 Estrutura do XML recebido:")
            print(etree.tostring(response_element, pretty_print=True, encoding="unicode")[:1000])
            return None, "cStat não encontrado no XML"

        cStat = cstat_elem.text
        xMotivo = xmotivo_elem.text if xmotivo_elem is not None else ""

        return str(cStat), xMotivo

    except Exception as e:
        return None, f"Erro ao parsear XML: {e}"


def extrair_documentos(response_element):
    """Extrai lista de documentos do lote"""
    try:
        docs = []

        doc_zips = response_element.findall(".//{http://www.portalfiscal.inf.br/nfe}docZip")

        if not doc_zips:
            doc_zips = response_element.findall(".//docZip")

        for doc_zip in doc_zips:
            nsu_elem = (
                doc_zip.get("NSU")
                or doc_zip.findtext(".//{http://www.portalfiscal.inf.br/nfe}NSU")
                or doc_zip.findtext(".//NSU")
            )
            value = doc_zip.text or ""

            if nsu_elem and value:
                docs.append({"NSU": nsu_elem, "value": value})

        return docs

    except Exception as e:
        print(f"⚠️ Erro ao extrair documentos: {e}")
        return []


def main():
    CERT_PFX = config.CERT_PFX
    CERT_PASSWORD = config.CERT_PASSWORD
    CNPJ_INTERESSADO = config.CNPJ_INTERESSADO
    CHAVE_DESEJADA = config.CHAVE_DESEJADA
    PASTA_XML = Path(__file__).parent / config.PASTA_XML
    ARQ_ULT_NSU = Path(__file__).parent / "ult_nsu.txt"

    PASTA_XML.mkdir(exist_ok=True)

    print(f"📁 XMLs serão salvos em: {PASTA_XML.resolve()}")

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

    if ARQ_ULT_NSU.exists():
        nsu = ARQ_ULT_NSU.read_text().strip()
    else:
        nsu = "000000000000000"

    print(f"🔁 ultNSU inicial: {nsu}")

    encontrado = False

    while True:
        print(f"🔍 Consultando NSU: {nsu}")

        try:
            # ✅ HEADER - Criar com namespace no elemento
            header_element = etree.Element("{http://www.portalfiscal.inf.br/nfe}nfeCabecMsg")
            etree.SubElement(header_element, "{http://www.portalfiscal.inf.br/nfe}cUF").text = "23"
            etree.SubElement(header_element, "{http://www.portalfiscal.inf.br/nfe}versaoDados").text = "1.01"

            # ✅ BODY - SEM PREFIXO, APENAS XMLNS DEFAULT
            distDFeInt = etree.Element("distDFeInt", versao="1.01", nsmap={None: NS})  # Namespace padrão SEM prefixo
            etree.SubElement(distDFeInt, "tpAmb").text = "1"
            etree.SubElement(distDFeInt, "CNPJ").text = CNPJ_INTERESSADO

            distNSU = etree.SubElement(distDFeInt, "distNSU")
            etree.SubElement(distNSU, "ultNSU").text = nsu

            response = client.service.nfeDistDFeInteresse(nfeDadosMsg=distDFeInt, _soapheaders=[header_element])

        except Fault as fault:
            print("❌ SOAP Fault retornado pela SEFAZ")
            print(f"Fault code: {fault.code}")
            print(f"Fault message: {fault.message}")
            break

        except Exception as e:
            print(f"❌ Erro na requisição SOAP: {e}")
            import traceback

            traceback.print_exc()
            break

        if response is None:
            print("❌ Resposta SOAP vazia (None).")
            break

        cStat, xMotivo = extrair_status_de_xml(response)

        print(f"📄 Retorno SEFAZ: {cStat} - {xMotivo}")

        if cStat is None:
            print("❌ Não foi possível interpretar o retorno da SEFAZ.")
            xml_debug = Path("resposta_debug.xml")
            xml_debug.write_bytes(etree.tostring(response, pretty_print=True))
            print(f"🧪 XML da resposta salvo em: {xml_debug.resolve()}")
            break

        if cStat in STATUS_MAP:
            print(f"ℹ️ {STATUS_MAP[cStat]}")
        else:
            print(f"⚠️ Status desconhecido retornado pela SEFAZ: {cStat}")

        if cStat == "137":
            break

        if cStat == "656":
            print("⏳ Aguarde 1 hora e reutilize o ultNSU.")
            break

        if cStat != "138":
            print("❌ Rejeição SEFAZ.")
            break

        docs = extrair_documentos(response)

        if not docs:
            print("ℹ️ Nenhum documento retornado.")
            break

        print(f"📦 {len(docs)} documento(s) encontrado(s) neste lote")

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

                if chave_xml == CHAVE_DESEJADA:
                    caminho = PASTA_XML / f"{chave_xml}.xml"
                    with open(caminho, "wb") as f:
                        f.write(xml_bytes)

                    print(f"✅ XML encontrado e salvo: {caminho}")
                    encontrado = True
                    break

            except Exception as e:
                print(f"⚠️ Erro ao processar NSU {nsu}: {e}")

        if encontrado or len(docs) < 50:
            break

    if not encontrado:
        print("❌ Nota fiscal não encontrada.")
        print("✔️ Verifique se o CNPJ participa da operação.")
        print("✔️ Verifique se a NF-e/NFC-e já foi distribuída.")


if __name__ == "__main__":
    main()
