# claro_contract_card
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

logger = logging.getLogger(__name__)

class ContratoCard:
    def __init__(self, driver, card_element: WebElement):
        self.driver = driver
        self.card_element = card_element
        self.wait = WebDriverWait(self.card_element, 2)
    def esta_encerrado(self) -> bool:
        try:
            span_inativo = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.contract__infos-inactive"))
            )
            return "encerrado" in span_inativo.text.strip().lower()
        except TimeoutException:
            return False
        except Exception as e:
            logger.warning(f"Erro ao verificar status de 'encerrado': {e}", exc_info=True)
            return False

    def clicar_selecionar(self) -> bool:
        try:
            botao = self.wait.until(
                EC.presence_of_element_located((By.XPATH, ".//button[contains(text(), 'Selecionar')]"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
            WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.XPATH, ".//button[contains(text(), 'Selecionar')]")))
            self.driver.execute_script("arguments[0].click();", botao)
            return True
        except Exception as e:
            logger.error(f"Erro ao clicar no botão 'Selecionar': {e}", exc_info=True)
            return False

    def obter_numero_contrato(self) -> str:
        try:
            numero_div = self.card_element.find_element(By.CSS_SELECTOR, "div.mdn-Text.mdn-Text--body")
            texto = numero_div.text.strip()
            try:
                span_inativo = numero_div.find_element(By.CSS_SELECTOR, "span.contract__infos-inactive")
                return texto.replace(span_inativo.text.strip(), "").strip()
            except NoSuchElementException:
                return texto

        except StaleElementReferenceException:
            logger.warning("Elemento de contrato ficou obsoleto. Tentando reanexar card...")
            try:
                refreshed_card = self.driver.find_element(By.XPATH, f"//div[@data-contract-id='{self.contract_id}']")
                numero_div = refreshed_card.find_element(By.CSS_SELECTOR, "div.mdn-Text.mdn-Text--body")
                texto = numero_div.text.strip()
                return texto
            except Exception as e:
                logger.error(f"Falha ao reanexar número do contrato: {e}")
                return "contrato_desconhecido"

        except Exception as e:
            logger.error(f"Não foi possível obter o número do contrato: {e}")
            return "contrato_desconhecido"