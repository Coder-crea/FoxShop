import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 15 * 60  # 15 минут
    JWT_REFRESH_TOKEN_EXPIRES = 30 * 24 * 60 * 60  # 30 дней

    # CORS
    FRONTEND_URL = os.getenv('FRONTEND_URL')