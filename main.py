from dotenv import load_dotenv
import os
import time

from utils.driver_factory import create_driver
from pages.login_page import LoginPage
from pages.home_page import HomePage
from customer_selector.customer_selector_page import CustomerSelectorPage
from customer_selector.cnpj_logger import CnpjLogger
from utils.faturas_downloader import baixar_todas_faturas_paginadas

def main():
    load_dotenv()

    usuario = os.getenv("LOGIN_USUARIO")
    senha = os.getenv("LOGIN_SENHA")

    if not usuario or not senha:
        print("❌ LOGIN_USUARIO ou LOGIN_SENHA não encontrados no .env")
        return

    driver = create_driver()
    print("🚀 Driver criado, iniciando execução.")

    try:
        print("🔑 Realizando login...")
        login_page = LoginPage(driver)
        login_page.open_login_page()
        login_page.perform_login(usuario, senha)
        print("✅ Login realizado com sucesso.")

        print("👥 Selecionando CNPJ...")
        customer_selector = CustomerSelectorPage(driver)
        cnpj_logger = CnpjLogger()

        customer_selector.abrir_lista_de_cnpjs()
        cnpj = customer_selector.clicar_primeiro_cnpj_da_lista()

        if cnpj:
            cnpj_logger.registrar(cnpj)
            print(f"✅ CNPJ registrado: {cnpj}")

            home_page = HomePage(driver)
            home_page.acessar_faturas()

            print("⏳ Aguardando página de faturas carregar...")
            time.sleep(3)

            print("📄 Iniciando download das faturas do mês atual e anterior...")
            baixar_todas_faturas_paginadas(driver)

            print("⏳ Pausando para garantir finalização do download...")
            time.sleep(3)
        else:
            print("⚠️ Nenhum CNPJ foi selecionado. Abortando operação.")

    except Exception as e:
        print(f"❌ Erro inesperado na execução: {e}")

    finally:
        input("✅ Pressione Enter para sair e fechar o navegador...")
        driver.quit()
        print("👋 Navegador fechado, script finalizado.")

if __name__ == "__main__":
    main()