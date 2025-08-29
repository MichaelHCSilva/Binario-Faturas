import os
import time
import logging
from selenium.common.exceptions import InvalidSessionIdException
from dotenv import load_dotenv
from utils.driver.vivo_chrome_driver import create_driver
from utils.popup_claro import PopupHandler
from pages.vivo.vivo_login_page import LoginPage
from processors.vivo.customer_invoice_processor_vivo import process_customers
from utils.session_manager import ensure_logged_in

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

    def run(self, skip_existing=True, max_login_attempts=3):
        if not self.usuario or not self.senha:
            logging.error("LOGIN_USUARIO ou LOGIN_SENHA não encontrados no .env")
            return

        try:
            self.driver = create_driver(self.pasta_download_base)
            self.popup_handler = PopupHandler(self.driver)
            self.login_page = LoginPage(self.driver)

            logging.info("Realizando login inicial...")
            self.login_page.open_login_page()
            self.login_page.perform_login(self.usuario, self.senha)

            attempt = 0
            while attempt < max_login_attempts:
                try:
                    ensure_logged_in(self.driver, self.login_page, self.usuario, self.senha)
                    break
                except Exception as e:
                    attempt += 1
                    logging.warning(f"Erro ao checar/refazer login (tentativa {attempt}): {e}")
                    time.sleep(2)
                    self.login_page.perform_login(self.usuario, self.senha)
            else:
                logging.error("Não foi possível garantir login após várias tentativas.")
                return

            process_customers(
                self.driver,
                self.popup_handler,
                self.login_page,
                self.usuario,
                self.senha,
                self.pasta_download_base,
                skip_existing=skip_existing
            )

            logging.info("Automação Vivo finalizada com sucesso.")

        except InvalidSessionIdException:
            logging.error("A sessão do navegador foi encerrada inesperadamente.")
        except Exception as e:
            import traceback
            logging.error("Erro inesperado na execução:")
            logging.error(traceback.format_exc())
        finally:
            if self.driver:
                self.driver.quit()
