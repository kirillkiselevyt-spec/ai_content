from sqlalchemy import Column, Integer, String, Text
from database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(String, unique=True, index=True)
    message_count = Column(Integer, default=0)
    history       = Column(Text, default="")
