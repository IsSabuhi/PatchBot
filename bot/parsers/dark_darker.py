import aiohttp
from typing import Optional, Dict
from bot.utils.html_cleaner import clean_html_text, truncate_text
from bot.utils.translator import translate_to_ru
import re

BASE_URL = "https://www.darkanddarker.com"
NEWS_URL = f"{BASE_URL}/news/all"

async def fetch_articles(page: int = 1) -> Optional[list]:
    """Получить список карточек со страницы /news/all"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json",
        "Referer": NEWS_URL,
        "Origin": BASE_URL,
    }
    payload = {"page": page, "type": "all"}

    try:
        async with aiohttp.ClientSession() as session:
            print(f"🔌 POST к {NEWS_URL} с page={page}")
            async with session.post(NEWS_URL, headers=headers, json=payload, timeout=15) as resp:
                print(f"📊 HTTP {resp.status}")
                
                if resp.status != 200:
                    text = await resp.text()
                    print(f"❌ Ошибка: {text[:200]}")
                    return None
                
                data = await resp.json()
                articles = data.get("articles", [])
                print(f"✅ Получено {len(articles)} карточек")
                
                if articles:
                    print(f"   Первая: {articles[0].get('article_title', 'NO TITLE')}")
                
                return articles
    except Exception as e:
        print(f"❌ ОШИБКА fetch_articles: {type(e).__name__}: {e}")
        return None

async def fetch_article_full(article_id: int, lang: str = "ru") -> Optional[Dict]:
    """
    Получить полное содержимое статьи через POST запрос
    
    Это запрос к https://www.darkanddarker.com/news/article/{article_id}
    с телом {"lang": "ru"}
    """
    url = f"{BASE_URL}/news/article/{article_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/news/all",
    }
    payload = {"lang": lang}

    try:
        print(f"📖 POST к {url} (lang={lang})")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=15) as resp:
                print(f"📊 HTTP {resp.status}")
                
                if resp.status != 200:
                    text = await resp.text()
                    print(f"❌ Ошибка: {text[:200]}")
                    return None
                
                data = await resp.json()
                
                if data.get("result") != 0:
                    print(f"❌ API error result: {data.get('result')}")
                    return None
                
                article = data.get("article", {})
                print(f"✅ Получена статья: {article.get('article_title')}")
                
                return article
    except Exception as e:
        print(f"❌ ОШИБКА fetch_article_full: {type(e).__name__}: {e}")
        return None

async def get_latest_article() -> Optional[Dict]:
    """Получить последнюю карточку и её полное содержимое"""
    print(f"🔍 Запрос get_latest_article...")
    
    articles = await fetch_articles(1)
    if not articles:
        print(f"❌ fetch_articles вернул None или []")
        return None
    
    a = articles[0]
    article_id = a.get("article_id")
    
    # Получаем полное содержимое статьи
    full_article = await fetch_article_full(article_id, lang="ru")
    
    if not full_article:
        print(f"⚠️ Не удалось получить полное содержимое, используем краткое")
        full_article = a
    
    # Очищаем HTML
    description_html = full_article.get("article_description", "")
    description_clean = clean_html_text(description_html)
    
    # Обрезаем если слишком длинный
    description_clean = truncate_text(description_clean, 2024)
    
    # Берём только небольшой summary (например, первые 3–4 строки)
    summary_lines = description_clean.split("\n")
    summary = "\n".join(summary_lines[:4])  # сколько хочешь оставить
    summary = truncate_text(summary, 512)

    # 1) режем по первому <h3> -> всё до первого заголовка
    intro_html = re.split(r'<h3>', description_html, maxsplit=1)[0]

    # 2) чистим HTML и форматируем
    intro_clean = clean_html_text(intro_html)

    # 3) чуть режем, чтобы не упереться в лимит (можно увеличить/уменьшить)
    intro_clean = truncate_text(intro_clean, 1500)

    result = {
        "article_id": str(article_id),        
        "external_id": str(article_id), 
        "title": full_article.get("article_title", "No title"),
        "description": intro_clean,                  
        "description_full": description_html,       
        "image": full_article.get("article_image", ""),
        "date": full_article.get("article_date", ""),
        "url": f"{BASE_URL}/news/article/{article_id}",
    }
    
    print(f"✅ Готова карточка: {result['title']}")
    return result