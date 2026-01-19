# sistema_de_download_nf_ce/config.py
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Caminho do certificado PFX
CERT_PFX_PATH = Path(os.getenv("CERT_PFX_PATH", "certificate/certificado.pfx"))
CERT_PASSWORD = os.getenv("CERT_PASSWORD")
CNPJ_INTERESSADO = os.getenv("CNPJ")  # Renomeado para clareza

# Validação obrigatória
if not CERT_PASSWORD:
    raise ValueError("CERT_PASSWORD não definido no .env")
if not CNPJ_INTERESSADO:
    raise ValueError("CNPJ não definido no .env")

# Arquivo de chaves (pode ser sobrescrito por .env)
ARQUIVO_CHAVES = Path(os.getenv("ARQUIVO_CHAVES", "chaves.txt"))

# Pasta de saída dos XMLs
PASTA_XML = "xmls"  # string, como esperado por salvar_xml()

AMBIENTE = 1  # 1 = produção, 2 = homologação
TIMEOUT = 30
