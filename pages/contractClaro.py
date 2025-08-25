# contractClaro.py
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class ContratoCard:
    def __init__(self, driver, card_element: WebElement):
        self.driver = driver
        self.card_element = card_element
        self.wait = WebDriverWait(self.driver, 10)

    def esta_encerrado(self) -> bool:
        try:
            span_inativo = WebDriverWait(self.card_element, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.contract__infos-inactive"))
            )
            texto = span_inativo.text.strip().lower()
            if "encerrado" in texto:
                logger.info("Contrato encerrado detectado.")
                return True
            return False
        except TimeoutException:
            logger.info("Contrato ativo (tag de encerrado não encontrada).")
            return False
        except Exception as e:
            logger.warning(f"Erro ao verificar status de 'encerrado': {e}", exc_info=True)
            return False

    def clicar_selecionar(self) -> bool:

        try:
            logger.info("Tentando clicar em 'Selecionar' no contrato.")
            botao_locator = (By.XPATH, ".//button[contains(text(), 'Selecionar')]")
            
            botao_selecionar = WebDriverWait(self.card_element, 5).until(
                EC.element_to_be_clickable(botao_locator)
            )
            
            self.driver.execute_script("arguments[0].click();", botao_selecionar)
            logger.info("Botão 'Selecionar' clicado com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao clicar no botão 'Selecionar': {e}")
            return False

    def obter_numero_contrato(self) -> str:

        try:
            numero_div = self.card_element.find_element(By.CSS_SELECTOR, "div.mdn-Text.mdn-Text--body")
            texto_completo = numero_div.text.strip()
            
            try:
                span_inativo = numero_div.find_element(By.CSS_SELECTOR, "span.contract__infos-inactive")
                texto_span = span_inativo.text.strip()
                numero = texto_completo.replace(texto_span, "").strip()
            except NoSuchElementException:
                numero = texto_completo
            
            logger.info(f"Número do contrato encontrado: {numero}")
            return numero
        except Exception as e:
            logger.error(f"Não foi possível obter o número do contrato: {e}")
            return "contrato_desconhecido"