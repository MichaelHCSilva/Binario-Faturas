# customer_invoice_processor_vivo.py
import os
import time
import logging
from datetime import datetime
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from pages.claro.claro_home_page import HomePage
from pages.vivo.customer_selector_page_vivo import CustomerSelectorPage
from services.vivo_invoice_download_service import download_all_paginated_invoices
from utils.session_manager_vivo import ensure_logged_in
from utils.json_failure_logger import JsonFailureLogger


def process_customers(driver, popup_manager, login_page, usuario, senha, pasta_download_base, skip_existing=True):
    customer_selector = CustomerSelectorPage(driver)
    customer_selector.open_menu()
    cnpjs = customer_selector.get_cnpjs()

    if not cnpjs:
        logging.warning("Nenhum CNPJ encontrado.")
        customer_selector.close_menu()
        return

    json_logger = JsonFailureLogger()

    for cnpj_atual in cnpjs:
        logging.info(f"--- Processando CNPJ: {cnpj_atual} ---\n")
        tentativas = 0
        sucesso = False
        ultimo_erro = None

        while tentativas < 3 and not sucesso:
            try:
                popup_manager.handle_all()

                if ensure_logged_in(driver, login_page, usuario, senha):
                    customer_selector.open_menu()
                    continue

                if not customer_selector.click_by_text(cnpj_atual):
                    tentativas += 1
                    ultimo_erro = f"Não foi possível selecionar {cnpj_atual}. Tentativa {tentativas}"
                    logging.warning(ultimo_erro)

                    time.sleep(2)
                    try:
                        customer_selector.open_menu()
                    except TimeoutException:
                        logging.warning("Timeout ao tentar reabrir a lista de CNPJs.")
                    continue

                home_page = HomePage(driver)
                popup_manager.handle_all()

                if not home_page.verificar_opcao_acessar_faturas():
                    ultimo_erro = f"{cnpj_atual} não possui opção 'Acessar faturas'. Avançando..."
                    logging.info(ultimo_erro)

                    driver.back()
                    time.sleep(2)
                    customer_selector.open_menu()
                    tentativas += 1
                    continue

                popup_manager.handle_all()
                home_page.acessar_faturas()
                time.sleep(2)

                download_all_paginated_invoices(
                    driver=driver,
                    popup_manager=popup_manager,
                    download_dir=pasta_download_base,
                    base_folder=pasta_download_base,
                    cnpj=cnpj_atual,
                    login_page=login_page,
                    usuario=usuario,
                    senha=senha,
                    skip_existing=skip_existing
                )

                time.sleep(2)
                driver.back()
                time.sleep(2)
                customer_selector.open_menu()
                sucesso = True

            except Exception as e:
                import traceback
                if isinstance(e, TimeoutException):
                    erro_msg = "Tempo limite ao aguardar a página ou elemento."
                    logging.error(f"Erro processando {cnpj_atual}: {erro_msg}")
                elif isinstance(e, NoSuchElementException):
                    erro_msg = "Elemento esperado não foi encontrado na página."
                    logging.error(f"Erro processando {cnpj_atual}: {erro_msg}")
                elif isinstance(e, WebDriverException):
                    erro_msg = "Problema de comunicação com o navegador."
                    logging.error(f"Erro processando {cnpj_atual}: {erro_msg}")
                else:
                    erro_msg = "Erro inesperado."
                    logging.error(f"Erro processando {cnpj_atual}: {erro_msg}")

                logging.debug(traceback.format_exc())

                tentativas += 1
                ultimo_erro = erro_msg
                time.sleep(3)

        if not sucesso:
            if not ultimo_erro:
                ultimo_erro = f"Falha após 3 tentativas no CNPJ {cnpj_atual}. Avançando para o próximo."
            else:
                ultimo_erro = f"Falha após 3 tentativas no CNPJ {cnpj_atual}. Último erro: {ultimo_erro}"

            logging.warning(ultimo_erro)

            dados_falha = {
                "cnpj": cnpj_atual,
                "tentativa": tentativas,
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "erro": ultimo_erro
            }
            json_logger.registrar_falha_vivo(dados_falha)
