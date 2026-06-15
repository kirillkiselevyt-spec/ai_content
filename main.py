import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash"

class RequestData(BaseModel):
    user_id: str
    niche: str
    audience: str
    goal: str
    style: str
    mode: str


def build_prompt(data: RequestData):

    base = f"""
Ты — сильный маркетолог и SMM-специалист.

Ниша: {data.niche}
Аудитория: {data.audience}
Цель: {data.goal}
Стиль: {data.style}

Правила:
- Без воды
- Конкретика
- Боль → решение → выгода
- Используй триггеры
- Добавляй CTA
"""

    if data.mode == "plan":
        task = """
Сделай контент-план на 7 дней:
- тема
- тип (продающий / вовлекающий / экспертный)
- краткое описание
"""
    elif data.mode == "series":
        task = """
Сделай прогрев из 5 постов:
каждый усиливает доверие
"""
    elif data.mode == "hooks":
        task = "Сделай 10 мощных заголовков"
    else:
        task = """
Сделай продающий пост:
1. Заголовок
2. Основной текст
3. CTA
4. Идея визуала
"""

    return base + "\n" + task


@app.post("/generate")
def generate(data: RequestData, db: Session = Depends(get_db)):

    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Нет API ключа")

    try:
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

        prompt = build_prompt(data)

        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)

        result = response.text if hasattr(response, "text") else ""

        user.history += f"\n---\n{prompt}\n{result}\n"
        db.commit()

        return {"result": result}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))