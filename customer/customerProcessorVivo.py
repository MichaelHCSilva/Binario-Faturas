import time
from selenium.common.exceptions import TimeoutException
from pages.homePage import HomePage
from customer.customerSelectorVivo import CustomerSelectorPage
from customer.cnpjLogger import CnpjLogger
from utils.downloadFaturaVivo import download_all_paginated_invoices
from utils.sessionManager import ensure_logged_in


def process_customers(driver, popup_handler, login_page, usuario, senha, pasta_download_base):
    customer_selector = CustomerSelectorPage(driver)
    cnpj_logger = CnpjLogger()

    customer_selector.open_menu()
    cnpjs = customer_selector.get_cnpjs()
    if not cnpjs:
        print("Nenhum CNPJ encontrado. Abortando.")
        customer_selector.close_menu()
        return

    print(f"Encontrados {len(cnpjs)} CNPJs: {cnpjs}")

    for cnpj_atual in cnpjs:
        print(f"\n--- Processando CNPJ: {cnpj_atual} ---")
        tentativas = 0
        sucesso = False

        while tentativas < 3 and not sucesso:
            try:
                popup_handler.force_remove_qualtrics_popup()

                if ensure_logged_in(driver, login_page, usuario, senha):
                    customer_selector.open_menu()
                    continue

                if not customer_selector.click_by_text(cnpj_atual):
                    print(f"Não foi possível selecionar {cnpj_atual}. Tentativa {tentativas+1}")
                    tentativas += 1
                    time.sleep(2)
                    try:
                        customer_selector.open_menu()
                    except TimeoutException:
                        print("Timeout ao tentar reabrir a lista de CNPJs.")
                    continue

                cnpj_logger.registrar(cnpj_atual)
                print(f"CNPJ registrado: {cnpj_atual}")

                home_page = HomePage(driver)
                popup_handler.force_remove_qualtrics_popup()

                if not home_page.verificar_opcao_acessar_faturas():
                    print(f"{cnpj_atual} não possui 'Acessar faturas'. Pulando...")
                    driver.back()
                    time.sleep(2)
                    customer_selector.open_menu()
                    tentativas += 1
                    continue

                popup_handler.force_remove_qualtrics_popup()
                home_page.acessar_faturas()
                time.sleep(3)

                download_all_paginated_invoices(driver, popup_handler, pasta_download_base, cnpj_atual)

                time.sleep(2)
                driver.back()
                time.sleep(2)
                customer_selector.open_menu()

                sucesso = True

            except Exception as e:
                print(f"Erro processando {cnpj_atual}: {e}")
                tentativas += 1
                time.sleep(3)

        if not sucesso:
            print(f"Falha após 3 tentativas no CNPJ {cnpj_atual}. Pulando para o próximo.")
