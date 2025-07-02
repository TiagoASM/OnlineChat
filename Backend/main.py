from fastapi import FastAPI, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from Controller.Auth import criar_token_acesso, autenticar_usuario, obter_usuario_logado, ACCESS_TOKEN_EXPIRE_MINUTES, Registo,registar_utilizador, LoginData
from datetime import timedelta
from database import get_db
from models import Users, ChatRequest
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
from sqlalchemy import or_, and_


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite qualquer origem (podes restringir)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    usuario = autenticar_usuario(db, data.email, data.pwd)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_acesso = criar_token_acesso({"sub": usuario.email}, token_expires)

    return {"access_token": token_acesso, "token_type": "bearer"}

@app.get("/perfil")
def perfil(usuario: Users = Depends(obter_usuario_logado)):
    return {"id": usuario.id_user, "nome": usuario.nome, "email": usuario.email}

@app.post("/registo")
def register(data_registo: Registo, db: Session = Depends(get_db)):

    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_acesso = criar_token_acesso({"sub": data_registo.email}, token_expires)
    return registar_utilizador(db, data_registo), {"access_token": token_acesso}


@app.get("/pesquisar")
def pesquisar_utilizadores(db: Session = Depends(get_db), query: str = Query(..., min_length=1)):
    users = db.query(Users).filter(Users.nome.ilike(f"%{query}%"))
    
    return [{"id": user.id_user, "nome": user.nome, "email": user.email} for user in users]

import Chat

clientes_conectados: Dict[int,WebSocket] = {}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, user_id: int = Query(...), db: Session = Depends(get_db)):
    try:
        print(f"Novo websocket id {user_id}")
        await websocket.accept()
        clientes_conectados[user_id] = websocket
        print(f"Cliente Conectado {user_id}")
        try:
            while True:
                data = await websocket.receive_json()

                if data["tipo"] == "mensagem":
                    destinatario_id = data["destinatario_id"]
                    conteudo = data["conteudo"]
                    remetente_id = data["remetente_id"]

                    print(f"Remetente_id {remetente_id}, destinatario_id {destinatario_id}")

                    chat_autorizado = db.query(ChatRequest).filter(
                        ChatRequest.aceito == True,
                        or_(
                            (ChatRequest.remetente_id == remetente_id) & (ChatRequest.destinatario_id == destinatario_id),
                            (ChatRequest.remetente_id == destinatario_id) & (ChatRequest.destinatario_id == remetente_id)
                        )
                    ).first()


                    if not chat_autorizado:
                        await websocket.send_json({
                            "tipo": "erro",
                            "mensagem": "O chat ainda não foi aceite pelo destinatário."
                        })
                        continue 

                    mensagem = {
                        "tipo": "mensagem",
                        "remetente_id": remetente_id,
                        "conteudo": conteudo 
                    }

                    destinatario_ws = clientes_conectados.get(destinatario_id)
                    if destinatario_ws:
                        await destinatario_ws.send_json(mensagem)
                
        except WebSocketDisconnect:
            print(f"Cliente desconectado: {user_id}")
            clientes_conectados.pop(user_id, None)

    except Exception as e:
        print(f"Erro no websocket do user {user_id}: {e}")
        clientes_conectados.pop(user_id, None)


@app.post("/enviar_chat_pedido")
async def new_chat_pedido(data: Chat.ChatRequestData, db: Session = Depends(get_db)):
    return await Chat.enviar_pedido_chat(data,db, clientes_conectados)

@app.get("/pedidos_pendentes")
def listar_pedidos_pendentes(usuario: Users = Depends(obter_usuario_logado), db: Session = Depends(get_db)):
    return Chat.get_pedidos(db, usuario.id_user)

@app.get("/amigos")
def listar_amigos(usuario: Users = Depends(obter_usuario_logado), db: Session = Depends(get_db)):
    return Chat.get_amizades(db, usuario.id_user)
    

class AceitarPedidoData(BaseModel):
    pedido_id: int

@app.post("/aceitar_pedido_chat")
def aceitar_pedido_chat(data: AceitarPedidoData, db: Session = Depends(get_db)):
    pedido = db.query(ChatRequest).filter(ChatRequest.id == data.pedido_id).first()

    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    pedido.aceito = True
    db.commit()

    return {"message": "Chat iniciado!"}

@app.get("/destinatario/{id_user}")
def get_destinatario(id_user: int, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id_user == id_user).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"nome":user.nome}

@app.get("/Utilizadores")
def get_utilizadores(db:Session = Depends(get_db)):
    utilizadores = db.query(Users).all()

    nomes = [{"nome": utilizador.nome, "id_user": utilizador.id_user} for utilizador in utilizadores]

    return nomes


    