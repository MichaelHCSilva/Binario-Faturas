import re
import pdfplumber
from datetime import datetime

def extrair_vivo(pdf_path: str) -> dict:
    dados = {
        "operadora": "VIVO",
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
            texto += pagina.extract_text() + "\n"

    linhas = texto.splitlines()

    for linha in linhas:
        if "Número da Conta:" in linha:
            dados["numero_contrato"] = linha.split("Número da Conta:")[1].strip()
            break

    for linha in linhas:
        if re.search(r"Telefônica|Vivo", linha, re.IGNORECASE):
            dados["nome_fornecedor"] = linha.strip()
            break

    for linha in linhas:
        if "Número da Fatura:" in linha:
            dados["numero_fatura"] = linha.split("Número da Fatura:")[1].strip()
            break

    for linha in linhas:
        if "Data de Emissão:" in linha:
            try:
                dados["data_emissao"] = datetime.strptime(
                    linha.split("Data de Emissão:")[1].strip(), "%d/%m/%Y"
                ).date()
            except:
                pass

    match_venc = re.search(r"VENCIMENTO\s*(\d{2}/\d{2}/\d{4})", texto, re.IGNORECASE)
    if match_venc:
        dados["data_vencimento"] = datetime.strptime(match_venc.group(1), "%d/%m/%Y").date()

    match_total = re.search(r"TOTAL GERAL\s*([\d.,]+)", texto, re.IGNORECASE)
    if match_total:
        dados["valor_total"] = float(match_total.group(1).replace(".", "").replace(",", "."))

    match_multa = re.search(r"(\d+)% de multa", texto)
    if match_multa:
        dados["valores_multa"] = match_multa.group(1) + "%"

    match_juros = re.search(r"(\d+)% de juros ao mês", texto)
    if match_juros:
        dados["valores_juros"] = match_juros.group(1) + "% ao mês"

    match_cb = re.search(r"(\d{44})", texto.replace(" ", ""))
    if match_cb:
        dados["codigo_barras"] = match_cb.group(1)

    forma_pagamento = None
    for linha in linhas:
        if "DÉBITO AUTOMÁTICO" in linha.upper():
            forma_pagamento = "Débito Automático"
            match_banco = re.search(r"Banco\s+(\w+)", linha, re.IGNORECASE)
            if match_banco:
                forma_pagamento += f" ({match_banco.group(1).title()})"
            break

    if forma_pagamento:
        dados["forma_pagamento"] = forma_pagamento
    elif dados["codigo_barras"]:
        dados["forma_pagamento"] = f"Boleto (código de barras: {dados['codigo_barras']})"

    cnpjs = re.findall(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto)
    if cnpjs:
        dados["numero_cnpj"] = cnpjs[0]

    match_nf = re.search(r"NFFST:\s*(\S+)", texto)
    if match_nf:
        dados["numero_nf"] = match_nf.group(1)
    else:
        match_nf2 = re.search(r"N[º°]?\s*NFCOM\s+(\d+)", texto, re.IGNORECASE)
        if match_nf2:
            dados["numero_nf"] = match_nf2.group(1)

    match_serie = re.search(r"Série:\s*(\S+)", texto, re.IGNORECASE)
    if match_serie:
        dados["numero_serie"] = match_serie.group(1)
    else:
        match_serie2 = re.search(r"S[ÉE]RIE\s+(\d+)", texto, re.IGNORECASE)
        if match_serie2:
            dados["numero_serie"] = match_serie2.group(1)

    match_valor_nf = re.search(r"TOTAL GERAL NOTA FISCAL\s*([\d.,]+)", texto)
    if match_valor_nf:
        dados["valor_nf"] = float(match_valor_nf.group(1).replace(".", "").replace(",", "."))
    else:
        match_valor_nf2 = re.search(r"VALOR TOTAL NF\s*([\d.,]+)", texto, re.IGNORECASE)
        if match_valor_nf2:
            dados["valor_nf"] = float(match_valor_nf2.group(1).replace(".", "").replace(",", "."))

    match_base_icms = re.search(r"Base de Cálculo:\s*R\$ ([\d.,]+)", texto)
    if match_base_icms:
        dados["base_calculo_icms"] = float(match_base_icms.group(1).replace(".", "").replace(",", "."))
    else:
        match_base_icms2 = re.search(r"BASE DE C[ÁA]LCULO\s*([\d.,]+)", texto, re.IGNORECASE)
        if match_base_icms2:
            dados["base_calculo_icms"] = float(match_base_icms2.group(1).replace(".", "").replace(",", "."))

    match_aliquota = re.search(r"ICMS:\s*(\d+)%", texto)
    if match_aliquota:
        dados["valor_aliquota"] = match_aliquota.group(1) + "%"
    else:
        match_aliquota2 = re.search(r"(\d{1,2},\d{2}%)", texto)
        if match_aliquota2:
            dados["valor_aliquota"] = match_aliquota2.group(1)

    match_valor_icms = re.search(r"Valor ICMS:\s*R\$ ([\d.,]+)", texto)
    if match_valor_icms:
        dados["valor_icms"] = float(match_valor_icms.group(1).replace(".", "").replace(",", "."))
    else:
        match_valor_icms2 = re.search(r"VALOR ICMS\s*([\d.,]+)", texto, re.IGNORECASE)
        if match_valor_icms2:
            dados["valor_icms"] = float(match_valor_icms2.group(1).replace(".", "").replace(",", "."))

    return dados
