import time

class CnpjProcessor:
    def __init__(self, selector, logger):
        self.selector = selector
        self.logger = logger

    def processar_todos(self, acao_por_cnpj):
        cnpjs = self.selector.get_cnpjs()
        print(f"{len(cnpjs)} CNPJs encontrados.") 

        for cnpj in cnpjs:
            if self.logger.ja_processado(cnpj):
                print(f"Já feito: {cnpj}")
                continue

            print(f"\nProcessando: {cnpj}")
            self.selector.open_menu()
            time.sleep(1)

            if self.selector.click_by_text(cnpj):
                acao_por_cnpj(cnpj)
                self.logger.registrar(cnpj)
                time.sleep(2)
