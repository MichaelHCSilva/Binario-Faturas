import logging
from dotenv import load_dotenv
from models.invoice_model import Base
from config.database_engine import engine
from apps.vivo_automation_app import ApplicationVivo
from apps.claro_automation_app import ClaroAutomationApp
from services.invoice_service import FaturaService
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfplumber").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # esconde SQL cru

# cria/verifica tabelas
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
                service = FaturaService(cnpj_folder)
                service.processar_todas_faturas_na_pasta()

    logging.info("\nIniciando automação Claro...")
    claro_app = ClaroAutomationApp()
    claro_app.run()
    logging.info("Automação Claro finalizada.\n")

    claro_folder = os.path.join(PASTA_FATURAS, "Claro")
    if os.path.exists(claro_folder):
        service = FaturaService(claro_folder)
        logging.info("Processando faturas Claro...")
        service.processar_todas_faturas_na_pasta()
        
    logging.info("\nServiço de faturas concluído.")

if __name__ == "__main__":
    main()
