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
            logger.info(f"Tentativa {attempt}/{retries}: abrindo página {self.url}")
            try:
                start = time.time()
                self.driver.get(self.url)
                self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[contains(@class, 'mdn-Button--primaryInverse') and .//span[text()='Entrar']]")
                    )
                )
                logger.info(f"Página de login carregada. Tempo: {time.time()-start:.2f}s")
                break
            except (TimeoutException, WebDriverException) as e:
                logger.warning(f"Timeout ou erro ao abrir a página (tentativa {attempt}/{retries}): {e}")
                if attempt == retries:
                    logger.error("Falha ao abrir a página de login após múltiplas tentativas.", exc_info=True)
                    raise
                time.sleep(2)

    def esta_logado(self):
        logger.info("Verificando se o usuário está logado...")
        short_wait = WebDriverWait(self.driver, 5)
        start = time.time()
        try:
            short_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard")))
            logger.info(f"Usuário já está logado. Tempo esperado: {time.time()-start:.2f}s")
            return True
        except TimeoutException:
            logger.info(f"Usuário não está logado. Tempo esperado: {time.time()-start:.2f}s")
            return False

    def perform_login(self, usuario: str, senha: str):
        self.open_login_page()
        self.click_entrar()
        self.selecionar_minha_claro_residencial()
        self.preencher_login_usuario(usuario)
        self.clicar_continuar()
        self.preencher_senha(senha)
        self.clicar_botao_acessar()

    def click_entrar(self):
        try:
            xpath = "//button[contains(@class, 'mdn-Button--primaryInverse') and .//span[text()='Entrar']]"
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("Botão 'Entrar' clicado com sucesso.")
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//p[text()='Minha Claro Residencial']")))
        except Exception as e:
            logger.error(f"Erro ao clicar no botão 'Entrar': {e}", exc_info=True)

    def selecionar_minha_claro_residencial(self):
        try:
            xpath = "//a[contains(@class, 'mdn-Shortcut') and .//p[text()='Minha Claro Residencial']]"
            link = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", link)
            self.driver.execute_script("arguments[0].click();", link)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="cpfCnpj"]')))
            logger.info("Selecionado 'Minha Claro Residencial'.")
        except Exception as e:
            logger.error(f"Erro ao selecionar 'Minha Claro Residencial': {e}", exc_info=True)

    def preencher_login_usuario(self, usuario: str):
        try:
            campo = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[data-testid="cpfCnpj"]')))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", campo)
            campo.clear()
            campo.send_keys(usuario)
            logger.info("Campo de usuário preenchido.")
        except Exception as e:
            logger.error(f"Erro ao preencher o campo de login: {e}", exc_info=True)

    def clicar_continuar(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='continuar']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait.until(EC.visibility_of_element_located((By.ID, "password")))
            logger.info("Botão 'Continuar' clicado.")
        except Exception as e:
            logger.error(f"Erro ao clicar no botão 'Continuar': {e}", exc_info=True)

    def preencher_senha(self, senha: str):
        try:
            campo_senha = self.wait.until(EC.visibility_of_element_located((By.ID, "password")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", campo_senha)
            campo_senha.send_keys(senha)
            logger.info("Senha preenchida.")
        except Exception as e:
            logger.error(f"Erro ao preencher a senha: {e}", exc_info=True)

    def clicar_botao_acessar(self):
        try:
            botao_acessar = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='acessar']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", botao_acessar)
            self.driver.execute_script("arguments[0].click();", botao_acessar)
            self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            logger.info("Botão 'Acessar' clicado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao clicar no botão 'Acessar': {e}", exc_info=True)
