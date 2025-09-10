import os
import uuid
import pdfplumber
import logging
import traceback
from datetime import datetime, timezone
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from config.database_engine import engine, Session
from models.invoice_model import Fatura
from extractors.claro.claro_invoice_extractor import extrair_claro
from extractors.vivo.vivo_invoice_extractor import extrair_vivo

logger = logging.getLogger(__name__)

Session = sessionmaker(bind=engine)

class FaturaService:
    def __init__(self, pasta_faturas: str):
        self.pasta_faturas = pasta_faturas
        self.session = Session()

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
        try:
            existente = self.session.query(Fatura).filter_by(
                numero_fatura=dados.get("numero_fatura"),
                numero_contrato=dados.get("numero_contrato"),
                numero_cnpj=dados.get("numero_cnpj") 
            ).first()

            if existente:
                return "existente"

            nova_fatura = Fatura(
                id=uuid.uuid4(),
                operadora=dados.get("operadora"),
                numero_contrato=dados.get("numero_contrato"),
                nome_fornecedor=dados.get("nome_fornecedor"),
                valor_total=dados.get("valor_total"),
                valores_multa=dados.get("valores_multa"),
                valores_juros=dados.get("valores_juros"),
                valores_retencoes=dados.get("valores_retencoes"),
                forma_pagamento=dados.get("forma_pagamento"),
                numero_cnpj=dados.get("numero_cnpj"),
                numero_nf=dados.get("numero_nf"),
                numero_serie=dados.get("numero_serie"),
                data_emissao=dados.get("data_emissao"),
                valor_nf=dados.get("valor_nf"),
                base_calculo_icms=dados.get("base_calculo_icms"),
                valor_aliquota=dados.get("valor_aliquota"),
                valor_icms=dados.get("valor_icms"),
                data_vencimento=dados.get("data_vencimento"),
                data_contabil=dados.get("data_contabil"),
                numero_fatura=dados.get("numero_fatura"),
                created_at=datetime.now(timezone.utc)
            )

            self.session.add(nova_fatura)
            self.session.commit()
            return "ok"

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Erro ao salvar fatura: {e}", exc_info=True)
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
                logger.warning(f"Nenhuma fatura extraída de {os.path.basename(caminho_pdf)}.")
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
                        "cnpj_fornecedor": dados.get("numero_cnpj"),
                        "erro": resultado
                    })

        except Exception:
            falhas.append({
                "numero_fatura": None,
                "numero_contrato": None,
                "cnpj_fornecedor": None,
                "erro": traceback.format_exc()
            })
        
        return {"inseridas": inseridas, "existentes": existentes, "falhas": falhas}

    def processar_todas_faturas_na_pasta(self):
        arquivos_pdf = [f for f in os.listdir(self.pasta_faturas) if f.lower().endswith('.pdf')]

        if not arquivos_pdf:
            logger.info("Nenhum arquivo PDF encontrado na pasta.")
            return

        total_inseridas = 0
        total_existentes = 0
        total_falhas = []

        logger.info(f"Iniciando processamento de {len(arquivos_pdf)} arquivo(s) PDF...")

        for arquivo in arquivos_pdf:
            caminho_completo = os.path.join(self.pasta_faturas, arquivo)
            resultado = self.processar_fatura_pdf(caminho_completo)

            total_inseridas += resultado["inseridas"]
            total_existentes += resultado["existentes"]
            if resultado["falhas"]:
                total_falhas.extend(resultado["falhas"])

        if not total_falhas:
            logger.info("Todas as faturas foram processadas com sucesso.")
        else:
            mensagem = (
                f"Processamento concluído: {total_inseridas} faturas inseridas, "
                f"{total_existentes} já existiam, {len(total_falhas)} falharam.\n"
            )
            for f in total_falhas:
                mensagem += (
                    f"   - Fatura: numero_fatura={f.get('numero_fatura', 'N/A')}, "
                    f"numero_contrato={f.get('numero_contrato', 'N/A')}, "
                    f"CNPJ={f.get('cnpj_fornecedor', 'N/A')}, erro={f['erro']}\n"
                )
            logger.warning(mensagem)
