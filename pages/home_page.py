from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class HomePage:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def acessar_faturas(self):
        try:
            print("⏳ Tentando clicar no menu 'Contas'...")
            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//li[@data-e2e-header-menu-invoices='']//span[text()='Contas']")
            )).click()
            print("✅ Menu 'Contas' clicado com sucesso.")

            print("⏳ Tentando acessar a opção 'Acessar faturas'...")
            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//li[@data-nav-menu-dropdown-item='invoices']//span[text()='Acessar faturas']")
            )).click()
            print("✅ Página de faturas acessada com sucesso.")
        except Exception as e:
            print(f"❌ Erro ao acessar menu de faturas: {e}")
