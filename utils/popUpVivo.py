# utils/interacoes.py
import logging
import time
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException

logger = logging.getLogger(__name__)

def tratar_popup_cookies(driver: WebDriver, timeout: int = 10):

    logger.info("Verificando a presença do popup de cookies...")
    try:
        wait = WebDriverWait(driver, timeout)
        accept_button = wait.until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_button.click()
        logger.info("Popup de cookies aceito com sucesso.")
        time.sleep(2)
    except (TimeoutException, ElementClickInterceptedException, NoSuchElementException):
        logger.info("Popup de cookies não foi encontrado ou não precisa ser tratado.")