from datetime import datetime
from sqlalchemy import MetaData, Table, Column, String, Float, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

faturas = Table(
    "faturas", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("operadora", String),
    Column("numero_contrato", String),
    Column("nome_fornecedor", String),
    Column("valor_total", Float),
    Column("valores_multa", String),
    Column("valores_juros", String),
    Column("valores_retencoes", String),
    Column("forma_pagamento", String),
    Column("numero_cnpj", String),
    Column("numero_nf", String),
    Column("numero_serie", String),
    Column("data_emissao", Date),
    Column("valor_nf", Float),
    Column("base_calculo_icms", Float),
    Column("valor_aliquota", String),
    Column("valor_icms", Float),
    Column("data_vencimento", Date),
    Column("data_contabil", Date),
    Column("numero_fatura", String),
    Column("created_at", DateTime)
)
