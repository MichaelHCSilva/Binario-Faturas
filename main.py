import logging
import os
from dotenv import load_dotenv

# Importa as classes de automação
from applicationVivo import ApplicationVivo
from applicationClaro import ClaroAutomationApp

def main():
    load_dotenv()  # caso precise variáveis de ambiente

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # Escolha de execução: Vivo e depois Claro (sequencial)
    logging.info("Iniciando automação Vivo...")
    vivo_app = ApplicationVivo()
    vivo_app.run()
    logging.info("Automação Vivo finalizada.\n")

    logging.info("Iniciando automação Claro...")
    claro_app = ClaroAutomationApp()
    claro_app.run()
    logging.info("Automação Claro finalizada.\n")

if __name__ == "__main__":
    main()
