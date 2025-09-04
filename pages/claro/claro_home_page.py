
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.popup_manager import PopupManager 

class HomePage:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.popup_manager = PopupManager(driver, timeout=2) 

    def acessar_faturas(self):
        try:
            self.popup_manager.handle_all()

            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//li[@data-e2e-header-menu-invoices='']//span[text()='Contas']"))
            ).click()

            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//li[@data-nav-menu-dropdown-item='invoices']//span[text()='Acessar faturas']"))
            ).click()
            print("Página de faturas acessada com sucesso.")
        except Exception as e:
            print(f"Erro ao acessar menu de faturas: {e}")

    def verificar_opcao_acessar_faturas(self):
        try:
            self.popup_manager.handle_all()

            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//li[@data-e2e-header-menu-invoices='']//span[text()='Contas']"))
            ).click()

            self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//li[@data-nav-menu-dropdown-item='invoices']//span[text()='Acessar faturas']"))
            )
            return True
        except Exception:
            print("Opção 'Acessar faturas' NÃO encontrada no menu para este CNPJ.")
            return False
