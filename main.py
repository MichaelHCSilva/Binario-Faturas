# main.py

from dotenv import load_dotenv
import os
import time

from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException, TimeoutException

from utils.driverFactory import create_driver
from pages.loginPage import LoginPage
from pages.homePage import HomePage
from customer_selector.customerSelectorPage import CustomerSelectorPage
from customer_selector.cnpjLogger import CnpjLogger
from utils.faturasDownloader import download_all_paginated_invoices
from utils.popUpHandler import PopupHandler  # ✅ Novo

def main():
    load_dotenv()

    usuario = os.getenv("LOGIN_USUARIO")
    senha = os.getenv("LOGIN_SENHA")

    if not usuario or not senha:
        print("LOGIN_USUARIO ou LOGIN_SENHA não encontrados no .env")
        return

    pasta_download_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faturas")
    driver = None

    try:
        driver = create_driver(pasta_download_base)
        print("Driver criado, iniciando execução.")

        popup_handler = PopupHandler(driver)  # ✅ Criando handler do popup

        print("Realizando login...")
        login_page = LoginPage(driver)
        login_page.open_login_page()
        login_page.perform_login(usuario, senha)
        print("Login realizado com sucesso.")

        print("Iniciando processamento de CNPJs...")
        customer_selector = CustomerSelectorPage(driver)
        cnpj_logger = CnpjLogger()

        customer_selector.open_menu()
        cnpj_list = customer_selector.get_cnpjs()

        if not cnpj_list:
            print("NENHUM CNPJ encontrado na lista. Abortando.")
            customer_selector.close_menu()
            return

        print(f"Encontrados {len(cnpj_list)} CNPJs para processar: {cnpj_list}")

        for cnpj_atual in cnpj_list:
            print(f"\n--- Processando CNPJ: {cnpj_atual} ---")

            popup_handler.force_remove_qualtrics_popup()  # ✅ Antes da tentativa de clicar

            if not customer_selector.click_by_text(cnpj_atual):
                print(f"Não foi possível selecionar o CNPJ {cnpj_atual}. Pulando para o próximo.")

                try:
                    customer_selector.open_menu()
                except TimeoutException:
                    print("Timeout ao tentar reabrir a lista de CNPJs. Tentando continuar...")

                continue

            cnpj_logger.registrar(cnpj_atual)
            print(f"CNPJ registrado no log: {cnpj_atual}")

            home_page = HomePage(driver)

            popup_handler.force_remove_qualtrics_popup()  # ✅ Antes de verificar faturas

            if not home_page.verificar_opcao_acessar_faturas():
                print(f"CNPJ {cnpj_atual} não possui opção 'Acessar faturas'. Pulando para o próximo.")
                driver.back()
                time.sleep(2)
                customer_selector.open_menu()
                continue

            popup_handler.force_remove_qualtrics_popup()  # ✅ Antes de tentar acessar faturas

            home_page.acessar_faturas()

            print("Aguardando página de faturas carregar...")
            time.sleep(3)

            print("Iniciando download das faturas...")
            # ✅ Ajustado: passa popup_handler como argumento
            download_all_paginated_invoices(driver, popup_handler, pasta_download_base, cnpj_atual)

            print("Pausando para garantir finalização do download e navegação de volta...")
            time.sleep(5)

            driver.back()
            time.sleep(2)
            customer_selector.open_menu()

    except (Exception, InvalidSessionIdException) as e:
        print(f"Erro inesperado na execução: {e}")
        if isinstance(e, InvalidSessionIdException):
            print("A sessão do navegador foi encerrada inesperadamente. Verifique a estabilidade da conexão e os recursos do sistema.")

    finally:
        if driver:
            input("Pressione Enter para sair e fechar o navegador...")
            driver.quit()
            print("Navegador fechado, script finalizado.")

if __name__ == "__main__":
    main()
