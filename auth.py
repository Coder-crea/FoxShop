import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, make_response
from config import Config


def hash_password(
    password: str,
) -> str:
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode('utf-8')
    hash_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hash_bytes.decode('utf-8')

def validate_password(password: str, hashed_password: bytes) -> bool:

    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')

    return bcrypt.checkpw(password=password_bytes, hashed_password=hashed_bytes)



def generate_tokens(user_id):
    """Генерация access и refresh токенов"""
    # Access token (короткоживущий)
    access_token = jwt.encode(
        {
            'user_id': str(user_id),
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
        },
        Config.JWT_SECRET_KEY,
        algorithm='HS256'
    )

    # Refresh token (долгоживущий)
    refresh_token = jwt.encode(
        {
            'user_id': str(user_id),
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_REFRESH_TOKEN_EXPIRES)
        },
        Config.JWT_SECRET_KEY,
        algorithm='HS256'
    )

    return access_token, refresh_token


def verify_token(token, token_type='access'):
    """Проверка токена"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        if payload['type'] != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Декоратор для защиты маршрутов"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Ищем токен в заголовке
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        payload = verify_token(token, 'access')
        if not payload:
            return jsonify({'message': 'Token is invalid or expired'}), 401

        # Добавляем user_id в запрос
        request.user_id = payload['user_id']
        return f(*args, **kwargs)

    return decorated