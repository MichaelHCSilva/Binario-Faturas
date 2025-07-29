from dotenv import load_dotenv
import os
import time

from utils.driver_factory import create_driver
from pages.login_page import LoginPage
from pages.home_page import HomePage
from customer_selector.customer_selector_page import CustomerSelectorPage
from customer_selector.cnpj_logger import CnpjLogger  # ✅ Certifique-se que o caminho está correto

def main():
    load_dotenv()

    usuario = os.getenv("LOGIN_USUARIO")
    senha = os.getenv("LOGIN_SENHA")

    driver = create_driver()

    try:
        # Login
        login_page = LoginPage(driver)
        login_page.open_login_page()
        login_page.perform_login(usuario, senha)

        # Seleção de CNPJ
        customer_selector = CustomerSelectorPage(driver)
        cnpj_logger = CnpjLogger()  # ✅ Instancia o logger

        customer_selector.abrir_lista_de_cnpjs()
        cnpj = customer_selector.clicar_primeiro_cnpj_da_lista()

        if cnpj:
            cnpj_logger.registrar(cnpj)  # ✅ Registra o CNPJ no arquivo
            print(f"✅ CNPJ registrado: {cnpj}")

            # Etapa seguinte: acessar faturas e baixar PDF
            home_page = HomePage(driver)
            home_page.acessar_faturas()
            time.sleep(3)
            home_page.baixar_boleto_pdf()
            time.sleep(3)
        else:
            print("⚠️ Nenhum CNPJ foi clicado.")

    finally:
        input("✅ Pressione Enter para sair e fechar o navegador...")
        driver.quit()

if __name__ == "__main__":
    main()
