# main.py

import base64
from pathlib import Path

from lxml import etree
from requests import Session
from requests_pkcs12 import Pkcs12Adapter
from zeep import Client
from zeep.transports import Transport

import config

NS = "http://www.portalfiscal.inf.br/nfe"


def main():
    CERT_PFX = config.CERT_PFX
    CERT_PASSWORD = config.CERT_PASSWORD
    CNPJ_INTERESSADO = config.CNPJ_INTERESSADO
    CHAVE_DESEJADA = config.CHAVE_DESEJADA
    PASTA_XML = Path(__file__).parent / config.PASTA_XML
    ARQ_ULT_NSU = Path(__file__).parent / "ult_nsu.txt"

    PASTA_XML.mkdir(exist_ok=True)

    print(f"📁 XMLs serão salvos em: {PASTA_XML.resolve()}")

    # ===============================
    # Sessão HTTPS com certificado A1
    # ===============================
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

    # ===============================
    # Controle de ultNSU persistido
    # ===============================
    if ARQ_ULT_NSU.exists():
        nsu = ARQ_ULT_NSU.read_text().strip()
    else:
        nsu = "000000000000000"

    print(f"🔁 ultNSU inicial: {nsu}")

    encontrado = False

    while True:
        print(f"🔍 Consultando NSU: {nsu}")

        try:
            # ===============================
            # SOAP HEADER (OBRIGATÓRIO)
            # ===============================
            cabec = etree.Element(f"{{{NS}}}nfeCabecMsg")
            etree.SubElement(cabec, f"{{{NS}}}cUF").text = "23"
            etree.SubElement(cabec, f"{{{NS}}}versaoDados").text = "1.01"

            # ===============================
            # SOAP BODY (xsd:any → SEM wrapper)
            # ===============================
            distDFeInt = etree.Element(
                "distDFeInt",
                versao="1.01",
                xmlns=NS,
            )

            etree.SubElement(distDFeInt, "tpAmb").text = "1"
            etree.SubElement(distDFeInt, "CNPJ").text = CNPJ_INTERESSADO

            distNSU = etree.SubElement(distDFeInt, "distNSU")
            etree.SubElement(distNSU, "ultNSU").text = nsu

            response = client.service.nfeDistDFeInteresse(
                distDFeInt,
                _soapheaders=[cabec],
            )

        except Exception as e:
            print(f"❌ Erro na requisição SOAP: {e}")
            break

        cStat = getattr(response, "cStat", None)
        xMotivo = getattr(response, "xMotivo", "")

        print(f"📄 Retorno SEFAZ: {cStat} - {xMotivo}")

        # ===============================
        # Tratamento de status
        # ===============================
        if cStat == "137":
            print("ℹ️ Nenhum documento disponível para este NSU.")
            break

        if cStat == "656":
            print("⏳ Consumo indevido. Aguarde 1 hora e reutilize o ultNSU.")
            break

        if cStat != "138":
            print("❌ Rejeição SEFAZ.")
            break

        lote = getattr(response, "loteDistDFeInt", None)
        docs = getattr(lote, "docZip", []) if lote else []

        if not docs:
            print("ℹ️ Nenhum documento retornado.")
            break

        for doc in docs:
            nsu = doc.NSU
            ARQ_ULT_NSU.write_text(nsu)

            try:
                xml_bytes = base64.b64decode(doc.value)
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
