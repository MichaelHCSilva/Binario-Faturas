import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from config.database_config import DATABASE_URL
from models.invoice_model import Base
from apps.vivo_automation_app import ApplicationVivo
from apps.claro_automation_app import ClaroAutomationApp
from services.invoice_service import FaturaService
from models.invoice_table import faturas
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfplumber").setLevel(logging.ERROR)

engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(bind=engine)
logging.info("Tabela 'faturas' criada ou verificada com sucesso.")

PASTA_FATURAS = "/mnt/c/Users/compu/OneDrive/Documentos/Binario-Faturas/faturas"

def main():
    logging.info("Iniciando automação Vivo...")
    vivo_app = ApplicationVivo()
    vivo_app.run()
    logging.info("Automação Vivo finalizada.\n")

    vivo_base = os.path.join(PASTA_FATURAS, "Vivo")
    if os.path.exists(vivo_base):
        for cnpj in os.listdir(vivo_base):
            cnpj_folder = os.path.join(vivo_base, cnpj)
            if os.path.isdir(cnpj_folder):
                logging.info(f"Processando faturas Vivo do CNPJ {cnpj}...")
                service = FaturaService(cnpj_folder, faturas)
                service.processar_todas_faturas_na_pasta()

    logging.info("\nIniciando automação Claro...")
    claro_app = ClaroAutomationApp()
    claro_app.run()
    logging.info("Automação Claro finalizada.\n")

    claro_folder = os.path.join(PASTA_FATURAS, "Claro")
    if os.path.exists(claro_folder):
        service = FaturaService(claro_folder, faturas)
        logging.info("Processando faturas Claro...")
        service.processar_todas_faturas_na_pasta()
        
    logging.info("\nServiço de faturas concluído.")

if __name__ == "__main__":
    main()