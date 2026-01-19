# download.py - VERSÃO FINAL COM mTLS
import base64
import gzip
import time
from pathlib import Path
import ssl
from lxml import etree
from signxml import XMLSigner, methods
from config import CERT_PFX_PATH, CERT_PASSWORD, CNPJ
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util.ssl_ import create_urllib3_context
# URLs oficiais do serviço NFeDistribuicaoDFe (produção)
URLS_DFE = {
    "AC": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "AL": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "AM": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "AP": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "BA": "https://dfe-svrs-1.sefazvirtual.rs.gov.br/ws/nfe/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "CE": "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
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
    """Detecta a UF a partir dos primeiros 2 dígitos da chave de acesso."""
    codigo = chave[:2]
    if codigo not in UF_PARA_CODIGO:
        raise ValueError(f"Código de UF inválido na chave: {codigo}")
    return UF_PARA_CODIGO[codigo]


def converter_pfx_para_pem(pfx_path: Path, senha: str):
    """
    Converte certificado PFX para formato PEM (cert + key).
    Retorna (cert.pem, key.pem)
    """
    import subprocess
    
    cert_pem = pfx_path.with_suffix(".cert.pem")
    key_pem = pfx_path.with_suffix(".key.pem")
    
    # Exportar certificado
    subprocess.run([
        "openssl", "pkcs12", "-in", str(pfx_path),
        "-clcerts", "-nokeys", "-out", str(cert_pem),
        "-passin", f"pass:{senha}"
    ], check=True, capture_output=True, text=True)
    
    # Exportar chave privada
    subprocess.run([
        "openssl", "pkcs12", "-in", str(pfx_path),
        "-nocerts", "-nodes", "-out", str(key_pem),
        "-passin", f"pass:{senha}"
    ], check=True, capture_output=True, text=True)
    
    return cert_pem, key_pem


def criar_sessao_sefaz(cert_pem: Path, key_pem: Path):
    """
    Cria uma sessão requests com mTLS (mutual TLS) configurado.
    CRÍTICO: O servidor SEFAZ requer certificado cliente durante handshake!
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    session = requests.Session()
    
    # IMPORTANTE: Configura certificado cliente para mTLS
    # O servidor SEFAZ pede certificado durante TLS handshake (Request CERT)
    session.cert = (str(cert_pem), str(key_pem))
    
    # Desabilita verificação de certificado do servidor
    # (SEFAZ usa certificados ICP-Brasil que podem não estar no truststore)
    session.verify = False
    
    return session


def distribuicao_dfe(chave: str, uf: str, cert_pem: Path, key_pem: Path, session: requests.Session):
    """
    Faz a requisição SOAP para o serviço NFeDistribuicaoDFe.
    Retorna o XML da nota fiscal ou None se não encontrado.
    """
    url = URLS_DFE.get(uf)
    if not url:
        raise ValueError(f"URL não configurada para UF: {uf}")

    # Monta o envelope SOAP
    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
        <soapenv:Header/>
        <soapenv:Body>
            <ns:distDFeInt>
                <distDFeInt xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01">
                    <tpAmb>1</tpAmb>
                    <cUFAutor>{chave[:2]}</cUFAutor>
                    <CNPJ>{CNPJ}</CNPJ>
                    <consChNFe>
                        <chNFe>{chave}</chNFe>
                    </consChNFe>
                </distDFeInt>
            </ns:distDFeInt>
        </soapenv:Body>
    </soapenv:Envelope>
    """.strip()

    # Parse e assina o XML
    root = etree.fromstring(soap_body.encode("utf-8"))
    ns = {"ns": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"}
    dist_dfe_int = root.xpath("//ns:distDFeInt", namespaces=ns)[0]
    
    # Assina digitalmente
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

    # Headers SOAP
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse"
    }
    print(f"\n📤 XML ENVIADO:")
    print(etree.tostring(root, pretty_print=True, encoding='unicode')[:1000])

    # Faz a requisição
    # A sessão já tem cert=(cert_pem, key_pem) configurado
    response = session.post(
        url,
        data=etree.tostring(root),
        headers=headers,
        timeout=30
    )

# ADICIONE AQUI:
    print(f"\n🔍 DEBUG:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")  # Pr
    response.raise_for_status()

    # Parse da resposta
    root_resp = etree.fromstring(response.content)
    lote_zip = root_resp.xpath("//ns:loteDistDFeZip", namespaces=ns)
    
    if not lote_zip or not lote_zip[0].text:
        # Verifica se há mensagem de erro
        cstat = root_resp.xpath("//ns:cStat", namespaces=ns)
        xmotivo = root_resp.xpath("//ns:xMotivo", namespaces=ns)
        
        if cstat and xmotivo:
            status = cstat[0].text
            motivo = xmotivo[0].text
            print(f"   ℹ️  Status {status}: {motivo}")
        
        return None

    # Descompacta o XML
    try:
        dados_zip = base64.b64decode(lote_zip[0].text)
        xml_bytes = gzip.decompress(dados_zip)
        return xml_bytes.decode("utf-8")
    except Exception as e:
        print(f"   ⚠️  Erro ao descomprimir XML: {e}")
        return None


def baixar_xml_por_chave(chave: str, pasta_saida: Path, cert_pem: Path, key_pem: Path, session: requests.Session):
    """Baixa o XML de uma NFe pela chave de acesso."""
    uf = detectar_uf_da_chave(chave)
    print(f"📥 Consultando chave {chave} (UF={uf})...")

    try:
        xml_nota = distribuicao_dfe(chave, uf, cert_pem, key_pem, session)
        if xml_nota:
            caminho_saida = pasta_saida / f"{chave}.xml"
            caminho_saida.write_text(xml_nota, encoding="utf-8")
            print(f"✅ Salvo: {chave}.xml")
            return True
        else:
            print(f"⚠️  Nenhum XML encontrado para {chave}")
            return False
    except Exception as e:
        print(f"❌ Erro na chave {chave}: {e}")
        import traceback
        traceback.print_exc()
        return False


def baixar_em_massa(chaves: list[str], pasta_saida: Path):
    """
    Baixa XMLs de múltiplas chaves de acesso.
    Exibe estatísticas ao final.
    """
    pasta_saida.mkdir(parents=True, exist_ok=True)
    
    # Converte certificado uma única vez
    print("🔐 Convertendo certificado...")
    cert_pem, key_pem = converter_pfx_para_pem(CERT_PFX_PATH, CERT_PASSWORD)
    
    # Cria sessão com mTLS (certificado cliente)
    print("🔗 Criando sessão com autenticação mTLS...")
    session = criar_sessao_sefaz(cert_pem, key_pem)
    
    # Estatísticas
    sucesso = 0
    falhas = 0
    nao_encontrados = 0

    try:
        for i, chave in enumerate(chaves, start=1):
            print(f"\n[{i}/{len(chaves)}]")
            
            # Valida chave
            if len(chave) != 44 or not chave.isdigit():
                print(f"⚠️  Chave inválida ignorada: {chave}")
                falhas += 1
                continue
            
            # Tenta baixar
            resultado = baixar_xml_por_chave(chave, pasta_saida, cert_pem, key_pem, session)
            
            if resultado:
                sucesso += 1
            else:
                nao_encontrados += 1
            
            # Delay entre requisições (respeita rate limit)
            if i < len(chaves):
                time.sleep(1.5)
    
    finally:
        # Limpeza de arquivos temporários
        print("\n🧹 Limpando arquivos temporários...")
        cert_pem.unlink(missing_ok=True)
        key_pem.unlink(missing_ok=True)
    
    # Exibe estatísticas
    print("\n" + "="*60)
    print("📊 RESUMO DA EXECUÇÃO")
    print("="*60)
    print(f"✅ Sucesso: {sucesso}")
    print(f"⚠️  Não encontrados: {nao_encontrados}")
    print(f"❌ Falhas: {falhas}")
    print(f"📁 Total processado: {len(chaves)}")
    print("="*60)