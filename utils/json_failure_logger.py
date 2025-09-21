import os
import json
import logging

logger = logging.getLogger(__name__)

class JsonFailureLogger:
    def __init__(self, pasta_faturas: str):
        self.json_path = os.path.join(pasta_faturas, "contratos_falhados.json")
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Erro ao criar arquivo JSON inicial de falhas: {e}")

    def registrar_falha(self, dados_falha: dict):
        try:
            falhas_existentes = []
            if os.path.exists(self.json_path):
                with open(self.json_path, "r", encoding="utf-8") as f:
                    falhas_existentes = json.load(f) or []
            falhas_existentes.append(dados_falha)
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(falhas_existentes, f, ensure_ascii=False, indent=4)
            logger.info(f"Falha registrada no JSON: {dados_falha}")
        except Exception as e:
            logger.error(f"Erro ao registrar falha em JSON: {e}")
