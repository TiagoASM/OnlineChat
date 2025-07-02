from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configuração da base de dados MySQL
DATABASE_URL = "mysql+pymysql://root:Skizzbravo1.@localhost/OnlineChat"

# Criar o motor de conexão síncrono
engine = create_engine(DATABASE_URL, echo=True)

# Criar uma sessão síncrona
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()

# Função para obter uma sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
