import uuid
from sqlalchemy import Column, String, Numeric, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Fatura(Base):
    __tablename__ = "faturas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    operadora = Column(String(50), nullable=False)
    numero_contrato = Column(String(50), nullable=True)
    nome_fornecedor = Column(String(255), nullable=True)
    valor_total = Column(Numeric(10, 2), nullable=True)
    valores_multa = Column(String(100), nullable=True) 
    valores_juros = Column(String(100), nullable=True)  
    valores_retencoes = Column(Numeric(10, 2), nullable=True)
    forma_pagamento = Column(String(100), nullable=True)
    numero_cnpj = Column(String(20), nullable=True)
    numero_nf = Column(String(50), nullable=True)
    numero_serie = Column(String(20), nullable=True)
    data_emissao = Column(Date, nullable=True)
    valor_nf = Column(Numeric(10, 2), nullable=True)
    base_calculo_icms = Column(Numeric(10, 2), nullable=True)
    valor_aliquota = Column(String(20), nullable=True)  
    valor_icms = Column(Numeric(10, 2), nullable=True)
    data_vencimento = Column(Date, nullable=True)
    data_contabil = Column(Date, nullable=True)
    numero_fatura = Column(String(50), nullable=True)
