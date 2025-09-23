import logging
import os
import json
from typing import Callable, Any, Optional
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from pages.claro.claro_contract_card import ContratoCard
from processors.invoice_processor import FaturaService
from utils.json_failure_logger import JsonFailureLogger
from pages.claro.claro_navigation_helper import NavigationHelper

logger = logging.getLogger(__name__)


class FaturaPage:
    def __init__(self, driver, pasta_faturas: str, timeout: int = 15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.pasta_faturas = pasta_faturas
        self.fatura_service = FaturaService(self.pasta_faturas)

        self.json_logger = JsonFailureLogger()
        self.navigation = NavigationHelper(self.driver, self.wait)

    def processar_todos_contratos_ativos(self, callback_processamento: Callable[[str], Any], contratos_url: str):
        pagina_atual = 1

        while True:
            try:
                self.navigation.aguardar_renderizacao_contratos()
            except TimeoutException:
                if not self.navigation.avancar_para_proxima_pagina(contratos_url, pagina_atual):
                    break
                pagina_atual += 1
                continue

            contratos_elements = self.driver.find_elements(By.CLASS_NAME, "contract")
            total_na_pagina = len(contratos_elements)
            logger.debug(f"Página {pagina_atual}: {total_na_pagina} contratos encontrados.")

            for i in range(total_na_pagina):
                try:
                    element = self.navigation.recapturar_elemento_card(i)
                    if element is None:
                        logger.warning(f"Elemento de contrato no índice {i} não encontrado (página {pagina_atual}). Avançando.")
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
                        self.json_logger.registrar_falha_claro(dados_falha)

                        continue

                    if not card.clicar_selecionar():
                        dados_falha = {
                            "contrato": card.obter_numero_contrato(),
                            "pagina": pagina_atual,
                            "posicao": i + 1,
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "erro": "Não foi possível clicar no botão 'Selecionar'."
                        }
                        self.json_logger.registrar_falha_claro(dados_falha)

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
                        self.json_logger.registrar_falha_claro(dados_falha)

                        self.navigation.voltar_para_pagina_contratos(contratos_url)
                        for _ in range(pagina_atual - 1):
                            if not self.navigation.avancar_para_proxima_pagina(contratos_url, pagina_atual):
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
                        self.json_logger.registrar_falha_claro(dados_falha)

                    else:
                        for arquivo in arquivos:
                            self.fatura_service.processar_fatura_pdf(os.path.join(self.fatura_service.pasta_faturas, arquivo))

                    self.navigation.voltar_para_pagina_contratos(contratos_url)
                    for _ in range(pagina_atual - 1):
                        if not self.navigation.avancar_para_proxima_pagina(contratos_url, pagina_atual):
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
                    self.json_logger.registrar_falha_claro(dados_falha)

                    continue
                except Exception as e:
                    dados_falha = {
                        "contrato": card.obter_numero_contrato() if 'card' in locals() and card is not None else "desconhecido",
                        "pagina": pagina_atual,
                        "posicao": i + 1,
                        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "erro": str(e)
                    }
                    self.json_logger.registrar_falha_claro(dados_falha)

                    try:
                        self.navigation.voltar_para_pagina_contratos(contratos_url)
                        for _ in range(pagina_atual - 1):
                            if not self.navigation.avancar_para_proxima_pagina(contratos_url, pagina_atual):
                                break
                    except Exception:
                        logger.warning("Falha ao tentar restaurar a página de contratos após erro.")

            if not self.navigation.avancar_para_proxima_pagina(contratos_url, pagina_atual):
                break

            pagina_atual += 1

    def _tentar_novamente_falhados(self, contratos_falhados, callback_processamento, contratos_url, max_tentativas: int):
        contratos_nao_processados = list(contratos_falhados)
        for tentativa in range(max_tentativas):
            if not contratos_nao_processados:
                return
            contratos_restantes = []
            self.driver.get(contratos_url)
            self.navigation.aguardar_renderizacao_contratos()
            for contrato_numero in contratos_nao_processados:
                try:
                    self._processar_contrato_unico(contrato_numero, callback_processamento)
                except Exception:
                    contratos_restantes.append(contrato_numero)
            contratos_nao_processados = contratos_restantes

    def _processar_contrato_unico(self, numero_contrato, callback_processamento: Callable[[str], Any]):
        while True:
            try:
                self.navigation.aguardar_renderizacao_contratos()
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
                        self.json_logger.registrar_falha_claro(dados_falha)
                        self.navigation.voltar_para_pagina_contratos(self.driver.current_url)
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

                    self.navigation.voltar_para_pagina_contratos(self.driver.current_url)
                    return

            if not self.navigation.avancar_para_proxima_pagina():
                raise NoSuchElementException(f"Contrato {numero_contrato} não encontrado.")
