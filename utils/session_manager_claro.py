import logging
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException

logger = logging.getLogger(__name__)

class ClaroSessionHandler:
    def __init__(self, driver, login_page, usuario, senha):
        self.driver = driver
        self.login_page = login_page
        self.usuario = usuario
        self.senha = senha

    def _is_session_active(self) -> bool:

        try:
            _ = self.driver.title
        except WebDriverException:
            logger.warning("Sessão Selenium inválida (WebDriver morreu).")
            return False

        try:
            if self.login_page.is_login_form_visible():
                logger.info("Sessão expirada, login necessário.")
                return False
        except Exception:
            return True

        return True

    def _login(self):
        logger.info("Realizando login na Claro...")
        self.login_page.login(self.usuario, self.senha)
        logger.info("Login realizado com sucesso.")

    def execute_with_session(self, action):

        try:
            if not self._is_session_active():
                self._login()
            return action()
        except (WebDriverException, TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Erro de sessão detectado ({e}), tentando refazer login...")
            self._login()
            return action()
