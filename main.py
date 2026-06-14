from fastapi import FastAPI, Depends
from pydantic import BaseModel
import google.generativeai as genai
import os

from database import SessionLocal, engine
from models import Base, User

Base.metadata.create_all(bind=engine)

app = FastAPI()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class RequestData(BaseModel):
    user_id: str
    niche: str
    audience: str
    goal: str
    style: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/generate")
def generate(data: RequestData, db=Depends(get_db)):

    user = db.query(User).filter(User.user_id == data.user_id).first()

    if not user:
        user = User(
            user_id=data.user_id,
            niche=data.niche,
            audience=data.audience,
            style=data.style,
            history=""
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    prompt = f"""
    Ты маркетолог и креатор контента.

    Пользователь:
    - Ниша: {data.niche}
    - Аудитория: {data.audience}
    - Цель: {data.goal}
    - Стиль: {data.style}

    История пользователя:
    {user.history}

    Сгенерируй 5 новых вирусных идей.
    """

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)

    user.history += "\n" + response.text
    db.commit()

    return {"result": response.text}
