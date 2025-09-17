# claro_invoice_page.py
import logging, os, json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pages.claro.claro_contract_card import ContratoCard
from typing import Callable, Any
from services.invoice_service import FaturaService

logger = logging.getLogger(__name__)

class FaturaPage:
    def __init__(self, driver, pasta_faturas: str, timeout=15):
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

    def _registrar_falha(self, dados_falha):
        try:
            falhas_existentes = []
            if os.path.exists(self.json_path):
                with open(self.json_path, "r", encoding="utf-8") as f:
                    falhas_existentes = json.load(f)
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

    def _avancar_para_proxima_pagina(self) -> bool:
        try:
            next_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.mdn-Pagination-Link.mdn-Pagination-Link--next:not([disabled="disabled"])'))
            )
            self.driver.execute_script("arguments[0].click();", next_btn)
            self.wait.until(EC.staleness_of(next_btn))
            self._aguardar_renderizacao_contratos()
            return True
        except TimeoutException:
            return False

    def _voltar_para_pagina_contratos(self, contratos_url: str):
        try:
            self.driver.get(contratos_url)
            self._aguardar_renderizacao_contratos()
        except Exception:
            self.driver.get(contratos_url)
            self._aguardar_renderizacao_contratos()

    def processar_todos_contratos_ativos(self, callback_processamento: Callable[[str], Any], contratos_url: str):
        pagina_atual = 1

        while True:
            try:
                self._aguardar_renderizacao_contratos()
            except TimeoutException:
                if not self._avancar_para_proxima_pagina():
                    break
                continue

            contratos_elements = self.driver.find_elements(By.CLASS_NAME, "contract")
            for i in range(len(contratos_elements)):
                try:
                    card = ContratoCard(self.driver, self.driver.find_elements(By.CLASS_NAME, "contract")[i])
                    if card.esta_encerrado():
                        continue

                    if card.clicar_selecionar():
                        numero_contrato = card.obter_numero_contrato()
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
                                "erro": erro_callback if erro_callback else "Arquivos não gerados pelo callback"
                            }
                            self._registrar_falha(dados_falha)
                        else:
                            for arquivo in arquivos:
                                self.fatura_service.processar_fatura_pdf(
                                    os.path.join(self.fatura_service.pasta_faturas, arquivo)
                                )

                        self._voltar_para_pagina_contratos(contratos_url)
                        for _ in range(pagina_atual-1):
                            if not self._avancar_para_proxima_pagina():
                                break
                except Exception as e:
                    dados_falha = {
                        "contrato": card.obter_numero_contrato() if 'card' in locals() else "desconhecido",
                        "pagina": pagina_atual,
                        "posicao": i + 1,
                        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "erro": str(e)
                    }
                    self._registrar_falha(dados_falha)
                    self._voltar_para_pagina_contratos(contratos_url)
                    for _ in range(pagina_atual-1):
                        if not self._avancar_para_proxima_pagina():
                            break

            if not self._avancar_para_proxima_pagina():
                break
            pagina_atual += 1

    def _tentar_novamente_falhados(self, contratos_falhados, callback_processamento, contratos_url, max_tentativas):
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

    def _processar_contrato_unico(self, numero_contrato, callback_processamento):
        while True:
            try:
                self._aguardar_renderizacao_contratos()
            except TimeoutException:
                break
            for card_element in self.driver.find_elements(By.CLASS_NAME, "contract"):
                card = ContratoCard(self.driver, card_element)
                if card.obter_numero_contrato() == numero_contrato:
                    if card.clicar_selecionar():
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
                                self.fatura_service.processar_fatura_pdf(
                                    os.path.join(self.fatura_service.pasta_faturas, arquivo)
                                )

                        self._voltar_para_pagina_contratos(self.driver.current_url)
                        return
            if not self._avancar_para_proxima_pagina():
                raise NoSuchElementException(f"Contrato {numero_contrato} não encontrado.")
