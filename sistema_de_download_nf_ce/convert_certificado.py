# convert_certificado.py
import subprocess
import sys
from pathlib import Path
from sistema_de_download_nf_ce.config import CERT_PFX_PATH, CERT_PASSWORD

def converter_pfx_para_pem(pfx_path: Path, senha: str) -> tuple[Path, Path]:
    """
    Converte .pfx para cert.pem e key.pem usando OpenSSL.
    Garante que cert.pem contenha APENAS o certificado do titular.
    """
    cert_pem = pfx_path.parent / "cert.pem"
    key_pem = pfx_path.parent / "key.pem"

    # Exportar chave privada
    cmd_key = [
        "openssl", "pkcs12", "-in", str(pfx_path),
        "-nocerts", "-nodes", "-out", str(key_pem),
        "-passin", f"pass:{senha}"
    ]
    # Exportar APENAS o certificado do titular
    cmd_cert = [
        "openssl", "pkcs12", "-in", str(pfx_path),
        "-clcerts", "-nokeys", "-out", str(cert_pem),
        "-passin", f"pass:{senha}"
    ]

    try:
        subprocess.run(cmd_key, check=True, capture_output=True)
        subprocess.run(cmd_cert, check=True, capture_output=True)

        # --- CORREÇÃO CRÍTICA: remover certificados extras ---
        with open(cert_pem, "r") as f:
            content = f.read()

        # Isola apenas o primeiro certificado
        if content.count("-----BEGIN CERTIFICATE-----") > 1:
            first_cert = "-----BEGIN CERTIFICATE-----" + \
                         content.split("-----BEGIN CERTIFICATE-----")[1].split("-----END CERTIFICATE-----")[0] + \
                         "-----END CERTIFICATE-----\n"
            with open(cert_pem, "w") as f:
                f.write(first_cert)

        print(f"✅ Certificado convertido: {cert_pem}, {key_pem}")
        return cert_pem, key_pem

    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao converter certificado: {e.stderr.decode()}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ OpenSSL não encontrado. Instale o OpenSSL.")
        sys.exit(1)

if __name__ == "__main__":
    converter_pfx_para_pem(CERT_PFX_PATH, CERT_PASSWORD) # type: ignore