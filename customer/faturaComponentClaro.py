#faturaComponent.py
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class FaturaCard:
    def __init__(self, driver, card_element: WebElement):
        self.driver = driver
        self.card_element = card_element
        self.wait = WebDriverWait(driver, 10)

    def esta_aguardando(self) -> bool:

        try:
            status_tag = self.card_element.find_element(By.CSS_SELECTOR, ".status-tag")
            return status_tag.text.strip() == "Aguardando"
        except:
            return False

    def clicar_selecionar(self) -> bool:

        try:
            print("Fatura pendente encontrada. Tentando clicar em 'Selecionar'.")
            
            botao_selecionar = self.card_element.find_element(By.XPATH, ".//a[contains(text(), 'Selecionar')]")
            
            self.wait.until(EC.element_to_be_clickable(botao_selecionar))

            print("Botão 'Selecionar' da fatura habilitado. Clicando...")
            self.driver.execute_script("arguments[0].click();", botao_selecionar)
            print("Botão 'Selecionar' da fatura clicado com sucesso.")
            return True
        except Exception as e:
            print(f"Erro ao clicar no botão 'Selecionar' da fatura: {e}")
            return False