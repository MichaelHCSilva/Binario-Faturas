#customer_selector_page_vivo.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time

class CustomerSelectorPage:

    def __init__(self, driver, timeout=30):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        
        self.botoes_menu_locators = [
            (By.ID, "customer-select-desktop"),
            (By.CSS_SELECTOR, "button[data-test='customer-select-desktop']"),
            (By.XPATH, "//button[contains(@class, 'customer-select-desktop')]")
        ]
        
        self.list_cnpjs_locator = (By.CSS_SELECTOR, "li.list-item-wrapper.only-title h1.title")
        self.backdrop_fechar_locator = (By.CSS_SELECTOR, "div.drawer__backdrop")

    def find_element(self, locators, is_panel=False):
        for locator in locators:
            try:
                if is_panel:
                    elemento = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(locator))
                else:
                    elemento = self.wait.until(EC.element_to_be_clickable(locator))
                return elemento
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                continue
        raise NoSuchElementException("Nenhum localizador encontrou o elemento.")

    def open_menu(self):
        botao_menu = self.find_element(self.botoes_menu_locators)
        try:
            botao_menu.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", botao_menu)
        self.wait.until(EC.visibility_of_element_located(self.list_cnpjs_locator))

    def close_menu(self):
        try:
            backdrop = self.wait.until(EC.element_to_be_clickable(self.backdrop_fechar_locator))
            backdrop.click()
            time.sleep(1)
        except Exception:
            pass

    def get_cnpjs(self):
        try:
            elementos = self.wait.until(EC.presence_of_all_elements_located(self.list_cnpjs_locator))
            return [el.text.strip() for el in elementos if el.text.strip()]
        except Exception:
            return []

    def click_by_text(self, cnpj_text):
        try:
            cnpj_list = self.wait.until(EC.presence_of_all_elements_located(self.list_cnpjs_locator))
            for el in cnpj_list:
                if el.text.strip() == cnpj_text:
                    el.click()
                    time.sleep(2)
                    return True
            return False
        except Exception:
            return False

    def click_first_item(self):
        try:
            first_cnpj = self.wait.until(EC.element_to_be_clickable(self.list_cnpjs_locator))
            cnpj_text = first_cnpj.text.strip()
            first_cnpj.click()
            time.sleep(2)
            return cnpj_text
        except Exception:
            return None
