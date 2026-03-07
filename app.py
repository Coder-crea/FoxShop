from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

from supabase import create_client
from datetime import datetime

from config import Config
from auth import hash_password, validate_password, generate_tokens, verify_token, token_required
from parsers import search_products_via_api

# расскажи про инициализацию app и про __name__ также есть ли автоматическая генерация документации как у FastApi?? что значит app.config
app = Flask(__name__)
app.config.from_object(Config)

# Настройка CORS для работы с cookies
# что такое CORS и как он рабоатет?
CORS(app,
     origins=[Config.FRONTEND_URL],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     expose_headers=['Set-Cookie'])

# Инициализация Supabase
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)


# ============= АВТОРИЗАЦИЯ =============
# Flask у нас приходит обьект request??? Просто в fastApi обычно модель pydantic приходит. Тут все так просто? Или я просто не использую pdantic здесь просто????
@app.route('/api/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    try:
        data = request.get_json()

        # Проверяем обязательные поля
        if not data.get('email') and not data.get('password'):
            return jsonify({'message': 'Email and password are required'}), 400

        # Проверяем, существует ли пользователь
        existing_user = supabase.table('users') \
            .select('*') \
            .eq('email', data['email']) \
            .execute()

        if existing_user.data:
            return jsonify({'message': 'User already exists'}), 409

        # Хешируем пароль и создаем пользователя
        password_hash = hash_password(data['password'])

        new_user = supabase.table('users').insert({
            'email': data['email'],
            'phone': data.get('phone'),
            'password_hash': password_hash,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).execute()

        if not new_user.data:
            return jsonify({'message': 'Failed to create user'}), 500

        user = new_user.data[0] #разве от new_user нам вернется data???/

        # Генерируем токены
        access_token, refresh_token = generate_tokens(user['id'])

        # Создаем ответ
        response = make_response(jsonify({
            'message': 'Registration successful',
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'phone': user.get('phone')
            }
        }), 201)

        # Устанавливаем refresh_token в httpOnly cookie
        # как это все работает???
        response.set_cookie(
            'refresh_token',
            refresh_token,
            httponly=True,
            secure=True,  # В продакшене
            samesite='Lax',
            max_age=Config.JWT_REFRESH_TOKEN_EXPIRES,
            path='/api/refresh'
        )

        return response

    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """Вход пользователя"""
    try:
        data = request.get_json()

        if not data.get('email') and not data.get('password'):
            return jsonify({'message': 'Email and password are required'}), 400

        # Ищем пользователя
        user_result = supabase.table('users') \
            .select('*') \
            .eq('email', data['email']) \
            .execute()

        if not user_result.data:
            return jsonify({'message': 'Пользователя с такими данными нет'}), 401

        user = user_result.data[0]

        # Проверяем пароль
        if not validate_password(data['password'], user['password_hash']):
            return jsonify({'message': 'Неправильный пароль'}), 401

        # Генерируем токены
        access_token, refresh_token = generate_tokens(user['id'])

        # Создаем ответ
        response = make_response(jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'phone': user.get('phone')
            }
        }), 200)

        # Устанавливаем refresh_token в httpOnly cookie
        response.set_cookie(
            'refresh_token',
            refresh_token,
            httponly=True,
            secure=True,
            samesite='Lax',
            max_age=Config.JWT_REFRESH_TOKEN_EXPIRES,
            path='/api/refresh'
        )

        return response

    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/refresh', methods=['POST'])
def refresh():
    """Обновление access token'а"""
    try:
        # Получаем refresh_token из cookie
        refresh_token = request.cookies.get('refresh_token')

        if not refresh_token:
            return jsonify({'message': 'Refresh token missing'}), 401

        # Проверяем refresh_token
        payload = verify_token(refresh_token, 'refresh')
        if not payload:
            return jsonify({'message': 'Invalid refresh token'}), 401

        # Генерируем новую пару токенов
        new_access_token, new_refresh_token = generate_tokens(payload['user_id'])

        # Создаем ответ
        response = make_response(jsonify({
            'access_token': new_access_token
        }), 200)

        # Обновляем refresh_token в cookie
        response.set_cookie(
            'refresh_token',
            new_refresh_token,
            httponly=True,
            secure=True,
            samesite='Lax',
            max_age=Config.JWT_REFRESH_TOKEN_EXPIRES,
            path='/api/refresh'
        )

        return response

    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """Выход пользователя"""
    response = make_response(jsonify({'message': 'Logout successful'}), 200)
    response.delete_cookie('refresh_token', path='/api/refresh')
    # может быть тут также стоит удалить access_token?? Ибо когда мы удалим refresh_token, то acсess_token будет еще доступен 15мин, и запросы будут еще выполняться. Или мы это как то на Fronted реализуем? Что при запросе logout мы удалим на клиенте access???
    return response


@app.route('/api/me', methods=['GET'])
@token_required
def get_current_user():
    """Получение информации о текущем пользователе"""
    try:
        user_result = supabase.table('users') \
            .select('id, email, phone, created_at') \
            .eq('id', request.user_id) \
            .execute()

        if not user_result.data:
            return jsonify({'message': 'User not found'}), 404

        return jsonify({'user': user_result.data[0]}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ============= ПОИСК ТОВАРОВ =============

@app.route('/api/search', methods=['GET'])
@token_required
def search_products():
    """Поиск товаров по запросу через Scrapingdog"""
    try:
        query = request.args.get('q', '')

        if not query:
            return jsonify({'message': 'Search query is required'}), 400

        # Получаем результаты через Scrapingdog
        results = search_products_via_api(query)

        # Если ничего не нашли
        if not results:
            results = [{
                'id': 'no_results',
                'title': f'По запросу "{query}" ничего не найдено',
                'price': 0,
                'currency': '₽',
                'image': 'https://via.placeholder.com/200?text=No+Results',
                'source': 'Система',
                'url': '#'
            }]

        supabase.table('search_history').insert({
            'user_id': request.user_id,
            'query': query,
            'created_at': datetime.utcnow().isoformat(),
            'offers': results
        }).execute()

        return jsonify({
            'query': query,
            'results': results
        }), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500



@app.route('/api/search/history', methods=['GET'])
@token_required
def get_search_history():
    """Получение истории поиска пользователя"""
    try:
        history = supabase.table('search_history') \
            .select('*') \
            .eq('user_id', request.user_id) \
            .order('created_at', desc=False) \
            .limit(50) \
            .execute()

        return jsonify({'history': history.data}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)