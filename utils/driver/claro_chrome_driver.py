#claro_chrome_driver
import logging
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def configurar_driver_chrome(
    user_data_dir: str, profile_directory: str, download_dir: str
) -> webdriver.Chrome:

    options = Options()
    
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--profile-directory={profile_directory}")
    
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)

    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    if not chromedriver_path:
        raise ValueError("Variável de ambiente 'CHROMEDRIVER_PATH' não encontrada.")
    
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })
    
    # Pequena espera para estabilidade
    time.sleep(3)
    
    return driver
