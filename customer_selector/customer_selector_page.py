from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class CustomerSelectorPage:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def abrir_lista_de_cnpjs(self):
        print("⏳ Abrindo menu de clientes...")
        self.wait.until(EC.element_to_be_clickable((By.ID, "customer-select-desktop"))).click()
        print("✅ Menu de clientes aberto.")

    def listar_cnpjs_visiveis(self):
        print("⏳ Capturando lista de CNPJs visíveis...")
        elementos = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "p.customer-name")))
        cnpjs = [el.text.strip() for el in elementos if el.text.strip()]
        print(f"✅ {len(cnpjs)} CNPJs capturados: {cnpjs}")
        return cnpjs

    def clicar_cnpj_por_texto(self, cnpj_texto):
        print(f"⏳ Tentando clicar no CNPJ: {cnpj_texto}")
        elementos = self.driver.find_elements(By.CSS_SELECTOR, "p.customer-name")
        for el in elementos:
            if el.text.strip() == cnpj_texto:
                el.click()
                print(f"✅ CNPJ '{cnpj_texto}' clicado.")
                time.sleep(2)
                return True
        print(f"⚠️ CNPJ '{cnpj_texto}' não encontrado.")
        return False

    def clicar_primeiro_cnpj_da_lista(self):
        try:
            print("⏳ Tentando clicar no primeiro CNPJ da lista...")
            primeiro = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "li.list-item-wrapper.only-title[data-test-customer]")
            ))
            cnpj_texto = primeiro.text.strip()
            primeiro.click()
            print(f"✅ Primeiro CNPJ clicado: {cnpj_texto}")
            time.sleep(2)
            return cnpj_texto
        except Exception as e:
            print(f"❌ Erro ao clicar no primeiro CNPJ da lista: {e}")
            return None
