# claro_invoice_page.py
import logging
import os
import json
import time
from datetime import datetime
from typing import Callable, Any, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)

from pages.claro.claro_contract_card import ContratoCard
from services.invoice_service import FaturaService

logger = logging.getLogger(__name__)


class FaturaPage:
    def __init__(self, driver, pasta_faturas: str, timeout: int = 15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.pasta_faturas = pasta_faturas
        self.fatura_service = FaturaService(self.pasta_faturas)
        self.json_path = os.path.join(self.fatura_service.pasta_faturas, "contratos_falhados.json")

        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Erro ao criar arquivo JSON inicial de falhas: {e}")

    def _registrar_falha(self, dados_falha: dict):
        try:
            falhas_existentes = []
            if os.path.exists(self.json_path):
                with open(self.json_path, "r", encoding="utf-8") as f:
                    falhas_existentes = json.load(f) or []
            falhas_existentes.append(dados_falha)
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(falhas_existentes, f, ensure_ascii=False, indent=4)
            logger.info(f"Falha registrada no JSON: {dados_falha}")
        except Exception as e:
            logger.error(f"Erro ao registrar falha em JSON: {e}")

    def _aguardar_renderizacao_contratos(self):
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "contract")))
            self.wait.until(lambda d: all(el.is_displayed() for el in d.find_elements(By.CLASS_NAME, "contract")))
        except TimeoutException:
            raise

    def _avancar_para_proxima_pagina(self, contratos_url: Optional[str] = None, pagina_atual: Optional[int] = None) -> bool:

        try:
            next_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '.mdn-Pagination-Link.mdn-Pagination-Link--next:not([disabled="disabled"])')
                )
            )
            self.driver.execute_script("arguments[0].click();", next_btn)
            self.wait.until(EC.staleness_of(next_btn))
            self._aguardar_renderizacao_contratos()
            logger.debug(f"Avançou para a próxima página (última conhecida: {pagina_atual}).")
            return True
        except TimeoutException:
            if pagina_atual is not None:
                logger.info(f"Processamento finalizado. Última página alcançada: {pagina_atual}.")
            else:
                logger.info("Botão 'próxima página' não encontrado — encerrando paginação.")
            return False
        except StaleElementReferenceException:
            logger.warning("Elemento 'próxima página' ficou obsoleto ao tentar clicar. Encerrando paginação.")
            return False

    def _voltar_para_pagina_contratos(self, contratos_url: str):
        try:
            self.driver.get(contratos_url)
            self._aguardar_renderizacao_contratos()
        except Exception:
            try:
                self.driver.get(contratos_url)
                self._aguardar_renderizacao_contratos()
            except Exception as e:
                logger.error(f"Erro ao voltar para página de contratos: {e}")
                raise

    def _recapturar_elemento_card(self, index: int, max_retries: int = 3, delay: float = 0.5):
       
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

    def processar_todos_contratos_ativos(self, callback_processamento: Callable[[str], Any], contratos_url: str):
        pagina_atual = 1

        while True:
            try:
                self._aguardar_renderizacao_contratos()
            except TimeoutException:
                if not self._avancar_para_proxima_pagina(contratos_url, pagina_atual):
                    break
                pagina_atual += 1
                continue

            contratos_elements = self.driver.find_elements(By.CLASS_NAME, "contract")
            total_na_pagina = len(contratos_elements)
            logger.debug(f"Página {pagina_atual}: {total_na_pagina} contratos encontrados.")

            for i in range(total_na_pagina):
                try:
                    element = self._recapturar_elemento_card(i)
                    if element is None:
                        logger.warning(f"Elemento de contrato no índice {i} não encontrado (página {pagina_atual}). Pulando.")
                        continue

                    card = ContratoCard(self.driver, element)

                    if card.esta_encerrado():
                        dados_falha = {
                            "contrato": card.obter_numero_contrato(),
                            "pagina": pagina_atual,
                            "posicao": i + 1,
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "erro": "Contrato encerrado, nenhuma fatura disponível"
                        }
                        self._registrar_falha(dados_falha)
                        continue

                    if not card.clicar_selecionar():
                        dados_falha = {
                            "contrato": card.obter_numero_contrato(),
                            "pagina": pagina_atual,
                            "posicao": i + 1,
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "erro": "Não foi possível clicar no botão 'Selecionar'."
                        }
                        self._registrar_falha(dados_falha)
                        continue

                    numero_contrato = card.obter_numero_contrato()

                    try:
                        no_invoices = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.no-invoices p")))
                        mensagem = no_invoices.text.strip()
                        dados_falha = {
                            "contrato": numero_contrato,
                            "pagina": pagina_atual,
                            "posicao": i + 1,
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "erro": mensagem
                        }
                        self._registrar_falha(dados_falha)
                        self._voltar_para_pagina_contratos(contratos_url)
                        for _ in range(pagina_atual - 1):
                            if not self._avancar_para_proxima_pagina(contratos_url, pagina_atual):
                                break
                        continue
                    except TimeoutException:
                        pass

                    arquivos = []
                    attempts = 0
                    erro_callback = None

                    while attempts < 3 and not arquivos:
                        try:
                            arquivos = callback_processamento(numero_contrato)
                        except Exception as e:
                            erro_callback = str(e)
                            logger.warning(f"Tentativa {attempts+1}/3 falhou para contrato {numero_contrato}: {e}")
                        attempts += 1

                    if not arquivos:
                        dados_falha = {
                            "contrato": numero_contrato,
                            "pagina": pagina_atual,
                            "posicao": i + 1,
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "erro": erro_callback if erro_callback else "Nenhum arquivo gerado após tentativas"
                        }
                        self._registrar_falha(dados_falha)
                    else:
                        for arquivo in arquivos:
                            self.fatura_service.processar_fatura_pdf(os.path.join(self.fatura_service.pasta_faturas, arquivo))

                    self._voltar_para_pagina_contratos(contratos_url)
                    for _ in range(pagina_atual - 1):
                        if not self._avancar_para_proxima_pagina(contratos_url, pagina_atual):
                            break

                except StaleElementReferenceException:
                    logger.warning(f"Elemento de contrato ficou obsoleto durante processamento (página {pagina_atual}, posição {i+1}). Registrando e prosseguindo.")
                    dados_falha = {
                        "contrato": "contrato_desconhecido",
                        "pagina": pagina_atual,
                        "posicao": i + 1,
                        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "erro": "Elemento de contrato ficou obsoleto (StaleElementReferenceException)"
                    }
                    self._registrar_falha(dados_falha)
                    continue
                except Exception as e:
                    dados_falha = {
                        "contrato": card.obter_numero_contrato() if 'card' in locals() and card is not None else "desconhecido",
                        "pagina": pagina_atual,
                        "posicao": i + 1,
                        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "erro": str(e)
                    }
                    self._registrar_falha(dados_falha)
                    try:
                        self._voltar_para_pagina_contratos(contratos_url)
                        for _ in range(pagina_atual - 1):
                            if not self._avancar_para_proxima_pagina(contratos_url, pagina_atual):
                                break
                    except Exception:
                        logger.warning("Falha ao tentar restaurar a página de contratos após erro.")

            if not self._avancar_para_proxima_pagina(contratos_url, pagina_atual):
                break

            pagina_atual += 1

    def _tentar_novamente_falhados(self, contratos_falhados, callback_processamento, contratos_url, max_tentativas: int):
        contratos_nao_processados = list(contratos_falhados)
        for tentativa in range(max_tentativas):
            if not contratos_nao_processados:
                return
            contratos_restantes = []
            self.driver.get(contratos_url)
            self._aguardar_renderizacao_contratos()
            for contrato_numero in contratos_nao_processados:
                try:
                    self._processar_contrato_unico(contrato_numero, callback_processamento)
                except Exception:
                    contratos_restantes.append(contrato_numero)
            contratos_nao_processados = contratos_restantes

    def _processar_contrato_unico(self, numero_contrato, callback_processamento: Callable[[str], Any]):
        while True:
            try:
                self._aguardar_renderizacao_contratos()
            except TimeoutException:
                break
            for card_element in self.driver.find_elements(By.CLASS_NAME, "contract"):
                card = ContratoCard(self.driver, card_element)
                if card.obter_numero_contrato() == numero_contrato:
                    if not card.clicar_selecionar():
                        raise Exception(f"Não foi possível selecionar contrato {numero_contrato}")

                    try:
                        no_invoices = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.no-invoices p")))
                        mensagem = no_invoices.text.strip()
                        dados_falha = {
                            "contrato": numero_contrato,
                            "pagina": None,
                            "posicao": None,
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "erro": mensagem
                        }
                        self._registrar_falha(dados_falha)
                        self._voltar_para_pagina_contratos(self.driver.current_url)
                        return
                    except TimeoutException:
                        pass

                    arquivos = []
                    attempts = 0
                    erro_callback = None
                    while attempts < 3 and not arquivos:
                        try:
                            arquivos = callback_processamento(numero_contrato)
                        except Exception as e:
                            erro_callback = str(e)
                            logger.warning(f"Tentativa {attempts+1}/3 falhou para contrato {numero_contrato}: {e}")
                        attempts += 1

                    if arquivos:
                        for arquivo in arquivos:
                            self.fatura_service.processar_fatura_pdf(os.path.join(self.fatura_service.pasta_faturas, arquivo))

                    self._voltar_para_pagina_contratos(self.driver.current_url)
                    return

            if not self._avancar_para_proxima_pagina():
                raise NoSuchElementException(f"Contrato {numero_contrato} não encontrado.")
