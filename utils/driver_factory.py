from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

def create_driver(download_dir):
    options = Options()
    options.add_argument("--start-maximized")

    # Garante que o diretório de download existe
    os.makedirs(download_dir, exist_ok=True)

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }

    options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)