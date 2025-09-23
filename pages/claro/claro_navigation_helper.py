import time
import logging
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

logger = logging.getLogger(__name__)


class NavigationHelper:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def aguardar_renderizacao_contratos(self):
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "contract")))
            self.wait.until(lambda d: all(el.is_displayed() for el in d.find_elements(By.CLASS_NAME, "contract")))
        except TimeoutException:
            raise

    def avancar_para_proxima_pagina(self, contratos_url: Optional[str] = None, pagina_atual: Optional[int] = None) -> bool:
        try:
            next_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '.mdn-Pagination-Link.mdn-Pagination-Link--next:not([disabled="disabled"])')
                )
            )
            self.driver.execute_script("arguments[0].click();", next_btn)
            self.wait.until(EC.staleness_of(next_btn))
            self.aguardar_renderizacao_contratos()
            logger.debug(f"Avançou para a próxima página (última conhecida: {pagina_atual}).")
            return True
        except TimeoutException:
            if pagina_atual is not None:
                logger.info(f"Processamento finalizado")
            else:
                logger.info("Botão 'próxima página' não encontrado — encerrando paginação.")
            return False
        except StaleElementReferenceException:
            logger.warning("Elemento 'próxima página' ficou obsoleto ao tentar clicar. Encerrando paginação.")
            return False

    def voltar_para_pagina_contratos(self, contratos_url: str):
        try:
            self.driver.get(contratos_url)
            self.aguardar_renderizacao_contratos()
        except Exception:
            try:
                self.driver.get(contratos_url)
                self.aguardar_renderizacao_contratos()
            except Exception as e:
                logger.error(f"Erro ao voltar para página de contratos: {e}")
                raise

    def recapturar_elemento_card(self, index: int, max_retries: int = 3, delay: float = 0.5):
        for attempt in range(max_retries):
            try:
                elements = self.driver.find_elements(By.CLASS_NAME, "contract")
                if index < len(elements):
                    return elements[index]
                else:
                    return None
            except StaleElementReferenceException:
                logger.warning(f"Elemento de contrato ficou obsoleto. Recapturando (tentativa {attempt+1}/{max_retries})...")
                time.sleep(delay)
        elements = self.driver.find_elements(By.CLASS_NAME, "contract")
        return elements[index] if index < len(elements) else None
