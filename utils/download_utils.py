import os
import time
import shutil
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CHROME_DOWNLOAD_DIR = os.getenv("CHROME_DOWNLOAD_DIR")

def garantir_diretorio(diretorio: str) -> None:
    try:
        if not os.path.exists(diretorio):
            os.makedirs(diretorio)
            logger.info(f"Diretório criado: {diretorio}")
        else:
            logger.info(f"Diretório já existe: {diretorio}")
    except Exception as e:
        logger.error(f"Erro ao garantir diretório {diretorio}: {e}", exc_info=True)

def esperar_arquivo_download_concluido(caminho_arquivo: str, timeout: int = 30) -> bool:
    tempo_espera = 0
    intervalo_checagem = 1
    logger.info(f"Aguardando arquivo: {caminho_arquivo}")
    while tempo_espera < timeout:
        try:
            if os.path.isfile(caminho_arquivo) and not (
                os.path.exists(caminho_arquivo + ".crdownload") or
                os.path.exists(caminho_arquivo + ".part")
            ):
                logger.info(f"Arquivo {caminho_arquivo} baixado com sucesso.")
                return True
        except Exception as e:
            logger.warning(f"Erro ao verificar arquivo {caminho_arquivo}: {e}", exc_info=True)

        time.sleep(intervalo_checagem)
        tempo_espera += intervalo_checagem

    logger.warning(f"Timeout: arquivo {caminho_arquivo} não apareceu após {timeout}s.")
    return False

def mover_arquivo(nome_arquivo_original: str, destino_dir: str, numero_contrato: str) -> None:
    if CHROME_DOWNLOAD_DIR is None:
        logger.error("A variável de ambiente 'CHROME_DOWNLOAD_DIR' não foi encontrada. Verifique o seu arquivo .env.")
        return

    origem = os.path.join(CHROME_DOWNLOAD_DIR, nome_arquivo_original)
    destino = os.path.join(destino_dir, nome_arquivo_original)

    logger.info(f"Iniciando mover para arquivo: {nome_arquivo_original}")
    logger.info(f"Caminho origem: {origem}")
    logger.info(f"Caminho destino: {destino}")

    if esperar_arquivo_download_concluido(origem):
        try:
            garantir_diretorio(destino_dir)
            shutil.move(origem, destino)
            logger.info(f"Arquivo movido para {destino}")
        except Exception as e:
            logger.error(f"Erro ao mover arquivo {nome_arquivo_original}: {e}", exc_info=True)
    else:
        logger.warning(f"Arquivo {origem} não foi baixado no diretório padrão do Chrome.")
