import logging
import time
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)

logger = logging.getLogger(__name__)

class PopupManager:
    def __init__(self, driver: WebDriver, timeout: int = 5):
        self.driver = driver
        self.timeout = timeout
        self._last_popup = None
        self._last_time = 0

    def _log_once(self, popup_name: str, message: str, level="info"):

        now = time.time()
        if self._last_popup == popup_name and now - self._last_time < 10:
            return
        self._last_popup = popup_name
        self._last_time = now
        if level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)

    def close_generic_popups(self) -> bool:
        selectors = [
            "button[data-qsi-creative-button-type='close']",
            "button[data-test-dialog-button='cancelar-download']",
            "button[class*='QSIWebResponsiveDialog-Layout1'][class*='close-btn']",
        ]
        for sel in selectors:
            try:
                btn = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                btn.click()
                self._log_once("generic", "Popup fechado com sucesso.")
                return True
            except TimeoutException:
                continue
        return False

    def close_qualtrics_iframe(self) -> bool:
        try:
            iframe = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[data-interceptid^='SI_']"))
            )
            self.driver.switch_to.frame(iframe)
            close_button = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='close-btn']"))
            )
            close_button.click()
            self.driver.switch_to.default_content()
            self._log_once("qualtrics_iframe", "Popup encerrado com sucesso.")
            return True
        except (TimeoutException, NoSuchElementException):
            self.driver.switch_to.default_content()
            return False

    def force_remove_qualtrics_popup(self) -> bool:
        try:
            removed = self.driver.execute_script("""
                const dialog = document.querySelector("div[class*='QSIWebResponsiveDialog-Layout1'][role='dialog']");
                if (dialog) { dialog.remove(); return true; } else { return false; }
            """)
            if removed:
                self._log_once("qualtrics_js", "Popup removido automaticamente..")
            return removed
        except Exception as e:
            self._log_once("qualtrics_js_error", f"Falha ao remover popup: {e}", level="error")
            return False

    def accept_cookies(self) -> bool:
        try:
            wait = WebDriverWait(self.driver, self.timeout)
            accept_button = wait.until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            accept_button.click()
            time.sleep(0.3)
            self._log_once("cookies", "Cookies aceitos com sucesso.")
            return True
        except (TimeoutException, ElementClickInterceptedException, NoSuchElementException):
            return False

    def handle_all(self) -> bool:
        handled = False
        handled |= self.close_generic_popups()
        handled |= self.close_qualtrics_iframe()
        handled |= self.force_remove_qualtrics_popup()
        handled |= self.accept_cookies()
        return handled
