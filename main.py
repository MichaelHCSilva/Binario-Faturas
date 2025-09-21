from dotenv import load_dotenv
from models.invoice_model import Base
from config.database_engine import engine
from apps.vivo_automation_app import ApplicationVivo
from apps.claro_automation_app import ClaroAutomationApp
from config.logger_config import setup_logging

load_dotenv()

logger = setup_logging()

Base.metadata.create_all(bind=engine)
logger.info("Tabela 'faturas' criada ou verificada com sucesso.")

def main():
    logger.info("Iniciando automação Vivo...\n")
    vivo_app = ApplicationVivo()
    vivo_app.run()
    logger.info("Automação Vivo finalizada.\n")

    logger.info("Iniciando automação Claro...")
    claro_app = ClaroAutomationApp()
    claro_app.run()
    logger.info("Automação Claro finalizada.\n")
        
    logger.info("Serviço de faturas concluído.")

if __name__ == "__main__":
    main()
