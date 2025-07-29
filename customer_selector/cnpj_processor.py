import time

class CnpjProcessor:
    def __init__(self, selector, logger):
        self.selector = selector
        self.logger = logger

    def processar_todos(self, acao_por_cnpj):
        cnpjs = self.selector.listar_cnpjs_visiveis()
        print(f"{len(cnpjs)} CNPJs encontrados.") 

        for cnpj in cnpjs:
            if self.logger.ja_processado(cnpj):
                print(f"Já feito: {cnpj}")
                continue

            print(f"\nProcessando: {cnpj}")
            self.selector.abrir_lista_de_cnpjs()
            time.sleep(1)

            if self.selector.clicar_cnpj_por_texto(cnpj):
                acao_por_cnpj(cnpj)
                self.logger.registrar(cnpj)
                time.sleep(2)
