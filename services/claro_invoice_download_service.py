import logging
from selenium.webdriver.support.ui import WebDriverWait
from utils.download_utils import mover_arquivo
from pages.claro.claro_pending_invoices_page import FaturasPendentesPage

logger = logging.getLogger(__name__)

class DownloadService:
    def __init__(self, driver, faturas_pendentes_page: FaturasPendentesPage, timeout=30):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.faturas_pendentes_page = faturas_pendentes_page

    def baixar_faturas(self, numero_contrato: str, linux_download_dir: str, _: str = None):
        logger.info(f"Iniciando processo de download para o contrato {numero_contrato}...")
        nome_arquivo = self.faturas_pendentes_page.selecionar_e_baixar_fatura()

        if nome_arquivo:
            logger.info(f"Nome do arquivo para download: {nome_arquivo}")
            status = mover_arquivo(nome_arquivo, linux_download_dir, numero_contrato)

            if status == "movido":
                logger.info("Download e movimento concluídos com sucesso.")
            elif status == "existia":
                logger.info("Arquivo já existia no destino. Nenhum movimento necessário.")
            elif status == "nao_encontrado":
                logger.warning("Arquivo não foi encontrado para mover.")
            else:
                logger.error("Ocorreu um erro ao mover o arquivo.")

            return [nome_arquivo]

        else:
            logger.info("Não foi possível iniciar o download da fatura. Nenhuma fatura pendente foi encontrada.")
            return []
