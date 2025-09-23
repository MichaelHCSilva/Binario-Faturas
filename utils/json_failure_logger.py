import os
import json
import logging

logger = logging.getLogger(__name__)

class JsonFailureLogger:
    def __init__(self):
        # Obtém o caminho do diretório de downloads do env
        base_path = os.environ.get("LINUX_DOWNLOAD_DIR")
        if not base_path:
            logger.error("A variável de ambiente LINUX_DOWNLOAD_DIR não está definida.")
            raise EnvironmentError("LINUX_DOWNLOAD_DIR não definido")

        # Cria o arquivo de falhas para Claro
        self.claro_json_path = os.path.join(base_path, "claro_failures.json")
        try:
            if not os.path.exists(self.claro_json_path):
                with open(self.claro_json_path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Erro ao criar arquivo JSON inicial de falhas (Claro): {e}")

        # Cria o arquivo de falhas para Vivo
        self.vivo_json_path = os.path.join(base_path, "vivo_failures.json")
        try:
            if not os.path.exists(self.vivo_json_path):
                with open(self.vivo_json_path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Erro ao criar arquivo JSON inicial de falhas (Vivo): {e}")

    def registrar_falha_claro(self, dados_falha: dict):
        try:
            falhas_existentes = []
            if os.path.exists(self.claro_json_path):
                with open(self.claro_json_path, "r", encoding="utf-8") as f:
                    falhas_existentes = json.load(f) or []
            falhas_existentes.append(dados_falha)
            with open(self.claro_json_path, "w", encoding="utf-8") as f:
                json.dump(falhas_existentes, f, ensure_ascii=False, indent=4)
            logger.info(f"Falha registrada no JSON (Claro): {dados_falha}")
        except Exception as e:
            logger.error(f"Erro ao registrar falha em JSON (Claro): {e}")

    def registrar_falha_vivo(self, dados_falha: dict):
        try:
            falhas_existentes = []
            if os.path.exists(self.vivo_json_path):
                with open(self.vivo_json_path, "r", encoding="utf-8") as f:
                    falhas_existentes = json.load(f) or []
            falhas_existentes.append(dados_falha)
            with open(self.vivo_json_path, "w", encoding="utf-8") as f:
                json.dump(falhas_existentes, f, ensure_ascii=False, indent=4)
            logger.info(f"Falha registrada no JSON (Vivo): {dados_falha}")
        except Exception as e:
            logger.error(f"Erro ao registrar falha em JSON (Vivo): {e}")
