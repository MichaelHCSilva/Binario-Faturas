from sqlalchemy import create_engine
from config.database_config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)  