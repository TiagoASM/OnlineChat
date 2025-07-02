from pydantic import BaseModel
from models import ChatRequest, Users
from fastapi import HTTPException
from typing import Optional
from sqlalchemy import or_


class ChatRequestData(BaseModel):
    id: Optional[int] = None
    remetente_id: int
    destinatario_id: int

async def enviar_pedido_chat(data: ChatRequestData, db, clientes_conectados):
    remetente = db.query(Users).filter(Users.id_user == data.remetente_id).first()
    destinatario = db.query(Users).filter(Users.id_user == data.destinatario_id).first()

    if not remetente or not destinatario:
        raise HTTPException(status_code=404, detail="User not found")
    
    pedido_existente = db.query(ChatRequest).filter(
        (ChatRequest.remetente_id == data.remetente_id) & 
        (ChatRequest.destinatario_id == data.destinatario_id)
    ).first()

    if pedido_existente:
        raise HTTPException(status_code=400, detail="Pedido já enviado")
    
    new_pedido = ChatRequest(
        remetente_id = data.remetente_id,
        destinatario_id = data.destinatario_id,
        aceito= False
    )

    db.add(new_pedido)
    db.commit()
    db.refresh(new_pedido)

    mensagem = {
        "tipo": "novo_pedido",
        "remetente_id": data.remetente_id,
        "destinatario_id": data.destinatario_id,
        "mensagem": f"Novo pedido de chat de {remetente.nome}!",
        "pedido_id": new_pedido.id
    }

    destinatario_ws = clientes_conectados.get(data.destinatario_id)
    if destinatario_ws:
        await destinatario_ws.send_json(mensagem)

def get_pedidos(db, user_id):
    pedidos = db.query(ChatRequest).filter(ChatRequest.destinatario_id == user_id, ChatRequest.aceito == False).all()

    if not pedidos:
        raise HTTPException(status_code=404, detail="not found")
    
    return pedidos

def get_amizades(db, user_id):
    pedidos = db.query(ChatRequest).filter(
        or_(
            ChatRequest.destinatario_id == user_id,
            ChatRequest.remetente_id == user_id
        ),
        ChatRequest.aceito == True
    ).all()

    if not pedidos:
        raise HTTPException(status_code=404, detail="not found")
    
    return pedidos
