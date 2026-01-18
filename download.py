# download.py
import base64
import gzip
import time
from pathlib import Path
import urllib3
from urllib3.util.ssl_ import create_urllib3_context
import ssl
from lxml import etree
from signxml import XMLSigner, methods
from config import CERT_PFX_PATH, CERT_PASSWORD

# Desativa avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URLs oficiais do serviço NFeDistribuicaoDFe (produção)
URLS_DFE = {
    "AC": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "AL": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "AM": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "AP": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "BA": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "CE": "https://nfe.sefaz.ce.gov.br/nfe4/services/NFeDistribuicaoDFe",
    "DF": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "ES": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "GO": "https://nfe.sefaz.go.gov.br/nfe/services/v2/NfeDistribuicaoDFe",
    "MA": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "MS": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "MT": "https://nfe.sefaz.mt.gov.br/nfews/v2/services/NfeDistribuicaoDFe",
    "PA": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "PB": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "PI": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "PR": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "RJ": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "RN": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "RO": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "RR": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "RS": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "SC": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "SE": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "SP": "https://nfe.fazenda.sp.gov.br/ws/nfedistribuicaodfe.asmx",
    "TO": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"
}

UF_PARA_CODIGO = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
    "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
    "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
    "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
    "52": "GO", "53": "DF"
}

def detectar_uf_da_chave(chave: str) -> str:
    codigo = chave[:2]
    if codigo not in UF_PARA_CODIGO:
        raise ValueError(f"Código de UF inválido na chave: {codigo}")
    return UF_PARA_CODIGO[codigo]

def converter_pfx_para_pem(pfx_path: Path, senha: str):
    import subprocess
    cert_pem = pfx_path.with_suffix(".cert.pem")
    key_pem = pfx_path.with_suffix(".key.pem")
    
    subprocess.run([
        "openssl", "pkcs12", "-in", str(pfx_path),
        "-clcerts", "-nokeys", "-out", str(cert_pem),
        "-passin", f"pass:{senha}"
    ], check=True, capture_output=True)
    
    subprocess.run([
        "openssl", "pkcs12", "-in", str(pfx_path),
        "-nocerts", "-nodes", "-out", str(key_pem),
        "-passin", f"pass:{senha}"
    ], check=True, capture_output=True)
    
    return cert_pem, key_pem

def distribuicao_dfe(chave: str, uf: str, cert_pem: Path, key_pem: Path):
    url = URLS_DFE.get(uf)
    if not url:
        raise ValueError(f"URL não configurada para UF: {uf}")

    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or 443
    path = parsed.path or "/"

    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
        <soapenv:Header/>
        <soapenv:Body>
            <ns:distDFeInt>
                <distDFeInt xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01">
                    <tpAmb>1</tpAmb>
                    <cUFAutor>{chave[:2]}</cUFAutor>
                    <consChNFe>
                        <chNFe>{chave}</chNFe>
                    </consChNFe>
                </distDFeInt>
            </ns:distDFeInt>
        </soapenv:Body>
    </soapenv:Envelope>
    """.strip()

    root = etree.fromstring(soap_body.encode("utf-8"))
    dist_dfe_int = root.xpath("//ns:distDFeInt", namespaces={"ns": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"})[0]
    
    with open(cert_pem, "rb") as f_cert, open(key_pem, "rb") as f_key:
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha1",
            digest_algorithm="sha1",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
        )
        signed_dist = signer.sign(dist_dfe_int, key=f_key.read(), cert=f_cert.read())
    
    parent = dist_dfe_int.getparent()
    parent.replace(dist_dfe_int, signed_dist)

    # Contexto SSL personalizado
    ctx = create_urllib3_context()
    ctx.set_ciphers('DEFAULT@SECLEVEL=1')
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    http = urllib3.HTTPSConnectionPool(
        host=host,
        port=port,
        ssl_context=ctx,
        timeout=30,
        retries=False
    )

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse"
    }

    response = http.request(
        "POST",
        path,
        body=etree.tostring(root),
        headers=headers
    )

    if response.status != 200:
        raise Exception(f"Erro HTTP {response.status}")

    root_resp = etree.fromstring(response.data)
    ns = {"ns": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"}
    lote_zip = root_resp.xpath("//ns:loteDistDFeZip", namespaces=ns)
    
    if not lote_zip or not lote_zip[0].text:
        return None

    try:
        dados_zip = base64.b64decode(lote_zip[0].text)
        xml_bytes = gzip.decompress(dados_zip)
        return xml_bytes.decode("utf-8")
    except Exception:
        return None

def baixar_xml_por_chave(chave: str, pasta_saida: Path, cert_pem: Path, key_pem: Path):
    uf = detectar_uf_da_chave(chave)
    print(f"📥 Consultando chave {chave} (UF={uf})...")

    try:
        xml_nota = distribuicao_dfe(chave, uf, cert_pem, key_pem)
        if xml_nota:
            caminho_saida = pasta_saida / f"{chave}.xml"
            caminho_saida.write_text(xml_nota, encoding="utf-8")
            print(f"✅ Salvo: {chave}.xml")
        else:
            print(f"⚠️  Nenhum XML encontrado para {chave}")
    except Exception as e:
        print(f"❌ Erro na chave {chave}: {e}")

def baixar_em_massa(chaves: list[str], pasta_saida: Path):
    pasta_saida.mkdir(parents=True, exist_ok=True)
    cert_pem, key_pem = converter_pfx_para_pem(CERT_PFX_PATH, CERT_PASSWORD)

    for i, chave in enumerate(chaves, start=1):
        print(f"\n[{i}/{len(chaves)}]")
        if len(chave) != 44 or not chave.isdigit():
            print(f"⚠️  Chave inválida ignorada: {chave}")
            continue
        baixar_xml_por_chave(chave, pasta_saida, cert_pem, key_pem)
        time.sleep(1.5)

    cert_pem.unlink(missing_ok=True)
    key_pem.unlink(missing_ok=True)