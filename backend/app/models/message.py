from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=True)
    lead_name = Column(String)
    lead_email = Column(String)
    subject = Column(String)
    content = Column(Text)
    status = Column(String, default="sent")  # sent, delivered, opened, clicked, replied, bounced, failed
    campaign_id = Column(Integer, nullable=True)
    campaign_name = Column(String)
    sent_date = Column(DateTime, default=datetime.utcnow)
    open_date = Column(DateTime, nullable=True)
    reply_date = Column(DateTime, nullable=True)
    
    # Nouveaux champs pour messagerie bidirectionnelle
    direction = Column(String, default="outbound")  # inbound/outbound
    sender_type = Column(String, default="ai")  # ai/user/lead
    thread_id = Column(String)  # Identifiant de conversation
    message_type = Column(String, default="email")  # email/sms/whatsapp
    sender_name = Column(String)  # Nom de l'expéditeur
    received_date = Column(DateTime, nullable=True)  # Date de réception
    message_id_external = Column(String)  # ID externe (Instantly, Twilio)

    # Relations temporairement supprimées pour éviter les erreurs
    # lead_id = Column(Integer, ForeignKey("leads.id"))
    # lead = relationship("Lead", back_populates="messages")
    # campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    # campaign = relationship("Campaign", back_populates="messages")
