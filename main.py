import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Импортируем твои модули базы данных
from database import SessionLocal, engine, Base
from models import User

# Создаем таблицы в БД, если они еще не созданы
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency для получения сессии БД на каждый запрос
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Инициализация API ключа
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash"

# Расширяем валидацию входящих данных — теперь ждем еще и user_id
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
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Ключ API Gemini не настроен на сервере.")

    try:
        # 1. Работа с историей пользователя в БД
        user = db.query(User).filter(User.user_id == data.user_id).first()
        
        if not user:
            # Если пользователя нет, создаем его и заполняем текущие параметры
            user = User(
                user_id=data.user_id,
                niche=data.niche,
                audience=data.audience,
                style=data.style,
                history=f"Запрос: {data.prompt}\n"
            )
            db.add(user)
        else:
            # Если пользователь есть, обновляем его текущие настройки и дописываем историю
            user.niche = data.niche
            user.audience = data.audience
            user.style = data.style
            # Дописываем новый запрос в историю (с разделением)
            user.history = (user.history or "") + f"--- \nЗапрос: {data.prompt}\n"
        
        # 2. Генерация контента через Gemini
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(data.prompt)

        if hasattr(response, "text") and response.text:
            generated_text = response.text
            
            # Дописываем результат генерации в историю этого же запроса
            user.history += f"Ответ: {generated_text}\n"
            
            # Сохраняем все изменения в базу данных коммитом
            db.commit()
            
            return {"result": generated_text}
        else:
            raise HTTPException(status_code=502, detail="Gemini вернул пустой ответ.")

    except Exception as e:
        db.rollback() # Откатываем транзакцию в БД, если что-то пошло не так
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")
