from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import Users
from pydantic import BaseModel

# Chave secreta para gerar tokens
SECRET_KEY = "chave_super_secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Configuração para encriptar senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do OAuth2 para receber tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class Registo(BaseModel):
    nome: str
    email: str
    pwd: str

class RegistoReturn(BaseModel):
    nome: str
    email: str

class LoginData(BaseModel):
    email: str
    pwd: str


def verificar_senha(senha_plana, senha_hashed):
    return pwd_context.verify(senha_plana, senha_hashed)

def gerar_senha_hashed(senha):
    return pwd_context.hash(senha)

def criar_token_acesso(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def obter_usuario_por_email(db: Session, email: str):
    return db.query(Users).filter(Users.email == email).first()

def autenticar_usuario(db: Session, email: str, senha: str):
    usuario = obter_usuario_por_email(db, email)
    if not usuario or not verificar_senha(senha, usuario.pwd):
        return None
    return usuario

def obter_usuario_logado(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return obter_usuario_por_email(db, email)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
def registar_utilizador(db, registo_data = Registo) -> RegistoReturn: 
    if db.query(Users).filter(Users.email == registo_data.email).first():
        raise HTTPException(status_code=500, detail="Este email já está associado a uma conta")

    new_user = Users(
        nome = registo_data.nome,
        email = registo_data.email,
        pwd = gerar_senha_hashed(registo_data.pwd)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user




