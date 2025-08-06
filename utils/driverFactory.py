# utils/driverFactory.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

from utils.faturasDownloader import TEMP_DOWNLOAD_FOLDER

def create_driver(pasta_download_base):
    options = Options()
    options.add_argument("--start-maximized")

    download_dir = TEMP_DOWNLOAD_FOLDER

    os.makedirs(download_dir, exist_ok=True)

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }

    options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)