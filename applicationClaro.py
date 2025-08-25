# application.py

import logging
import os
from dotenv import load_dotenv

from pages.loginClaro import LoginPage
from pages.faturaClaro import FaturaPage
from pages.faturasPendentes import FaturasPendentesPage
from utils.downloadFaturaClaro import DownloadService
from utils.downloadUtils import garantir_diretorio
from utils.driver.driverFactoryClaro import configurar_driver_chrome
from utils.popUpVivo import tratar_popup_cookies

logger = logging.getLogger(__name__)

class ClaroAutomationApp:
    def __init__(self):
        load_dotenv()
        self.driver = None
        self.USUARIO_CLARO = os.getenv("USUARIO_CLARO")
        self.SENHA_CLARO = os.getenv("SENHA_CLARO")
        self.LOGIN_URL = os.getenv("LOGIN_URL")
        self.CONTRATOS_URL = os.getenv("CONTRATOS_URL")

        self.LINUX_DOWNLOAD_DIR = os.getenv("LINUX_DOWNLOAD_DIR")
        self.WINDOWS_DOWNLOAD_DIR = os.getenv("WINDOWS_DOWNLOAD_DIR")
        self.USER_DATA_DIR = os.getenv("CHROME_USER_DATA_DIR")
        self.PROFILE_DIRECTORY = os.getenv("CHROME_PROFILE_DIRECTORY")

        self.download_dir = self.LINUX_DOWNLOAD_DIR if os.name == 'posix' else self.WINDOWS_DOWNLOAD_DIR
        garantir_diretorio(self.download_dir)

    def _setup_driver(self):
        try:
            self.driver = configurar_driver_chrome(
                user_data_dir=self.USER_DATA_DIR,
                profile_directory=self.PROFILE_DIRECTORY,
                download_dir=self.download_dir
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao configurar o driver: {e}", exc_info=True)
            return False

    def _login(self):
        login_page = LoginPage(self.driver, self.LOGIN_URL)
        login_page.open_login_page()

        if not login_page.esta_logado():
            logger.info("Usuário não está logado. Iniciando login...")
            login_page.click_entrar()
            login_page.selecionar_minha_claro_residencial()
            tratar_popup_cookies(self.driver)
            login_page.preencher_login_usuario(self.USUARIO_CLARO)
            login_page.clicar_continuar()
            login_page.preencher_senha(self.SENHA_CLARO)
            login_page.clicar_botao_acessar()
        else:
            logger.info("Sessão já ativa, pulando login.")
            tratar_popup_cookies(self.driver)

    def _process_contracts(self):
        fatura_page = FaturaPage(self.driver)
        faturas_pendentes_page = FaturasPendentesPage(self.driver)
        download_service = DownloadService(self.driver, faturas_pendentes_page)

        def download_faturas_callback(numero_contrato: str):
            download_service.baixar_faturas(numero_contrato, self.LINUX_DOWNLOAD_DIR, self.WINDOWS_DOWNLOAD_DIR)

        fatura_page.processar_todos_contratos_ativos(download_faturas_callback, self.CONTRATOS_URL)

    def run(self):
        if not self._setup_driver():
            return

        try:
            logger.info("Iniciando o processo de login...")
            self._login()

            logger.info("Iniciando o processo de download de faturas...")
            self._process_contracts()
            
        except Exception as e:
            logger.error(f"Erro geral na execução: {e}", exc_info=True)
        finally:
            input("⏸ Pressione Enter para encerrar...")
            if self.driver:
                self.driver.quit()