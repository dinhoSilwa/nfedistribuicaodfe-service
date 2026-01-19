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

    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:nfe="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
  <soap:Header/>
  <soap:Body>
    <nfe:nfeDistDFeInteresse>
      <nfe:distDFeInt xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01">
        <tpAmb>{ambiente}</tpAmb>
        <cUF>{chave[:2]}</cUF>
        <CNPJ>{cnpj_interessado}</CNPJ>
        <consChNFe>
          <chNFe>{chave}</chNFe>
        </consChNFe>
      </nfe:distDFeInt>
    </nfe:nfeDistDFeInteresse>
  </soap:Body>
</soap:Envelope>"""

    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
        "SOAPAction": '"http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse"'
    }

    session = requests.Session()
    session.mount("https://", Pkcs12Adapter(
        pkcs12_filename=cert_pfx,
        pkcs12_password=cert_password
    ))

    try:
        resp = session.post(url, data=soap_body, headers=headers, timeout=timeout, verify=False)
        resp.raise_for_status()

        root = etree.fromstring(resp.content)
        ns = {"nfe": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"}
        lote_zip = root.xpath("//nfe:loteDistDFeZip", namespaces=ns)

        if lote_zip and lote_zip[0].text:
            dados_zip = base64.b64decode(lote_zip[0].text)
            return gzip.decompress(dados_zip)
        else:
            # Verifica se houve erro na resposta
            cStat = root.xpath("//nfe:cStat", namespaces=ns)
            if cStat:
                cStat_val = cStat[0].text
                xMotivo = root.xpath("//nfe:xMotivo", namespaces=ns)
                motivo = xMotivo[0].text if xMotivo else "Sem motivo"
                print(f"⚠️ Erro SEFAZ: cStat={cStat_val}, xMotivo={motivo}")
            return None

    except Exception as e:
        print(f"❌ Erro ao buscar chave {chave}: {e}")
        return None