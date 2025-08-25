import os
from dotenv import load_dotenv
from selenium.common.exceptions import InvalidSessionIdException
from utils.driver.driverFactoryVivo import create_driver
from utils.popUpClaro import PopupHandler
from pages.loginVivo import LoginPage
from customer.customerProcessorVivo import process_customers
from utils.sessionManager import ensure_logged_in
import logging
import time

class ApplicationVivo:
    def __init__(self):
        load_dotenv()
        self.usuario = os.getenv("LOGIN_USUARIO")
        self.senha = os.getenv("LOGIN_SENHA")
        self.pasta_download_base = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "faturas"
        )
        self.driver = None
        self.popup_handler = None
        self.login_page = None

    def click_element_safe(self, element, max_attempts=3):
        attempts = 0
        while attempts < max_attempts:
            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", element
                )
                element.click()
                return True
            except Exception:
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception:
                    attempts += 1
                    time.sleep(0.5)
        return False

    def run(self):
        if not self.usuario or not self.senha:
            print("LOGIN_USUARIO ou LOGIN_SENHA não encontrados no .env")
            return

        try:
            self.driver = create_driver(self.pasta_download_base)
            self.popup_handler = PopupHandler(self.driver)
            self.login_page = LoginPage(self.driver)

            self.login_page.open_login_page()
            self.login_page.perform_login(self.usuario, self.senha)

            ensure_logged_in(self.driver, self.login_page, self.usuario, self.senha)

            process_customers(
                self.driver,
                self.popup_handler,
                self.login_page,
                self.usuario,
                self.senha,
                self.pasta_download_base
            )

            logging.info("Automação Vivo finalizada. Continuando automaticamente...")

        except InvalidSessionIdException:
            print("A sessão do navegador foi encerrada inesperadamente.")
        except Exception as e:
            print(f"Erro inesperado na execução: {e}")
        finally:
            if self.driver:
                self.driver.quit()
