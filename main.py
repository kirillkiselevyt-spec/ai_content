import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Импортируем модули для работы с базой данных
from database import SessionLocal, engine, Base
from models import User

# Автоматически создаем таблицы в базе данных при старте приложения
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Разрешаем CORS, чтобы фронтенд на GitHub Pages мог общаться с бэкендом на Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Функция (Dependency) для управления сессиями БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Инициализация API-ключа Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Рабочая актуальная модель
MODEL_NAME = "gemini-2.5-flash"

# Описываем структуру входящих данных. Теперь мы принимаем не только промпт, но и метаданные
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
        # 1. Запись в базу данных и работа с историей
        user = db.query(User).filter(User.user_id == data.user_id).first()
        
        if not user:
            # Если пользователя нет в БД, создаем новую запись
            user = User(
                user_id=data.user_id,
                niche=data.niche,
                audience=data.audience,
                style=data.style,
                history=f"Запрос: {data.prompt}\n"
            )
            db.add(user)
        else:
            # Если пользователь существует, обновляем текущие параметры и добавляем историю
            user.niche = data.niche
            user.audience = data.audience
            user.style = data.style
            user.history = (user.history or "") + f"--- \nЗапрос: {data.prompt}\n"
        
        # 2. Генерация текста через Gemini
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(data.prompt)

        if hasattr(response, "text") and response.text:
            generated_text = response.text
            
            # Дописываем сгенерированный ответ в историю пользователя
            user.history += f"Ответ: {generated_text}\n"
            
            # Сохраняем все изменения в базу данных
            db.commit()
            
            return {"result": generated_text}
        else:
            raise HTTPException(status_code=502, detail="Gemini вернул пустой ответ.")

    except Exception as e:
        db.rollback()  # Откатываем транзакцию в случае ошибки
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")
