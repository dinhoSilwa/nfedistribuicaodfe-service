```python
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CHAVE = "23250834683891000140650260000032871604904017"
URL = "https://dfe-portal.svrs.rs.gov.br/NfceSSL/DownloadXmlDfe"

PASTA_DOWNLOAD = Path("downloads").resolve()
PASTA_DOWNLOAD.mkdir(parents=True, exist_ok=True)

def aguardar_download_completo(pasta: Path, arquivos_antes: set, timeout: int = 90) -> Path:
    inicio = time.time()
    crdownload_detectado = False

    while time.time() - inicio < timeout:
        arquivos_atual = set(pasta.iterdir())
        novos = arquivos_atual - arquivos_antes
        crdownloads = [a for a in novos if a.suffix == ".crdownload"]
        xmls = [a for a in novos if a.suffix == ".xml"]

        if crdownloads:
            crdownload_detectado = True

        if crdownload_detectado and not crdownloads and xmls:
            return xmls[0]

        time.sleep(0.5)

    raise TimeoutError("Download não finalizado dentro do tempo esperado")

def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    prefs = {
        "download.default_directory": str(PASTA_DOWNLOAD),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = None
    try:
        logging.info("Iniciando o WebDriver...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 30)

        logging.info(f"Acessando URL: {URL}")
        driver.get(URL)

        if "Erro no processamento do Portal" in driver.page_source:
            raise RuntimeError("Página retornou erro imediato. Certifique-se de que o certificado digital está configurado.")

        arquivos_antes = set(PASTA_DOWNLOAD.iterdir())

        logging.info("Preenchendo chave de acesso...")
        input_chave = wait.until(EC.presence_of_element_located((By.ID, "ChaveAcessoDfe")))
        input_chave.clear()
        input_chave.send_keys(CHAVE)

        logging.info("Clicando em 'Consultar'...")
        botao_consultar = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary")))
        botao_consultar.click()

        time.sleep(2)

        erros = driver.find_elements(By.CLASS_NAME, "alert-danger")
        if erros:
            raise RuntimeError(f"Erro retornado pelo portal: {erros[0].text.strip()}")

        logging.info("Aguardando botão de download...")
        botao_download = wait.until(EC.element_to_be_clickable((By.ID, "btnExportar")))

        logging.info("Iniciando download...")
        botao_download.click()

        arquivo_xml = aguardar_download_completo(pasta=PASTA_DOWNLOAD, arquivos_antes=arquivos_antes)
        logging.info(f"Download concluído com sucesso: {arquivo_xml.name}")

    except Exception as e:
        logging.error(f"Ocorreu um erro: {e}")
        raise
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
```