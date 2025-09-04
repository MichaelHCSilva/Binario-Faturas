# customer_invoice_processor_vivo.py
import os
import time
import logging
from selenium.common.exceptions import TimeoutException
from pages.claro.claro_home_page import HomePage
from pages.vivo.customer_selector_page_vivo import CustomerSelectorPage
from services.vivo_invoice_download_service import download_all_paginated_invoices
from utils.session_manager import ensure_logged_in

def process_customers(driver, popup_manager, login_page, usuario, senha, pasta_download_base, skip_existing=True):
    customer_selector = CustomerSelectorPage(driver)
    customer_selector.open_menu()
    cnpjs = customer_selector.get_cnpjs()

    if not cnpjs:
        logging.warning("Nenhum CNPJ encontrado. Abortando.")
        customer_selector.close_menu()
        return

    logging.info(f"Encontrados {len(cnpjs)} CNPJs.")

    for cnpj_atual in cnpjs:
        logging.info(f"--- Processando CNPJ: {cnpj_atual} ---")
        tentativas = 0
        sucesso = False

        while tentativas < 3 and not sucesso:
            try:
                popup_manager.handle_all()

                if ensure_logged_in(driver, login_page, usuario, senha):
                    customer_selector.open_menu()
                    continue

                if not customer_selector.click_by_text(cnpj_atual):
                    tentativas += 1
                    logging.warning(f"Não foi possível selecionar {cnpj_atual}. Tentativa {tentativas}")
                    time.sleep(2)
                    try:
                        customer_selector.open_menu()
                    except TimeoutException:
                        logging.warning("Timeout ao tentar reabrir a lista de CNPJs.")
                    continue

                home_page = HomePage(driver)
                popup_manager.handle_all()

                if not home_page.verificar_opcao_acessar_faturas():
                    logging.info(f"{cnpj_atual} não possui 'Acessar faturas'. Pulando...")
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
                logging.error(f"Erro processando {cnpj_atual}: {e}")
                logging.error(traceback.format_exc())
                tentativas += 1
                time.sleep(3)

        if not sucesso:
            logging.warning(f"Falha após 3 tentativas no CNPJ {cnpj_atual}. Pulando para o próximo.")
