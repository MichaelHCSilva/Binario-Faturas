from models.modelsFatura import Base
from config.database_engine import engine

Base.metadata.create_all(bind=engine)

print("Tabela 'faturas' criada com sucesso!")
