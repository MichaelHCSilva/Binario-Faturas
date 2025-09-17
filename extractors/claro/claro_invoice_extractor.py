import re
import pdfplumber
from datetime import datetime

def extrair_claro(pdf_path: str) -> list:
    dados = {
        "operadora": "CLARO",
        "numero_contrato": None,
        "nome_fornecedor": None, 
        "valor_total": None,
        "valores_multa": None, 
        "valores_juros": None,
        "valores_retencoes": None,  
        "forma_pagamento": None,
        "codigo_barras": None,
        "numero_cnpj": None,  
        "numero_nf": None,    
        "numero_serie": None,
        "data_emissao": None,
        "valor_nf": None,     
        "base_calculo_icms": None,
        "valor_aliquota": None,
        "valor_icms": None,
        "data_vencimento": None,
        "data_contabil": None,
        "numero_fatura": None,
    }

    with pdfplumber.open(pdf_path) as pdf:
        texto = ""
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto += t + "\n"

    texto = re.sub(r'\s+', ' ', texto).strip()

    match_contrato = re.search(r"C[oó]digo[:\s]*(\d+/\d+)", texto, re.IGNORECASE)
    if match_contrato:
        dados["numero_contrato"] = match_contrato.group(1).strip()

    match_fatura = re.search(r"N[uú]mero[:\s]*(\d+)", texto, re.IGNORECASE)
    if match_fatura:
        dados["numero_fatura"] = match_fatura.group(1).strip()

    match_numero_nf = re.search(r"(\d{6,})\s*N[uú]mero", texto, re.IGNORECASE)
    if match_numero_nf:
        dados["numero_nf"] = match_numero_nf.group(1).strip()

    match_fornecedor = re.search(
        r"(Claro\s+NXT\s+Telecomunica[cç][oõ]es\s+S\.?A\.?)", texto, re.IGNORECASE
    )
    if match_fornecedor:
        dados["nome_fornecedor"] = match_fornecedor.group(1).strip()

    match_emissao = re.search(r"Emiss[aã]o[:\s]*(\d{2}/\d{2}/\d{4})", texto, re.IGNORECASE)
    if match_emissao:
        dados["data_emissao"] = datetime.strptime(match_emissao.group(1), "%d/%m/%Y").date()

    match_venc = re.search(r"Vencimento[:\s]*(\d{2}/\d{2}/\d{4})", texto, re.IGNORECASE)
    if match_venc:
        dados["data_vencimento"] = datetime.strptime(match_venc.group(1), "%d/%m/%Y").date()

    match_total = re.search(r"Valor total[:\s]*([\d.,]+)", texto, re.IGNORECASE)
    if match_total:
        dados["valor_total"] = float(match_total.group(1).replace(".", "").replace(",", "."))

    match_juros = re.search(r"juros\s+\w+\s+de\s+([\d.,]+)%", texto, re.IGNORECASE)
    if match_juros:
        dados["valores_juros"] = match_juros.group(1) + "% ao dia"

    match_multa = re.search(r"multa\s+de\s+([\d.,]+)%", texto, re.IGNORECASE)
    if match_multa:
        dados["valores_multa"] = match_multa.group(1) + "%"

    if "DÉBITO AUTOMÁTICO" in texto.upper():
        dados["forma_pagamento"] = "Débito Automático"

    match_cnpj = re.search(r"CNPJ[:\s]*([\d./-]+)", texto, re.IGNORECASE)
    if match_cnpj:
        dados["numero_cnpj"] = match_cnpj.group(1).strip()

    match_valor_nf = re.search(r"TOTAL\s+DA\s+NOTA\s+FISCAL[:\s]*([\d.,]+)", texto, re.IGNORECASE)
    if match_valor_nf:
        valor_nf_str = match_valor_nf.group(1).replace(".", "").replace(",", ".")
        try:
            dados["valor_nf"] = float(valor_nf_str)
        except ValueError:
            dados["valor_nf"] = None

    match_serie = re.search(r"S[EÉ]RIE[:\s]*([A-Z0-9]+)", texto, re.IGNORECASE)
    if match_serie:
        dados["numero_serie"] = match_serie.group(1).strip()

    match_icms = re.search(r"ICMS.*?Valor[:\s]*([\d.,]+)", texto, re.IGNORECASE)
    if match_icms:
        dados["valor_icms"] = float(match_icms.group(1).replace(".", "").replace(",", "."))

    match_base_icms = re.search(r"Base de C[áa]lculo[:\s]*([\d.,]+)", texto, re.IGNORECASE)
    if match_base_icms:
        dados["base_calculo_icms"] = float(match_base_icms.group(1).replace(".", "").replace(",", "."))

    match_aliquota = re.search(r"Al[ií]quota[:\s]*([\d.,]+)%", texto, re.IGNORECASE)
    if match_aliquota:
        dados["valor_aliquota"] = match_aliquota.group(1) + "%"

    dados["valores_retencoes"] = None

    return [dados]
