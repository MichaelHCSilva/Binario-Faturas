#claro_automation_app
import logging, os, time
from dotenv import load_dotenv
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from pages.claro.claro_login_page import LoginPage
from pages.claro.claro_invoice_page import FaturaPage
from pages.claro.claro_pending_invoices_page import FaturasPendentesPage
from services.claro_invoice_download_service import DownloadService
from utils.download_utils import garantir_diretorio
from utils.driver.claro_chrome_driver import configurar_driver_chrome
from utils.popup_manager import PopupManager
from utils.session_manager_claro import ClaroSessionHandler

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

        self.session_handler = None
        self.fatura_page = None
        self.download_service = None

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
        try:
            login_page = LoginPage(self.driver, self.CLARO_LOGIN_URL)
            popup_manager = PopupManager(self.driver, timeout=2)

            logger.info("Abrindo página da Claro...")
            login_page.open_login_page()
            popup_manager.handle_all()

            WebDriverWait(self.driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(1)

            if login_page.esta_logado():
                logger.info("Sessão já ativa, pulando login.")
            else:
                logger.info("Usuário não está logado. Iniciando login...")
                login_page.perform_login(self.USUARIO_CLARO, self.SENHA_CLARO)
                popup_manager.handle_all()
                WebDriverWait(self.driver, 20).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(1)
                logger.info("Login concluído e página estabilizada.")

            self.session_handler = ClaroSessionHandler(
                self.driver, login_page, self.USUARIO_CLARO, self.SENHA_CLARO
            )

        except Exception as e:
            logger.error(f"Erro durante o login: {type(e).__name__} - {e}", exc_info=True)
            raise

    def _init_services(self):
        self.fatura_page = FaturaPage(self.driver, self.claro_base_folder)
        faturas_pendentes_page = FaturasPendentesPage(self.driver)
        self.download_service = DownloadService(self.driver, faturas_pendentes_page)

    def _process_contracts(self):
        def download_faturas_callback(numero_contrato: str):
            def action():
                return self.download_service.baixar_faturas(
                    numero_contrato,
                    self.claro_base_folder,
                    self.claro_base_folder
                )
            try:
                return self.session_handler.execute_with_session(action)
            except Exception as e:
                logger.error(
                    f"Erro ao baixar faturas do contrato {numero_contrato}: {type(e).__name__} - {e}",
                    exc_info=True
                )
                return []

        def action():
            self.fatura_page.processar_todos_contratos_ativos(
                download_faturas_callback,
                self.CONTRATOS_URL
            )

        self.session_handler.execute_with_session(action)

    def run(self):
        if not self._setup_driver():
            return

        try:
            self._login()

            self._init_services()

            self._process_contracts()
        except Exception as e:
            logger.error(f"Erro inesperado na automação Claro: {type(e).__name__} - {e}", exc_info=True)
        finally:
            input("⏸ Pressione Enter para encerrar...")
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning(f"Erro ao encerrar driver: {type(e).__name__} - {e}")
