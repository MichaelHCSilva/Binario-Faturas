# claro_login_page.py
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class LoginPage:
    def __init__(self, driver, login_url: str, timeout=15):
        self.driver = driver
        self.url = login_url
        self.wait = WebDriverWait(driver, timeout)
        self.driver.set_page_load_timeout(40)

    def open_login_page(self, retries=3):
        for attempt in range(1, retries + 1):
            try:
                self.driver.get(self.url)
                self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[contains(@class,'mdn-Button--primaryInverse') and .//span[text()='Entrar']]")
                    )
                )
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                break
            except (TimeoutException, WebDriverException):
                if attempt == retries:
                    logger.warning("Falha técnica ao abrir página de login (tempo limite).")
                    raise
                logger.warning(f"Tentativa {attempt} falhou ao abrir página de login. Repetindo...")
                time.sleep(2)

    def esta_logado(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard"))
            )
            return True
        except TimeoutException:
            return False

    def perform_login(self, usuario: str, senha: str):
        self.open_login_page()
        self.click_entrar()
        self.selecionar_minha_claro_residencial()
        self.preencher_login_usuario(usuario)
        self.clicar_continuar()
        self.preencher_senha(senha)
        self.clicar_botao_acessar()
        
        WebDriverWait(self.driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        logger.info("Login concluído e página carregada com sucesso.")

    def click_entrar(self):
        try:
            btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(@class,'mdn-Button--primaryInverse') and .//span[text()='Entrar']]"
                ))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            logger.warning("Falha técnica ao clicar no botão 'Entrar'.")

    def selecionar_minha_claro_residencial(self):
        try:
            link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(@class,'mdn-Shortcut') and .//p[text()='Minha Claro Residencial']]"
                ))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
            self.driver.execute_script("arguments[0].click();", link)
        except Exception:
            logger.warning("Falha técnica ao selecionar 'Minha Claro Residencial'.")

    def preencher_login_usuario(self, usuario: str):
        try:
            campo = self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[data-testid="cpfCnpj"]'))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
            campo.clear()
            campo.send_keys(usuario)
        except Exception:
            logger.warning("Falha técnica ao preencher o usuário no campo de login.")

    def clicar_continuar(self):
        try:
            btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='continuar']"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            logger.warning("Falha técnica ao clicar no botão 'Continuar'.")

    def preencher_senha(self, senha: str):
        try:
            campo = self.wait.until(
                EC.visibility_of_element_located((By.ID, "password"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
            campo.send_keys(senha)
            logger.info("Senha preenchida com sucesso.")
        except Exception:
            logger.warning("Falha técnica ao preencher a senha.")

    def clicar_botao_acessar(self):
        try:
            btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='acessar']"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            logger.warning("Falha técnica ao clicar no botão 'Acessar'.")
