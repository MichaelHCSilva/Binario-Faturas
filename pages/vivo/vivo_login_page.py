import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class LoginPageVivo:
    def __init__(self, driver, login_url: str, timeout=15):
        self.driver = driver
        self.url = login_url
        self.wait = WebDriverWait(driver, timeout)
        self.driver.set_page_load_timeout(40)

    def open_login_page(self, retries=2):
        for attempt in range(retries):
            try:
                start = time.time()
                self.driver.get(self.url)
                self.wait.until(EC.presence_of_element_located((By.ID, "login-input")))
                break
            except (TimeoutException, WebDriverException) as e:
                logger.warning(f"Erro ao abrir página Vivo (tentativa {attempt+1}/{retries}): {e}")
                if attempt == retries - 1:
                    logger.error("Falha ao abrir página de login Vivo após múltiplas tentativas.", exc_info=True)
                    raise

    def preencher_usuario(self, usuario: str):
        try:
            campo = self.wait.until(EC.visibility_of_element_located((By.ID, "login-input")))
            campo.clear()
            campo.send_keys(usuario)
        except Exception as e:
            logger.error(f"Erro ao preencher usuário Vivo: {e}", exc_info=True)

    def clicar_continuar(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test-access-button]")))
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password'][name='password']")))         
        except Exception as e:
            logger.error(f"Erro ao clicar em 'Continuar' (Vivo): {e}", exc_info=True)

    def preencher_senha(self, senha: str):
        try:
            campo_senha = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password'][name='password']")))
            campo_senha.clear()
            campo_senha.send_keys(senha)
        except Exception as e:
            logger.error(f"Erro ao preencher senha Vivo: {e}", exc_info=True)

    def clicar_login(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and @data-test-access-button]")))
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("Login com sucesso (Vivo).")
        except Exception as e:
            logger.error(f"Erro ao clicar em 'Entrar' (Vivo): {e}", exc_info=True)

    def perform_login(self, usuario: str, senha: str):
        self.open_login_page()
        self.preencher_usuario(usuario)
        self.clicar_continuar()
        self.preencher_senha(senha)
        self.clicar_login()
