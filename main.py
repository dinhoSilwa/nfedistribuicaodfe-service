# main.py (CORRIGIDO - FORMATO CORRETO)

import base64
from pathlib import Path

from lxml import etree
from requests import Session
from requests_pkcs12 import Pkcs12Adapter
from zeep import Client
from zeep.exceptions import Fault
from zeep.transports import Transport
from zeep.wsse.utils import WSU

import config

NS = "http://www.portalfiscal.inf.br/nfe"

STATUS_MAP = {
    "137": "Nenhum documento disponível",
    "138": "Documentos localizados",
    "656": "Consumo indevido",
    "217": "Rejeição: Falha no schema XML",
    "225": "Rejeição: Falha no Schema XML da NFe",
    "214": "Tamanho da mensagem excedeu o limite",
    "999": "Erro interno SEFAZ",
}


def extrair_status(resposta):
    """Extrai cStat e xMotivo de forma segura"""
    if resposta is None:
        return None, "Resposta SOAP vazia"

    try:
        cStat = getattr(resposta, "cStat", None)
        xMotivo = getattr(resposta, "xMotivo", None)

        if cStat is None:
            return None, "Resposta sem cStat (estrutura inesperada)"

        return str(cStat), xMotivo or ""

    except Exception as e:
        return None, f"Erro ao interpretar resposta: {e}"


def salvar_xml_erro(client, nome_arquivo="erro_sefaz.xml"):
    """Salva XML bruto da resposta em caso de erro"""
    try:
        raw_xml = client.transport.session.last_response.content
        erro_xml = Path(nome_arquivo)
        erro_xml.write_bytes(raw_xml)
        print(f"🧪 XML bruto salvo para análise: {erro_xml.resolve()}")

        # Mostrar o XML também
        print("\n📄 XML da Resposta:")
        print(raw_xml.decode("utf-8")[:2000])  # Primeiros 2000 chars
        print("...")

    except Exception as e:
        print(f"⚠️ Não foi possível salvar XML de erro: {e}")


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
            # ✅ CRIAR HEADER COM NAMESPACE CORRETO
            header_element = etree.Element("{http://www.portalfiscal.inf.br/nfe}nfeCabecMsg")
            etree.SubElement(header_element, "{http://www.portalfiscal.inf.br/nfe}cUF").text = "23"
            etree.SubElement(header_element, "{http://www.portalfiscal.inf.br/nfe}versaoDados").text = "1.01"

            # ✅ CRIAR BODY - ELEMENTO XML PURO
            distDFeInt = etree.Element("{http://www.portalfiscal.inf.br/nfe}distDFeInt", versao="1.01")
            etree.SubElement(distDFeInt, "{http://www.portalfiscal.inf.br/nfe}tpAmb").text = "1"
            etree.SubElement(distDFeInt, "{http://www.portalfiscal.inf.br/nfe}CNPJ").text = CNPJ_INTERESSADO

            distNSU = etree.SubElement(distDFeInt, "{http://www.portalfiscal.inf.br/nfe}distNSU")
            etree.SubElement(distNSU, "{http://www.portalfiscal.inf.br/nfe}ultNSU").text = nsu

            # ✅ CHAMAR SERVIÇO COM ELEMENTO XML DIRETO
            response = client.service.nfeDistDFeInteresse(
                nfeDadosMsg=distDFeInt, _soapheaders=[header_element]  # XML Element direto
            )

        except Fault as fault:
            print("❌ SOAP Fault retornado pela SEFAZ")
            print(f"Fault code: {fault.code}")
            print(f"Fault message: {fault.message}")
            salvar_xml_erro(client, "fault_sefaz.xml")
            break

        except Exception as e:
            print(f"❌ Erro na requisição SOAP: {e}")
            import traceback

            traceback.print_exc()
            salvar_xml_erro(client, "exception_sefaz.xml")
            break

        if response is None:
            print("❌ Resposta SOAP vazia (None).")
            print("➡️ Possível erro de schema, rejeição grave ou falha de comunicação.")
            salvar_xml_erro(client, "none_response.xml")
            break

        # DEBUG: Ver estrutura da resposta
        print(f"\n🔬 Tipo da resposta: {type(response)}")
        print(f"🔬 Atributos disponíveis: {[a for a in dir(response) if not a.startswith('_')]}")

        cStat, xMotivo = extrair_status(response)

        print(f"📄 Retorno SEFAZ: {cStat} - {xMotivo}")

        if cStat is None:
            print("❌ Não foi possível interpretar o retorno da SEFAZ.")
            salvar_xml_erro(client, "no_cstat.xml")
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
            salvar_xml_erro(client, f"rejeicao_{cStat}.xml")
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
