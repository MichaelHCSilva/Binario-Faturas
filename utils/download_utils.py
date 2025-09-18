# utils/download_utils.py
import os
import time
import shutil
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CHROME_DOWNLOAD_DIR = os.getenv("CHROME_DOWNLOAD_DIR")


def garantir_diretorio(diretorio: str) -> None:
    try:
        if not os.path.exists(diretorio):
            os.makedirs(diretorio)
            logger.info(f"Diretório criado: {diretorio}")
    except Exception as e:
        logger.error(f"Erro ao garantir diretório {diretorio}: {e}", exc_info=True)


def esperar_arquivo_dinamico(caminho_arquivo: str, intervalo_checar: float = 0.5, timeout: int = 60) -> bool:
    inicio = time.time()
    while True:
        try:
            if os.path.isfile(caminho_arquivo) and not (
                os.path.exists(caminho_arquivo + ".crdownload") or
                os.path.exists(caminho_arquivo + ".part")
            ):
                return True
        except Exception as e:
            logger.warning(f"Erro ao verificar arquivo {caminho_arquivo}: {e}", exc_info=True)

        if time.time() - inicio > timeout:
            logger.warning(f"Timeout: arquivo {caminho_arquivo} não apareceu em até {timeout}s.")
            return False

        time.sleep(intervalo_checar)


def mover_arquivo(nome_arquivo_original: str, destino_dir: str, numero_contrato: str) -> str:
    if CHROME_DOWNLOAD_DIR is None:
        logger.error(
            "A variável de ambiente 'CHROME_DOWNLOAD_DIR' não foi encontrada. Verifique o arquivo .env."
        )
        return "erro"

    origem = os.path.join(CHROME_DOWNLOAD_DIR, nome_arquivo_original)
    destino = os.path.join(destino_dir, nome_arquivo_original)

    if os.path.exists(origem) and os.path.exists(destino):
        logger.info(f"Arquivo já existe em ambos os caminhos: {origem} e {destino}. Pulando.")
        return "existia"

    if esperar_arquivo_dinamico(origem):
        try:
            garantir_diretorio(destino_dir)

            if os.path.exists(destino):
                logger.info(f"Arquivo já existe no destino: {destino}. Pulando movimento.")
                if os.path.exists(origem):
                    os.remove(origem)
                    logger.info(f"Arquivo removido do diretório de origem: {origem}")
                return "existia"

            shutil.move(origem, destino)
            return "movido"

        except Exception as e:
            logger.error(f"Erro ao mover arquivo {nome_arquivo_original}: {e}", exc_info=True)
            return "erro"
    else:
        logger.warning(
            f"Arquivo {origem} não encontrado no diretório de downloads do Chrome. Não foi possível mover."
        )
        return "nao_encontrado"
