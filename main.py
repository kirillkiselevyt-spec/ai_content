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
    prompt: str
    niche: str
    audience: str
    style: str


@app.get("/")
def root():
    return {"status": "ok", "database": "connected"}


@app.post("/generate")
def generate(data: RequestData, db: Session = Depends(get_db)):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Ключ API GEMINI_API_KEY не установлен в переменных Render.")

    try:
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
            user.history = (user.history or "") + f"\n--- Следующий запрос ---\nЗапрос: {data.prompt}\n"
        
        # Конфигурируем модель с отключением строгой блокировки контента (для тем вроде крафтового алкоголя)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)
        response = model.generate_content(data.prompt)

        # Более надежное извлечение сгенерированного текста
        generated_text = ""
        if hasattr(response, "text") and response.text:
            generated_text = response.text
        elif zip(response.candidates):
            try:
                generated_text = response.candidates[0].content.parts[0].text
            except:
                pass

        if generated_text:
            user.history += f"Ответ ИИ:\n{generated_text}\n"
            db.commit()
            return {"result": generated_text}
        else:
            # Если сработал внутренний фильтр Google, даем внятный ответ вместо падения
            raise HTTPException(status_code=422, detail="Запрос заблокирован внутренними фильтрами безопасности Gemini API.")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
