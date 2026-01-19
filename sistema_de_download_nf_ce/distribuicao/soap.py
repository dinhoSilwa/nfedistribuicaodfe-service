import base64
import gzip
import requests
from requests_pkcs12 import Pkcs12Adapter
from lxml import etree
from .urls import URLS_DFE

def distribuicao_dfe_por_chave(
    chave: str,
    cnpj_interessado: str,
    cert_pfx: str,
    cert_password: str,
    ambiente: int = 1,
    timeout: int = 30
) -> bytes | None:
    from .utils import detectar_uf_da_chave
    uf = detectar_uf_da_chave(chave)
    url = URLS_DFE.get(uf)
    if not url:
        raise ValueError(f"URL do serviço DistDFe não configurada para UF: {uf}")

    # Correção 1: usar cUFAutor=91 para SVRS (todas as UFs que usam SVRS)
    # Correção 2: XML de negócio dentro de CDATA, dentro de nfeDadosMsg
    corpo_negocio = f"""<distDFeInt xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01">
  <tpAmb>{ambiente}</tpAmb>
  <cUFAutor>91</cUFAutor>
  <CNPJ>{cnpj_interessado}</CNPJ>
  <consChNFe>
    <chNFe>{chave}</chNFe>
  </consChNFe>
</distDFeInt>"""

    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Body>
    <nfe:nfeDistDFeInteresse xmlns:nfe="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
      <nfe:nfeDadosMsg><![CDATA[{corpo_negocio}]]></nfe:nfeDadosMsg>
    </nfe:nfeDistDFeInteresse>
  </soap:Body>
</soap:Envelope>"""

    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8"
        # SOAPAction removido (opcional em SOAP 1.2 e causa problemas se malformado)
    }

    session = requests.Session()
    session.mount("https://", Pkcs12Adapter(
        pkcs12_filename=cert_pfx,
        pkcs12_password=cert_password
    ))

    try:
        resp = session.post(url, data=soap_body, headers=headers, timeout=timeout, verify=False)
        resp.raise_for_status()

        # Correção 3: namespace da resposta é 'http://www.portalfiscal.inf.br/nfe', NÃO o WSDL
        root = etree.fromstring(resp.content)
        ns = {
            "soap": "http://www.w3.org/2003/05/soap-envelope",
            "nfe": "http://www.portalfiscal.inf.br/nfe"
        }

        lote_zip = root.xpath("//nfe:loteDistDFeZip", namespaces=ns)
        if lote_zip and lote_zip[0].text:
            dados_zip = base64.b64decode(lote_zip[0].text)
            return gzip.decompress(dados_zip)

        # Verifica erros mesmo sem lote
        cStat_nodes = root.xpath("//nfe:cStat", namespaces=ns)
        if cStat_nodes:
            cStat_val = cStat_nodes[0].text
            xMotivo_nodes = root.xpath("//nfe:xMotivo", namespaces=ns)
            motivo = xMotivo_nodes[0].text if xMotivo_nodes else "Sem motivo"
            print(f"⚠️ Erro SEFAZ: cStat={cStat_val}, xMotivo={motivo}")
        else:
            print("⚠️ Resposta inesperada: nenhum loteDistDFeZip ou cStat encontrado.")

        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de rede ao buscar chave {chave}: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro inesperado ao buscar chave {chave}: {e}")
        return None