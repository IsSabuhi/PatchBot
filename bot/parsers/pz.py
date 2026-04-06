from bs4 import BeautifulSoup
from typing import Optional, Dict
import aiohttp

BASE_URL = "https://projectzomboid.com"
NEWS_URL = f"{BASE_URL}/blog/news/"

async def fetch_html(url: str) -> Optional[str]:
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=15) as resp:
            if resp.status != 200:
                print("❌ PZ HTTP", resp.status, url)
                return None
            return await resp.text()

async def get_latest_article_pz() -> Optional[Dict]:
    index_html = await fetch_html(NEWS_URL)
    if not index_html:
        return None

    index_soup = BeautifulSoup(index_html, "lxml")

    article_link = None
    for a in index_soup.find_all("a", href=True):
        href = a["href"]
        if "/blog/news/" in href and href.count("/") >= 5:
            article_link = href
            break

    if not article_link:
        print("❌ PZ: не нашёл ссылку на новость")
        return None

    article_url = article_link if article_link.startswith("http") else BASE_URL + article_link
    external_id = article_url.rstrip("/").split("/")[-1]

    article_html = await fetch_html(article_url)
    if not article_html:
        return None

    soup = BeautifulSoup(article_html, "lxml")

    # Заголовок
    h1 = soup.find("h1", class_="c-header--2-tertiary") or soup.find("h1")
    title = h1.get_text(strip=True) if h1 else external_id

    # Дата
    date_text = ""
    date_div = soup.find("div", class_="published-date")
    if date_div:
        date_text = date_div.get_text(strip=True)

    # Картинка
    image = ""
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        image = og_img["content"]

    # Основной контент: div.c-post--content
    content_div = soup.find("div", class_="c-post--content")
    if not content_div:
        print("⚠️ PZ: не найден div.c-post--content, вернём только заголовок")
        return {
            "external_id": external_id,
            "title": title,
            "description": "",
            "description_full": "",
            "image": image,
            "date": date_text,
            "url": article_url,
        }

    inner = content_div.find("div") or content_div
    paragraphs = inner.find_all("p")
    intro_text = ""
    if paragraphs:
        intro_text = "\n\n".join(p.get_text(" ", strip=True) for p in paragraphs[:2])

    full_html = "".join(str(child) for child in inner.children)

    return {
        "external_id": external_id,
        "title": title,
        "description": intro_text,
        "description_full": full_html,   
        "image": image,
        "date": date_text,
        "url": article_url,
    }