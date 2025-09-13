# claro_contract_card.py
import logging, time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException,
    WebDriverException
)

logger = logging.getLogger(__name__)

class ContratoCard:
    def __init__(self, driver, card_element: WebElement):
        self.driver = driver
        self.card_element = card_element

    def esta_encerrado(self) -> bool:
        for tentativa in range(3):
            try:
                span_inativo = WebDriverWait(self.card_element, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.contract__infos-inactive"))
                )
                return "encerrado" in span_inativo.text.strip().lower()
            except TimeoutException:
                return False
            except StaleElementReferenceException:
                logger.warning("Elemento de status ficou obsoleto. Tentando recapturar...")
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Erro ao verificar status de encerrado (tentativa {tentativa+1}): {e}")
                time.sleep(1)
        return False

    def clicar_selecionar(self, tentativas=3) -> bool:
        for tentativa in range(1, tentativas + 1):
            try:
                botao = WebDriverWait(self.card_element, 5).until(
                    EC.presence_of_element_located((By.XPATH, ".//button[contains(text(), 'Selecionar')]"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)

                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, ".//button[contains(text(), 'Selecionar')]"))
                )

                try:
                    botao.click()
                except WebDriverException:
                    logger.warning("Click direto falhou, tentando via JavaScript...")
                    self.driver.execute_script("arguments[0].click();", botao)

                logger.info("Botão 'Selecionar' clicado com sucesso.")
                return True

            except TimeoutException:
                logger.warning(f"Botão 'Selecionar' não disponível (tentativa {tentativa}).")
            except StaleElementReferenceException:
                logger.warning(f"Elemento ficou obsoleto (tentativa {tentativa}). Tentando recapturar card...")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Erro inesperado ao clicar em 'Selecionar': {e}", exc_info=True)

            if tentativa < tentativas:
                logger.info("Aguardando antes da nova tentativa...")
                time.sleep(tentativa * 2)

        logger.error("Não foi possível clicar no botão 'Selecionar' após várias tentativas.")
        return False

    def obter_numero_contrato(self) -> str:
        for tentativa in range(3):
            try:
                numero_div = self.card_element.find_element(By.CSS_SELECTOR, "div.mdn-Text.mdn-Text--body")
                texto = numero_div.text.strip()

                try:
                    span_inativo = numero_div.find_element(By.CSS_SELECTOR, "span.contract__infos-inactive")
                    return texto.replace(span_inativo.text.strip(), "").strip()
                except NoSuchElementException:
                    return texto

            except StaleElementReferenceException:
                logger.warning("Elemento de contrato ficou obsoleto. Tentando recapturar...")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Erro ao obter número do contrato (tentativa {tentativa+1}): {e}")
                time.sleep(1)

        logger.error("Não foi possível obter número do contrato após várias tentativas.")
        return "contrato_desconhecido"
