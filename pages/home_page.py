from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class HomePage:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def acessar_faturas(self):
        try:
            contas = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[@data-e2e-header-menu-invoices='']//span[text()='Contas']"
            )))
            contas.click()
            print("📂 Menu 'Contas' clicado.")

            faturas = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[@data-nav-menu-dropdown-item='invoices']//span[text()='Acessar faturas']"
            )))
            faturas.click()
            print("🧾 Acessando página de faturas.")
        except Exception as e:
            print(f"❌ Erro ao acessar menu de faturas: {e}")

    def baixar_boleto_pdf(self):
        try:
            btn_baixar = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[contains(., 'Baixar agora')]"
            )))
            btn_baixar.click()
            print("⬇️ Botão 'Baixar agora' clicado.")

            boleto_opcao = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[contains(., 'Boleto (.pdf)')]"
            )))
            boleto_opcao.click()
            print("📥 Boleto PDF solicitado.")
        except Exception as e:
            print(f"❌ Erro ao baixar o boleto PDF: {e}")
