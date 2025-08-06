import os

class CnpjLogger:
    def __init__(self, arquivo="cnpjs_processados.txt"):
        self.arquivo = arquivo
        self.cnpjs = set()
        if os.path.exists(self.arquivo):
            with open(self.arquivo, "r", encoding="utf-8") as f:
                self.cnpjs = {linha.strip() for linha in f if linha.strip()}

    def ja_processado(self, cnpj):
        return cnpj in self.cnpjs

    def registrar(self, cnpj):
        if not self.ja_processado(cnpj):
            with open(self.arquivo, "a", encoding="utf-8") as f:
                f.write(cnpj + "\n")
            self.cnpjs.add(cnpj)
            print(f"Registrado: {cnpj}")
