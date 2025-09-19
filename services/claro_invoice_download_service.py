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
        logger.info(f"Iniciando processo de download para contrato {numero_contrato}...")

        try:
            nome_arquivo = self.faturas_pendentes_page.selecionar_e_baixar_fatura()
            if not nome_arquivo:
                logger.warning("Nenhuma fatura pendente disponível para download.")
                return []

            status = mover_arquivo(nome_arquivo, linux_download_dir, numero_contrato)

            if status == "movido":
                logger.info("Download concluído.\n")
            elif status == "existia":
                logger.info("Arquivo já baixado e presente no diretório de destino.\n")
            elif status == "nao_encontrado":
                logger.warning("Falha técnica: arquivo não encontrado.\n")
            else:
                logger.error("Falha técnica: erro inesperado ao mover o arquivo.\n")

            return [nome_arquivo]

        except Exception as e:
            logger.error(f"Falha técnica durante o processo de download. Erro: {type(e).__name__}")
            return []
