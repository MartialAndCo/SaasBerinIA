from sqlalchemy import Column, Integer, String, Text
from app.database.base import Base

class MessengerDirectives(Base):
    """
    Modèle pour stocker les directives du Messenger Agent
    """
    __tablename__ = "messenger_directives"

    id = Column(Integer, primary_key=True, index=True)
    sms_instructions = Column(Text, nullable=True)
    email_instructions = Column(Text, nullable=True)
