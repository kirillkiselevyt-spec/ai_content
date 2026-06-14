import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Подключаем базу данных и модели
from database import SessionLocal, engine, Base
from models import User

# Автоматически создаем таблицы в SQLite при старте
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Разрешаем CORS для связи с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация API ключа
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Твоя рабочая модель
MODEL_NAME = "models/gemini-3.5-flash"

# Функция получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Расширенная схема данных для сохранения в базу
class RequestData(BaseModel):
    user_id: str
    prompt: str
    niche: str
    audience: str
    style: str


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/generate")
def generate(data: RequestData, db: Session = Depends(get_db)):
    try:
        # 1. Запись в базу данных и ведение истории
        user = db.query(User).filter(User.user_id == data.user_id).first()
        
        if not user:
            user = User(
                user_id=data.user_id,
                niche=data.niche,
                audience=data.audience,
                style=data.style,
                history=f"Запрос: {data.prompt}\n"
            )
            db.add(user)
        else:
            user.niche = data.niche
            user.audience = data.audience
            user.style = data.style
            user.history = (user.history or "") + f"\n--- Новый запрос ---\nЗапрос: {data.prompt}\n"

        # 2. Обращение к генеративной модели
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(data.prompt)

        result_text = response.text if hasattr(response, "text") else str(response)
        
        # Дописываем ответ ИИ в историю и сохраняем изменения
        user.history += f"Ответ:\n{result_text}\n"
        db.commit()

        return {"result": result_text}

    except Exception as e:
        db.rollback()
        return {
            "error": "Gemini API error",
            "details": str(e)
        }
