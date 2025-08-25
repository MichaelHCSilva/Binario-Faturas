from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class PopupHandler:
    def __init__(self, driver, wait_time=5):
        self.driver = driver
        self.wait_time = wait_time

    def close_known_popups(self):
        selectors = [
            "button[data-qsi-creative-button-type='close']",
            "button[data-test-dialog-button='cancelar-download']",
            "button[class*='QSIWebResponsiveDialog-Layout1'][class*='close-btn']"
        ]
        for sel in selectors:
            try:
                btn = WebDriverWait(self.driver, self.wait_time).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                btn.click()
                print(f"[PopupHandler] Popup fechado: {sel}")
                return True
            except TimeoutException:
                continue
        return False

    def close_qualtrics_iframe_popup(self):
        try:
            iframe = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[data-interceptid^='SI_']"))
            )
            self.driver.switch_to.frame(iframe)
            print("[PopupHandler] Switch para o iframe feito com sucesso.")

            close_button = WebDriverWait(self.driver, self.wait_time).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='close-btn']"))
            )
            close_button.click()
            print("[PopupHandler] Botão de fechar clicado com sucesso.")

            self.driver.switch_to.default_content()
            return True

        except (TimeoutException, NoSuchElementException) as e:
            print("[PopupHandler] Popup do Qualtrics não encontrado ou botão não clicável:", e)
            self.driver.switch_to.default_content()
            return False

    def force_remove_qualtrics_popup(self):
        try:
            self.driver.execute_script("""
                const dialog = document.querySelector("div[class*='QSIWebResponsiveDialog-Layout1'][role='dialog']");
                if (dialog) {
                    dialog.remove();
                    console.log('Qualtrics popup removed forcibly.');
                }
            """)
            print("[PopupHandler] Popup do Qualtrics removido com JS.")
            return True
        except Exception as e:
            print("[PopupHandler] Erro ao remover popup com JS:", e)
            return False
