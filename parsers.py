# import requests
# import os
# import urllib.parse
# import time
# import re
# import html
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
#
# load_dotenv()
#
# SCRAPINGBEE_KEY = os.getenv("SCRAPINGBEE_KEY")
#
#
# def fix_encoding(text):
#     """
#     Исправление кодировки для русских текстов
#     """
#     if not text:
#         return ""
#
#     # Убираем HTML entities
#     text = html.unescape(text)
#
#     # Если текст уже в нормальном виде, просто чистим
#     if any(ord(c) > 255 for c in text):
#         # Уже есть русские буквы
#         return text.strip()
#
#     # Пробуем декодировать из разных кодировок
#     try:
#         # Сначала пробуем как utf-8 (если пришло в байтах)
#         if isinstance(text, str):
#             text_bytes = text.encode('latin1')
#         else:
#             text_bytes = text
#         decoded = text_bytes.decode('utf-8')
#         if decoded and any(ord(c) > 127 for c in decoded):
#             return decoded.strip()
#     except:
#         pass
#
#     try:
#         # Пробуем cp1251 (Windows-1251)
#         if isinstance(text, str):
#             text_bytes = text.encode('latin1')
#         else:
#             text_bytes = text
#         decoded = text_bytes.decode('cp1251')
#         if decoded and any(ord(c) > 127 for c in decoded):
#             return decoded.strip()
#     except:
#         pass
#
#     # Если ничего не помогло, убираем непечатные символы
#     cleaned = re.sub(r'[^\w\s\-\.\,\!\?\(\)а-яА-Яa-zA-Z0-9]', ' ', text)
#     return cleaned.strip()
#
#
# def search_products_via_api(query, max_retries=2):
#     """
#     Поиск товаров через ScrapingBee API с Google Shopping
#     """
#     if not SCRAPINGBEE_KEY:
#         print("❌ SCRAPINGBEE_KEY not found")
#         return []
#
#     search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}&tbm=shop"
#
#     for attempt in range(max_retries):
#         try:
#             print(f"🔍 Attempt {attempt + 1} for '{query}'...")
#
#             if attempt > 0:
#                 wait_time = (attempt + 1) * 3
#                 print(f"⏳ Waiting {wait_time} seconds...")
#                 time.sleep(wait_time)
#
#             params = {
#                 "api_key": SCRAPINGBEE_KEY,
#                 "url": search_url,
#                 "custom_google": "true",
#                 "render_js": "true",
#                 "premium_proxy": "true",
#                 "country_code": "ru",
#                 "device": "desktop",
#                 "wait": "3000",
#             }
#
#             print(f"📤 Sending request to ScrapingBee...")
#
#             response = requests.get(
#                 "https://app.scrapingbee.com/api/v1/",
#                 params=params,
#                 timeout=60
#             )
#
#             print(f"📡 Status: {response.status_code}")
#
#             if response.status_code == 200:
#                 # Сохраняем для отладки
#                 with open(f"debug_{query}.html", "w", encoding="utf-8") as f:
#                     f.write(response.text)
#                 print(f"💾 Saved HTML to debug_{query}.html")
#
#                 # Парсим HTML
#                 soup = BeautifulSoup(response.text, 'html.parser')
#                 results = parse_google_shopping_final(soup, query)
#
#                 if results:
#                     print(f"✅ Found {len(results)} products")
#                     return results[:20]
#                 else:
#                     print("⚠️ No products found in HTML")
#
#             elif response.status_code == 402:
#                 print("❌ Insufficient credits")
#                 return []
#             else:
#                 print(f"⚠️ Status: {response.status_code}")
#
#         except Exception as e:
#             print(f"❌ Error: {e}")
#             continue
#
#     return []
#
#
# def parse_google_shopping_final(soup, query):
#     """
#     Финальная версия парсинга с исправлением кодировки
#     """
#     results = []
#
#     # Ищем карточки товаров
#     products = soup.select('li.YBo8bb')
#
#     if not products:
#         products = soup.select('div[data-ri]')
#
#     if not products:
#         products = soup.select('div.sh-dgr__content')
#
#     print(f"  Found {len(products)} product cards")
#
#     for idx, product in enumerate(products[:30]):
#         try:
#             # 1. Название
#             title = query
#             title_elem = product.select_one('h3')
#             if not title_elem:
#                 title_elem = product.select_one('.gkQHve')
#             if not title_elem:
#                 title_elem = product.select_one('[role="heading"]')
#
#             if title_elem:
#                 raw_title = title_elem.get_text(strip=True)
#                 title = fix_encoding(raw_title)
#
#                 # Если название начинается с мусора, пытаемся очистить
#                 # Часто название выглядит как "ÐÑÑÐºÐ Outventure"
#                 # Нужно извлечь нормальную часть после мусора
#                 if ' ' in title and len(title.split()) > 1:
#                     # Берем последнее слово или фразу, которая выглядит нормально
#                     words = title.split()
#                     # Ищем слово, которое содержит русские буквы
#                     for i, word in enumerate(words):
#                         if any(ord(c) > 1024 for c in word):  # русские буквы
#                             title = ' '.join(words[i:])
#                             break
#
#             # 2. Цена
#             price = "Цена не указана"
#             price_elem = product.select_one('.lmQWe')
#             if not price_elem:
#                 price_elem = product.select_one('.a8Pemb')
#             if not price_elem:
#                 price_elem = product.select_one('[aria-label*="цена"]')
#
#             if price_elem:
#                 raw_price = price_elem.get_text(strip=True)
#                 price = fix_encoding(raw_price)
#                 # Очищаем цену от лишних символов
#                 price = re.sub(r'[^\d\s₽руб\.\,]', '', price)
#                 if not price.strip():
#                     price = "Цена не указана"
#
#             # 3. Магазин
#             retailer = "Unknown"
#             retailer_elem = product.select_one('.WJMUdc')
#             if not retailer_elem:
#                 retailer_elem = product.select_one('.aULzUe')
#             if not retailer_elem:
#                 retailer_elem = product.select_one('.sh-np__merchant')
#
#             if retailer_elem:
#                 raw_retailer = retailer_elem.get_text(strip=True)
#                 retailer = fix_encoding(raw_retailer)
#
#             # 4. Ссылка
#             url = "#"
#             link_elem = product.select_one('a[href*="/shopping/product"]')
#             if not link_elem:
#                 link_elem = product.find('a', href=re.compile(r'/shopping/product'))
#
#             if link_elem and link_elem.get('href'):
#                 url = link_elem['href']
#                 if url.startswith('/'):
#                     url = f"https://www.google.com{url}"
#
#             # 5. Изображение
#             image = 'https://via.placeholder.com/200'
#             img_elem = product.select_one('img')
#             if img_elem:
#                 image = img_elem.get('src') or img_elem.get('data-src')
#                 if image and (image.startswith('data:') or not image.startswith('http')):
#                     image = 'https://via.placeholder.com/200'
#
#             # 6. Рейтинг
#             rating = None
#             rating_elem = product.select_one('.yi40Hd')
#             if rating_elem:
#                 rating_text = rating_elem.get_text(strip=True)
#                 rating_match = re.search(r'(\d+[,\.]?\d*)', rating_text)
#                 if rating_match:
#                     rating = rating_match.group(1)
#
#             # 7. Количество отзывов
#             reviews = None
#             reviews_elem = product.select_one('.RDApEe')
#             if reviews_elem:
#                 reviews_text = reviews_elem.get_text(strip=True)
#                 reviews_match = re.search(r'\((\d+[\s]?[\d]*)\s*тыс', reviews_text)
#                 if reviews_match:
#                     reviews = reviews_match.group(1).replace(' ', '')
#
#             # Добавляем товар
#             if title and title != query and len(title) > 3:
#                 results.append({
#                     'id': f"prod_{idx}",
#                     'title': title[:100],
#                     'price': price,
#                     'image': image,
#                     'source': retailer,
#                     'url': url,
#                     'rating': rating,
#                     'reviews': reviews
#                 })
#
#                 print(f"    ✅ Added: {title[:50]}... - {price}")
#
#         except Exception as e:
#             print(f"    ❌ Error parsing product {idx}: {e}")
#             continue
#     print(results)
#     return results
#
#
# if __name__ == "__main__":
#     print("🚀 Starting Google Shopping search...")
#     print("=" * 50)
#
#     if SCRAPINGBEE_KEY:
#         print(f"Using ScrapingBee API...")
#
#         # Тестируем
#         query = "штаны"
#         results = search_products_via_api(query)
#
#         if results:
#             print(f"\n{'=' * 60}")
#             print(f"✅ НАЙДЕНО ТОВАРОВ: {len(results)}")
#             print('=' * 60)
#
#             for i, product in enumerate(results[:20], 1):
#                 print(f"\n--- Товар {i} ---")
#                 print(f"  📦 Название: {product['title']}")
#                 print(f"  💰 Цена: {product['price']}")
#                 print(f"  🏪 Магазин: {product['source']}")
#                 if product.get('rating'):
#                     print(f"  ⭐ Рейтинг: {product['rating']}")
#                 if product.get('reviews'):
#                     print(f"  📊 Отзывов: {product['reviews']} тыс.")
#                 if product['url'] != '#':
#                     print(f"  🔗 Ссылка: {product['url'][:100]}..." if len(
#                         product['url']) > 100 else f"  🔗 Ссылка: {product['url']}")
#         else:
#             print("\n❌ Не удалось найти товары")
#     else:
#         print("❌ SCRAPINGBEE_KEY not found in .env file")

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
    results = search_products_via_api("рубашка")
    print(f"\n✅ Найдено товаров: {len(results)}")
    for i, r in enumerate(results[:5]):  # Покажем первые 5
        print(f"\n--- Товар {i + 1} ---")
        print(f"  Название: {r['title']}")
        print(f"  Цена: {r['price']}")
        print(f"  Магазин: {r['source']}")
        print(f"  Ссылка: {r['url']}")