import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException
)
from pages.claro.claro_contract_card import ContratoCard
from typing import Callable, Any
from services.invoice_service import FaturaService
from models.invoice_table import faturas
import os

logger = logging.getLogger(__name__)

class FaturaPage:
    def __init__(self, driver, pasta_faturas: str, timeout=15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.pasta_faturas = pasta_faturas  
        self.fatura_service = FaturaService(self.pasta_faturas, faturas)
    
    def _aguardar_renderizacao_contratos(self):
        logger.info("Aguardando renderização completa dos contratos...")
        try:
            self.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "contract"))
            )
            self.wait.until(
                lambda d: all(el.is_displayed() for el in d.find_elements(By.CLASS_NAME, "contract"))
            )
            logger.info("Todos os contratos estão visíveis e carregados.")
        except TimeoutException:
            logger.warning("Timeout ao esperar pelos contratos. A página pode estar vazia.")
            raise

    def _avancar_para_proxima_pagina(self) -> bool:
        try:
            next_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    '.mdn-Pagination-Link.mdn-Pagination-Link--next:not([disabled="disabled"])'
                ))
            )
            self.driver.execute_script("arguments[0].click();", next_button)
            self.wait.until(EC.staleness_of(next_button))
            self._aguardar_renderizacao_contratos()
            return True
        except TimeoutException:
            logger.info("Botão de próxima página não encontrado ou desabilitado.")
            return False

    def _voltar_para_pagina_contratos(self, contratos_url: str):
        try:
            self.driver.back()
            self._aguardar_renderizacao_contratos()
            logger.info("Retorno à página de contratos via 'driver.back()' bem-sucedido.")
        except (TimeoutException, Exception):
            logger.warning("Falha ao usar 'driver.back()'. Tentando retorno completo via URL...")
            self.driver.get(contratos_url)
            self._aguardar_renderizacao_contratos()
            logger.info("Retorno à página de contratos via URL bem-sucedido.")

    def processar_todos_contratos_ativos(self, callback_processamento: Callable[[str], Any], contratos_url: str):
        pagina_atual = 1
        contratos_falhados = []
        max_tentativas = 3

        while True:
            logger.info(f"Processando contratos na página {pagina_atual}...")
            try:
                self._aguardar_renderizacao_contratos()
            except TimeoutException:
                logger.warning(f"Timeout ao carregar a página {pagina_atual}. O processo pode ter terminado ou a página está vazia.")
                if not self._avancar_para_proxima_pagina():
                    break
                else:
                    continue

            contratos_elements = self.driver.find_elements(By.CLASS_NAME, "contract")
            for i in range(len(contratos_elements)):
                try:
                    contrato_element = self.driver.find_elements(By.CLASS_NAME, "contract")[i]
                    card = ContratoCard(self.driver, contrato_element)

                    if card.esta_encerrado():
                        logger.info(f"Contrato {card.obter_numero_contrato()} está encerrado, pulando.")
                        continue

                    if card.clicar_selecionar():
                        numero_contrato = card.obter_numero_contrato()
                        logger.info(f"Contrato {numero_contrato} selecionado para download.")

                        arquivos_baixados = callback_processamento(numero_contrato)

                        if arquivos_baixados:
                            logger.info(f"Processando {len(arquivos_baixados)} PDFs do contrato {numero_contrato}...")
                            for arquivo in arquivos_baixados:
                                caminho_pdf = os.path.join(self.fatura_service.pasta_faturas, arquivo)
                                self.fatura_service.processar_fatura_pdf(caminho_pdf)
                            logger.info(f"PDFs do contrato {numero_contrato} processados com sucesso.")
                        else:
                            logger.info(f"Contrato {numero_contrato} não possui faturas pendentes. Pulando processamento.")

                        self._voltar_para_pagina_contratos(contratos_url)
                        for _ in range(pagina_atual - 1):
                            if not self._avancar_para_proxima_pagina():
                                break

                except Exception as e:
                    contrato_numero = card.obter_numero_contrato() if 'card' in locals() else "desconhecido"
                    logger.error(f"Falha ao processar o contrato {contrato_numero}. Adicionando à lista de falhas. Erro: {e}", exc_info=True)
                    contratos_falhados.append(contrato_numero)

                    try:
                        self._voltar_para_pagina_contratos(contratos_url)
                        for _ in range(pagina_atual - 1):
                            if not self._avancar_para_proxima_pagina():
                                break
                    except Exception as fallback_e:
                        logger.error(f"Falha na tentativa de recuperação. O processo será interrompido: {fallback_e}")
                        return

            if not self._avancar_para_proxima_pagina():
                logger.info("Não há mais páginas. Processamento da primeira rodada concluído.")
                break

            pagina_atual += 1

        if contratos_falhados:
            self._tentar_novamente_falhados(contratos_falhados, callback_processamento, contratos_url, max_tentativas)

    def _tentar_novamente_falhados(self, contratos_falhados: list, callback_processamento: Callable, contratos_url: str, max_tentativas: int):
        logger.info(f"Iniciando a segunda rodada de tentativas para {len(contratos_falhados)} contratos falhados.")
        contratos_nao_processados = list(contratos_falhados)
        
        for tentativa in range(max_tentativas):
            if not contratos_nao_processados:
                logger.info("Todos os contratos falhados foram processados com sucesso nas tentativas.")
                return

            contratos_restantes = []
            logger.info(f"Tentativa {tentativa + 1} de {max_tentativas} para os contratos falhados.")

            self.driver.get(contratos_url)
            self._aguardar_renderizacao_contratos()

            for contrato_numero in contratos_nao_processados:
                try:
                    self._processar_contrato_unico(contrato_numero, callback_processamento)
                except Exception as e:
                    logger.error(f"Falha na tentativa de reprocessamento do contrato {contrato_numero}. Erro: {e}")
                    contratos_restantes.append(contrato_numero)

            contratos_nao_processados = contratos_restantes
            
        if contratos_nao_processados:
            logger.error(f"Falha ao processar os seguintes contratos após {max_tentativas} tentativas: {contratos_nao_processados}")
        else:
            logger.info("Todas as tentativas de reprocessamento foram concluídas.")

    def _processar_contrato_unico(self, numero_contrato: str, callback_processamento: Callable):
        logger.info(f"Buscando e processando contrato individual: {numero_contrato}")

        while True:
            try:
                self._aguardar_renderizacao_contratos()
            except TimeoutException:
                logger.warning("Página vazia. Não há mais contratos a buscar.")
                break
                
            cards = self.driver.find_elements(By.CLASS_NAME, "contract")
            for card_element in cards:
                card = ContratoCard(self.driver, card_element)
                if card.obter_numero_contrato() == numero_contrato:
                    logger.info(f"Contrato {numero_contrato} encontrado para reprocessamento.")
                    if card.clicar_selecionar():
                        callback_processamento(numero_contrato)
                        for arquivo in os.listdir(self.fatura_service.pasta_faturas):
                            if arquivo.lower().endswith(".pdf"):
                                caminho_pdf = os.path.join(self.fatura_service.pasta_faturas, arquivo)
                                self.fatura_service.processar_fatura_pdf(caminho_pdf)
                        self._voltar_para_pagina_contratos(self.driver.current_url)
                        return
            
            if not self._avancar_para_proxima_pagina():
                raise NoSuchElementException(f"Contrato com número {numero_contrato} não encontrado para reprocessamento após varrer todas as páginas.")
