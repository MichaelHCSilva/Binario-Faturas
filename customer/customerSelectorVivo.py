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
                
                print(f"Elemento encontrado com locator: {locator}")
                return elemento
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                print(f"Locator {locator} falhou.")
                continue
        raise NoSuchElementException("Nenhum localizador da lista encontrou o elemento.")

    def open_menu(self):
        print("Abrindo menu de clientes...")
        try:
            print("Procurando pelo botão do menu...")
            botao_menu = self.find_element(self.botoes_menu_locators)
            
            try:
                botao_menu.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", botao_menu)

            print("Botão do menu clicado. Esperando a lista de CNPJs...")
            self.wait.until(EC.visibility_of_element_located(self.list_cnpjs_locator))
            print("Lista de CNPJs está visível. Prosseguindo.")

        except Exception as e:
            print(f"Erro ao abrir menu de clientes: {e}")
            raise

    def close_menu(self):
        print("Tentando fechar o menu de clientes...")
        try:
            backdrop = self.wait.until(EC.element_to_be_clickable(self.backdrop_fechar_locator))
            backdrop.click()
            print("Menu de clientes fechado com sucesso.")
            time.sleep(1)
        except (TimeoutException, NoSuchElementException, Exception):
            print("Menu de clientes já estava fechado ou o backdrop não foi encontrado.")

    def get_cnpjs(self):
        print("Capturando lista de CNPJs visíveis...")
        try:
            elementos = self.wait.until(EC.presence_of_all_elements_located(self.list_cnpjs_locator))
            cnpjs = [el.text.strip() for el in elementos if el.text.strip()]
            print(f"{len(cnpjs)} CNPJs capturados: {cnpjs}")
            return cnpjs
        except Exception as e:
            print(f"Erro ao capturar CNPJs: {e}")
            return []

    def click_by_text(self, cnpj_text ):
        print(f"Tentando clicar no CNPJ: {cnpj_text }")
        try:
            cnpj_list  = self.wait.until(EC.presence_of_all_elements_located(self.list_cnpjs_locator))
            for el in cnpj_list :
                if el.text.strip() == cnpj_text :
                    el.click()
                    print(f"CNPJ '{cnpj_text }' clicado.")
                    time.sleep(2)
                    return True
            print(f"CNPJ '{cnpj_text }' não encontrado na lista.")
            return False
        except Exception as e:
            print(f"Erro ao tentar clicar no CNPJ '{cnpj_text }': {e}")
            return False

    def click_first_item(self):
        try:
            print("Tentando clicar no primeiro CNPJ da lista...")
            first_cnpj = self.wait.until(EC.element_to_be_clickable(self.list_cnpjs_locator))
            cnpj_text  = first_cnpj.text.strip()
            first_cnpj()
            print(f"Primeiro CNPJ clicado: {cnpj_text }")
            time.sleep(2)
            return cnpj_text 
        except Exception as e:
            print(f"Erro ao clicar no primeiro CNPJ da lista: {e}")
            return None