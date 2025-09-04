import logging
import os
from dotenv import load_dotenv
from selenium.common.exceptions import TimeoutException, WebDriverException

from pages.claro.claro_login_page import LoginPage
from pages.claro.claro_invoice_page import FaturaPage
from pages.claro.claro_pending_invoices_page import FaturasPendentesPage
from services.claro_invoice_download_service import DownloadService
from utils.download_utils import garantir_diretorio
from utils.driver.claro_chrome_driver import configurar_driver_chrome
from utils.popup_manager import PopupManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class ClaroAutomationApp:
    def __init__(self):
        load_dotenv()
        self.driver = None
        self.USUARIO_CLARO = os.getenv("USUARIO_CLARO")
        self.SENHA_CLARO = os.getenv("SENHA_CLARO")
        self.CLARO_LOGIN_URL = os.getenv("CLARO_LOGIN_URL")
        self.CONTRATOS_URL = os.getenv("CONTRATOS_URL")

        self.LINUX_DOWNLOAD_DIR = os.getenv("LINUX_DOWNLOAD_DIR")
        self.USER_DATA_DIR = os.getenv("CHROME_USER_DATA_DIR")
        self.PROFILE_DIRECTORY = os.getenv("CHROME_PROFILE_DIRECTORY")

        self.claro_base_folder = os.path.join(self.LINUX_DOWNLOAD_DIR, "Claro")
        garantir_diretorio(self.claro_base_folder)

    def _setup_driver(self):
        try:
            self.driver = configurar_driver_chrome(
                user_data_dir=self.USER_DATA_DIR,
                profile_directory=self.PROFILE_DIRECTORY,
                download_dir=self.claro_base_folder
            )
            self.driver.set_page_load_timeout(70)
            return True
        except WebDriverException as e:
            logger.error(f"Erro ao configurar o driver: {type(e).__name__} - {e}", exc_info=True)
            return False

    def _login(self):
        login_page = LoginPage(self.driver, self.CLARO_LOGIN_URL)
        popup_manager = PopupManager(self.driver, timeout=2)
        
        try:
            login_page.open_login_page(retries=3)
        except Exception as e:
            logger.error(f"Falha ao abrir a página de login: {type(e).__name__} - {e}", exc_info=True)
            return

        popup_manager.handle_all()

        if login_page.esta_logado():
            logger.info("Sessão já ativa, pulando login.")
            return

        logger.info("Usuário não está logado. Iniciando login...")

        try:
            login_page.click_entrar()
            login_page.selecionar_minha_claro_residencial()
        except Exception as e:
            logger.error(f"Erro ao iniciar login: {type(e).__name__} - {e}", exc_info=True)
            return

        popup_manager.handle_all()

        try:
            login_page.preencher_login_usuario(self.USUARIO_CLARO)
            login_page.clicar_continuar()
            login_page.preencher_senha(self.SENHA_CLARO)
            login_page.clicar_botao_acessar()
        except Exception as e:
            logger.error(f"Erro ao preencher login/senha e acessar: {type(e).__name__} - {e}", exc_info=True)
            return

        if login_page.esta_logado():
            logger.info("Login realizado com sucesso.")
        else:
            logger.error("Falha: login não foi concluído mesmo após preencher usuário e senha.")

    def _process_contracts(self):
        fatura_page = FaturaPage(self.driver, self.claro_base_folder)
        faturas_pendentes_page = FaturasPendentesPage(self.driver)
        download_service = DownloadService(self.driver, faturas_pendentes_page)
        popup_manager = PopupManager(self.driver, timeout=2) 
        
        def download_faturas_callback(numero_contrato: str):
            try:
                arquivos_baixados = download_service.baixar_faturas(
                    numero_contrato,
                    self.claro_base_folder,
                    self.claro_base_folder
                )
                return arquivos_baixados
            except Exception as e:
                logger.error(
                    f"Erro ao baixar faturas do contrato {numero_contrato}: {type(e).__name__} - {e}",
                    exc_info=True
                )
                return []

        fatura_page.processar_todos_contratos_ativos(
            callback_processamento=download_faturas_callback,
            contratos_url=self.CONTRATOS_URL
        )

    def run(self):
        if not self._setup_driver():
            return

        try:
            logger.info("Iniciando o processo de login...")
            self._login()

            logger.info("Iniciando o processo de download de faturas...")
            self._process_contracts()

        except Exception as e:
            logger.error(f"Erro geral na execução: {type(e).__name__} - {e}", exc_info=True)
        finally:
            input("⏸ Pressione Enter para encerrar...")
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning(f"Erro ao encerrar driver: {type(e).__name__} - {e}")
