from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Users(Base):
    __tablename__ = "Users"

    id_user = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50))
    email = Column(String(50))
    pwd = Column(String(50))

    pedidos_enviados = relationship("ChatRequest", foreign_keys="ChatRequest.remetente_id", back_populates="remetente")
    pedidos_recebidos = relationship("ChatRequest", foreign_keys="ChatRequest.destinatario_id", back_populates="destinatario")

class ChatRequest(Base):
    __tablename__ = "chat_requests"

    id = Column(Integer, primary_key=True, index=True)
    remetente_id = Column(Integer, ForeignKey("Users.id_user"), nullable=False)
    destinatario_id = Column(Integer, ForeignKey("Users.id_user"), nullable=False)
    aceito = Column(Boolean, default=False)

    remetente = relationship("Users", foreign_keys=[remetente_id], back_populates="pedidos_enviados")
    destinatario = relationship("Users", foreign_keys=[destinatario_id], back_populates="pedidos_recebidos")