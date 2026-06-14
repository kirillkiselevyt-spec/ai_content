from sqlalchemy import Column, Integer, String, Text
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)

    niche = Column(String)
    audience = Column(String)
    style = Column(String)

    history = Column(Text, default="")