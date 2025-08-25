import os
from dotenv import load_dotenv
from selenium.common.exceptions import InvalidSessionIdException
from utils.driverFactory import create_driver
from utils.popUpHandler import PopupHandler
from pages.loginPage import LoginPage
from customer.customerProcessor import process_customers

class ApplicationVivo:
    def __init__(self):
        load_dotenv()
        self.usuario = os.getenv("LOGIN_USUARIO")
        self.senha = os.getenv("LOGIN_SENHA")
        self.pasta_download_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faturas")
        self.driver = None
        self.popup_handler = None
        self.login_page = None

    def run(self):
        if not self.usuario or not self.senha:
            print("LOGIN_USUARIO ou LOGIN_SENHA não encontrados no .env")
            return

        try:
            self.driver = create_driver(self.pasta_download_base)  # ✅ Passa pasta de download
            self.popup_handler = PopupHandler(self.driver)
            self.login_page = LoginPage(self.driver)

            # Login inicial
            self.login_page.open_login_page()
            self.login_page.perform_login(self.usuario, self.senha)

            # Processa todos os clientes
            process_customers(
                self.driver,
                self.popup_handler,
                self.login_page,
                self.usuario,
                self.senha,
                self.pasta_download_base
            )

        except InvalidSessionIdException:
            print("⚠️ A sessão do navegador foi encerrada inesperadamente.")
        except Exception as e:
            print(f"Erro inesperado na execução: {e}")
        finally:
            if self.driver:
                input("Pressione Enter para fechar o navegador...")
                self.driver.quit()
