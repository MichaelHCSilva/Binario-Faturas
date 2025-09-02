import os
import uuid
import pdfplumber
import logging
import traceback
from datetime import datetime, timezone
from sqlalchemy import create_engine, Table, insert, select
from config.database_config import DATABASE_URL
from extractors.claro.claro_invoice_extractor import extrair_claro
from extractors.vivo.vivo_invoice_extractor import extrair_vivo

class FaturaService:
    def __init__(self, pasta_faturas: str, faturas_table: Table):
        self.pasta_faturas = pasta_faturas
        self.engine = create_engine(DATABASE_URL)
        self.faturas = faturas_table

    def identificar_operadora(self, texto: str) -> str:
        texto_lower = texto.lower()
        if "telefônica" in texto_lower or "vivo" in texto_lower:
            return "VIVO"
        if "claro" in texto_lower:
            return "CLARO"
        return "DESCONHECIDA"

    def extrair_operadora(self, operadora: str, caminho_pdf: str):
        if operadora == "CLARO":
            return extrair_claro(caminho_pdf)
        if operadora == "VIVO":
            return [extrair_vivo(caminho_pdf)]
        return []

    def ler_texto_pdf(self, caminho_pdf: str) -> str:
        texto_pdf = ""
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                t = pagina.extract_text()
                if t:
                    texto_pdf += t + "\n"
        return texto_pdf

    def salvar_fatura(self, dados: dict) -> str:
        dados["id"] = uuid.uuid4()
        dados["created_at"] = datetime.now(timezone.utc)
        if "valores_retencoes" not in dados:
            dados["valores_retencoes"] = None

        colunas = self.faturas.columns.keys()
        dados_filtrados = {k: v for k, v in dados.items() if k in colunas}

        try:
            with self.engine.begin() as conn:
                stmt_check = select(self.faturas).where(
                    self.faturas.c.numero_fatura == dados_filtrados.get("numero_fatura"),
                    self.faturas.c.numero_contrato == dados_filtrados.get("numero_contrato"),
                    self.faturas.c.numero_cnpj == dados_filtrados.get("numero_cnpj")
                )
                existe = conn.execute(stmt_check).fetchone()

                if existe:
                    return "existente"

                stmt = insert(self.faturas).values(**dados_filtrados)
                conn.execute(stmt)

            return "ok"

        except Exception as e:
            return f"erro: {str(e)}"

    def processar_fatura_pdf(self, caminho_pdf: str) -> dict:
        falhas = []
        inseridas = 0
        existentes = 0

        try:
            texto_pdf = self.ler_texto_pdf(caminho_pdf)
            operadora = self.identificar_operadora(texto_pdf)
            lista_faturas = self.extrair_operadora(operadora, caminho_pdf)

            if not lista_faturas:
                logging.warning(f"Nenhuma fatura extraída de {os.path.basename(caminho_pdf)}.")
                return {"inseridas": 0, "existentes": 0, "falhas": []}

            for dados in lista_faturas:
                resultado = self.salvar_fatura(dados)
                if resultado == "ok":
                    inseridas += 1
                elif resultado == "existente":
                    existentes += 1
                else:
                    falhas.append({
                        "numero_fatura": dados.get("numero_fatura"),
                        "numero_contrato": dados.get("numero_contrato"),
                        "numero_cnpj": dados.get("numero_cnpj"),
                        "erro": resultado
                    })

        except Exception:
            falhas.append({
                "numero_fatura": None,
                "numero_contrato": None,
                "numero_cnpj": None,
                "erro": traceback.format_exc()
            })
        
        return {"inseridas": inseridas, "existentes": existentes, "falhas": falhas}

    def processar_todas_faturas_na_pasta(self):
        total_inseridas = 0
        total_existentes = 0
        total_falhas = []
        
        arquivos_pdf = [f for f in os.listdir(self.pasta_faturas) if f.lower().endswith('.pdf')]
        
        if not arquivos_pdf:
            logging.info("Nenhum arquivo PDF encontrado na pasta.")
            return

        logging.info(f"Iniciando processamento de {len(arquivos_pdf)} arquivo(s) PDF...")

        for arquivo in arquivos_pdf:
            caminho_completo = os.path.join(self.pasta_faturas, arquivo)
            resultado = self.processar_fatura_pdf(caminho_completo)
            
            total_inseridas += resultado["inseridas"]
            total_existentes += resultado["existentes"]
            if resultado["falhas"]:
                total_falhas.extend(resultado["falhas"])

        if not total_falhas:
            logging.info("Todas as faturas foram processadas com sucesso.")
        else:
            mensagem = (
                f"Processamento concluído: {total_inseridas} faturas inseridas, "
                f"{total_existentes} já existiam, {len(total_falhas)} falharam.\n"
            )
            for f in total_falhas:
                mensagem += (
                    f"   - Fatura: numero_fatura={f.get('numero_fatura', 'N/A')}, "
                    f"numero_contrato={f.get('numero_contrato', 'N/A')}, "
                    f"CNPJ={f.get('numero_cnpj', 'N/A')}, erro={f['erro']}\n"
                )
            logging.warning(mensagem)