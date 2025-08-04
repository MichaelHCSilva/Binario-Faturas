# main.py

from dotenv import load_dotenv
import os
import time

from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException, TimeoutException

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

    pasta_download_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faturas")
    driver = None
    try:
        driver = create_driver(pasta_download_base)
        print("🚀 Driver criado, iniciando execução.")

        print("🔑 Realizando login...")
        login_page = LoginPage(driver)
        login_page.open_login_page()
        login_page.perform_login(usuario, senha)
        print("✅ Login realizado com sucesso.")

        print("👥 Iniciando processamento de CNPJs...")
        customer_selector = CustomerSelectorPage(driver)
        cnpj_logger = CnpjLogger()

        customer_selector.abrir_lista_de_cnpjs()
        lista_cnpjs = customer_selector.listar_cnpjs_visiveis()
        
        if not lista_cnpjs:
            print("⚠️ NENHUM CNPJ encontrado na lista. Abortando.")
            customer_selector.fechar_lista_de_cnpjs()
            return

        print(f"✅ Encontrados {len(lista_cnpjs)} CNPJs para processar: {lista_cnpjs}")

        for cnpj_atual in lista_cnpjs:
            print(f"\n--- 🔄 Processando CNPJ: {cnpj_atual} ---")
            
            if not customer_selector.clicar_cnpj_por_texto(cnpj_atual):
                print(f"⚠️ Não foi possível selecionar o CNPJ {cnpj_atual}. Pulando para o próximo.")
                
                try:
                    customer_selector.abrir_lista_de_cnpjs()
                except TimeoutException:
                    print("⚠️ Timeout ao tentar reabrir a lista de CNPJs. Tentando continuar...")

                continue
            
            cnpj_logger.registrar(cnpj_atual)
            print(f"✅ CNPJ registrado no log: {cnpj_atual}")

            home_page = HomePage(driver)
            home_page.acessar_faturas()

            print("⏳ Aguardando página de faturas carregar...")
            time.sleep(3)

            print("📄 Iniciando download das faturas...")
            baixar_todas_faturas_paginadas(driver, pasta_download_base, cnpj_atual)
            
            print("⏳ Pausando para garantir finalização do download e navegação de volta...")
            time.sleep(5)
            
            driver.back()
            time.sleep(2)
            
            customer_selector.abrir_lista_de_cnpjs()

    except (Exception, InvalidSessionIdException) as e:
        print(f"❌ Erro inesperado na execução: {e}")
        if isinstance(e, InvalidSessionIdException):
            print("❗ A sessão do navegador foi encerrada inesperadamente. Verifique a estabilidade da conexão e os recursos do sistema.")

    finally:
        if driver:
            input("✅ Pressione Enter para sair e fechar o navegador...")
            driver.quit()
            print("👋 Navegador fechado, script finalizado.")

if __name__ == "__main__":
    main()