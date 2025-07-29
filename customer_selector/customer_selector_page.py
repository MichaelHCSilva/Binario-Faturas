from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

class CustomerSelectorPage:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def abrir_lista_de_cnpjs(self):
        self.wait.until(EC.element_to_be_clickable((By.ID, "customer-select-desktop"))).click()
        print("Menu de clientes aberto.")

    def listar_cnpjs_visiveis(self):
        elementos = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "p.customer-name")))
        return [el.text.strip() for el in elementos if el.text.strip()]

    def clicar_cnpj_por_texto(self, cnpj_texto):
        elementos = self.driver.find_elements(By.CSS_SELECTOR, "p.customer-name")
        for el in elementos:
            if el.text.strip() == cnpj_texto:
                el.click()
                print(f"Clicado: {cnpj_texto}")
                time.sleep(2)  # Pequena pausa para garantir a troca
                return True
        print(f"CNPJ '{cnpj_texto}' não encontrado.")
        return False

    def clicar_primeiro_cnpj_da_lista(self):
        try:
            primeiro = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "li.list-item-wrapper.only-title[data-test-customer]"
            )))
            cnpj_texto = primeiro.text.strip()
            primeiro.click()
            print(f"Primeiro CNPJ clicado: {cnpj_texto}")
            time.sleep(2)
            return cnpj_texto  # ✅ Retorna o texto
        except Exception as e:
            print(f"Erro ao clicar no primeiro CNPJ da lista: {e}")
            return None

class CnpjLogger:
    def __init__(self, arquivo="cnpjs_processados.txt"):
        self.arquivo = arquivo
        self.cnpjs = set()

        if os.path.exists(self.arquivo):
            with open(self.arquivo, "r", encoding="utf-8") as f:
                self.cnpjs = {linha.strip() for linha in f if linha.strip()}

    def ja_processado(self, cnpj):
        return cnpj in self.cnpjs

    def registrar(self, cnpj):
        if not self.ja_processado(cnpj):
            with open(self.arquivo, "a", encoding="utf-8") as f:
                f.write(cnpj + "\n")
            self.cnpjs.add(cnpj)
            print(f"Registrado: {cnpj}")
