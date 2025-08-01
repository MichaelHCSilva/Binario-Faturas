from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time

class CustomerSelectorPage:
    def __init__(self, driver, timeout=30):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        
        # Localizadores para o botão do menu (funcionando)
        self.botoes_menu_locators = [
            (By.ID, "customer-select-desktop"),
            (By.CSS_SELECTOR, "button[data-test='customer-select-desktop']"),
            (By.XPATH, "//button[contains(@class, 'customer-select-desktop')]")
        ]
        
        # Localizadores para a lista de CNPJs (o novo foco)
        self.lista_cnpjs_locator = (By.CSS_SELECTOR, "li.list-item-wrapper.only-title h1.title")
        
        # Localizador do backdrop para fechar o menu
        self.backdrop_fechar_locator = (By.CSS_SELECTOR, "div.drawer__backdrop")

    def encontrar_elemento_por_varios_locators(self, locators, is_panel=False):
        for locator in locators:
            try:
                if is_panel:
                    elemento = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(locator))
                else:
                    elemento = self.wait.until(EC.element_to_be_clickable(locator))
                
                print(f"✅ Elemento encontrado com locator: {locator}")
                return elemento
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                print(f"⚠️ Locator {locator} falhou.")
                continue
        raise NoSuchElementException("Nenhum localizador da lista encontrou o elemento.")

    def abrir_lista_de_cnpjs(self):
        print("⏳ Abrindo menu de clientes...")
        try:
            print("🔍 Procurando pelo botão do menu...")
            botao_menu = self.encontrar_elemento_por_varios_locators(self.botoes_menu_locators)
            
            try:
                botao_menu.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", botao_menu)

            print("✅ Botão do menu clicado. Esperando a lista de CNPJs...")
            # A nova estratégia é esperar diretamente pelos itens da lista
            self.wait.until(EC.visibility_of_element_located(self.lista_cnpjs_locator))
            print("✅ Lista de CNPJs está visível. Prosseguindo.")

        except Exception as e:
            print(f"❌ Erro ao abrir menu de clientes: {e}")
            raise

    def fechar_lista_de_cnpjs(self):
        print("⏳ Tentando fechar o menu de clientes...")
        try:
            backdrop = self.wait.until(EC.element_to_be_clickable(self.backdrop_fechar_locator))
            backdrop.click()
            print("✅ Menu de clientes fechado com sucesso.")
            time.sleep(1)
            # A espera pela invisibilidade pode ser inconsistente, vamos apenas assumir que o clique funcionou
        except (TimeoutException, NoSuchElementException, Exception):
            print("⚠️ Menu de clientes já estava fechado ou o backdrop não foi encontrado.")

    def listar_cnpjs_visiveis(self):
        print("⏳ Capturando lista de CNPJs visíveis...")
        try:
            elementos = self.wait.until(EC.presence_of_all_elements_located(self.lista_cnpjs_locator))
            cnpjs = [el.text.strip() for el in elementos if el.text.strip()]
            print(f"✅ {len(cnpjs)} CNPJs capturados: {cnpjs}")
            return cnpjs
        except Exception as e:
            print(f"❌ Erro ao capturar CNPJs: {e}")
            return []

    def clicar_cnpj_por_texto(self, cnpj_texto):
        print(f"⏳ Tentando clicar no CNPJ: {cnpj_texto}")
        try:
            lista_cnpjs = self.wait.until(EC.presence_of_all_elements_located(self.lista_cnpjs_locator))
            for el in lista_cnpjs:
                if el.text.strip() == cnpj_texto:
                    el.click()
                    print(f"✅ CNPJ '{cnpj_texto}' clicado.")
                    time.sleep(2)
                    return True
            print(f"⚠️ CNPJ '{cnpj_texto}' não encontrado na lista.")
            return False
        except Exception as e:
            print(f"⚠️ Erro ao tentar clicar no CNPJ '{cnpj_texto}': {e}")
            return False

    def clicar_primeiro_cnpj_da_lista(self):
        try:
            print("⏳ Tentando clicar no primeiro CNPJ da lista...")
            primeiro = self.wait.until(EC.element_to_be_clickable(self.lista_cnpjs_locator))
            cnpj_texto = primeiro.text.strip()
            primeiro.click()
            print(f"✅ Primeiro CNPJ clicado: {cnpj_texto}")
            time.sleep(2)
            return cnpj_texto
        except Exception as e:
            print(f"❌ Erro ao clicar no primeiro CNPJ da lista: {e}")
            return None