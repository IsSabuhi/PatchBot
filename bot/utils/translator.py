import os
import aiohttp
import asyncio

PROXY_URL = os.getenv("PROXY_URL", "http://127.0.0.1:10808")

async def translate_to_ru(text: str) -> str:
    """Перевод через Google Translate API с прокси"""
    if not text or len(text.strip()) == 0:
        return text
    
    try:
        # Обрезаем текст
        text_to_translate = text[:2000] if len(text) > 2000 else text
        
        # Используем прокси
        proxy = PROXY_URL
        
        # Формируем запрос к Google Translate
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "ru",
            "dt": "t",
            "q": text_to_translate
        }
        
        # Настраиваем коннектор с прокси
        connector = aiohttp.TCPConnector()
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url, 
                params=params, 
                proxy=proxy,  # Важно: указываем прокси здесь!
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    translated = ''.join([part[0] for part in data[0]])
                    return translated
                else:
                    print(f"❌ Translate HTTP {response.status} (proxy={proxy})")
                    return text
    except Exception as e:
        print(f"❌ Ошибка перевода (proxy={PROXY_URL}): {type(e).__name__}: {e}")
        return text