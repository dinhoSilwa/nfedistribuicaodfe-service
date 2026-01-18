# config.py
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

ARQUIVO_CHAVES = Path("chaves.txt").resolve()
PASTA_XMLS = Path("xmls_baixados").resolve()
CERT_PFX_PATH = Path(os.getenv("CERT_PFX_PATH", "certificado.pfx")).resolve()
CERT_PASSWORD = os.getenv("CERT_PASSWORD")