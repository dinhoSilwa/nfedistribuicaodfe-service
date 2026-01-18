# config.py
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Arquivo de chaves
ARQUIVO_CHAVES = Path("chaves.txt").resolve()

# Pasta de saída dos XMLs
PASTA_XMLS = Path("xmls_baixados").resolve()

# Certificado
CERT_PFX_PATH = Path(os.getenv("CERT_PFX_PATH", "certificado.pfx")).resolve()
CERT_PASSWORD = os.getenv("CERT_PASSWORD")

# Validação
if not CERT_PFX_PATH.exists():
    raise FileNotFoundError(f"Certificado não encontrado: {CERT_PFX_PATH}")
if not CERT_PASSWORD:
    raise ValueError("Senha do certificado ausente em CERT_PASSWORD no .env")