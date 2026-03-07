import requests
import os

from dotenv import load_dotenv

load_dotenv()
SCRAPINGDOG_API_KEY = os.getenv("SCRAPINGDOG_API_KEY")



def search_products_via_api(query):
    """
    Поиск товаров через Scrapingdog Google Shopping API
    Документация: https://www.scrapingdog.com/docs/google-shopping
    """
    url = "https://api.scrapingdog.com/google_shopping/"

    params = {
        "api_key": SCRAPINGDOG_API_KEY,
        "query": query,
        "results": 20,
        "country": "ru",  # Для теста оставь us, но можешь поменять на ru
        "currency": "RUB",  # Меняем на USD, так как ищем на английском
        "page": 0
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"API Response Status: {response.status_code}")

        if response.status_code != 200:
            print(f"Scrapingdog error: {response.status_code}")
            print(f"Response text: {response.text}")
            return []

        data = response.json()

        # 🔥 ИСПРАВЛЕНИЕ: используем правильный ключ 'shopping_results'
        products = data.get('shopping_results', [])
        print(products)
        print(f"Found {len(products)} products in 'shopping_results'")

        results = []

        for idx, product in enumerate(products):
            try:
                # Цена
                price = 0
                if product.get('price'):
                    # Убираем символ валюты и конвертируем в число
                    price_str = product['price'].replace('$', '').replace('₽', '').strip()
                    try:
                        price = int(float(price_str))
                    except:
                        price = 0

                # Название магазина
                source = product.get('source')

                # Изображение
                image = product.get('thumbnail', 'https://via.placeholder.com/200')

                results.append({
                    'id': f"sd_{idx}_{hash(product.get('product_link', '')) % 10000}",
                    'title': product.get('title', query),
                    'price': product.get('price'),
                    'image': image,
                    'source': source,
                    'url': product.get('product_url')
                })
            except Exception as e:
                print(f"Error parsing product: {e}")
                continue

        return results

    except Exception as e:
        print(f"Scrapingdog search failed: {e}")
        return []


if __name__ == "__main__":
    # Тестируем
    results = search_products_via_api("кроссовки")
    print(f"\n✅ Найдено товаров: {len(results)}")
    for i, r in enumerate(results[:5]):  # Покажем первые 5
        print(f"\n--- Товар {i + 1} ---")
        print(f"  Название: {r['title']}")
        print(f"  Цена: {r['price']}{r['currency']}")
        print(f"  Магазин: {r['source']}")
        print(f"  Ссылка: {r['url']}")